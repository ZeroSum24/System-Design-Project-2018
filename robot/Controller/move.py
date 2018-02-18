#!/usr/bin/env python3
"""Wrapper library for moving the ev3"""

# pylint: disable=fixme, import-error, wildcard-import, missing-docstring,
# pylint: disable=no-member, redefined-outer-name, invalid-name,
# pylint: disable=global-statement, no-else-return, too-many-arguments,
# pylint: disable=too-many-locals, too-many-branches

import imp
import os
from os import path
from math import pi, cos, sin
from collections import namedtuple
import time

import ev3dev.ev3 as ev3
from ev3dev.ev3 import Motor

import Directions
import Colors
from double_map import DoubleMap
from sensors import read_color, sonar_poll, read_reflect
from PID import pid_speeds, _delta_deg, _omega
import Junctions
from DisconnectedErrors import (EXCEPTIONS, MotorDisconnectedError,
                                SonarDisconnectedError,
                                ReflectivityDisconnectedError,
                                ColorDisconnectedError)

##### Setup #####

# Globals used elsewhere in the file (Set by init)
# Files containing odometer data, one per motor
_ODOMETERS = None
# Mapping of human readable motor names to their ports on the ev3
_MOTORS = None
# Circumference of the wheel
_WHEEL_CIRCUM = None
# Ratio of base rotations to wheel rotations
_BASE_ROT_TO_WHEEL_ROT = None
# Default speed for the robot
_DEFAULT_RUN_SPEED = None
# Default turning speed for the robot
_DEFAULT_TURN_SPEED = None
# Used to normalise the motors direction (Forward and Right)
_SCALERS = None
# Diameter of the robot
_ROBOT_DIAMETER = None
# Reflectivity range for the line sensor
_MAXREF = None
_MINREF = None
# Threshold between line and floor
_TARGET = None
# Magic constants for PID
_KP = None
_KD = None
_KI = None
# Used as a default value in the movement functions
_DEFAULT_MULTIPLIER = None
# Supplies information expected by the movement functions
_MOTOR_PARAMS = None
_SONAR_DIST = None
_JUNCTION_MARKERS = None
# PID calibration flag
_PID_CALIBRATION = False

