#!/usr/bin/env python3
"""Wrapper library for moving the ev3"""

# pylint: disable=fixme, import-error, wildcard-import, missing-docstring,
# pylint: disable=no-member, redefined-outer-name, invalid-name,
# pylint: disable=global-statement, no-else-return, too-many-arguments,
# pylint: disable=too-many-locals, too-many-branches

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
from double_map import DoubleMap
from sensors import read_color, sonar_poll, read_reflect
from PID import pid_speeds
from DisconnectedErrors import (EXCEPTIONS, MotorDisconnectedError,
                                SonarDisconnectedError,
                                ReflectivityDisconnectedError)

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

def init():
    # Pull in Globals to initalise module state
    global _ODOMETERS, _MOTORS, _WHEEL_CIRCUM, _BASE_ROT_TO_WHEEL_ROT
    global _DEFAULT_RUN_SPEED, _SCALERS, _ROBOT_DIAMETER, _DEFAULT_MULTIPLIER
    global _MAXREF, _MINREF, _TARGET, _KP, _KD, _KI, _MOTOR_PARAMS

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

    # Bi-directional map linking human readable motor names to their ports in
    # the brick
    portmap = DoubleMap(config.port_map)

    # Named tuples are light weight immutable objects that respond to dot
    # notation, the names of the attributes are given in the second string of
    # the constructor
    MOTORS = namedtuple('motors', 'front back left right')(
        ev3.LargeMotor(portmap['front']), # Front
        ev3.LargeMotor(portmap['back']),  # Back
        ev3.LargeMotor(portmap['left']),  # Left
        ev3.LargeMotor(portmap['right'])  # Right
    )

    # Normalises the direction of each motor (Left to right axis drives forward,
    # front to back axis drives right)
    _SCALERS = {MOTORS.front : config.scalers['front'],
                MOTORS.back  : config.scalers['back'],
                MOTORS.left  : config.scalers['left'],
                MOTORS.right : config.scalers['right']}

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
            _ODOMETERS[getattr(MOTORS, portmap[name])] = path.join(root, motor, 'position')

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
                     Directions.ROT_LEFT  : {_MOTORS.front :  1,
                                             _MOTORS.back  : -1,
                                             _MOTORS.left  : -1,
                                             _MOTORS.right :  1},
                     Directions.ROT_RIGHT : {_MOTORS.front : -1,
                                             _MOTORS.back  :  1,
                                             _MOTORS.left  :  1,
                                             _MOTORS.right : -1}}
    _MAXREF = config.max_ref
    _MINREF = config.min_ref
    _TARGET = config.target_ref
    _KP = config.KP
    _KD = config.KD
    _KI = config.KI
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
    dead_motor = motors.back # disconnected motor is the back motor by default
    bool_dead = False
    for motor in motors:
        try:
            motor.stop(stop_action=Motor.STOP_ACTION_BRAKE)
        except EXCEPTIONS:
            bool_dead = True
            dead_motor = motor
    if bool_dead:
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
    time.sleep(0.00)

### End PID ###

##### PID Tuning #####

def changeP(state): # pylint: disable=unused-argument
    global _KP
    _KP += .025
    print("p: " + str(_KP))

def changeD(state): # pylint: disable=unused-argument
    global _KD
    _KD += 0.005
    print("d: " + str(_KD))

def changeI(state): # pylint: disable=unused-argument
    global _KI
    _KI += 0.005
    print("i: " + str(_KI))

def reset(state): # pylint: disable=unused-argument
    global _KP
    _KP = 1
    global _KD
    _KD = 0
    global _KI
    _KI = 0
    print("p: " + str(_KP) + " d: " + str(_KD) + " i: " + str(_KI))

### End PID Tuning ###

##### Movement #####

