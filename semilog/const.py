"""
Constants
"""
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

DEFAULT_PORT = 9000  # Listen port for socket messages