def init():
    # Pull in Globals to initalise module state
    global _ODOMETERS, _MOTORS, _WHEEL_CIRCUM, _BASE_ROT_TO_WHEEL_ROT
    global _DEFAULT_RUN_SPEED, _DEFAULT_TURN_SPEED, _SCALERS, _ROBOT_DIAMETER
    global _DEFAULT_MULTIPLIER, _MAXREF, _MINREF, _TARGET, _KP, _KD, _KI
    global  _MOTOR_PARAMS, _SONAR_DIST, _JUNCTION_MARKERS

    # Read config file (In python modules are just objects, the basic import
    # syntax just parses a file as the definition of a module and places the
    # resulting object in the global namespace. imp has hooks to allow user
    # level access to the standard import machinery, load_source interprets the
    # given file as python code and returns the resulting module object). The
    # with statement is a context manager, in the case of files the filehandle
    # created by open is assigned to the variable specified after as for the
    # duration of the block, the filehandle is gaurenteed to be closed when
    # execution exits the block regardless of how that happens. TODO: imp is
    # deprecated in favor of importlib apparently
    with open('move.conf') as config_file:
        config = imp.load_source('config', '', config_file)

    # Populate Globals
    _WHEEL_CIRCUM = config.wheel_diameter * pi
    _BASE_ROT_TO_WHEEL_ROT = (config.robot_diameter * pi) / _WHEEL_CIRCUM
    _DEFAULT_RUN_SPEED = config.default_run_speed
    _DEFAULT_TURN_SPEED = config.default_turn_speed
    _ROBOT_DIAMETER = config.robot_diameter

    # Bi-directional map linking human readable motor names to their ports in
    # the brick
    portmap = DoubleMap(config.port_map)

    # Named tuples are light weight immutable objects that respond to dot
    # notation, the names of the attributes are given in the second string of
    # the constructor
    _MOTORS = namedtuple('motors', 'front back left right')(
        ev3.LargeMotor(portmap['front']), # Front
        ev3.LargeMotor(portmap['back']),  # Back
        ev3.LargeMotor(portmap['left']),  # Left
        ev3.LargeMotor(portmap['right'])  # Right
    )

    # Normalises the direction of each motor (Left to right axis drives forward,
    # front to back axis drives right)
    _SCALERS = {_MOTORS.front : config.scalers['front'],
                _MOTORS.back  : config.scalers['back'],
                _MOTORS.left  : config.scalers['left'],
                _MOTORS.right : config.scalers['right']}

    _ODOMETERS = {}
    root = config.motor_root
    for motor in os.listdir(root):
        # The address file contains the real name of the motor (out*)
        with open(path.join(root, motor, 'address')) as file:
            # Read one line from the file (There should only be 1 line) and
            # strip off trailing whitespace
            name = file.readline().rstrip()
            # Map each motor to the relavent file (getattr allows the addressing
            # of objects by string rather than dot notation)
            _ODOMETERS[getattr(_MOTORS, portmap[name])] = path.join(root, motor, 'position')

    # Used as a default value in the movement functions
    _DEFAULT_MULTIPLIER = {_MOTORS.front : 1,
                           _MOTORS.back  : 1,
                           _MOTORS.left  : 1,
                           _MOTORS.right : 1}

    # Supplies information expected by the movement functions
    _MOTOR_PARAMS = {Directions.FORWARD   : ((_MOTORS.left, _MOTORS.right), False),
                     Directions.BACKWARD  : ((_MOTORS.left, _MOTORS.right), True),
                     Directions.LEFT      : ((_MOTORS.front, _MOTORS.back), True),
                     Directions.RIGHT     : ((_MOTORS.front, _MOTORS.back), False),
                     Directions.ROT_RIGHT : {_MOTORS.front :  1,
                                             _MOTORS.back  : -1,
                                             _MOTORS.left  : -1,
                                             _MOTORS.right :  1},
                     Directions.ROT_LEFT : {_MOTORS.front : -1,
                                             _MOTORS.back  :  1,
                                             _MOTORS.left  :  1,
                                             _MOTORS.right : -1}}
    _MAXREF = config.max_ref
    _MINREF = config.min_ref
    _TARGET = config.target_ref
    _KP = config.KP
    _KD = config.KD
    _KI = config.KI
    _SONAR_DIST = config.sonar_dist
    _JUNCTION_MARKERS = config.junction_markers
init()

### End Setup ###

##### Sensors #####

def _read_odometer(motor):
    """Read the odometer on one motor."""
    with open(_ODOMETERS[motor]) as file:
        # abs as actual direction of rotation is irrelevent
        return abs(int(file.readline()))

def _parse_by_average(readings):
    """Average seperate odometer readings to estimate distace traveled."""
    return sum(readings) // len(readings)

def _parse_to_omega(left_motor, right_motor):
    """Return the angle (in degrees) through which the robot has turned per second"""
    l = _read_odometer(left_motor)
    r = _read_odometer(right_motor)
    result = abs(_omega(l, r, _WHEEL_CIRCUM, _ROBOT_DIAMETER) * 180 / pi)
    return result

def _detect_color(color=Colors.BLACK):
    return read_color() is color

### End Sensors ###

##### Distance Measures #####

def _straight_line_odometry(dist):
    # The distance covered by one degree of rotation of a wheel is
    # _WHEEL_CIRCUM // 360. Thus the total number of degrees of rotation is
    # dist // (_WHEEL_CIRCUM // 360) == (360 * dist) // _WHEEL_CIRCUM
    return (360 * dist) // _WHEEL_CIRCUM

