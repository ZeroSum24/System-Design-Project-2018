#!/usr/bin/env python3

from Controller import slave, incoming
from queue import Empty

while True:
    print('Robot')
    slave.reverse('Robot')
    try:
        result = incomming.get_nowait()
    except Empty:
        pass
    else:
        print(result)
        
