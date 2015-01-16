"""
Example of timing code
"""
__author__ = 'Dan Gunter <dkgunter@lbl.gov>'
__date__ = '2015-01-16'

import time
from semilog import timer, Subject, Stream

subject = Subject()
timer.default_log = subject.info

# Basic usage

@timer.time_fn
def somefunc(x, y):
    time.sleep(x * y)

# Advanced usage

n = 0
def next_customer():
    global n
    n += 1
    return n

subject.configure({'observers': {'dbg': Stream(severity='D', fmt=Subject.default_fmt)}})
dbglog = subject.debug

@timer.time_fn(timer=next_customer, log=dbglog)
def otherfunc(x, y):
    time.sleep(x * y)

# Can be used independently, too

def printit(event, funcname=None, sec=0, **kw):
    print("Function {}: {:.3f}".format(funcname, sec))
@timer.time_fn(log=printit)
def foofunc(x, y):
    time.sleep(x * y)

def main():
    for i in range(5):
        somefunc(2, 0.1)
    for i in range(5):
        otherfunc(2, 0.1)
    for i in range(5):
        foofunc(2, 0.1)

if __name__ == '__main__':
    main()
