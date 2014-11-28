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
import re
import six
import sys
import time
import zmq
from semilog.const import Keys, Severity, MAX_SEVERITY, DEFAULT_PORT

class Subject(object):
    """Subject role in the observer pattern.

    Events are created on a subject with event().

    All observers attached to a subject will be asked to accept() each event and,
    if that returns true, receive it through event().
    """
    default_severity = 'I'  # of generated events
    default_config = {
        Keys.obs: {'default': 'Stream("{level} {isotime} {event}: {kvp}")'}
    }

    def __init__(self, config=None):
        self.observers = {}
        if config is None:
            config = self.default_config
        self.configure(config)

    def configure(self, config):
        """Configure the subject.

         Args:
             config (dict): Has the following keys:
                  - observers: List of Observer instances
        """
        if Keys.obs in config:
            for obs_name, obs in config[Keys.obs].items():
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
        mapping[Keys.ts] = time.time()
        mapping[Keys.event] = name
        mapping[Keys.lvl] = severity[0].upper()
        for _, obs in self.observers.items():
            if obs.accept(mapping):
                obs.event(mapping.copy())

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

    def __init__(self, severity='I'):
        if isinstance(severity, int):
            self.accept_severity = max(severity, 0)
        else:
            s = severity or self.default_severity
            self.accept_severity = Severity[s.upper()]

    def accept(self, mapping):
        s = mapping[Keys.severity]
        return Severity.get(s, MAX_SEVERITY) <= self.accept_severity

    def event(self, mapping):
        pass

class TextFormatter(object):
    """Format an event as text.
    """

    derived_values = ['isotime', 'level']
    derived_shadow = {'isotime': Keys.ts, 'level': Keys.lvl}
    KVP_SEP, KV_SEP = ' ', '='
    SEV_NAMES = {'F': 'FATAL', 'E': 'ERROR', 'W': 'WARNING', 'I': 'INFO',
                 'D': 'DEBUG', 'T': 'TRACE'}

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
                if k == Keys.ts:
                    v = '{:.6f}'.format(v)
                elif k == Keys.lvl:
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
        m['isotime'] = datetime.fromtimestamp(m[Keys.ts]).isoformat()

    def format_level(self, m):
        m['level'] = self.SEV_NAMES[m[Keys.lvl]]


class Stream(Observer):
    """Write events as JSON or pickled objects to a stream.
    """

    json_format = True  # if False, use pickle

    REC_SEP = '\n'  # record separator, for formatted text and JSON

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
        stream.write(self._fmt.format_event(mapping) + self.REC_SEP)

    def _dump_json(self, mapping, stream):
        json.dump(mapping, self.stream)
        stream.write(self.REC_SEP)

    def event(self, mapping):
        self._dump(mapping, self.stream)
        self.stream.flush()

class Remote(Observer):
    """Send events to a remote receiver.
    """

    json_format = True  # if False (and no format), use pickle

    _context = None  # internal zmq state

    def __init__(self, host, port=DEFAULT_PORT, fmt=None, **kwargs):
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
            self._fmt, self._send = fmt, self._send_text
        elif self.json_format:
            self._send = self.socket.send_json
        else:
            self._send = self.socket.send_pyobj

    def _send_text(self, mapping):
        s = self._fmt.format_event(mapping) + self.REC_SEP
        self.socket.send_string(s)

    def event(self, mapping):
        self._send(mapping)


def __test():
    log = Subject()
    log.observers['default'].accept_severity = Severity['W']
    log.observers['errs'] = Stream(fmt="**ERROR** {event} :: {text}", severity='E')
    log.observers['json'] = Stream(severity='W')
    log.event('i', 'greeting', text='Hello, World!')
    log.event('e', 'alert', text='Look out, World!')

if __name__ == '__main__':
    __test()
