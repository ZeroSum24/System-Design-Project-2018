"""Decorator to push an arbitary callable onto a background thread"""

class GenericThread(threading.Thread):
    """Generic thread object, runs the passed target with arguments"""
    def __init__(self, target, args):
        threading.Thread.__init__(self)
        self._target = target
        self._args = args
    def run(self):
        self._target(*self._args)

def thread(func):
    """Pushes the decorated callable onto a background thread"""
    @wraps(func)
    def wrapper(*args):
        thread = GenericThread(func, args)
        return thread.start()
    return wrapper
