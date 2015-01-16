# -*- coding: utf-8 -*-
"""
Semi-structured logging library.

A semi-structured log is essentially a Python dictionary, serialized.

Design goals are minimal code, maximum flexibility, useful functionality.

See package README.md for usage examples.
"""

from datetime import datetime
import json
from six.moves import cPickle as pickle
from collections import deque
import re
import six
import sys
import syslog
import threading
import time
import types
import zmq
from semilog import const # import Keys, Severity, MAX_SEVERITY, DEFAULT_PORT

class Subject(object):
    """Subject role in the observer pattern.

    Events are created on a subject with event(). If you don't want to pass
    the severity level as a letter-code, you can also use a method name equal
    to the lowercased valuefor the corresponding severity in const.Levelname.
    So, e.g., `event('i', 'foo')` can be also written as `info('foo')`.

    All observers attached to a subject will be asked to `accept()` each event and,
    if that returns true, receive it through `event()`.
    """
    default_severity = 'I'  # of generated events
    default_fmt = "{level} {isotime} {event}: {kvp}"
    default_config = {
        const.Keys.obs: {'default': 'Stream("{level} {isotime} {event}: {kvp}")'}
    }
    MAX_STORED = 100  # max. num events buffered async.

    def __init__(self, config=None, async=False):
        """Create new instance.

        Args:
            config (dict): Configuration (see `configure()` method)
            async (bool): If true, send events from a separate thread to
                          avoid blocking the caller.
        """
        self.observers = {}
        if config is None:
            config = self.default_config
        self.configure(config)
        self._add_sugar()
        if async:
            # init for async. sending thread
            self._q = deque(maxlen=self.MAX_STORED)
            self._thr = threading.Thread(target=self._send_events, daemon=True)
            self._thr.start()
        else:
            self._q = None  # use as flag

    def configure(self, config):
        """Configure the subject.

         Args:
             config (dict): Has the following keys:
                  - observers: Mapping or list of Observer instances
        """
        if not hasattr(config, 'items'):
            raise TypeError('configure: dict argument required')
        observers = config.get(const.Keys.obs, None)
        if observers:
            items =(observers.items()
                if hasattr(observers, 'items')  # dict
                else enumerate(observers, 1))   # list
            for obs_name, obs in items:
                if isinstance(obs, six.string_types):
                    obs = eval(obs)
                self.observers[obs_name] = obs

    def event(self, severity, name, **mapping):
        """Log an event.

        Args:
            severity (str): Letter code for severity
            name (str): Name of event
            mapping (dict): Other key/value pairs for event
        """
        K = const.Keys
        t = time.time()
        mapping[K.ts] = t
        mapping[K.event] = name
        mapping[K.lvl] = severity[0].upper()
        for name, obs in self.observers.items():
            if obs.accept(mapping):
                mcopy = mapping.copy()  # allows observer to muck w/mapping
                if self._q is not None:
                    self._q.append((obs, mcopy))
                else:
                    obs.event(mcopy)

    def qlen(self):
        """Number of queued messages."""
        if self._q is None:
            return 0
        return len(self._q)

    def drain(self, timeout=10):
        """Wait for queue to drain.

        Args:
            timeout (float): Timeout in seconds
        """
        t = time.time()
        while self.qlen() > 0:
            time.sleep(0.1)
            if time.time() - t > timeout:
                return False
        return True

    def _send_events(self):
        """Send events from queue forever.
        Intended to run in a separate thread.
        """
        while True:
            while len(self._q) > 0:
                obs, mapping = self._q[0]
                obs.event(mapping)
                # only pop after event, so empty queue means truly finished
                self._q.popleft()
            time.sleep(0.1)  # pause for new data

    def _add_sugar(self):
        """Add syntax sugar methods, one for each const.Levelname, to Subject."""
        for sev, lvl in const.Levelname.items():
            sugar = lambda self, n, __sev=sev, **m: self.event(__sev, n, **m)
            setattr(self, lvl.lower(), types.MethodType(sugar, self))


class NullSubject(object):
    """Subject that does nothing."""
    def __init__(self, **kw):
        pass

    def event(self, *args, **kw):
        pass

class Observer(object):
    """Base class for observer role in the observer pattern.

    See also: `Subject` class
    """

    default_severity = 'I'  # of accepted events

    def __init__(self, severity=default_severity):
        if isinstance(severity, int):
            self.accept_severity = max(severity, 0)
        else:
            self.accept_severity = const.Severity[severity.upper()]

    def accept(self, mapping):
        s = mapping[const.Keys.severity]
        return const.Severity.get(s, const.MAX_SEVERITY) <= self.accept_severity

    def event(self, mapping):
        pass

