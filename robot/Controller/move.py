#!/usr/bin/env python3
"""Wrapper library for moving the ev3"""

import imp
import os
from os import path
from math import pi, sin, cos
from collections import namedtuple
from functools import partial
import time
import sys

import ev3dev.ev3 as ev3
from ev3dev.ev3 import Motor
from ev3dev.auto import *

import Directions
import Colors
from double_map import DoubleMap
from sensors import read_color, sonar_poll, read_reflect
from thread_decorator import thread, ThreadKiller

# Known exceptions produced when motors or sensors disconnect
EXCEPTIONS = (OSError, FileNotFoundError)

class MotorDisconnectedError(Exception):
    pass

class SonarDisconnectedError(Exception):
    pass

class ReflectivityDisconnectedError(Exception):
    pass

class ColorDisconnectedError(Exception):
    pass

# Known Running threads (So they can be killed on with stop_motors
THREADS = set()

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

def _register_thread(t):
    THREADS.add(t)

def _read_odometer(motor):
    """Read the odometer on one motor."""
    with open(_ODOMETERS[motor]) as file:
        # abs as actual direction of rotation is irrelevent
        return abs(int(file.readline()))

def _default_odometry(readings):
    """By default the actual distance traveled is conservativly estimated as
       the minimum of all supplied readings."""
    return sum(readings)//2

def _detect_color(color=Colors.BLACK):
    return read_color() is color

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
        return (motors.left, motors.right), False
    elif direction is Directions.BACKWARD:
        return (motors.left, motors.right), True
    elif direction is Directions.RIGHT:
        return (motors.front, motors.back), False
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

_last_error = 0
_integral = 0
_MAXREF = 54
_MINREF = 20
_TARGET = 37
_KP = 1.55
_KD = 0.0
_KI = 0.8

def _course_correction(delta_time, front=MOTORS.front, back=MOTORS.back, lefty=MOTORS.left, righty=MOTORS.right):
    """Default course correction routine

    Required Arguments:
    correction_flag -- A member of the Turning enum, indicates which direction
                       if any the robot is currently turning.

    Optional Arguments:
    motors -- The motors available for use, intended for dependency injection.
    scalers -- Dict containing scalers to influence the motor's speed, intended
               for dependency injection.
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

    for (motor, speed) in zip([lefty, righty, front, back], _steering(course, _DEFAULT_RUN_SPEED)):
        run_motor(motor, speed)
    time.sleep(0.00)

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
                                # must move perpendicular to the direction of travel (cm)
    return IC_dist(vel_left, vel_right) - omega_to_axis(vel_left, vel_right)

def delta_deg(vel_left, vel_right): # converting distance to the number of degrees the wheel must move through in a second
    if abs(vel_left-vel_right) > 3:
        return 360 * delta(vel_left, vel_right)/_WHEEL_CIRCUM
    else:
        return 0

def stop_motors(motors=MOTORS):
    """Stop specified motors.

    Optional Arguments:
    motors -- The motors to stop, defaults to all of them.
    """
    # Kill all known movement threads
    for t in THREADS:
        t.stop()

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

    # Supresses ThreadKiller Stack Trace
    try:
        ticks = distance(dist)
        traveled = 0
        previous_time = time.time()
        for motor in motors:
            run_motor(motor, speed=multiplier[motor]*speed, reset = True)
        while traveled < ticks + tolerance:
            print(traveled)
            print(ticks)
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
                print ("overshoot")
                return False

    except ThreadKiller:
        sys.exit()

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
    motors, should_reverse = _get_motor_params(direction)

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

    motors, multiplier = _get_motor_params(direction)
    _base_move(angle, tolerance, motors, multiplier=multiplier, rotating = True, distance=_rotation_odometry)

def turn_junction(angle, tolerance):
    rotate(angle, tolerance)


if __name__ == '__main__':
    btn = ev3.Button()
    btn.on_left = changeP
    btn.on_right = changeD
    btn.on_down = changeI
    btn.on_up = reset

    if forward(20, 395):
        turn_junction(50, 5)
