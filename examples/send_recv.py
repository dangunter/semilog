"""
Example of sender/receiver
"""
__author__ = 'Dan Gunter <dkgunter@lbl.gov>'
__date__ = '2014-11-28'

import threading
import time
from semilog import send, receive

_log = send.Subject()  # internal logging

count = 0

def got_message(msg):
    global count
    print("Got message: {}".format(msg))
    count += 1

def main():
    # create sender
    sender = send.Subject({})
    host, port = '127.0.0.1', 9999
    # add 3 observers (clients of remote receiver)
    sender.observers = {
        'send{:d}'.format(i): send.Remote(host=host, port=port)
        for i in range(3)}

    # create receiver
    server = receive.Server(got_message, host=host, port=port)
    _log.event('i', 'server.start', host=host, port=port)
    server.start()

    # send some messages
    n = 5
    _log.event('i', "sender.start", n=n)
    for i in range(n):
        sender.event('i', 'hello', i=i)
    _log.event('i', "sender.done", n=n, status=0)

    # wait for messages to be processed
    while count < (n * 3):
        time.sleep(0.1)

    # stop the receiver
    _log.event('i', 'server.stop', timeout=5)
    server.stop()
    _log.event('i', 'server.done', status=0)

    return 0

if __name__ == '__main__':
    main()