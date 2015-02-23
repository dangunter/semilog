"""
Test scalability to many senders and a receiver
over localhost.
"""
__author__ = 'Dan Gunter <dkgunter@lbl.gov>'
__date__ = '2/21/15'

import argparse
import sys
import threading
import time

import semilog
from semilog import Server, Remote
from semilog.send import Observer # base class

class SyncSender(threading.Thread):
    def __init__(self, log ,n):
        self.n = n
        self.log = log
        threading.Thread.__init__(self)

    def run(self):
        i, n = 0, self.n
        while i < n:
            self.log.debug("SyncSender", i=i, action="run")
            i += 1

n_received = 0
def count(data):
    global n_received
    n_received += 1

def send_messages(n_senders, n_messages):
    server = Server(count, '127.0.0.1')
    server.start()
    config = {'observers': [Remote(host='127.0.0.1', severity='D')]}
    log = semilog.Subject(config=config)
    threads = [SyncSender(log, n_messages) for i in range(n_senders)]
    t0 = time.time()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    if n_received == n_senders * n_messages:
        t1 = time.time()
        server.stop()
    else:
        while n_received < n_senders * n_messages:
            time.sleep(.001)
        t1 = time.time()
        server.stop()
        print("Got all messages")
    return t1 - t0

def main():
    p = argparse.ArgumentParser()
    p.add_argument("num_senders", type=int)
    p.add_argument("num_messages", type=int)
    args = p.parse_args()
    assert args.num_senders > 0
    assert args.num_messages > 0
    s, m = args.num_senders, args.num_messages
    print("Sending {:d} messages from each of {:d} threads".format(m, s))
    print("Receiving the messages at localhost")
    print("...")
    sec = send_messages(s, m)
    print("Sent {:d} messages in {:f} seconds".format(s * m, sec))
    print()
    rate = int(1. * m / sec)
    print("Sender rate = {:d} messages/second".format(rate))
    delay = sec / m
    print("Sender time per message = {:f} ms".format(delay * 1000.))
    print()
    rate = int((s * m) / sec)
    print("Total rate = {:d} messages/second".format(rate))
    delay = sec / (s * m)
    print("Total time per message = {:f} ms".format(delay * 1000.))
    return 0

if __name__ == '__main__':
    sys.exit(main())