def _base_move(dist, tolerance, motors, speed=_DEFAULT_RUN_SPEED, multiplier=None,
               distance=None, odometry=None, rotating=False, correction=None):
    """Base control loop for moving, behavior is managed by arguments and
    customised by the movement functions below

    Required Arguments:
    dist -- The 'distance' that should be traveled, meaning of distance is
            determined by the distance argument
    motors -- The motors that should be used for this motion

    Optional Arguments:
    speed -- The base speed of the motors
    multiplier -- A dict contiaining 1 or -1 for each motor, used to affect the
                  direction of each motor individually
    distance -- The distance measure to use, it should be a function that
                accepts the distance to travel and returns the number of degrees
                the drive wheels should move through. It defaults to the
                identity function
    odometry -- Strategy for unifying individual odometer readings into a single
                number. It will be passed a tuple containing the reading for
                each motor.
    correction -- Course correction routine. It will be passed a member of the
                  Turning Enum indicating the direction the robot is currently
                  turning. It should also return a member of Turning.
    """

    if multiplier is None:
        multiplier = _DEFAULT_MULTIPLIER
    if distance is None:
        distance = lambda x: x
    if odometry is None:
        odometry = _parse_by_average

    ticks = distance(dist)
    traveled = 0
    previous_time = time.time()
    for motor in motors:
        run_motor(motor, speed=multiplier[motor]*speed, reset=True)
    while traveled < ticks + tolerance:
        print(traveled)
        print(ticks)
        # TODO: We have a specific exception for Color disconnect
        try:
            junction_marker = _detect_color(Colors.BLACK)
            if sonar_poll() < 12:
                stop_motors()
                break
        except EXCEPTIONS:
            stop_motors()
            raise SonarDisconnectedError('Sonar/Color sensor disconnected')
        #btn.process()

        if correction is not None:
            delta_time = time.time() - previous_time
            previous_time = time.time()
            correction(delta_time)

        odometer_readings = tuple(map(_read_odometer, motors))
        traveled = odometry(odometer_readings)

        if rotating:
            if traveled >= ticks - tolerance:
                try:
                    ref_read = read_reflect()
                except EXCEPTIONS:
                    stop_motors()
                    raise ReflectivityDisconnectedError('Reflectivity sensor disconnected')
                if _MAXREF >= ref_read >= _TARGET:
                    print("rot win")
                    return True

        else:
            if junction_marker:
                if traveled <= ticks - tolerance:
                    stop_motors()
                    print("print dist undershoot")
                    return False
                else:
                    stop_motors()
                    print("dist win")
                    return True

        if traveled >= ticks + tolerance:
            stop_motors()
            print("overshoot")
            return False

def _generic_axis(dist, tolerance, direction, correction=False):
    # TODO: Check incomming direction enum, correction can only be true when
    # direction is FORWARD
    """Specialization of _base_move for axis motions (forward, backward, left
    and right)

    Required Arguments:
    dist -- Distance in cm to move
    direction -- Member of the Directions Enum, indicates which direction to
                 move (Note: ROT_* members are invalid but this is never
                 checked)

    Optional Arguments:
    correction -- If true apply course correction to this motion, defaults to
                  false (Note: due to the placement of the sensors this is only
                  applicable to forward motion, this is also never checked)
    """

    # Get the relavent parameters
    motors, should_reverse = _MOTOR_PARAMS[direction]

    # Partially apply some of the arguments of _base_move now we know them
    func = partial(_base_move, dist, tolerance, motors, distance=_straight_line_odometry)

    # If we need course correction add that too
    if correction:
        func = partial(func, correction=_course_correction)

    # If we need to reverse motors make a copy of the _DEFAULT_MULTIPLIER dict,
    # change the relavant values and add that (dict constructor does a shallow
    # copy but as ints are immutable this is ok and cheaper than a full copy)
    if should_reverse:
        multiplier = dict(_DEFAULT_MULTIPLIER)
        for motor in motors:
            multiplier[motor] = -1
        func = partial(func, multiplier=multiplier)
    return func()

### End Movement ###

##### Exports #####
# The only interesting thing here is forward has course correction on by default
# but can have it turned off by setting it's correction argument to false, the
# rest don't provide a means to turn course correction on. Also every function
# here must return the result of calling the lower level move function in order
# to pass the thread object up to where it is needed
def forward(dist, tolerance, correction=True):
    """Move forward.

    Required Arguments:
    dist -- distance to move in cm

    Optional Arguments:
    correction -- Set to False to disable course correction
    """

    return _generic_axis(dist, tolerance, Directions.FORWARD, correction=correction)

def backward(dist, tolerance):
    """Move backward.

    Required Arguments:
    dist -- distance to move in cm
    """
    return _generic_axis(dist, tolerance, Directions.BACKWARD)

def left(dist, tolerance):
    """Move left.

    Required Arguments:
    dist -- distance to move in cm
    """
    return _generic_axis(dist, tolerance, Directions.LEFT)

def right(dist, tolerance):
    """Move right.

    Required Arguments:
    dist -- distance to move in cm
    """
    return _generic_axis(dist, tolerance, Directions.RIGHT)

# Direction of rotation defaults to left but can be set, this one calls directly
# into _base_move
def rotate(angle, tolerance, direction=Directions.ROT_RIGHT):
    """Rotate inplace.

    Required Arguments:
    angle -- Angle to rotate through, in degrees

    Optional Arguments:
    direction -- Member of the Directions Enum, the direction to rotate it
                 defaults to ROT_LEFT. ROT_RIGHT is also applicable, no
                 other members are and this is never checked
    """

    motors, multiplier = _MOTOR_PARAMS[direction]
    _base_move(angle, tolerance, motors, multiplier=multiplier, rotating=True,
               distance=_rotation_odometry)

# TODO, this can just be rotate
def turn_junction(angle, tolerance):
    rotate(angle, tolerance)
### End Exports ###

if __name__ == '__main__':
    btn = ev3.Button()
    btn.on_left = changeP
    btn.on_right = changeD
    btn.on_down = changeI
    btn.on_up = reset

    if forward(20, 395):
        turn_junction(50, 5)
