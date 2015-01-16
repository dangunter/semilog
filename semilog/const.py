"""
Constants
"""
import syslog

# Special keys
class Keys(object):
    obs = observers = 'observers'  # for Subject.configure()
    ts = timestamp = 'ts'
    event = 'event'
    lvl = severity = 'severity'

MAX_SEVERITY = 99  #: anything higher will be ignored

#: Letter codes for message severity level
Severity = {
    'F': 0,  # Fatal
    'E': 1,  # Error
    'W': 2,  # Warning
    'I': 3,  # Info
    'D': 4,  # Debug
    'T': 5,  # Trace
}

#: Names for message severity level
Levelname = {
    'F': 'FATAL',
    'E': 'ERROR',
    'W': 'WARNING',
    'I': 'INFO',
    'D': 'DEBUG',
    'T': 'TRACE'}

#: Map severity to syslog priorities
Priority = {
    'F': syslog.LOG_CRIT,
    'E': syslog.LOG_ERR,
    'W': syslog.LOG_WARNING,
    'I': syslog.LOG_INFO,
    'D': syslog.LOG_DEBUG,
    'T': syslog.LOG_DEBUG,
}

DEFAULT_PORT = 9000  #: Listen port for socket messages

REC_SEP = '\n'  #: Record separator, for formatted text and JSON
