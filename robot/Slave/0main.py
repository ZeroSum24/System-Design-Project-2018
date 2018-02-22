#!/usr/bin/env python3

from Slave import controller, incomming
from queue import Empty
from dispenser import dump

while True:
    try:
        slot = incoming.get_nowait()
    except Empty:
        pass
    else:
        for slot in slots:
            dump(slot)
        controller.dumped()
