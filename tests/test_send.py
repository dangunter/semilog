# -*- coding: utf-8 -*-
"""
Tests for send module
"""
import pytest
import time
from semilog import send

def test_subject():
    s = send.Subject()
    assert len(s.observers) == 1

def test_configure():
    s = send.Subject({})
    s.configure({})
    assert len(s.observers) == 0
    pytest.raises(TypeError, s.configure, None)

def test_event():
    s = send.Subject({})
    s.event('x', 'dumb')
    s.event('x', 'dumb', val=[1, 3])
    s.event('i', 'hi', val={1:3})

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

class Pokey(send.Observer):
    def __init__(self, sec):
        send.Observer.__init__(self)
        self.sec = sec

    def event(self, event):
        time.sleep(self.sec)