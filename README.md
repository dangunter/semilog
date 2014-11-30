# semilog: Simple structured logging library for Python

A semi-structured log is essentially a Python dictionary, serialized.

Design goals are minimal code, maximum flexibility, useful functionality.

The library follows the subject/observer pattern to send logs to destinations.
The observers all have a 'severity' level that filters the logs that they
receive.

Logs can be easily sent to local streams (files or stdout/stderr) or to
remote ZeroMQ receivers. Built-in formats are user-specified text format,
JSON, and Python's pickle.

# Installation

* From source: `python setup.py install`
* COMING SOON: With pip: `pip install semilog`

Dependencies: see `requirements.txt`

## Tests

The tests are written using the *pytest* framework.
See http://pytest.org/ for details.

To run the tests (from the top level of the package):
    
    py.test tests
    
# Examples

Below are some examples of usage.

## Basic

A log object is an instance of `Subject`, with one or more `Observer` subclasses attached to it. By default, a `Stream` observer, logging to stderr with a text format, is added to a new Subject instance.

    from semilog import Subject
    log = Subject()  # adds default Stream observer
    log.event('i', 'hello', msg="Hello, world!")

## Multiple local destinations

Using the `configure()` method, or directly modifying the `observers` attribute of the Subject instance, you can add multiple log destinations. A severity filter is understood by the built-in Observers.

    from semilog import Subject, Stream
    log = Subject({})  # empty dict avoids default config
    logfile = open("/tmp/mylog", "a")
    fmt = "[{level}] {isotime} {event}: {msg}"
    log.configure({'observers': {
        # Log anything at warning and above to stderr
        'console': Stream(fmt=fmt, severity='W'),
        # Log everything including traces to the file
        'logfile': Stream(fmt=fmt, stream=logfile, severity='T')}})
    log.event('i', 'hello', msg="Hello, world!")  # only to file
    log.event('w', 'goodbye', msg="Later!")  # both

## Remote destinations

Logging to remote destinations requires both a sender and receiver. The sender is created by adding a `Remote` observer to a subject. Then a Server needs to be run on the same port (and expecting the same message format, JSON by default). The underlying networking, and formatting, is handled by the ZeroMQ library.

    from semilog import Subject, Remote, Server
    
    localhost = '127.0.0.1'
    count = 0
    
    # create sender
    sender = Subject({'observers': [Remote(localhost)]})
    # create and start receiver
    server = Server(lambda m: print("Got: {}".format(m)), host=localhost)
    server.start()
    # send some messages
    for i in range(5):
        sender.event('i', 'hello', i=i)
    # wait for messages to be processed
    while count < 5:
        time.sleep(0.1)
    # stop the receiver
    server.stop()

## Asynchronous logging

If you are worried about the logger blocking your application, you can use the `async` keyword to tell the Subject to buffer events and send them with a separate thread. This allows the `event()` calls to return immediately. The thread is a "daemon" thread, so it will be automatically killed when the main thread exits.

To show this in action, we can create a subclass of Observer that just sleeps every time it gets an event:

    import time
    from semilog import send
    class Pokey(send.Observer):
        def event(self, event):
            time.sleep(1)


Then we can simply add the `async=True` keyword to the Subject constructor, and see that 5 log messages do not wait 5 seconds to complete, but complete in well under a second.

    log = send.Subject({'observers':[Pokey()]}, async=True)
    t0 = time.time()
    for i in range(5):
        log.event('i', 'zoom-zoom')
    dt = time.time() - t0
    assert dt < 1.0

If you need to wait for all events to be processed, i.e. the queue to drain, then use the `drain()` method. To avoid hanging the application, a timeout of 10 seconds is the default; put a big number if you want to wait "forever".

    # wait 30 sec. for log 's queue to drain
    log.drain(30)
    # wait Carl Sagan-like times for the queue to drain
    log.drain(9e9)
    
# Contact

Help improve this software! Contributions are welcome, although subject to review for quality and adherence to the design goals (and if you don't like that, then just go fork it, man!).

Contact the author at <dkgunter@lbl.gov>.
