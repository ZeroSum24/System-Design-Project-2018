#!/usr/bin/env python3
"""Wrapper library for moving the ev3"""

import imp
import os
from os import path
from math import pi, sin, cos
from collections import namedtuple
import time

import speech_lib

import ev3dev.ev3 as ev3
from ev3dev.ev3 import Motor
from ev3dev.auto import *

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
_STOP_TIMEOUT = None
_JUNCTION_MARKERS = None
# PID calibration flag
_PID_CALIBRATION = False

def init():
    # Pull in Globals to initalise module state
    global _ODOMETERS, _MOTORS, _WHEEL_CIRCUM, _BASE_ROT_TO_WHEEL_ROT
    global _DEFAULT_RUN_SPEED, _DEFAULT_TURN_SPEED, _SCALERS, _ROBOT_DIAMETER
    global _DEFAULT_MULTIPLIER, _MAXREF, _MINREF, _TARGET, _KP, _KD, _KI
    global  _MOTOR_PARAMS, _SONAR_DIST, _STOP_TIMEOUT,_JUNCTION_MARKERS

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
                                             _MOTORS.left  :  1,
                                             _MOTORS.right : -1},
                     Directions.ROT_LEFT : {_MOTORS.front : -1,
                                            _MOTORS.back  :  1,
                                            _MOTORS.left  : -1,
                                            _MOTORS.right :  1}}
    _MAXREF = config.max_ref
    _MINREF = config.min_ref
    _TARGET = config.target_ref
    _KP = config.KP
    _KD = config.KD
    _KI = config.KI
    _SONAR_DIST = config.sonar_dist
    _STOP_TIMEOUT = config.stop_timeout
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

def _detect_color(color=Colors.GREEN):
    return read_color() is color

def get_odometry(rotating=False):
    if rotating:
        # Map is lazy by default, tuple forces strict evaluation
        odometer_readings = tuple(map(_read_odometer, [_MOTORS.left, _MOTORS.right, _MOTORS.front, _MOTORS.back]))
        return _rev_rotation_odometry(_parse_by_average(odometer_readings))
    else:
        odometer_readings = tuple(map(_read_odometer, [_MOTORS.left, _MOTORS.right]))
        return _rev_straight_line_odometry(_parse_by_average(odometer_readings))

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

def _rev_rotation_odometry(angle):
    # Reverse of _rotation_odometry
    return angle / _BASE_ROT_TO_WHEEL_ROT

def _rev_straight_line_odometry(dist):
    # Same for straight line
    return (dist * _WHEEL_CIRCUM) // 360

### End Distance Measures ###

##### Motor Controls #####
def run_motor(motor, speed=_DEFAULT_RUN_SPEED, scalers=None, reset=False):
    """Run the specified motor forever.

    Required Arguments:
    motor -- A LargeMotor object representing the motor to run.

    Optional Arguments:
    speed -- Speed to run the motor at.
    scalers -- Dict containing scalers to influence the motor's speed
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
    motors -- The motors available for use.
    """

    #global _last_error
    global _integral

    try:
        ref_read = read_reflect()
    except EXCEPTIONS:
        stop_motors()
        raise ReflectivityDisconnectedError('Reflectivity sensor disconnected')

    # Percentage deviation from the target reflectivity
    error = _TARGET - (100 * (ref_read - _MINREF) / (_MAXREF - _MINREF))
    #derivative = (error - _last_error) / delta_time
    #_last_error = error
    # _intergral collects every past error with ever decreasing performance
    _integral = 0.5 * _integral + error
    # PID calculation without the D
    course = _KP * error + _KI * _integral * delta_time #- _KD * derivative

    # Pairs up each motor with the speeds required to make the current turn
    motors_with_speeds = zip([lefty, righty, front, back],
                             pid_speeds(course, _DEFAULT_RUN_SPEED,
                                        _WHEEL_CIRCUM, _ROBOT_DIAMETER))
    # Run each
    for (motor, speed) in motors_with_speeds:
        run_motor(motor, speed)

### End PID ###

##### Movement #####

# Move a fixed distance in the given direction, only check for obstructions
# infront of the robot via the sonar (Note: infront is the direction the robot
# goes when told to go forward, for all other directions the sonar is on the
# wrong face of the robot, this is as stupid as it sounds, this function is
# unused however)
def _move_distance(dist, direction):
    # Convert the distance to travel into the number of degrees of rotation of
    # the wheel
    ticks = _straight_line_odometry(dist)
    traveled = 0

    # Decide which motors to use and what direction they should go in
    motors, should_reverse = _MOTOR_PARAMS[direction]
    multiplier = -1 if should_reverse else 1

    # Start running each motor
    for motor in motors:
        run_motor(motor, speed=multiplier*_DEFAULT_RUN_SPEED, reset=True)

    while True:
        # Try to check the sonar and abort if we can't
        try:
            if sonar_poll() < _SONAR_DIST:
                stop_motors()
                break
        except EXCEPTIONS:
            stop_motors()
            raise SonarDisconnectedError('Sonar disconnected')

        # Check how far we have gone
        odometer_readings = tuple(map(_read_odometer, motors))
        traveled = _parse_by_average(odometer_readings)

        # If we've gone too far stop
        if traveled > ticks:
            stop_motors()
            break

