#!/usr/bin/env python3

from Slave import controller, incoming
from queue import Empty
from dispenser import dump
import catcher

slots = []
while True:
    try:
        slots = incoming.get_nowait()
        print("slots")
        print(slots)
    except Empty:
        print("Empty")
        pass
    else:
        print(slots)
        for slot in slots:
            dump(slot)
        controller.dumped()
