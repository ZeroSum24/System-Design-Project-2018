"""Wrapper library for moving the ev3"""

import threading
from functools import wraps
from thread_decorator import thread
from enum import Enum

WHEEL_CIRCUM = 1

Directions = Enum('Directions', 'FORWARD BACKWARD LEFT RIGHT')

class GenericMovement:

    # Motor objects by location on the chassis
    front = None
    back  = None
    left  = None
    right = None

    def _stop_all_motors(self):
        # Stop everything
        pass

class StraightLineMovement(GenericMovement):

    ## Override These Methods ##
    def calc_expected_ticks(self, dist):
        pass

    def course_correction(self, sensors):
        # Should be non-blocking, should use the motors in self.rudder
        pass
    ## End Overrides ##

    def _zero_ododmeter(self):
        # Odometer should start counting from 1
        pass

    def _read_odometer(self):
        # Read the current value of the odometer
        pass

    def _run_motors(self):
        # Run the motors in self.drive for 1 second, don't block
        pass

    def _read_line_sensors(self):
        # Return a 2 tuple representing what the sensors can see
        pass

    @thread
    def __call__(self, dist):
        # Reset the odometer
        self._zero_odometer()
        # Calculate how far to go
        ticks = self.calc_expected_ticks(self, dist)
        ticks_traveled = 0
        # Keep moving until we reach the destination
        # Will tend to overshoot by strictly less than 2 rotations
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
                # Apply any course corrections
                sensor_output = self._read_line_sensors()
                self.course_correction(sensor_output)

class AxisMovement(StraightLineMovement):
    def __init__(self, direction):
        if direction is Directions.FORWARD or direction is Directions.BACKWARD:
            self.drive = [self.left, self.right]
            self.rudder = [self.front, self.back]
        elif direction is Directions.LEFT or direction is Directions.RIGHT:
            self.drive = [self.front, self.back]
            self.rudder = [self.left, self.right]
        else:
            raise ValueError('Incompatible Direction for AxisMovement: {!r}'.format(direction))

    def calc_expected_ticks(self, dist):
        # This underestimates the number of ticks needed e.g 5.9 ticks in
        # reality will give 5 with this. Coupled with the control loop's
        # tendency to overshoot however I think this could be reasonably
        # accurate, tests will have to confirm that however
        return dist // WHEEL_CIRCUM

    def course_correction(self, sensors):
        pass

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
