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
    # exception. As read_color is stateful the tuple constructor is used to
    # instantly consume the generator into a tuple preserving the values for
    # safer use later
    return tuple(map(lambda x: x is color, read_color()))

def _get_motor_params(direction, motors=MOTORS):
    """Centeralises the access of the relavent parameters for each kind of
       motion. There's likely a better way of doing this.

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
                         motors.left  : -1,
                         motors.right :  1})
    elif direction is Directions.ROT_LEFT:
        return (motors, {motors.front : -1,
                         motors.back  :  1,
                         motors.left  :  1,
                         motors.right : -1})
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

def run_motor(motor, speed=_DEFAULT_RUN_SPEED, scalers=None, reset=True):
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

    if correct:
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
            # And start running the stopped wheel
            run_motor(motors.left, _DEFAULT_RUN_SPEED, reset=False)
            return Turning.NONE # Stopped turning
        else:
            return correction_flag # Still turning

    # If we are turning left
    elif correction_flag == Turning.LEFT:
        # And we can't see the line in the left sensor
        if not left:
            # Stop running the turning motors
            stop_motors(turning_motors)
            # And start running the stopped wheel
            run_motor(motors.right, _DEFAULT_RUN_SPEED, reset=False)
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
                number. It will be passes a tuple containing the reading for
                each motor.d
    correction -- Course correction routine. It will be passed a member of the
                  Turning Enum indicating the direction the robot is currently
                  turning. It should also return a member of Turning.
    """

    if multiplier is None:
        multiplier = _DEFAULT_MULTIPLIER
    if distance is None:
        distance = lambda x: x
    if odometry is None:
        odometry = _default_odometry
    if correction is None:
        correction = lambda x: Turning.NONE

    # Calculate distance to travel in degrees of rotation
    ticks = distance(dist)
    traveled = 0
    correction_flag = Turning.NONE
    # Start all the motors at the correct speed and direction
    for motor in motors:
        run_motor(motor, speed=multiplier[motor]*speed)
    # While we haven't reached the distance yet
    while traveled < ticks:
        # If the sonar picks up anything stop TODO: Magic number
        if sonar_poll() < 7:
            stop_motors()
            break
        # Attempt course correction
        correction_flag = correction(correction_flag)
        # Produce a tuple of odometer readings
        odometer_readings = tuple(map(_read_odometer, motors))
        # Parse them
        traveled = odometry(odometer_readings)
        # Stop if we have travelled too far
        if traveled >= ticks:
            stop_motors()
            break

def _generic_axis(dist, direction, correction=False):
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
    motors, should_reverse = _get_motor_params(direction)

    # Partially apply some of the arguments of _base_move now we know them
    func = partial(_base_move, dist, motors, distance=_straight_line_odometry)

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
    # Return the result of calling the function (Does the requested motion and
    # returns a thread object back to the caller)
    return func()

# The only interesting thing here is forward has course correction on by default
# but can have it turned off by setting it's correction argument to false, the
# rest don't provide a means to turn course correction on. Also every function
# here must return the result of calling the lower level move function in order
# to pass the thread object up to where it is needed
def forward(dist, correction=True):
    """Move forward.

    Required Arguments:
    dist -- distance to move in cm

    Optional Arguments:
    correction -- Set to False to disable course correction
    """

    return _generic_axis(dist, Directions.FORWARD, correction=correction)

def backward(dist):
    """Move backward.

    Required Arguments:
    dist -- distance to move in cm
    """
    return _generic_axis(dist, Directions.BACKWARD)

def left(dist):
    """Move left.

    Required Arguments:
    dist -- distance to move in cm
    """
    return _generic_axis(dist, Directions.LEFT)

def right(dist):
    """Move right.

    Required Arguments:
    dist -- distance to move in cm
    """
    return _generic_axis(dist, Directions.RIGHT)

# Direction of rotation defaults to left but can be set, this one calls directly
# into _base_move
def rotate(angle, direction=Directions.ROT_LEFT):
    """Rotate inplace.

    Required Arguments:
    angle -- Angle to rotate through, in degrees

    Optional Arguments:
    direction -- Member of the Directions Enum, the direction to rotate it
                 defaults to ROT_LEFT. ROT_RIGHT is also applicable, no
                 other members are and this is never checked
    """

    motors, multiplier = _get_motor_params(direction)
    _base_move(angle, motors, multiplier=multiplier, distance=_rotation_odometry)
