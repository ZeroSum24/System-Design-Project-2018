"""Wrapper library for moving the ev3"""

from thread_decorator import thread
from enum import Enum
from collections import namedtuple
from os import path

import ev3dev.ev3 as ev3
from ev3dev.core import Motor

MOTOR_ROOT = '/sys/class/tacho-motor'

WHEEL_CIRCUM = 20

Directions = Enum('Directions', 'FORWARD BACKWARD LEFT RIGHT')

class GenericMovement:

    # Motor objects by location on the chassis
    motors = namedtuple('motors', 'front back left right')(
        ev3.LargeMotor('outD'), # Front
        ev3.LargeMotor('outA'), # Back
        ev3.LargeMotor('outB'), # Left
        ev3.LargeMotor('outC')  # Right
    )

    motor_files = { motors.front : path.join(MOTOR_ROOT, 'motor4', 'position'),
                    motors.back : path.join(MOTOR_ROOT, 'motor3', 'position'),
                    motors.left : path.join(MOTOR_ROOT, 'motor2', 'position'),
                    motors.right : path.join(MOTOR_ROOT, 'motor1', 'position') }

    scalers = { motors.front : -1,
                motors.back  :  1,
                motors.left  : -1,
                motors.right : -1 }

    modifiers = { motors.front : 1,
                  motors.back  : 1,
                  motors.left  : 1,
                  motors.right : 1 }

    def __init__(self):
        for motor in self.motors:
            motor.run_timed(speed_sp=1, time_sp=1)
            motor.stop(stop_action=Motor.STOP_ACTION_BRAKE)
            motor.reset()

    def _run_motor(self, motor):
        motor.run_forever(speed_sp=self.modifiers[motor]*self.scalers[motor]*500)

    def _stop_all_motors(self):
        for motor in self.motors:
            motor.stop(stop_action=Motor.STOP_ACTION_BRAKE)

class StraightLineMovement(GenericMovement):
    """Move in a straight line for a specfic distance

       Subclasses should define self.drive and self.rudder, self.drive should
       contain the motors that will be used to move the robot, self.rudder
       should contain the motors for course correction. Subclasses should also
       override calc_expected_ticks and course_correction. Finally setting any
       of the modifier parameters to -1 reverses the direction of the relavent
       motor"""

    ## Override These Methods ##
    def calc_expected_ticks(self, dist):
        pass

    def course_correction(self, sensors):
        # Should be non-blocking, use the motors in self.rudder
        pass

    def parse_odometer(self, readings):
        pass
    ## End Overrides ##

    def _zero_odometer(self):
        for motor in self.drive:
            motor.reset()

    def _read_odometer_base(self, motor):
        with open(self.motor_files[motor]) as file:
            return int(file.readline())

    def _read_odometer(self):
        return tuple(map(self._read_odometer_base, self.drive))

    def _run_motors(self):
        # Run the motors in self.drive for 1 second, don't block
        for motor in self.drive:
            self._run_motor(motor)

    def _read_line_sensors(self):
        # Return a 2 tuple representing what the sensors can see
        pass

    @thread
    def __call__(self, dist):
        self._zero_odometer()
        ticks = self.calc_expected_ticks(dist)
        traveled = 0
        self._run_motors()
        while traveled < ticks:
            while any(map(lambda m: m.state == ["running"], self.motors)):
                traveled = self.parse_odometer(self._read_odometer())
                if traveled >= ticks:
                    self._stop_all_motors()
                    break
# Course correction and distance measuring stuff
'''
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
            while any(map(lambda m: m.state == ["running"], self._motors)):
                # Calculate how far we've gone
                ticks_traveled = self._read_odometer()
                # If we made it stop
                if ticks_traveled >= ticks:
                    self._stop_all_motors()
                    break
                # Apply any course corrections
                sensor_output = self._read_line_sensors()
                self.course_correction(sensor_output)
'''

class AxisMovement(StraightLineMovement):
    def __init__(self, direction):
        StraightLineMovement.__init__(self)
        if direction is Directions.FORWARD or direction is Directions.BACKWARD:
            self.drive = [self.motors.left, self.motors.right]
            self.rudder = [self.motors.front, self.motors.back]
        elif direction is Directions.LEFT or direction is Directions.RIGHT:
            self.drive = [self.motors.front, self.motors.back]
            self.rudder = [self.motors.left, self.motors.right]
        else:
            raise ValueError('Incompatible Direction for AxisMovement: {!r}'.format(direction))
        
        if direction is Directions.BACKWARD or direction is Directions.LEFT:
            for motor in self.drive:
                self.modifiers[motor] = -1

    def calc_expected_ticks(self, dist):
        # This underestimates the number of ticks needed e.g 5.9 ticks in
        # reality will give 5 with this. Coupled with the control loop's
        # tendency to overshoot however I think this could be reasonably
        # accurate, tests will have to confirm that however
        return (360 * dist) // WHEEL_CIRCUM

    def parse_odometer(self, readings):
        return min(readings)

class DiagonalMovement(StraightLineMovement):
    pass

class Rotation(GenericMovement):
    def __init__(self):
        GenericMovement.__init__(self)
    def __call__(self, direction):
        for modifier in self.modifiers:
            self.modifiers[modifier] = 1
        if direction is Directions.RIGHT:
            self.modifiers[self.motors.left] = -1
            self.modifiers[self.motors.back] = -1
        elif direction is Directions.LEFT:
            self.modifiers[self.motors.right] = -1
            self.modifiers[self.motors.front] = -1
        else:
            raise ValueError('Incompatible Direction for Rotation: {!r}'.format(direction))
        for motor in self.motors:
            self._run_motor(motor)

forward  = AxisMovement(Directions.FORWARD)
backward = AxisMovement(Directions.BACKWARD)
left     = AxisMovement(Directions.LEFT)
right    = AxisMovement(Directions.RIGHT)

rotate   = Rotation()