def _rotation_odometry(angle):
    # To convert between the angle the base should move through to the angle the
    # wheel should move through we multiply by the ratio of the two
    # circumferences and floor to int
    return int(angle * _BASE_ROT_TO_WHEEL_ROT)

### End Distance Measures ###

##### Motor Controls #####
def run_motor(motor, speed=_DEFAULT_RUN_SPEED, scalers=None, reset=False):
    """Run the specified motor forever.

    Required Arguments:
    motor -- A LargeMotor object representing the motor to run.

    Optional Arguments:
    speed -- Speed to run the motor at.
    scalers -- Dict containing scalers to influence the motor's speed,
               intended for dependency injection.
    reset -- If False, don't reset the motor's odometer on restart
    """

    # Mutable structures shouldn't be passed as default arguments. Python
    # evaluates default arguments at definition time not call time so the
    # objects passed as default arguments are always the same across function
    # calls. With mutable structures if the function modifies the argument while
    # using the default further calls of the same function will receive the
    # modified structure. The None trick forces assignment of default arguments
    # at call time
    if scalers is None:
        scalers = _SCALERS
    try:
        if reset:
            # Zero the motor's odometer
            motor.reset()
            # Fixes the odometer reading bug
            motor.run_timed(speed_sp=500, time_sp=500)

        # Preempts the previous command
        motor.run_forever(speed_sp=scalers[motor]*speed)
    except EXCEPTIONS:
        stop_motors()
        #raise MotorDisconnectedError('Motor disconnected')

def stop_motors(motors=_MOTORS):
    """Stop specified motors.

    Optional Arguments:
    motors -- The motors to stop, defaults to all of them.
    """
    dead_motor = None
    for motor in motors:
        try:
            motor.stop(stop_action=Motor.STOP_ACTION_BRAKE)
        except EXCEPTIONS:
            dead_motor = motor
    if dead_motor:
        raise MotorDisconnectedError("Motor " + str(dead_motor) + " disconnected")

### End Motor Controls ###

##### PID #####

# Persistant state for the PID routine
_last_error = 0
_integral = 0
# TODO: All motors are used, just pass the _MOTORS object
def _course_correction(delta_time, front=_MOTORS.front, back=_MOTORS.back,
                       lefty=_MOTORS.left, righty=_MOTORS.right):
    """Default course correction routine, uses PID controller.

    Required Arguments:
    delta_time -- The time elapsed since the last call to _course_correction.

    Optional Arguments:
    motors -- The motors available for use, intended for dependency injection.
    """

    global _last_error
    global _integral

    try:
        ref_read = read_reflect()
    except EXCEPTIONS:
        stop_motors()
        raise ReflectivityDisconnectedError('Reflectivity sensor disconnected')

    error = _TARGET - (100 * (ref_read - _MINREF) / (_MAXREF - _MINREF))
    derivative = (error - _last_error) / delta_time
    _last_error = error
    _integral = 0.5 * _integral + error
    course = -(_KP * error - _KD * derivative + _KI * _integral * delta_time)

    motors_with_speeds = zip([lefty, righty, front, back],
                             pid_speeds(course, _DEFAULT_RUN_SPEED, _WHEEL_CIRCUM, _ROBOT_DIAMETER))
    for (motor, speed) in motors_with_speeds:
        run_motor(motor, speed)
    #time.sleep(0.00)

### End PID ###

##### Movement #####

def _move_distance(dist, direction):
    ticks = _straight_line_odometry(dist)
    traveled = 0

    motors, should_reverse = _MOTOR_PARAMS[direction]
    multiplier = -1 if should_reverse else 1

    for motor in motors:
        run_motor(motor, speed=multiplier*_DEFAULT_RUN_SPEED, reset=True)

    while True:
        try:
            if sonar_poll() < _SONAR_DIST:
                stop_motors()
                break
        except EXCEPTIONS:
            stop_motors()
            raise SonarDisconnectedError('Sonar disconnected')

        odometer_readings = tuple(map(_read_odometer, motors))
        traveled = _parse_by_average(odometer_readings)

        if traveled > ticks:
            stop_motors()
            break

