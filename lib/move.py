"""Wrapper library for moving the ev3"""

import threading
from functools import wraps
from thread_decorator import thread
from enum import Enum
from collections import namedtuple

WHEEL_CIRCUM = 1

Directions = Enum('Directions', 'FORWARD BACKWARD LEFT RIGHT')

class GenericMovement:

    # Motor objects by location on the chassis
    motors = namedtuple('motors', 'front back left right')(
        None, # Front
        None, # Back
        None, # Left
        None  # Right
    )

    # TODO: Tune these to normalise the direction of the motors
    scalers = namedtuple('scalers', 'front back left right')(
        1, # Front
        1, # Back
        1, # Left
        1  # Right
    )

    def _stop_all_motors(self):
        # Stop everything
        pass

class StraightLineMovement(GenericMovement):
    """Move in a straight line for a specfic distance

       Subclasses should define self.drive and self.rudder, self.drive should
       contain the motors that will be used to move the robot, self.rudder
       should contain the motors for course correction. Subclasses should also
       override calc_expected_ticks and course_correction. Finally setting any
       of the modifier parameters to -1 reverses the direction of the relavent
       motor"""

    modifiers = namedtuple('modifiers', 'front back left right')(
        1,
        1,
        1,
        1
    )
    
    ## Override These Methods ##
    def calc_expected_ticks(self, dist):
        pass

    def course_correction(self, sensors):
        # Should be non-blocking, use the motors in self.rudder
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
            self.drive = ['left', 'right']
            self.rudder = ['front', 'back']
        elif direction is Directions.LEFT or direction is Directions.RIGHT:
            self.drive = ['front', 'back']
            self.rudder = ['left', 'right']
        else:
            raise ValueError('Incompatible Direction for AxisMovement: {!r}'.format(direction))
        
        if direction is Directions.BACKWARD or direction is Directions.LEFT:
            self.modifier = -1

    def calc_expected_ticks(self, dist):
        # This underestimates the number of ticks needed e.g 5.9 ticks in
        # reality will give 5 with this. Coupled with the control loop's
        # tendency to overshoot however I think this could be reasonably
        # accurate, tests will have to confirm that however
        return dist // WHEEL_CIRCUM

forward  = AxisMovement(Directions.FORWARD)
backward = AxisMovement(Directions.BACKWARD)
left     = AxisMovement(Directions.LEFT)
right    = AxisMovement(Directions.RIGHT)

'''class RotationalMovement(GenericMovement):
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
'''
