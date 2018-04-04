#!/usr/bin/env python3

# This file is probably never used

class Instruction():
    pass

class Report(Instruction):
    def __init__(self, where):
        Instruction.__init__(self)
        self.where = where
    def __repr__(self):
        return 'At {}'.format(self.where)

class Move(Instruction):
    def __init__(self, dist, tolerance):
        Instruction.__init__(self)
        self.dist = dist
        self.tolerance = tolerance
    def __repr__(self):
        return 'Move {}'.format(self.dist)

class Rotate(Instruction):
    def __init__(self, angle, tolerance):
        Instruction.__init__(self)
        self.angle = angle
        self.tolerance = tolerance
    def __repr__(self):
        return 'Rotate {}'.format(self.angle)

class ToDesk(Instruction):
    def __init__(self, is_left, angle=90):
        Instruction.__init__(self)
        self.is_left = is_left
        self.angle = angle
    def __repr__(self):
        return 'Go to desk on left' if self.is_left else 'Go to desk on right'

class FromDesk(Instruction):
    def __init__(self, is_left, angle=90):
        Instruction.__init__(self)
        self.is_left = is_left
        self.angle = angle
    def __repr__(self):
        return 'Go from desk on left' if self.is_left else 'Go from desk on right'

class Dump(Instruction):
    def __init__(self, slots):
        Instruction.__init__(self)
        self.slots = slots
    def __repr__(self):
        return 'Dump Slot(s) {} '.format(self.slots)
