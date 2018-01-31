"""Wrapper library for moving the ev3"""

import ev3dev.ev3 as ev3
import Directions
import Colors
import imp
from double_map import DoubleMap
import os
from math import pi
from sensors import read_color, sonar_poll
from collections import namedtuple
from os import path
from ev3dev.ev3 import Motor
from thread_decorator import thread
from functools import partial

##### Setup #####

_WHEEL_CIRCUM = 20.106193
_BASE_ROT_TO_WHEEL_ROT = (24 * pi) / _WHEEL_CIRCUM
_MOTOR_ROOT = '/sys/class/tacho-motor'
_DEFAULT_RUN_SPEED = 200
_DEFAULT_TURN_SPEED = 200
_DEFAULT_TURN_TIME = 100

_ODOMETERS = {}

# Mapping between motor names and addresses in the ev3 (Read from config file
with open('motors.conf') as f:
    _PORTMAP = DoubleMap(imp.load_source('data', '', f).port_map)

MOTORS = namedtuple('motors', 'front back left right')(
    ev3.LargeMotor(_PORTMAP['front']), # Front
    ev3.LargeMotor(_PORTMAP['back']),  # Back
    ev3.LargeMotor(_PORTMAP['left']),  # Left
    ev3.LargeMotor(_PORTMAP['right'])  # Right
)

# Normalises the direction of each motor (Left to right axis drives forward,
# front to back axis drives right)
_SCALERS = {MOTORS.front : -1,
            MOTORS.back  :  1,
            MOTORS.left  : -1,
            MOTORS.right : -1}

_DEFAULT_MULTIPLIER = {MOTORS.front : 1,
                       MOTORS.back  : 1,
                       MOTORS.left  : 1,
                       MOTORS.right : 1}

# Autodiscover the mapping between each motor and the file that holds it's
# position information (Not stable across boots)
for motor in os.listdir(_MOTOR_ROOT):
    # The address file contains the real name of the motor (out*)
    with open(path.join(_MOTOR_ROOT, motor, 'address')) as file:
        name = file.readline().rstrip()
        _ODOMETERS[getattr(MOTORS, _PORTMAP[name])] = path.join(_MOTOR_ROOT, motor, 'position')

del _MOTOR_ROOT
del _PORTMAP

### End Setup ###

def _read_odometer(motor):
        """Read the odometer on one motor"""
        with open(_ODOMETERS[motor]) as file:
            return abs(int(file.readline()))

def _default_odometry(readings):
    return min(readings)

def _detect_color(color=Colors.BLACK):
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
        return (motors, {motors.front :  1,
                         motors.back  : -1,
                         motors.left  :  1,
                         motors.right : -1})
        elif direction is Directions.LEFT:
            self.modifiers[self.motors.left] = -1
            self.modifiers[self.motors.front] = -1
    elif direction is Directions.ROT_LEFT:
        return (motors, {motors.front : -1,
                         motors.back  :  1,
                         motors.left  : -1,
                         motors.right :  1})
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

def _course_correction(front=MOTORS.front, back=MOTORS.back, scalers=_SCALERS):
    left, right = _detect_color()
    if left:
       front.run_timed(speed_sp=scalers[front]*-1*_DEFAULT_TURN_SPEED, time_sp=_DEFAULT_TURN_TIME, stop_action=Motor.STOP_ACTION_BRAKE)
       back.run_timed(speed_sp=scalers[back]*_DEFAULT_TURN_SPEED, time_sp=_DEFAULT_TURN_TIME, stop_action=Motor.STOP_ACTION_BRAKE)
    elif right:
       front.run_timed(speed_sp=scalers[front]*_DEFAULT_TURN_SPEED, time_sp=_DEFAULT_TURN_TIME, stop_action=Motor.STOP_ACTION_BRAKE)
       back.run_timed(speed_sp=scalers[back]*-1*_DEFAULT_TURN_SPEED, time_sp=_DEFAULT_TURN_TIME, stop_action=Motor.STOP_ACTION_BRAKE)

def stop_motors(motors=MOTORS):
    for motor in motors:
        motor.stop(stop_action=Motor.STOP_ACTION_BRAKE)

@thread
def _base_move(dist, motors, speed=_DEFAULT_RUN_SPEED, multiplier=_DEFAULT_MULTIPLER, distance=None, odometry=None, correction=None):

    if distance is None:
        return
    if odometry is None:
        odometry = _default_odometry
    if correction is None:
        correction = lambda: None

    ticks = distance(dist)
    traveled = 0
    for motor in motors:
        run_motor(motor, speed=multiplier[motor]*speed)
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

def _generic_axis(dist, direction, correction=False):
    motors, should_reverse = _get_motor_params(direction)
    func = partial(_base_move, dist, motors, distance=_straight_line_odometry)
    if correction:
        func = partial(func, correction=_course_correction)
    if should_reverse:
        multiplier = dict(_DEFAULT_MULTIPLIER)
        for motor in motors:
            multiplier[motor] = -1
        func = partial(func, multiplier=multiplier)
    return func()
    
def forward(dist, correction=True):
    return _generic_axis(dist, Directions.FORWARD, correction=correction)

def backward(dist):
    return _generic_axis(dist, Directions.BACKWARD)

def left(dist):
    return _generic_axis(dist, Directions.LEFT)

def right(dist):
    return _generic_axis(dist, Directions.RIGHT)

def rotate(angle, direction=Directions.ROT_LEFT):
    motors, multiplier = _get_motor_params(direction)
    _base_move(angle, motors, multiplier=multiplier, distance=_rotation_odometry)
