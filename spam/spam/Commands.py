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
        self.is_desk = False
    def __repr__(self):
        if self.is_desk:
            return 'Move {} to desk'.format(self.dist)
        else:
            return 'Move {} to junction'.format(self.dist)

class Rotate(Instruction):
    def __init__(self, angle, tolerance):
        Instruction.__init__(self)
        self.angle = angle
        self.tolerance = tolerance
    def __repr__(self):
        return 'Rotate {}'.format(self.angle)

class Dump(Instruction):
    def __init__(self, slot):
        Instruction.__init__(self)
        self.slot = slot
    def __repr__(self):
        return 'Dump Slot {}'.format(self.slot)
