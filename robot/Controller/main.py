#!/usr/bin/env python3

from Controller import slave, incoming
from queue import Empty

while True:
    print(1)
    slave.reverse('Robot')
    print(2)
    try:
        print(3)
        result = incoming.get_nowait()
        print(4)
    except Empty:
        print(5)
    else:
        print(6)
        print(result)
