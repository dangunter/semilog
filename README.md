# semilog: Simple structured logging library for Python

A semi-structured log is essentially a Python dictionary, serialized.

Design goals are minimal code, maximum flexibility, useful functionality.

## Basic usage

    from semilog import Subject
    log = Subject()  # adds default TextStream observer
    log.event('i', 'hello', msg="Hello, world!")

