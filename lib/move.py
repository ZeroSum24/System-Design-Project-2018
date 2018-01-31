"""Wrapper library for moving the ev3"""

import Directions
import Colors
import imp
from double_map import DoubleMap
import os
from math import pi
from sensors import read_color, sonar_poll

##### Config #####

_WHEEL_CIRCUM = 20.106193
_BASE_ROT_TO_WHEEL_ROT = (24 * pi) / _WHEEL_CIRCUM
_MOTOR_ROOT = '/sys/class/tacho-motor'
_DEFAULT_RUN_SPEED = 200

# Normalises the direction of each motor (Left to right axis drives forward,
# front to back axis drives right)
_SCALERS = {MOTORS.front : -1,
 `          MOTORS.back  :  1,
            MOTORS.left  : -1,
            MOTORS.right : -1}

### End Config ###

##### Setup #####

_ODOMETERS = {}

# Mapping between motor names and addresses in the ev3 (Read from config file
with open('../config/motors.conf') as f:
    _PORTMAP = DoubleMap(imp.load_source('data', '', f).port_map)

MOTORS = namedtuple('motors', 'front back left right')(
    ev3.LargeMotor(_PORTMAP['front']), # Front
    ev3.LargeMotor(_PORTMAP['back']),  # Back
    ev3.LargeMotor(_PORTMAP['left']),  # Left
    ev3.LargeMotor(_PORTMAP['right'])  # Right
)

# Autodiscover the mapping between each motor and the file that holds it's
# position information (Not stable across boots)
for motor in os.listdir(root):
    # The address file contains the real name of the motor (out*)
    with open(path.join(_MOTOR_ROOT, motor, 'address')) as file:
        name = file.readline().rstrip()
        _ODOMETERS[getattr(MOTORS, _PORTMAP[name])] = path.join(_MOTOR_ROOT, motor, 'position')

del _MOTOR_ROOT
del _PORTMAP

### End Setup ###

def _read_odometer(motor):
        """Read the odometer on one motor"""
        with open(self._pos_files[motor]) as file:
            return abs(int(file.readline()))

def _default_odometry(readings):
    return min(readings)

def _detect_color(color=Colors.Black):
    return map(lambda x: x is color, read_color())

def _get_motor_params(direction, motors=MOTORS):
    if direction is Directions.FORWARD:
        return ((motors.left, motors.right), False)
    elif direction is Directions.BACKWARD:
        return ((motors.left, motors.right), True)
    elif direction is Directions.RIGHT:
        return ((motors.forward, motors.backward), False)
    elif direction is Directions.LEFT:
        return ((motors.forward, motors.backward), True)
    elif direction is Directions.ROT_RIGHT:
        return (motors, False)
    elif direction is Directions.ROT_LEFT:
        return (motors, True)
    else:
        raise ValueError('Unknown Direction: {}'.format(direction))

def _straight_line_odometry(dist):
    return (360 * dist) // _WHEEL_CIRCUM

def _rotation_odometry(angle):
    return int(angle * _BASE_ROT_TO_WHEEL_ROT)

def run_motor(motor, speed=_DEFAULT_RUN_SPEED, scalers=_SCALERS):
	# Zero the motor's odometer
        motor.reset()
        # Fixes the odometer reading bug
        motor.run_timed(speed_sp=500, time_sp=500)
        # Preempts the previous command
        motor.run_forever(speed_sp=scalers[motor]*speed)

def stop_motors(motors=MOTORS):
    for motor in motors:
        motor.stop(stop_action=Motor.STOP_ACTION_BRAKE)

def _base_move(dist, motors, speed=200, distance=None odometry=None, correction=None):

    if distance is None:
        distance = lambda x: 0
    if odometry is None:
        odometry = _default_odometry
    if correction is None:
        correction = lambda x: None

    ticks = distance(dist)
    traveled = 0
    for motor in motors:
        run_motor(motor, speed=speed)
    while traveled < ticks:
        if sonar_poll() < 7:
            stop_motors()
            break
        correction()
        odometer_readings = tuple(map(_read_odometer, motors))
        traveled = odometry(odometer_readings)
        if traveled >= ticks:
            stop_motors()
            break

def forward(dist, correction=True):
    pass

def backward(dist):
    pass

def left(dist):
    pass

def right(dist):
    pass

def rotate(angle, direction=Directions.LEFT):
    pass

'''
    def course_correction(self):
        left, right = self._read_line_sensors()
        if left:
           self.motors.front.run_timed(speed_sp=self.scalers[self.motors.front]*-200, time_sp=100, stop_action=Motor.STOP_ACTION_BRAKE)
           self.motors.back.run_timed(speed_sp=self.scalers[self.motors.back]*200, time_sp=100, stop_action=Motor.STOP_ACTION_BRAKE)
        elif right:
           self.motors.front.run_timed(speed_sp=self.scalers[self.motors.front]*200, time_sp=100, stop_action=Motor.STOP_ACTION_BRAKE)
           self.motors.back.run_timed(speed_sp=self.scalers[self.motors.back]*-200, time_sp=100, stop_action=Motor.STOP_ACTION_BRAKE)

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
'''
