"""
Integrated send/receive test
"""

import pytest
import threading
import time
from semilog import Server, Subject, Remote, Keys

localhost = '127.0.0.1'

events = []

@pytest.fixture
def server(request):
    global events
    events = []
    srv = Server(got_event, localhost)
    srv.start()
    def fin():
        srv.stop()
    request.addfinalizer(fin)
    return srv

@pytest.fixture
def client():
    log = Subject({'observers': [Remote(localhost)]})
    return log

def test_sr(client, server):
    client.event('i', 'hello', n=1)
    time.sleep(1)
    assert len(events) == 1
    e = events[0]
    assert e['n'] == 1
    assert e[Keys.event] == 'hello'

def got_event(e):
    events.append(e)

