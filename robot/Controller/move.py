"""Wrapper library for moving the ev3"""

# pylint: disable=import-error, no-member, redefined-outer-name, too-many-arguments
# pylint: disable=no-else-return

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

# Read config file (In python modules are just objects, the basic import syntax
# just parses a file as the definition of a module and places the resulting
# object in the global namespace. imp has hooks to allow user level access to
# the standard import machinery, load_source interprets the given file as python
# code and returns the resulting module object). The with statement is a context
# manager, in the case of files the filehandle created by open is assigned to
# the variable specified after as for the duration of the block, the filehandle
# is gaurenteed to be closed when execution exits the block regardless of how
# that happens. TODO: imp is deprecated in favor of importlib apparently
with open('move.conf') as f:
    _CONFIG = imp.load_source('config', '', f)

# Assign parameters from the config file to global constants
_WHEEL_CIRCUM = _CONFIG.wheel_diameter * pi
_BASE_ROT_TO_WHEEL_ROT = (_CONFIG.robot_diameter * pi) / _WHEEL_CIRCUM
_DEFAULT_RUN_SPEED = _CONFIG.default_run_speed
_DEFAULT_TURN_SPEED = _CONFIG.default_turn_speed

# Bi-directional map linking human readable motor names to their ports in the
# brick
_PORTMAP = DoubleMap(_CONFIG.port_map)

