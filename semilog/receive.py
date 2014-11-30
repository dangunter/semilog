# -*- coding: utf-8 -*-
"""
Receive logs
"""
__author__ = 'Dan Gunter <dkgunter@lbl.gov>'
__date__ = '2014-11-27'

import threading
import zmq
from .const import DEFAULT_PORT
from . import NullSubject
from .shared import registry

_log = registry.get('internal', NullSubject())

class Server(object):

    def __init__(self, cb, host, port=DEFAULT_PORT, json=True, text=False):
        url = "tcp://{}:{:d}".format(host, port)
        _log.event('i', 'server.connect', url=url)
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.PULL)
        self.socket.bind(url)
        if json:
            self._recv = self.socket.recv_json
        elif text:
            self._recv = self.socket.recv_string
        else:
            self._recv = self.socket.recv_pyobj
        self.cb = cb
        self._done, self._done_mtx = False, threading.Lock()
        self.thread = None

    def start(self):
        """Start running server in a thread."""
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def stop(self, timeout=5):
        """Stop running server thread.
        Does nothing if the thread is not started.

        Args:
            timeout (int): Timeout in seconds to join thread
        Return:
            True if thread is/was stopped, False otherwise
        """
        if self.thread is None or self.is_done():
            return True
        self.is_done(True)
        self.thread.join(timeout)
        self.thread = None

    def is_done(self, value=None):
        """Thread-safe boolean attribute, to stop the loop."""
        with self._done_mtx:
            if value is not None:
                self._done = value
            d = self._done
        return d

    def run(self):
        while True:  # repeat/until loop
            if self.socket.poll(100):
                self.cb(self._recv())
            if self.is_done():
                break

