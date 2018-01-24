"""Wrapper library for moving the ev3"""

import threading
from functools import wraps
from thread_decorator import thread
from enum import Enum

Directions = Enum('Directions', 'FORWARD BACKWARD LEFT RIGHT')

class GenericMovement:

    # Motor objects by location on the chassis
    _front = None
    _back  = None
    _left  = None
    _right = None

    '''
    # Override this
    def calc_expected_ticks(self, motion):
        pass

    def _zero_ododmeter(self):
        # Odometer should start counting from 1
        pass

    def _read_odometer(self):
        # Read the current value of the odometer
        pass

    def _run_motors(self):
        # Run applicable motors for 1 second, don't block
        pass

    def _stop_all_motors(self):
        # Stop everything
        pass
    
    @thread
    def __call__(self, dist):
        # Reset the odometer
        self._zero_odometer()
        # Calculate how far to go
        ticks = self.calc_expected_ticks(self, dist)
        ticks_traveled = 0
        # Keep moving until we reach the destination
        while ticks < ticks_traveled:
            # Run the motors for a bit
            self._run_motors()
            # Poll while any motor is running
            while any(map(lamda m: m.state == ["running"], self._motors)):
                # Calculate how far we've gone
                ticks_traveled = self._read_odometer()
                # If we made it stop
                if ticks_traveled >= ticks:
                    self._stop_all_motors()
                    break
'''

class AxisMovement(GenericMovement):
    def __init__(self, direction)

class RotationalMovement(GenericMovement):
    def calc_expected_ticks(self, deg):
        # Convert degrees of rotation into wheel ticks
        pass

# Add the relavent motors to these

# Movement along axis
forward = AxisMovement([])
backward = AxisMovement([])
left = AxisMovement([])
right = AxisMovement([])

# These may need a different class
# Diagonals
front_left = AxisMovement([])
front_right = AxisMovement([])
back_left = AxisMovement([])
back_right = AxisMovement([])

# Rotation
rotate = RotationalMovement([])