### End Movement ###

##### Exports #####

# TODO: Disable junction search when there is no correction
def forward(dist, tolerance=50, junction_type=Junctions.DESK, correction=True):
    """Go forward a distance with tolerance, stop when a junction is found.

    Required Arguments:
    dist -- The distance to travel.

    Optional Arguments:
    tolerance -- Percentage tolerance, the robot will start searching for
                 junctions at the lower bound and panic if it exceeds the upper
                 bound without finding any.
    junction_type -- Legacy parameter. This is ignored.
    correction -- If False PID correction will be disabled, this has no
                  practical use.
    """
    
    if correction:
        # This is the only branch used

        # Calculate the search area
        upper = int(_straight_line_odometry(dist + (tolerance/100 * dist)))
        lower = int(_straight_line_odometry(dist - (tolerance/100 * dist)))

        traveled = 0
        # Track time intervals for PID
        previous_time = time.time()

        # Allows the robot to wait before panicking in responce to an
        # obstruction
        stopped = False
        time_of_stoppage = 0

        # Ignored
        search_color = _JUNCTION_MARKERS[junction_type]

        # Start the drive motors
        run_motor(_MOTORS.left, reset=True)
        run_motor(_MOTORS.right, reset=True)

        while True:
            # Attempt to access the sonar, abort if it doesn't exist
            try:
                # If something is visible in the sonar
                if sonar_poll() < _SONAR_DIST:
                    if not stopped:
                        # If we havent stopped yet then stop
                        stopped = True
                        stop_motors()
                        time_of_stoppage = time.time()
                        speech_lib.obstacle_detected()
                        continue
                    if stopped:
                        # Otherwise iterate all of the above as fast as possible
                        # until the timeout is exceeded, at which point fail
                        if time.time() - time_of_stoppage < _STOP_TIMEOUT:
                            continue
                        else:
                            return False
                else:
                    if stopped:
                        # If at any point the obstruction dissappears keep going
                        stopped = False
                        continue
            except EXCEPTIONS:
                stop_motors()
                raise SonarDisconnectedError('Sonar disconnected')

            #if _PID_CALIBRATION:
            #    btn.process()

            # PID correction
            delta_time = time.time() - previous_time
            previous_time = time.time()
            _course_correction(delta_time)

            # Figure out how far we have gone
            odometer_readings = tuple(map(_read_odometer, [_MOTORS.left, _MOTORS.right]))
            traveled = _parse_by_average(odometer_readings)

            # Try to read the color sensor, abort if it doesn't exist
            try:
                junction_marker = read_color() is Colors.GREEN #_detect_color(search_color)
            except EXCEPTIONS:
                stop_motors()
                raise ColorDisconnectedError('Color sensor disconnected')
            if junction_marker:
                # If we found one
                if traveled <= lower:
                    # If it's too soon ignore it (This will happen at least once
                    # as the robot starts each move segment sitting on the old
                    # junction marker)
                    continue
                else:
                    # Otherwise we found the next junction, return success
                    stop_motors()
                    return True

            # If we went too far abort
            if traveled > upper:
                stop_motors()
                return False
    else:
        # This is never used
        _move_distance(dist, Directions.FORWARD)

# These three are never used
def backward(dist):
    _move_distance(dist, Directions.BACKWARD)

def left(dist):
    _move_distance(dist, Directions.LEFT)

def right(dist):
    _move_distance(dist, Directions.RIGHT)

def rotate(angle, tolerance=50, direction=Directions.ROT_RIGHT):
    """Go rotate through an angle with tolerance, stop when a line is found.

    Required Arguments:
    angle -- The angle to rotate through.

    Optional Arguments:
    tolerance -- Percentage tolerance, the robot will start searching for
                 lines at the lower bound and panic if it exceeds the upper
                 bound without finding any.
    direction -- Direction to rotate in.
    """

    # Calculate the search area
    upper = int(_rotation_odometry(angle + (tolerance/100 * angle)))
    lower = int(_rotation_odometry(angle - (tolerance/100 * angle)))

    traveled = 0

    multiplier = _MOTOR_PARAMS[direction]

    # Run all the motors
    for motor in _MOTORS:
        run_motor(motor, speed=multiplier[motor]*_DEFAULT_TURN_SPEED, reset=True)

    while True:
        # Figure out how far we've gone
        odometer_readings = tuple(map(_read_odometer, [_MOTORS.left, _MOTORS.right, _MOTORS.front, _MOTORS.back]))
        traveled = _parse_by_average(odometer_readings)

        # If we've not reached the search area yet go around again
        if traveled < lower:
            continue

        # If we've found a line (Defined as a something lighter than the floor)
        # stop
        ref = read_reflect()
        if 100 >= ref >= _TARGET:
            stop_motors()
            return True

        # If we exceed the search area abort
        if traveled > upper:
            stop_motors()
            return False

