# semilog: Simple structured logging library for Python

A semi-structured log is essentially a Python dictionary, serialized.

Design goals are minimal code, maximum flexibility, useful functionality.

The library follows the subject/observer pattern to send logs to destinations.
The observers all have a 'severity' level that filters the logs that they
receive.

Logs can be easily sent to local streams (files or stdout/stderr) or to
remote ZeroMQ receivers. Built-in formats are user-specified text format,
JSON, and Python's pickle.

# Installation

* From source: `python setup.py install`
* With pip: `pip install semilog`

Dependencies: see `requirements.txt`

# Examples

Below are some examples of usage.

## Basic

    from semilog import Subject
    log = Subject()  # adds default Stream observer
    log.event('i', 'hello', msg="Hello, world!")

## Multiple local destinations

    from semilog.semilog import Subject, Stream

    log = Subject({})  # empty dict avoids default config

    logfile = open("/tmp/mylog", "a")
    fmt = "[{level}] {isotime} {event}: {msg}"
    log.configure({'observers': {
        # Log anything at warning and above to stderr
        'console': Stream(fmt=fmt, severity='W'),
        # Log everything including traces to the file
        'logfile': Stream(fmt=fmt, stream=logfile, severity='T')}})

    log.event('i', 'hello', msg="Hello, world!")  # only to file
    log.event('w', 'goodbye', msg="Later!")  # both

## Remote destinations