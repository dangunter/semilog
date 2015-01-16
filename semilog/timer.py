"""
Generate timings with a decorator.

See `examples/timings.py` for an example

Decorator code adapted from: https://github.com/mgedmin/profilehooks
"""
import time

default_log = None

def time_fn(fn=None, log=None, timer=None):
    """Wrap `fn` and log its execution time.

    Args:
        fn (function): Function to wrap
        log (function): Log method, with interface of Subject.info()
        timer (function): If present, called in place of `time.time` to get the
                          current time in seconds.
    """
    # Mode: Create decorator
    if fn is None:
        def decorator(fn):
            return time_fn(fn, log=log, timer=timer)
        return decorator

    # Mode: Be decorator
    if timer is None:
        timer = time.time
    fp = FuncTimer(fn, timer=timer, log=log)
    # Return a plain function. Cannot return fp or fp.__call__ directly
    # as that would break method definitions.
    def new_fn(*args, **kw):
        return fp(*args, **kw)
    new_fn.__doc__ = fn.__doc__
    new_fn.__name__ = fn.__name__
    new_fn.__dict__ = fn.__dict__
    new_fn.__module__ = fn.__module__

    return new_fn


class FuncTimer(object):
    """Class that performs the timings.
    """
    def __init__(self, fn, timer, log):
        self.fn = fn
        self.ncalls = 0
        self.totaltime = 0
        self.timer = timer
        self.log = log or default_log

    def __call__(self, *args, **kw):
        """Profile a single call to the function."""
        fn = self.fn
        timer = self.timer
        self.ncalls += 1
        try:
            start = timer()
            return fn(*args, **kw)
        finally:
            self.duration = timer() - start
            self.totaltime += self.duration
            self.log('time_fn', **self._info())

    def _info(self):
        result = {'funcname': self.fn.__name__,
                  'filename': self.fn.__code__.co_filename,
                  'lineno': self.fn.__code__.co_firstlineno,
                  'ncalls': self.ncalls,
                  'sec': self.duration,
                  'total_sec': self.totaltime}
        result['avg_sec'] = 0. if self.ncalls == 0 else \
            self.totaltime / self.ncalls
        return result
