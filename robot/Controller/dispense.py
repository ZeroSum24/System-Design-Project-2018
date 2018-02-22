#!/usr/bin/env python3

from Controller import slave, incoming

slave.dump(1)
if incoming.get():
    slave.dump(2)
    if incoming.get():
        slave.stop(3)
        if incoming.get():
            slave.dump(4)
            if incoming.get():
                slave.dump(5)
