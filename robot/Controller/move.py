#!/usr/bin/env python3
"""Wrapper library for moving the ev3"""

import imp
import os
from os import path
from math import pi, sin, cos
from collections import namedtuple
from functools import partial
import time
from functools import wraps

import ev3dev.ev3 as ev3
from ev3dev.ev3 import Motor
from ev3dev.auto import *

import Directions
import Colors
from double_map import DoubleMap
from sensors import read_color, sonar_poll, read_reflect
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
        return (motors.left, motors.right), False
    elif direction is Directions.BACKWARD:
        return (motors.left, motors.right), True
    elif direction is Directions.RIGHT:
        return (motors.front, motors.back), False
    elif direction is Directions.LEFT:
        return (motors.front, motors.back), True
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
    #motor.reset()
    # Fixes the odometer reading bug
    #motor.run_timed(speed_sp=500, time_sp=500)
    # Preempts the previous command
    motor.run_forever(speed_sp=scalers[motor]*speed)



_last_error = 0
_integral = 0
_MAXREF = 54
_MINREF = 20
_TARGET = 37
_KP = 1.55
_KD = 0
_KI = 0.8


def _course_correction(delta_time, front=MOTORS.front, back=MOTORS.back, lefty=MOTORS.left, righty=MOTORS.right):
    global _last_error
    global _integral

    ref_read = read_reflect()
    error = _TARGET - (100 * (ref_read - _MINREF) / (_MAXREF - _MINREF))
    derivative = (error - _last_error) / delta_time
    _last_error = error
    _integral = (0.5 * _integral + error)
    course = -(_KP * error - _KD * derivative + _KI * _integral * delta_time)

    for (motor, speed) in zip([lefty, righty, front, back], _steering(course, _DEFAULT_RUN_SPEED)):
        run_motor(motor, speed)

def _steering(course, speed):
    if course >= 0:
        if course > 100:
            speed_right = 0
            speed_left = speed
        else:
            speed_left = speed
            speed_right = speed - ((speed * course) / 100)
    else:
        if course < -100:
            speed_left = 0
            speed_right = speed
        else:
            speed_right = speed
            speed_left = speed + ((speed * course) / 100)

    speed_front = -delta_deg(speed_left, speed_right)
    speed_back = delta_deg(speed_left, speed_right)

    return [int(speed_left), int(speed_right), int(speed_front), int(speed_back)]

def d_deg(): # distance traveled per degree by a wheel
    return _WHEEL_CIRCUM/360

def dist(velocity): # distance traveled by each wheel per second in cm
    return velocity * d_deg()

def diff_in_dist(vel_left, vel_right): # the difference in distance traveled by the left and right wheels in cm
    return dist(vel_left) - dist(vel_right)

def omega(vel_left, vel_right): # angle of base rotation per second in radians
    return (diff_in_dist(vel_left, vel_right)/_CONFIG.robot_diameter)

def IC_dist(vel_left, vel_right): # the distance from the centre of rotation to the centre of the drive axis
    return (_CONFIG.robot_diameter/2)*( (vel_right + vel_left)/(vel_right - vel_left) )

def omega_to_axis(vel_left, vel_right):
    # Result of rotating the vector defined by IC_dist through omega
    # in euclidian space, only the x coordinate is required in cm
    # (L/2 is the original y coordinate)
    result = IC_dist(vel_left, vel_right) * cos(omega(vel_left, vel_right))
    result -= _CONFIG.robot_diameter/2 * sin(omega(vel_left, vel_right))
    return result

def delta(vel_left, vel_right): # change is x coordinate is how far the front wheel
                                # must move perpendicular tothe direction of travel (cm)
    return IC_dist(vel_left, vel_right) - omega_to_axis(vel_left, vel_right)

def delta_deg(vel_left, vel_right): # converting distance to the number of degrees the wheel must move through in a second
    if abs(vel_left-vel_right) > 3:
        return 360 * delta(vel_left, vel_right)/_WHEEL_CIRCUM
    else:
        return 0

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
    previous_time = time.time()
    for motor in motors:
        try:
            run_motor(motor, speed=multiplier[motor]*speed)
        except:
            print("Motor not connected")
    while traveled < ticks:
        delta_time = time.time() - previous_time
        previous_time = time.time()
        if sonar_poll() < 12:
            stop_motors()
            break
        btn.process()
        correction(delta_time)
        odometer_readings = tuple(map(_read_odometer, motors))
        traveled = odometry(odometer_readings)
        if traveled >= ticks:
            stop_motors()
            break

def changeP(state):
    global _KP
    _KP += .025
    print("p: " + str(_KP))

def changeD(state):
    global _KD
    _KD += 0.005
    print("d: " + str(_KD))

def changeI(state):
    global _KI
    _KI += 0.005
    print("i: " + str(_KI))

def reset(state):
    global _KP
    _KP = 1
    global _KD
    _KD = 0
    global _KI
    _KI = 0
    print("p: " + str(_KP) + " d: " + str(_KD) + " i: " + str(_KI))

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

def rotate(angle, direction=Directions.ROT_LEFT):
    motors, multiplier = _get_motor_params(direction)
    _base_move(angle, motors, multiplier=multiplier, distance=_rotation_odometry)

def timer(f):
    """Returns the elasped time of function execution"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        f(*args, **kwargs)
        return time.time() - start_time
    return wrapper

btn = ev3.Button()
btn.on_left = changeP
btn.on_right = changeD
btn.on_down = changeI
btn.on_up = reset

forward(99999999).join()
