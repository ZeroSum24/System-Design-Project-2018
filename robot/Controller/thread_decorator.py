"""Decorator to push an arbitary callable onto a background thread"""

import threading
from functools import wraps

class GenericThread(threading.Thread):
    """Generic thread object, runs the passed target with arguments"""
    def __init__(self, target, args, kwargs):
        threading.Thread.__init__(self)
        self._target = target
        self._args = args
        self._kwargs = kwargs
    # Run is called in a seperate thread when the object's start() method is
    # called
    def run(self):
        self._target(*self._args, **self._kwargs)

# Decorator: use with @thread on a callable
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
