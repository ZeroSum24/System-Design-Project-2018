# Coroutines need to be primed by calling .send(None) on the resulting
# object. This decorator automates that
def coroutine(func):
    def start(*args,**kwargs):
        cr = func(*args,**kwargs)
        cr.send(None)
        return cr
    return start
