"""Decorator to push an arbitary callable onto a background thread"""

import threading
from functools import wraps
import ctypes
from time import sleep

class ThreadKiller(Exception):
    def __init__(self):
        self.thrower = ThreadKiller.thrower

class ThreadDying(Exception):
    pass

def acknowledge(exception):
    """Raises a ThreadDying exception in a thread in responce to a recived
    ThreadKiller Exception"""
    
    # Only allow ThreadKiller to be acknowleged in this way
    if not isinstance(exception, ThreadKiller):
        return
    thrower = exception.thrower

    # Uses the Python C api to send an exception across the thread boundry
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(thrower), ctypes.py_object(ThreadDying))
    if res == 0:
        return
    elif res != 1:
        # If it returns > 1 we need to repair the damage done and try again
        # later
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thrower, 0)
        return

class GenericThread(threading.Thread):
    """Generic thread object, runs the passed target with arguments"""

    # Threads spawned with daemon = True don't count towards the main thread's
    # child count. This means if the main thread exits (normally or with an
    # execption) the interpreter will die immedatly and bring these threads down
    # with it.
    daemon = True

    # Set to False to make the thread immune to ThreadKiller
    stoppable = True

    def __init__(self, target, args, kwargs):
        threading.Thread.__init__(self)
        self._target = target
        self._args = args
        self._kwargs = kwargs

    # Run is called in a seperate thread when the object's start() method is
    # called
    def run(self):
        self._target(*self._args, **self._kwargs)

    # From https://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread-in-python#325528
    def _get_tid(self):
        """Get the current thread's tid (Caches due to the looping in stop)"""
        # If it's cached return it
        if hasattr(self, "_tid"):
            return self._tid

        # Or look it up
        for tid, tobj in threading._active.items():
            if tobj is self:
                self._tid = tid
                return tid
    
    def _raise_exc(self):
        """Raises a ThreadKiller exception in the thread, note this is blocked
        by system calls (sleep, io, network, etc...)"""

        # Uses the Python C api to send an exception across the thread boundry
        ThreadKiller.thrower = threading.get_ident()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self._get_tid()), ctypes.py_object(ThreadKiller))
        if res == 0:
            return
        elif res != 1:
            # If it returns > 1 we need to repair the damage done and try again
            # later
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self._get_tid()), 0)
            return

    def stop(self):
        """Loop _raise_exc until the thread dies"""
        # Exit instantly if this thread isn't stoppable
        if not self.stoppable:
            return
        # Kill the thread
        try:
            # Need to loop as threads are immune to exceptions during system calls
            while self.isAlive():
                # Small sleep so we don't bombard the thread with exceptions
                sleep(.1)
                self._raise_exc()
        # A RuntimeError can be raised if _raise_exc gets called after the
        # thread dies
        except RuntimeError:
            pass
        except ThreadDying:
            # ThreadDying can be thrown back by the killed thread to ask for
            # time to clean up before exiting
            pass

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