### End Movement ###

##### Exports #####

# TODO: Disable junction search when there is no correction
def forward(dist, tolerance, junction_type=Junctions.NORMAL, correction=True):
    if correction:
        upper = int(_straight_line_odometry(dist + (tolerance/100 * dist)))
        lower = int(_straight_line_odometry(dist - (tolerance * dist)))

        traveled = 0
        previous_time = time.time()

        search_color = _JUNCTION_MARKERS[junction_type]

        run_motor(_MOTORS.left, reset=True)
        run_motor(_MOTORS.right, reset=True)

        while True:
            try:
                if sonar_poll() < _SONAR_DIST:
                    stop_motors()
                    break
            except EXCEPTIONS:
                stop_motors()
                raise SonarDisconnectedError('Sonar disconnected')

            if _PID_CALIBRATION:
                btn.process()

            delta_time = time.time() - previous_time
            previous_time = time.time()
            _course_correction(delta_time)

            odometer_readings = tuple(map(_read_odometer, [_MOTORS.left, _MOTORS.right]))
            traveled = _parse_by_average(odometer_readings)

            try:
                junction_marker = _detect_color(search_color)
            except EXCEPTIONS:
                stop_motors()
                raise ColorDisconnectedError('Color sensor disconnected')
            if junction_marker:
                if traveled <= lower:
                    stop_motors()
                    return False
                else:
                    stop_motors()
                    return True

            if traveled > upper:
                stop_motors()
                return False
    else:
        _move_distance(dist, Directions.FORWARD)

def backward(dist):
    _move_distance(dist, Directions.BACKWARD)

def left(dist):
    _move_distance(dist, Directions.LEFT)

def right(dist):
    _move_distance(dist, Directions.RIGHT)

def rotate(angle, tolerance, direction=Directions.ROT_RIGHT):
    upper = int(_rotation_odometry(angle + (tolerance/100 * angle)))
    lower = int(_rotation_odometry(angle - (tolerance/100 * angle)))

    traveled = 0

    multiplier = _MOTOR_PARAMS[direction]

    for motor in _MOTORS:
        run_motor(motor, speed=multiplier[motor]*_DEFAULT_TURN_SPEED, reset=True)

    while True:
        odometer_readings = tuple(map(_read_odometer, [_MOTORS.left, _MOTORS.right, _MOTORS.front, _MOTORS.back]))
        traveled = _parse_by_average(odometer_readings)

        if traveled < lower:
            continue

        if traveled > upper:
            stop_motors()
            return False

        ref = read_reflect()
        if 100 >= ref >= _TARGET:
            stop_motors()
            return True

def test_angle_accuracy():
    primary_speed = -_DEFAULT_RUN_SPEED # overshoots when this value is negative,
                                        # regardless whether turning right or left
    r = primary_speed//2                # turning left/right is done by swapping
    l = primary_speed                   # which primary speed is divided
    non_driver_speed = _delta_deg(l, r, _WHEEL_CIRCUM, _ROBOT_DIAMETER)

    run_motor(_MOTORS.front, r, reset = True)
    run_motor(_MOTORS.back, l, reset = True)
    run_motor(_MOTORS.left, non_driver_speed)
    run_motor(_MOTORS.right, -non_driver_speed)

    previous_time = time.time()
    base_angle_so_far = 0.0
    while base_angle_so_far < 90:
        delta_time = time.time() - previous_time
        previous_time = time.time()
        base_angle_so_far += abs(_omega(l, r, _WHEEL_CIRCUM, _ROBOT_DIAMETER)*delta_time*180/pi)
        print(str(base_angle_so_far) + "<< time-based")
        print(str(_parse_to_omega(_MOTORS.back, _MOTORS.front)) + "<< odometry-based")
        time.sleep(0.05)
    stop_motors()

