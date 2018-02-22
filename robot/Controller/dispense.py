#!/usr/bin/env python3

from Controller import slave, incomming

import dispenser

slave.dump(1)
if incomming.get():
    slave.dump(2)
    if incomming.get():
        slave.stop(3)
        if incomming.get():
            slave.dump(4)
            if incomming.get():
                slave.dump(5)
