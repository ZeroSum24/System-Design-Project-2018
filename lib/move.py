"""Wrapper library for moving the ev3"""

from thread_decorator import thread
from enum import Enum
from collections import namedtuple
from os import path
import os
from double_map import DoubleMap

import ev3dev.ev3 as ev3
from ev3dev.core import Motor

MOTOR_ROOT = '/sys/class/tacho-motor'

WHEEL_CIRCUM = 20

Directions = Enum('Directions', 'FORWARD BACKWARD LEFT RIGHT')

class GenericMovement:

    # Mapping between motor names and addresses in the ev3
    _motor_mapping = DoubleMap({'front': 'outD',
                                'back' : 'outA',
                                'left' : 'outB',
                                'right': 'outC'})
    
    # Motor objects by location on the chassis
    motors = namedtuple('motors', 'front back left right')(
        ev3.LargeMotor(_motor_mapping['front']), # Front
        ev3.LargeMotor(_motor_mapping['back']), # Back
        ev3.LargeMotor(_motor_mapping['left']), # Left
        ev3.LargeMotor(_motor_mapping['right'])  # Right
    )

    # Normalises the direction of each motor (Left to right axis drives forward,
    # front to back axis drives right)
    scalers = {motors.front : -1,
               motors.back  :  1,
               motors.left  : -1,
               motors.right : -1}

    # Can be set by subclasses to selectivly scale motor speed and direction
    modifiers = {motors.front : 1,
                 motors.back  : 1,
                 motors.left  : 1,
                 motors.right : 1}

    def __init__(self):
        # Seems to fix the position bug
        for motor in self.motors:
            motor.run_timed(speed_sp=1, time_sp=1)
            motor.stop(stop_action=Motor.STOP_ACTION_BRAKE)
            motor.reset()

        # Autodiscover the mapping between each motor and the file that holds
        # it's position information
        motor_dirs = os.listdir(MOTOR_ROOT)
        for motor in motor_dirs:
            # The address file contains the real name of the motor (out*)
            with open(path.join(MOTOR_ROOT, motor, 'address')) as file:
                name = file.readline()
            # Add to the correct mapping
            self.pos_files[self.motors[self._motor_mapping[name]]] = path.join(MOTOR_ROOT, motor, 'position')

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
       of the modifier can be used to scale the each motor's speed and direction"""

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
        """Read the odometer on one motor"""
        with open(self.pos_files[motor]) as file:
            return int(file.readline())

    def _read_odometer(self):
        """Read the odometer on all the motors"""
        return tuple(map(self._read_odometer_base, self.drive))

    def _run_motors(self):
        """Run all the drive motors"""
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
    """This is currently rotate forever, it will be changed"""
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