# For the approach motion below
def diagonal_speeds(angle, speed, front=_MOTORS.front, back=_MOTORS.back,
                    lefty=_MOTORS.left, righty=_MOTORS.right):
    # Diagrams are better here but essentially we start with knowlage of what
    # angle we want to travel at and how fast we want to do it. Assuming a unit
    # vector in the direction we want to travel the two calculations below give
    # the lengths of the two axis vectors that form a triangle with the original
    # unit vector. These numbers are the fractions of the desired speed required
    # for each axle to achieve the desired speed and angle.
    primary_speed = speed*cos(angle*pi/180)
    secondary_speed = speed*sin(angle*pi/180)

    return {front  : secondary_speed,
            back   : secondary_speed,
            lefty  : primary_speed,
            righty : primary_speed}

def approach(angle=90, tolerance=50, direction=Directions.ROT_LEFT, reverse = False):
    # Rotation odometry is enough here, as the diagonal movement adds speed in
    # the same direction on opposite wheels, making them cancel out in the
    # _parse_by_average calculation
    traveled = 0
    ticks = _rotation_odometry(angle)
    if reverse: # In case the robot is reversing the angle needs to be phase
                # shifted for the diagonal_speeds calculation; this will result
                # in mirroring the movement backwards - simple sign change is
                # not enough

        # If returning, the robot will search for the white line within these
        # bounds
        upper = int(_rotation_odometry(angle + (tolerance/100 * angle)))
        lower = int(_rotation_odometry(angle - (tolerance/100 * angle)))

        angle+=90
        if direction == Directions.ROT_LEFT: # This ensures that if you do
                                             # forward-left followed by reverse
                                             # left, you will end up in the
                                             # original orientation on the line
            direction = Directions.ROT_RIGHT
        else:
            direction = Directions.ROT_LEFT


    multiplier = _MOTOR_PARAMS[direction]
    turning_speed = _DEFAULT_TURN_SPEED//2 # The turning and driver_speeds are
                                           # halved, so their sum is capped at
                                           # _DEFAULT_RUN_SPEED


    # The angle needs a sign change for diagonal_speeds depending on direction
    if direction == Directions.ROT_LEFT:
        start_angle = -angle
    else:
        start_angle = angle
    driver_speed = diagonal_speeds(start_angle, _DEFAULT_TURN_SPEED-turning_speed)

    # Run all the motors with the correct speeds (The speed for diagonal
    # movement is added to the speed
    for motor in _MOTORS:
        run_motor(motor,
                  speed=multiplier[motor]*turning_speed+driver_speed[motor],
                  reset=True)
    while True:
        # Figure out how far we have gone (The diagonal movement is ignored
        # here, all 'distances' are angles)
        odometer_readings = tuple(map(_read_odometer,
                                      [_MOTORS.left, _MOTORS.right,
                                       _MOTORS.front, _MOTORS.back]))
        traveled = _parse_by_average(odometer_readings)

        if traveled < ticks:
            # Convert angle of wheel rotation into the angle the robot has
            # rotated
            angle_so_far = _rev_rotation_odometry(traveled)
            # The angle needs a sign change for diagonal_speeds depending on direction
            if direction == Directions.ROT_RIGHT:
                angle_so_far = -angle_so_far

            # Adapt to where we are and rerun all the motors with the new speeds
            driver_speed = diagonal_speeds(angle_so_far + start_angle, _DEFAULT_TURN_SPEED-turning_speed)
            for motor in _MOTORS:
                run_motor(motor, speed=multiplier[motor]*turning_speed+driver_speed[motor])

        # Search for a line on the way back
        if reverse:
            # Don't start to search before the lower bound
            if traveled < lower:
                continue

            # If we see the line stop and return success
            ref = read_reflect()
            if 100 >= ref >= _TARGET:
                stop_motors()
                return True

            # If we exceed the upper bound fail
            if traveled > upper:
                stop_motors()
                return False
        else:
            # For the way out, stop when we have gone far enough
            if traveled > ticks:
                break

    stop_motors()

### End Exports ###

##### PID Tuning #####

# None of these are used
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
    forward(99999, 50)

### End PID Tuning ###
