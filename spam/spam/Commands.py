#!/usr/bin/env python3

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

class Dump(Instruction):
    def __init__(self, slots, is_right):
        Instruction.__init__(self)
        self.slot = slots
        self.is_right = is_right
        self.turn = False
    def __repr__(self):
        direction = 'right' if self.is_right else 'left'
        turn = ' then turn around' if self.turn else ''
        return 'Dump Slot(s) {} to the {}{}'.format(self.slot, direction, turn)
