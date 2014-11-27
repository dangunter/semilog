# semilog: Simple structured logging library for Python

A semi-structured log is essentially a Python dictionary, serialized.

Design goals are minimal code, maximum flexibility, useful functionality.

## Basic usage

    from semilog import Subject
    log = Subject()  # adds default TextStream observer
    log.event('i', 'hello', msg="Hello, world!")

## Multiple destinations

    from semilog.semilog import Subject, TextStream

    log = Subject({})  # empty dict avoids default config

    logfile = open("/tmp/mylog", "a")
    fmt = "[{level}] {isotime} {event}: {msg}"

    log.configure({ 'observers': {
        # Log anything at warning and above to stderr
        'console': TextStream(fmt, severity='W'),
        # Log everything including traces to the file
        'logfile': TextStream(fmt, stream=logfile, severity='T')}})

    log.event('i', 'hello', msg="Hello, world!")  # only to file
    log.event('w', 'goodbye', msg="Later!")  # both
