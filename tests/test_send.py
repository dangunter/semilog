# -*- coding: utf-8 -*-
"""
Tests for send module
"""
from io import StringIO
import time

import pytest

from semilog import send

def test_subject():
    s = send.Subject()
    assert len(s.observers) == 1
    s.event('I', 'hello', {'1+1': 2})
    s.event('W', 'bye', one_and_one=2, two_and_two='four')

def test_configure():
    s = send.Subject({})
    s.configure({})
    assert len(s.observers) == 0

def test_event():
    s = send.Subject({})
    s.event('x', 'dumb')
    s.event('x', 'dumb', val=[1, 3])
    s.event('i', 'hi', val={1:3})

def test_sugar():
    obs = Last()
    s = send.Subject({'observers': [obs]})
    s.info('yo')
    print(obs.last_event)
    assert obs.last_event['severity'] == 'I'
    s.error('doh')
    assert obs.last_event['severity'] == 'E'

def test_async():
    log = send.Subject({'observers':[Pokey(1)]}, async=True)
    t0 = time.time()
    for i in range(5):
        log.event('i', 'zoom-zoom')
    dt = time.time() - t0
    assert dt < 1.0

def test_drain():
    n, sec = 2, 0.25
    log = send.Subject({'observers': [Pokey(sec)]}, async=True)
    t0 = time.time()
    for i in range(n):
        log.event('i', 'zoom-zoom')
    log.drain()
    dt = time.time() - t0
    assert dt >= (n * sec)

def test_send_defaults():
    obs = Last(severity='T')
    s = send.Subject({'observers': [obs]})
    s.trace('hello', {'1 + 1': 2})
    e = obs.last_event
    assert e['event'] == 'hello'

class Pokey(send.Observer):
    def __init__(self, sec):
        send.Observer.__init__(self)
        self.sec = sec

    def event(self, event):
        time.sleep(self.sec)

class Last(send.Observer):
    def accept(self, m):
        return True
    def event(self, event):
        self.last_event = event

