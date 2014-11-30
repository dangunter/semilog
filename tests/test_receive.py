# -*- coding: utf-8 -*-
"""
Tests for receive module
"""
import pytest
import threading
from semilog import receive

event_count = 0

@pytest.fixture(scope='module')
def server(request):
    srv = receive.Server(got_event, '127.0.0.1', port=9001)
    thr = threading.Thread(target=srv.run)
    thr.start()
    request.addfinalizer(lambda : thr.join())
    return srv

def test_server(server):
    global event_count
    event_count = 0
    assert server.is_done() == False
    server.is_done(True)
    assert server.is_done() == True
    assert event_count == 0

def got_event(e):
    global event_count
    event_count += 1