# Named tuples are light weight immutable objects that respond to dot notation,
# the names of the attributes are given in the second string of the constructor
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
       position information (Not stable across boots)."""
    odometers = {}
    for motor in os.listdir(root):
        # The address file contains the real name of the motor (out*)
        with open(path.join(root, motor, 'address')) as file:
            # Read one line from the file (There should only be 1 line) and
            # strip off trailing whitespace
            name = file.readline().rstrip()
            # Map each motor to the relavent file (getattr allows the addressing
            # of objects by string rather than dot notation)
            odometers[getattr(MOTORS, portmap[name])] = path.join(root, motor, 'position')
    return odometers
_ODOMETERS = _get_odometers(_CONFIG.motor_root, _PORTMAP)

### End Setup ###

def _read_odometer(motor):
    """Read the odometer on one motor."""
    with open(_ODOMETERS[motor]) as file:
        # abs as actual direction of rotation is irrelevent
        return abs(int(file.readline()))

def _default_odometry(readings):
    """By default the actual distance traveled is conservativly estimated as
       the minimum of all supplied readings."""
    return min(readings)

def _detect_color(color=Colors.BLACK):
    # Map returns a generator which lazily computes its values, they can't be
    # indexed and can only be consumed once, subsequent attempts result in an
    # exception. As read_color is stateful the tuple constructor it used to
    # instantly consume the generator into a tuple preserving the values for
    # safer use later
    return tuple(map(lambda x: x is color, read_color()))

def _get_motor_params(direction, motors=MOTORS):
    """Centeralises the access of the relavent parameters for each kind of 
       motion. There's likly a better way of doing this.

    Reqired Arguments:
    direction -- A member of the Directions Enum, identifies the kind of motion.

    Optional Arguments:
    motors -- The motors to return, for dependency injection.
    """

    # Forward, Backward, Left and Right recive a tuple containing the motors
    # they should use to drive and a boolean indicating whether the default
    # direction should be reversed
    if direction is Directions.FORWARD:
        return ((motors.left, motors.right), False)
    elif direction is Directions.BACKWARD:
        return ((motors.left, motors.right), True)
    elif direction is Directions.RIGHT:
        return ((motors.front, motors.back), False)
    elif direction is Directions.LEFT:
        return ((motors.front, motors.back), True)

    # The rotations always receive all the motors (TODO: there is no point in
    # doing this) and a dict using the same format as _DEFAULT_MULTIPLER
    # indicating which motors should be reversed
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
    # Die noisily if a direction was missed
    else:
        raise ValueError('Unknown Direction: {}'.format(direction))

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

def run_motor(motor, speed=_DEFAULT_RUN_SPEED, scalers=None):
    """Run the specified motor forever.

    Required Arguments:
    motor -- A LargeMotor object representing the motor to run.

    Optional Arguments:
    speed -- Speed to run the motor at.
    scalers -- Dict containing scalers to influence the motor's speed,
               intended for dependency injection.
    """

    # Mutable structures shouldn't be passed as default arguments. Python
    # evaluates default arguments at definition time not call time so the
    # objects passed as default arguments are always the same across function
    # calls. With mutable structures if the function modifies the argument while
    # using the default further calls of the same function will recive the
    # modified structure. The None trick forces assignment of default arguments
    # at call time
    if scalers is None:
        scalers = _SCALERS

    # Zero the motor's odometer
    motor.reset()
    # Fixes the odometer reading bug
    motor.run_timed(speed_sp=500, time_sp=500)
    # Preempts the previous command
    motor.run_forever(speed_sp=scalers[motor]*speed)

def _course_correction(correction_flag, motors=MOTORS, scalers=None):
    """Default course correction routine

    Required Arguments:
    correction_flag -- A member of the Turning enum, indicates which direction
                       if any the robot is currently turning.

    Optional Arguments:
    motors -- The motors available for use, intended for dependency injection.
    scalers -- Dict containing scalers to influence the motor's speed, intended
               for dependency injection.
    """

    if scalers is None:
        scalers = _SCALERS

    # For clarity below
    turning_motors = (motors.left, motors.right)

    left, right = _detect_color()

    # If we are turning right
    if correction_flag == Turning.RIGHT:
        # And we can't see the line in the right sensor
        if not right:
            # Stop running the turning motors
            stop_motors(turning_motors)
            # And start running the stopped wheel TODO: Resets the odometer in
            # that wheel
            run_motor(motors.left, _DEFAULT_RUN_SPEED)
            return Turning.NONE # Stopped turning
        else:
            return correction_flag # Still turning

    # If we are turning left
    elif correction_flag == Turning.LEFT:
        # And we can't see the line in the left sensor
        if not left:
            # Stop running the turning motors
            stop_motors(turning_motors)
            # And start running the stopped wheel TODO: Resets the odometer in
            # that wheel
            run_motor(motors.right, _DEFAULT_RUN_SPEED)
            return Turning.NONE # Stopped turning
        else:
            return correction_flag # Still turning

    # We are not turning
    else:
        # We can see the line in the right sensor
        if right:
            # Run the front motor right and the back motor left
            run_motor(motors.front, _DEFAULT_TURN_SPEED)
            run_motor(motors.back, -1*_DEFAULT_TURN_SPEED)
            # Stop the left motor
            stop_motors([motors.left])
            # Allows the kernel to shedule other threads if required for sensor
            # input
            time.sleep(0)
            return Turning.RIGHT # Start turning right
        elif left:
            # Run the front motor left and the back motor right
            run_motor(motors.front, -1*_DEFAULT_TURN_SPEED)
            run_motor(motors.back, _DEFAULT_TURN_SPEED)
            # Stop the right motor
            stop_motors([motors.right])
            # Allows the kernel to shedule other threads if required for sensor
            # input
            time.sleep(0)
            return Turning.LEFT # Start turning left

def stop_motors(motors=MOTORS):
    """Stop specified motors.

    Optional Arguments:
    motors -- The motors to stop, defaults to all of them.
    """

    for motor in motors:
        motor.stop(stop_action=Motor.STOP_ACTION_BRAKE)

# Force the function onto a background thread, function now returns the thread
# it is running on
@thread
def _base_move(dist, motors, speed=_DEFAULT_RUN_SPEED, multiplier=None,
               distance=None, odometry=None, correction=None):
    """Base controll loop for moving, behavior is managed by arguments and 
    customised by the movement functions below

    Required Arguments:
    dist -- The 'distance' that should be traveled, meaning of distance is 
            determined by the distance argument
    motors -- The motors that should be used for this motion"""

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
    correction_flag = Turning.NONE
    for motor in motors:
        run_motor(motor, speed=multiplier[motor]*speed)
    while traveled < ticks:
        if sonar_poll() < 7:
            stop_motors()
            break
        correction_flag = correction(correction_flag)
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
