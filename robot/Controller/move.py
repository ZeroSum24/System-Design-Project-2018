"""Wrapper library for moving the ev3"""

import imp
import os
from os import path
from math import pi
from collections import namedtuple
from functools import partial
import time

import ev3dev.ev3 as ev3
from ev3dev.ev3 import Motor

import Directions
import Colors
import Turning
from double_map import DoubleMap
from sensors import read_color, sonar_poll
from thread_decorator import thread

##### Setup #####

# Read config file
with open('move.conf') as f:
    _CONFIG = imp.load_source('config', '', f)

_WHEEL_CIRCUM = _CONFIG.wheel_diameter * pi
_BASE_ROT_TO_WHEEL_ROT = (_CONFIG.robot_diameter * pi) / _WHEEL_CIRCUM
_DEFAULT_RUN_SPEED = _CONFIG.default_run_speed
_DEFAULT_TURN_SPEED = _CONFIG.default_turn_speed
_DEFAULT_TURN_TIME = _CONFIG.default_turn_time

_PORTMAP = DoubleMap(_CONFIG.port_map)

MOTORS = namedtuple('motors', 'front back left right')(
    ev3.LargeMotor(_PORTMAP['front']), # Front
    ev3.LargeMotor(_PORTMAP['back']),  # Back
    ev3.LargeMotor(_PORTMAP['left']),  # Left
    ev3.LargeMotor(_PORTMAP['right'])  # Right
)

# Normalises the direction of each motor (Left to right axis drives forward,
# front to back axis drives right)
_SCALERS = {MOTORS.front : _CONFIG.scalers['front'],
            MOTORS.back  : _CONFIG.scalers['back'],
            MOTORS.left  : _CONFIG.scalers['left'],
            MOTORS.right : _CONFIG.scalers['right']}

_DEFAULT_MULTIPLIER = {MOTORS.front : 1,
                       MOTORS.back  : 1,
                       MOTORS.left  : 1,
                       MOTORS.right : 1}

def _get_odometers(root, portmap):
    """Autodiscover the mapping between each motor and the file that holds it's
       position information (Not stable across boots)"""
    odometers = {}
    for motor in os.listdir(root):
        # The address file contains the real name of the motor (out*)
        with open(path.join(root, motor, 'address')) as file:
            name = file.readline().rstrip()
            odometers[getattr(MOTORS, portmap[name])] = path.join(root, motor, 'position')
    return odometers
_ODOMETERS = _get_odometers(_CONFIG.motor_root, _PORTMAP)

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
        return ((motors.front, motors.back), False)
    elif direction is Directions.LEFT:
        return ((motors.front, motors.back), True)
    elif direction is Directions.ROT_RIGHT:
        return (motors, {motors.front :  1,
                         motors.back  : -1,
                         motors.left  :  1,
                         motors.right : -1})
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

def run_motor(motor, speed=_DEFAULT_RUN_SPEED, scalers=None):

    if scalers is None:
        scalers = _SCALERS

    # Zero the motor's odometer
    motor.reset()
    # Fixes the odometer reading bug
    motor.run_timed(speed_sp=500, time_sp=500)
    # Preempts the previous command
    motor.run_forever(speed_sp=scalers[motor]*speed)

def _course_correction(correctionFlag, front=MOTORS.front, back=MOTORS.back,
                        lefty=MOTORS.left, righty=MOTORS.right, scalers=None):

    if scalers is None:
        scalers = _SCALERS

    left, right = _detect_color()

    if correctionFlag == Turning.RIGHT: # its turning right
        if not right:
            stop_motors([front, back])
            run_motor(lefty, _DEFAULT_RUN_SPEED)
            return Turning.NONE # indicate correction exit
        else:
            return correctionFlag # still turning

    elif correctionFlag == Turning.LEFT: # its turning left
        if not left:
            stop_motors([front, back])
            run_motor(righty, _DEFAULT_RUN_SPEED)
            return Turning.NONE # indicate correction exit
        else:
            return correctionFlag # still turning

    else: # not turning
        if right:
            run_motor(front, _DEFAULT_TURN_SPEED)
            run_motor(back, -1*_DEFAULT_TURN_SPEED)
            stop_motors([lefty])
            time.sleep(_DEFAULT_TURN_TIME/1000)
            return Turning.RIGHT # indicate turning right
        elif left:
            run_motor(front, -1*_DEFAULT_TURN_SPEED)
            run_motor(back, _DEFAULT_TURN_SPEED)
            stop_motors([righty])
            time.sleep(_DEFAULT_TURN_TIME/1000)
            return Turning.LEFT # indicate turning left


def stop_motors(motors=MOTORS):
    for motor in motors:
        motor.stop(stop_action=Motor.STOP_ACTION_BRAKE)

@thread
def _base_move(dist, motors, speed=_DEFAULT_RUN_SPEED, multiplier=None,
               distance=None, odometry=None, correction=None):

    if multiplier is None:
        multiplier = _DEFAULT_MULTIPLIER
    if distance is None:
        return
    if odometry is None:
        odometry = _default_odometry
    if correction is None:
        correction = lambda: None

    ticks = distance(dist)
    traveled = 0
    correctionFlag = Turning.NONE
    for motor in motors:
        run_motor(motor, speed=multiplier[motor]*speed)
    while traveled < ticks:
        if sonar_poll() < 7:
            stop_motors()
            break
        correctionFlag = correction(correctionFlag)
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
