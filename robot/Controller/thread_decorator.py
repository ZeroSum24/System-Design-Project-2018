"""Decorator to push an arbitary callable onto a background thread"""

import threading
from functools import wraps

class GenericThread(threading.Thread):
    """Generic thread object, runs the passed target with arguments"""

    # Threads spawned with daemon = True don't count towards the main thread's
    # child count. This means if the main thread exits (normally or with an
    # execption) the interpreter will die immedatly and bring these threads down
    # with it.
    daemon = True

    def __init__(self, target, args, kwargs):
        threading.Thread.__init__(self)
        self._target = target
        self._args = args
        self._kwargs = kwargs

    # Run is called in a seperate thread when the object's start() method is
    # called
    def run(self):
        self._target(*self._args, **self._kwargs)

# Decorators in python nearly implement the decorator pattern (See
# Wikipedia). A python decorator is a function that accepts a function as a
# parameter and returns a function, generally the returned function calls the
# original function as well as doing some background work. In this case the
# returned function when called will call the original function through the
# GenericThread class above then return the thread object created. The intention
# is for the thread object to be passed back to the caller so they can call
# .join() on it to make the function call blocking if desired
def thread(func):
    """Pushes the decorated callable onto a background thread"""
    # Prevents the decorator from corrupting the wrapped function's metadata
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Create a new thread to run the function
        thread = GenericThread(func, args, kwargs)
        # Run it
        thread.start()
        # Return it
        return thread
    return wrapper