def desk_approach():
    primary_speed = _DEFAULT_RUN_SPEED
    non_driver_speed = _delta_deg(primary_speed//3, primary_speed, _WHEEL_CIRCUM, _ROBOT_DIAMETER)

    run_motor(_MOTORS.front, -primary_speed, reset = True)
    run_motor(_MOTORS.back, -primary_speed//3, reset = True)
    run_motor(_MOTORS.left, -non_driver_speed)
    run_motor(_MOTORS.right, non_driver_speed)

    while _parse_to_omega(_MOTORS.back, _MOTORS.front) < 45:
        time.sleep(0.05)

    run_motor(_MOTORS.left, primary_speed, reset = True)
    run_motor(_MOTORS.right, primary_speed//3, reset = True)
    run_motor(_MOTORS.front, non_driver_speed)
    run_motor(_MOTORS.back, -non_driver_speed)

    while _parse_to_omega(_MOTORS.right, _MOTORS.left) < 45:
        time.sleep(0.05)

    run_motor(_MOTORS.left, -primary_speed, reset = True)
    run_motor(_MOTORS.right, -primary_speed//3, reset = True)
    run_motor(_MOTORS.front, -non_driver_speed)
    run_motor(_MOTORS.back, non_driver_speed)

    while _parse_to_omega(_MOTORS.right, _MOTORS.left) < 45:
        time.sleep(0.05)

    run_motor(_MOTORS.front, primary_speed, reset = True)
    run_motor(_MOTORS.back, primary_speed//3, reset = True)
    run_motor(_MOTORS.left, non_driver_speed)
    run_motor(_MOTORS.right, -non_driver_speed)

    while _parse_to_omega(_MOTORS.back, _MOTORS.front) < 45:
        time.sleep(0.05)

    stop_motors()

def diagonal(angle):
    primary_speed = _DEFAULT_RUN_SPEED*cos(angle*180/pi)
    secondary_speed = _DEFAULT_RUN_SPEED*sin(angle*180/pi)

    run_motor(_MOTORS.front, secondary_speed, reset = True)
    run_motor(_MOTORS.back, secondary_speed, reset = True)
    run_motor(_MOTORS.left, primary_speed, reset = True)
    run_motor(_MOTORS.right, primary_speed, reset = True)

    time.sleep(2)
    stop_motors()

def rot_timed(direction=Directions.ROT_LEFT):
    angle=90
    ticks = _rotation_odometry(angle)
    traveled = 0

    multiplier = _MOTOR_PARAMS[direction]
    turning_speed = _DEFAULT_RUN_SPEED//2

    for motor in _MOTORS:
        run_motor(motor, speed=multiplier[motor]*turning_speed, reset=True)

    while True:
        odometer_readings = tuple(map(_read_odometer, [_MOTORS.left, _MOTORS.right, _MOTORS.front, _MOTORS.back]))
        traveled = _parse_by_average(odometer_readings)

        if traveled > ticks:
            break
    stop_motors()

### End Exports ###

##### PID Tuning #####

def _changeP(state): # pylint: disable=unused-argument
    global _KP
    _KP += .025
    print("p: " + str(_KP))

def _changeD(state): # pylint: disable=unused-argument
    global _KD
    _KD += 0.005
    print("d: " + str(_KD))

def _changeI(state): # pylint: disable=unused-argument
    global _KI
    _KI += 0.005
    print("i: " + str(_KI))

def _reset(state): # pylint: disable=unused-argument
    global _KP
    _KP = 1
    global _KD
    _KD = 0
    global _KI
    _KI = 0
    print("p: " + str(_KP) + " d: " + str(_KD) + " i: " + str(_KI))

if __name__ == '__main__':
    _PID_CALIBRATION = True
    btn = ev3.Button()
    btn.on_left = _changeP
    btn.on_right = _changeD
    btn.on_down = _changeI
    btn.on_up = _reset
    desk_approach()
    #test_angle_accuracy()
    #diagonal()
    #forward(99999, 50)
    #rot_timed()

### End PID Tuning ###
