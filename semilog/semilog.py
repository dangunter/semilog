# -*- coding: utf-8 -*-
"""
Semi-structured logging library.

A semi-structured log is essentially a Python dictionary, serialized.

Design goals are minimal code, maximum flexibility, useful functionality.

See package README.md for usage examples.
"""
__author__ = "Dan Gunter <dkgunter@lbl.gov>"
__created__ = "2014-11-26"
__version__ = '0.0.1'

from datetime import datetime

try:
    import cPickle as pickle
except ImportError:
    import pickle
import re

try:
    import cStringIO as cStringIO
except ImportError:
    import StringIO
import socket
import struct
import sys
import time

# Special keys
class Keys(object):
    obs = observers = 'observers'  # for Subject.configure()
    ts = timestamp = 'ts'
    event = 'event'
    lvl = severity = 'severity'

MAX_SEVERITY = 99  # anything higher will be ignored 

# Letter codes for message severity level
Severity = {
    'F': 0,  # Fatal
    'E': 1,  # Error
    'W': 2,  # Warning
    'I': 3,  # Info
    'D': 4,  # Debug
    'T': 5,  # Trace
}

class Subject(object):
    """Subject role in the observer pattern.

    Events are created on a subject with event().

    All observers attached to a subject will be asked to accept() each event and,
    if that returns true, receive it through event().
    """
    default_severity = 'I'  # of generated events
    default_config = {
        Keys.obs: {'default': 'TextStream("{level} {isotime} {event}: {kvp}")'}
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
                if isinstance(obs, basestring):
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

class Observer(object):
    """Base class for observer role in the observer pattern.

    See also: `Subject` class
    """

    default_severity = 'I'  # of accepted events

    def __init__(self, severity):
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

class TextFormatter(Observer):
    """Format an event as text.
    """

    derived_values = ['isotime', 'kvp', 'level']
    KVP_SEP, KV_SEP = ' ', '='
    SEV_NAMES = {'F': 'FATAL', 'E': 'ERROR', 'W': 'WARNING', 'I': 'INFO',
                 'D': 'DEBUG', 'T': 'TRACE'}

    def __init__(self, format, severity=None):
        """Create new formatter.

        Args:
           format (str): Format string, using '{keyword}'-style placeholders.
           severity (str): Accepted severity, passed up to parent class.
        """
        Observer.__init__(self, severity)
        self.format = format
        self.derivations = {}
        self.fields = set(re.findall("\{(\w.*?)\}", format))
        for dv in self.derived_values:
            if dv in self.fields:
                self.derivations[dv] = getattr(self, 'format_' + dv)

    def event(self, mapping):
        for key, func in self.derivations.items():
            mapping[key] = func(mapping)
        return self.format.format(**mapping)

    def format_isotime(self, m):
        """Replace timestamp with ISO8601 string."""
        ts = m[Keys.ts]
        del m[Keys.ts]
        return datetime.fromtimestamp(ts).isoformat()

    def format_kvp(self, m):
        pairs = []
        for k, v in m.items():
            if k not in self.fields:
                if k == Keys.ts:
                    v = '{:.6f}'.format(v)
                elif k == Keys.lvl:
                    v = self.SEV_NAMES[v]
                if isinstance(v, basestring):
                    if ' ' in v or '\t' in v:
                        v = '"' + v.replace('"', '\\"') + '"'
                pairs.append((k, v))
        return self.KVP_SEP.join(['{}{}{}'.format(k, self.KV_SEP, v)
                                  for k, v in pairs])

    def format_level(self, m):
        return self.SEV_NAMES[m[Keys.lvl]]


class TextStream(TextFormatter):
    """Write formatted text events to a stream.
    """

    REC_SEP = '\n'

    def __init__(self, format, stream=sys.stderr, **kwargs):
        """Create new text stream.

        Args:
            format (str): see `TextFormatter`
            stream (file): Object with `write()` method
            kwargs (dict): Keywords for parent class
        """
        TextFormatter.__init__(self, format, **kwargs)
        self.stream = stream

    def event(self, mapping):
        self.stream.write(TextFormatter.event(self, mapping) + self.REC_SEP)

class PickleStream(Observer):
    """Write pickled events to a stream.
    """

    default_protocol = 1  # for pickle's 'protocol' argument

    def __init__(self, stream=sys.stderr, protocol=None, severity=None):
        Observer.__init__(self, severity)
        self.protocol = protocol or self.default_protocol
        self.pickler = pickle.Pickler(stream, protocol=self.protocol)

    def event(self, mapping):
        self.pickler.dump(mapping)


class PickleSocket(PickleStream):
    """Write pickled events to a TCP/UDP socket.

    Message format is 4-byte length and `PickleStream` pickled message.
    """

    def __init__(self, host='127.0.0.1', port=9000, **kwargs):
        PickleStream.__init__(self, stream=self, **kwargs)
        self.sock = socket.socket()
        self.sock.connect((host, port))

    def write(self, data):
        sio = StringIO.StringIO()
        sio.write(data)
        s = sio.getvalue()
        self.sock.sendall(struct.pack(">L", len(s)) + s)

def __test():
    log = Subject()
    log.observers['default'].accept_severity = Severity['W']
    log.observers['errs'] = TextStream("**ERROR** {event} :: {text}", severity='E')
    # log.observers['p'] = PickleStream(severity)
    log.event('i', 'greeting', text='Hello, World!')
    log.event('e', 'alert', text='Look out, World!')

if __name__ == '__main__':
    __test()