class TextFormatter(object):
    """Format an event as text.
    """

    derived_values = ['isotime', 'level']
    derived_shadow = {'isotime': const.Keys.ts, 'level': const.Keys.lvl}
    KVP_SEP, KV_SEP = ' ', '='
    SEV_NAMES = const.Levelname

    def __init__(self, format_str):
        """Create new formatter.

        Args:
           format_str (str): Format string, using '{keyword}'-style placeholders.
        """
        self.format_str = format_str
        self.derivations = {}
        self.fields = set(re.findall("\{(\w.*?)\}", format_str))
        for dv in self.derived_values:
            if dv in self.fields:
                self.derivations[dv] = getattr(self, 'format_' + dv)
        self._kvp = 'kvp' in self.fields

    def add_kvp(self, m):
        """Add key-value pairs to mapping."""
        pairs = []
        for k, v in m.items():
            if k not in self.fields:
                if k == const.Keys.ts:
                    v = '{:.6f}'.format(v)
                elif k == const.Keys.lvl:
                    v = self.SEV_NAMES[v]
                if isinstance(v, six.string_types):
                    if ' ' in v or '\t' in v:
                        v = '"' + v.replace('"', '\\"') + '"'
                pairs.append((k, v))
        m['kvp'] = self.KVP_SEP.join(['{}{}{}'.format(k, self.KV_SEP, v)
                                      for k, v in pairs])

    def format_event(self, mapping):
        for key, func in self.derivations.items():
            func(mapping)
            if key in self.derived_shadow:  # remove 'shadowed' value
                del mapping[self.derived_shadow[key]]
        if self._kvp:
            self.add_kvp(mapping)
        return self.format_str.format(**mapping)

    def format_isotime(self, m):
        m['isotime'] = datetime.fromtimestamp(m[const.Keys.ts]).isoformat()

    def format_level(self, m):
        m['level'] = self.SEV_NAMES[m[const.Keys.lvl]]


class Stream(Observer):
    """Write events as JSON or pickled objects to a stream.
    """

    json_format = True  # if False, use pickle

    def __init__(self, fmt=None, stream=sys.stderr, **kwargs):
        """Create new stream.

        Default format is JSON, also available is Python pickle.

        Args:
            fmt (str): If not None, use format with `TextFormatter`
            stream (file): Object with `write()` method
            kwargs (dict): Keywords for parent class
        """
        Observer.__init__(self, **kwargs)
        self.stream = stream
        if fmt is not None:
            self._fmt = TextFormatter(fmt)
            self._dump = self._dump_text
        elif self.json_format:
            self._dump = self._dump_json
        else:
            self._dump = pickle.dump

    def _dump_text(self, mapping, stream):
        stream.write(self._fmt.format_event(mapping) + const.REC_SEP)

    def _dump_json(self, mapping, stream):
        json.dump(mapping, self.stream)
        stream.write(const.REC_SEP)

    def event(self, mapping):
        self._dump(mapping, self.stream)
        self.stream.flush()

class Remote(Observer):
    """Send events to a remote receiver.
    """

    json_format = True  # if False (and no format), use pickle

    _context = None  # internal zmq state

    def __init__(self, host, port=const.DEFAULT_PORT, fmt=None, **kwargs):
        """Create new stream.

        Default format is JSON, also available is Python pickle or text.

        Args:
            host (str): Remote host TCP/IP address
            port (int): Remote port
            fmt (str): If not None, use format with `TextFormatter`
            stream (file): Object with `write()` method
            kwargs (dict): Keywords for parent class
        """
        Observer.__init__(self, **kwargs)
        url = "tcp://{}:{:d}".format(host, port)
        if self._context is None:
            self._context = zmq.Context()
        self.socket = self._context.socket(zmq.PUSH)
        self.socket.connect(url)
        if fmt is not None:
            self._fmt, self._send = TextFormatter(fmt), self._send_text
        elif self.json_format:
            self._send = self.socket.send_json
        else:
            self._send = self.socket.send_pyobj

    def _send_text(self, mapping):
        s = self._fmt.format_event(mapping) + const.REC_SEP
        self.socket.send_string(s)

    def event(self, mapping):
        self._send(mapping)


class Syslog(Observer):
    """Send events to Unix syslog.
    """
    def __init__(self, facility, fmt="{isotime} {kvp}", options=0, **kwargs):
        """Create new syslogger.

        Args:
            facility (int): The syslog module facility (LOG_KERN, LOG_USER, ..)
                            that will be used for all events.
            fmt (str): Text Format for messages. If None, use JSON
            options (int): Value for `logoption` argument to syslog.openlog()
            kwargs (dict): Keywords passed to Observer
        """
        Observer.__init__(self, **kwargs)
        self.syslog = syslog.openlog(facility=facility, logoption=options)
        self._fmt = TextFormatter(fmt)

    def event(self, mapping):
        msg = self._fmt.format_event(mapping)
        sev = mapping[const.Keys.severity]
        priority = const.Priority.get(sev, syslog.LOG_NOTICE)
        self.syslog.syslog(priority, msg)
