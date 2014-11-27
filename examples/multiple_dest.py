#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example of logging to multiple destinations
"""
__author__ = 'Dan Gunter <dkgunter@lbl.gov>'

from semilog.semilog import Subject, TextStream

if __name__ == '__main__':
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

