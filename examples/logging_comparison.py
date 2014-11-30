"""
Compare with standard Python logging
"""
import logging
import time
import semilog

def main():
    # logging: init a log to stderr
    plog = logging.getLogger("mine")
    plog.setLevel(logging.INFO)
    hnd = logging.StreamHandler()
    fmtr = logging.Formatter("%(levelname)s %(asctime)s %(message)s")
    hnd.setFormatter(fmtr)
    plog.addHandler(hnd)
    # semilog: init a log to stderr
    text_fmt = "{level} {isotime} {event}: {kvp}"
    slog = semilog.Subject({'observers': [semilog.Stream(text_fmt)]})
    # write messages
    for i in range(5):
        plog.info("{e}: i={i}".format(e="hello", i=i))
        slog.event('i', 'hello', i=i)
    # drop old dest; set new one to /dev/null
    # logging
    plog.removeHandler(hnd)
    hnd = logging.FileHandler("/dev/null")
    hnd.setFormatter(fmtr)
    plog.addHandler(hnd)
    # semilog
    slog.observers = {
        'devnull': semilog.Stream(text_fmt, stream=open("/dev/null", "a"))
    }
    # run a timing test
    times = {}
    n = 10000
    i = 0
    t0 = time.time()
    while i < n:
        plog.info("{e}: i={i}".format(e="hello", i=i))
        i += 1
    times['logging'] = time.time() - t0
    i = 0
    t0 = time.time()
    while i < n:
        slog.event('i', 'hello', i=i)
        i += 1
    times['semilog'] = time.time() - t0
    print("Times for {:d} events to /dev/null:\n{}".format(n, times))

if __name__ == '__main__':
    main()