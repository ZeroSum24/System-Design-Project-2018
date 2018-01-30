"""Wrapper library for moving the ev3"""

from thread_decorator import thread
from enum import Enum
from collections import namedtuple
from os import path
import os
from double_map import DoubleMap
import catcher
from math import pi
from sensor import read_color, sonar_poll
from colors import Colors

# Squash the exceptions resulting from running the code outside of the ev3
try:
    import ev3dev.ev3 as ev3
    from ev3dev.core import Motor
    _HAVE_EV3 = True
except ModuleNotFoundError:
    class _PlaceHolder:
        # Whenever an attribute is requested return another placeholder
        def __getattr__(self, attr):
            return _PlaceHolder()
        # When called accept any arguments and return another placeholder
        def __call__(self, *args, **kwargs):
            return _PlaceHolder()
    ev3 = _PlaceHolder()
    Motor = _PlaceHolder()
    _HAVE_EV3 = False

_MOTOR_ROOT = '/sys/class/tacho-motor'

_WHEEL_CIRCUM = 20.106193
_BASE_ROT_TO_WHEEL_ROT = (24 * pi) / _WHEEL_CIRCUM

Directions = Enum('Directions', 'FORWARD BACKWARD LEFT RIGHT')

class _GenericMovement:

    _pos_files = {}

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

    def __init__(self):
        # Can be set by subclasses to selectivly scale motor speed and direction
        self.modifiers = {self.motors.front : 1,
                          self.motors.back  : 1,
                          self.motors.left  : 1,
                          self.motors.right : 1}

        # Autodiscover the mapping between each motor and the file that holds
        # it's position information
        try:
            motor_dirs = os.listdir(_MOTOR_ROOT)
        except FileNotFoundError:
            pass
        else:
            for motor in motor_dirs:
                # The address file contains the real name of the motor (out*)
                with open(path.join(_MOTOR_ROOT, motor, 'address')) as file:
                    name = file.readline().rstrip()
                    # Add to the correct mapping
                    self._pos_files[getattr(self.motors, self._motor_mapping[name])] = path.join(_MOTOR_ROOT, motor, 'position')

    def _run_motor(self, motor, speed):
	# Zero the motor's odometer
        motor.reset()
        # Fixes the odometer reading bug
        motor.run_timed(speed_sp=500, time_sp=500)
        # Preempts the previous command
        motor.run_forever(speed_sp=self.modifiers[motor]*self.scalers[motor]*speed)

    def _stop_all_motors(self):
        for motor in self.motors:
            motor.stop(stop_action=Motor.STOP_ACTION_BRAKE)

    ## Override These Methods ##
    def calc_expected_ticks(self, dist):
        pass

    def parse_odometer(self, readings):
        pass

    def course_correction(self):
        # Should be non-blocking, use the motors in self.rudder
        pass
    ## End Overrides ##

    def _read_odometer_base(self, motor):
        """Read the odometer on one motor"""
        with open(self._pos_files[motor]) as file:
            return abs(int(file.readline()))

    def _read_odometer(self):
        """Read the odometer on all the motors"""
        return tuple(map(self._read_odometer_base, self.drive))

    def _run_motors(self, speed):
        """Run all the drive motors"""
        for motor in self.drive:
            self._run_motor(motor, speed)

    def _read_line_sensors(self):
        return map(lambda x: x is Colors.BLACK, read_color())

    @thread
    def __call__(self, dist, speed=200):
        # Only attempt to run the real motor routine if the ev3 module is
        # present
        if _HAVE_EV3:
            ticks = self.calc_expected_ticks(dist)
            traveled = 0
            self._run_motors(speed)
            while traveled < ticks:
                if sonar_poll() < 7:
                    self._stop_all_motors()
                    break
                self.course_correction()
                traveled = self.parse_odometer(self._read_odometer())
                if traveled >= ticks:
                    self._stop_all_motors()
                    break

class _StraightLineMovement(_GenericMovement):
    """Move in a straight line for a specfic distance

       Subclasses should define self.drive and self.rudder, self.drive should
       contain the motors that will be used to move the robot, self.rudder
       should contain the motors for course correction. Subclasses should also
       override calc_expected_ticks and course_correction. Finally setting any
       of the modifier can be used to scale the each motor's speed and direction"""

class _AxisMovement(_StraightLineMovement):
    def __init__(self, direction):
        _StraightLineMovement.__init__(self)
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
        return (360 * dist) // _WHEEL_CIRCUM

    def parse_odometer(self, readings):
        return min(readings)

    def course_correction(self):
        left, right = self._read_line_sensors()
        if left:
           self.motors.front.run_timed(speed_sp=self.scalers[self.motors.front]*-200, time_sp=100, stop_action=Motor.STOP_ACTION_BRAKE)
           self.motors.back.run_timed(speed_sp=self.scalers[self.motors.back]*200, time_sp=100, stop_action=Motor.STOP_ACTION_BRAKE)
        elif right:
           self.motors.front.run_timed(speed_sp=self.scalers[self.motors.front]*200, time_sp=100, stop_action=Motor.STOP_ACTION_BRAKE)
           self.motors.back.run_timed(speed_sp=self.scalers[self.motors.back]*-200, time_sp=100, stop_action=Motor.STOP_ACTION_BRAKE)

class _DiagonalMovement(_StraightLineMovement):
    pass

class _Rotation(_GenericMovement):
    """This is currently rotate forever, it will be changed"""
    def __init__(self, direction):
        _GenericMovement.__init__(self)
        if direction is Directions.RIGHT:
            self.modifiers[self.motors.right] = -1
            self.modifiers[self.motors.back] = -1
        elif direction is Directions.LEFT:
            self.modifiers[self.motors.left] = -1
            self.modifiers[self.motors.front] = -1
        else:
            raise ValueError('Incompatible Direction for Rotation: {!r}'.format(direction))
        self.drive = self.motors

    def calc_expected_ticks(self, angle):
        return int(angle * _BASE_ROT_TO_WHEEL_ROT)

    def parse_odometer(self, readings):
        return min(readings)

forward  = _AxisMovement(Directions.FORWARD)
backward = _AxisMovement(Directions.BACKWARD)
left     = _AxisMovement(Directions.LEFT)
right    = _AxisMovement(Directions.RIGHT)

rotatel   = _Rotation(Directions.LEFT)
rotater   = _Rotation(Directions.RIGHT)
