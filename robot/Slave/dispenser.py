import ev3dev.ev3 as ev3
from ev3dev.ev3 import Motor
import time
import imp
from collections import namedtuple
from double_map import DoubleMap
from functools import partial
from coroutine import coroutine
import os
from os import path

##### Setup #####

# Read config file
with open('dispenser.conf') as f:
    _CONFIG = imp.load_source('config', '', f)

_PORTMAP = DoubleMap(_CONFIG.port_map)

MOTORS = namedtuple('motors', 'dumper slider')(
    ev3.MediumMotor(_PORTMAP['dumper']),
    ev3.MediumMotor(_PORTMAP['slider'])
)

_ODOMETERS = {}
root = _CONFIG.motor_root
for motor in os.listdir(root):
    # The address file contains the real name of the motor (out*)
    with open(path.join(root, motor, 'address')) as file:
        # Read one line from the file (There should only be 1 line) and
        # strip off trailing whitespace
        name = file.readline().rstrip()
        # Map each motor to the relavent file (getattr allows the addressing
        # of objects by string rather than dot notation)
        _ODOMETERS[getattr(MOTORS, _PORTMAP[name])] = path.join(root, motor, 'position')

SHIFT_FOR_DROP = 70

def _read_odometer(motor):
    """Read the odometer on one motor."""
    with open(_ODOMETERS[motor]) as file:
        # abs as actual direction of rotation is irrelevent
        return abs(int(file.readline()))

def _dump_bracket(bracket):
    if bracket == 1:
        pos = 0
    elif bracket == 2:
        pos = 89
    elif bracket == 3:
        pos = 165
    elif bracket == 4:
        pos = 245
    elif bracket == 5:
        pos = 315

    r = _run_to_dump(pos)
    r.send(None)
    r.send(None)

class stop:
    def __init__(self, bracket):
        if bracket == 1:
            self.pos = 49
        elif bracket == 2:
            self.pos = 121
        elif bracket == 3:
            self.pos = 193
        elif bracket == 4:
            self.pos = 273
        self.__call__()

    def __call__(self):
        self.r = _run_to_stop(self.pos)

    def go_further(self):
        self.r.send(None)

@coroutine
def _base_run_to(pos, in_between_action = None, shifted_return = False):

    if in_between_action is None:
        in_between_action = lambda: None

    _motor_setup(MOTORS.slider, pos, speed = 500)
    _coast()
    yield
    if shifted_return:
        pos -= SHIFT_FOR_DROP
    in_between_action()
    _coast()
    yield
    _motor_debrief(MOTORS.slider, pos, speed = 500)

    # making sure the motor touches the end
    MOTORS.slider.run_timed(speed_sp=-100, time_sp=500)
    _wait_for_motor(MOTORS.slider)
    time.sleep(0.5) # give the motor time to settle
    yield

def _coast():
    MOTORS.slider.stop_action=Motor.STOP_ACTION_COAST
    MOTORS.slider.run_timed(speed_sp=0, time_sp=0)

def _run_to_dump(pos):
    func = partial(_base_run_to, pos, in_between_action = _raise_dumper)
    return func()

def _run_to_stop(pos):
    func = partial(_base_run_to, pos, in_between_action = _drop_letter, shifted_return = True)
    return func()

def _motor_setup(motor, pos, speed = 500):
    # solving a wierd bug, where the motor doesn't move w/o this line
    motor.run_timed(speed_sp=500, time_sp=500)
    _run_to_rel_pos(motor, pos, speed, precise = True)

def _motor_debrief(motor, pos, speed = 500, precise = True):
    # solving a wierd bug, where the motor doesn't move w/o this line
    motor.run_timed(speed_sp=500, time_sp=500)
    _run_to_rel_pos(motor, -pos, speed, stop_action = Motor.STOP_ACTION_COAST, precise = precise)

## IN-BETWEEN ACTIONS ##
def _raise_dumper():
    # solving a wierd bug, where the motor doesn't move w/o this line
    MOTORS.dumper.run_timed(speed_sp=500, time_sp=500)
    _run_to_rel_pos(MOTORS.dumper, 120, 500)
    time.sleep(0.5) # wait for 2 seconds for the letter to slide out
    _shaky_shaky()
    time.sleep(2)
    _run_to_rel_pos(MOTORS.dumper, -160, 500, precise = True, stop_action = Motor.STOP_ACTION_COAST)
    # fed a slightly larger value to reset itself on the bottom

def _drop_letter():
    # shifts slot to one over, to drop letter
    _motor_debrief(MOTORS.slider, SHIFT_FOR_DROP, speed = 200, precise = False)

def _shaky_shaky():
    _run_to_rel_pos(MOTORS.dumper, -30, 500)
    _run_to_rel_pos(MOTORS.dumper, 30, 500)
    _run_to_rel_pos(MOTORS.dumper, -30, 500)
    _run_to_rel_pos(MOTORS.dumper, 30, 500)
    _run_to_rel_pos(MOTORS.dumper, -30, 500)
    _run_to_rel_pos(MOTORS.dumper, 30, 500)

########################

def _wait_for_motor(motor):
    time.sleep(0.1) # Make sure that motor has time to start
    while motor.state==["running"]:
        # print(_read_odometer(motor))
        pass

def _run_to_rel_pos(motor, pos, speed, stop_action = Motor.STOP_ACTION_HOLD, precise = False):
    # making it into flag
    precise = not precise
    motor.reset()
    abspos = abs(pos)

    if pos < 0:
        speed *= -1
    # print("reset odometry: " + str(_read_odometer(motor)))
    motor.run_forever(speed_sp = speed)
    init_time = time.time()
    odometry = _read_odometer(motor)

    while (odometry < abspos and time.time() - init_time < abspos/100 + .9):
        if precise == False and odometry > abspos - 60:
            precise = True
            motor.run_forever(speed_sp = speed/5)
        # print("pos: " + str(pos))
        # print("odometer: " + str(_read_odometer(motor)))
        # print("time cap: " + str(abspos/100 + .9))
        # print("time: " + str(time.time() - init_time))
        odometry = _read_odometer(motor)
    motor.stop(stop_action=stop_action)
    # print("final odometry: " + str(_read_odometer(motor)))


def reset_dumper():
    MOTORS.slider.run_timed(speed_sp = -100, time_sp = 3000)
    _wait_for_motor(MOTORS.slider)
    time.sleep(0.5)
    # making sure the motor touches the end
    MOTORS.slider.run_timed(speed_sp=-100, time_sp=500)
    _wait_for_motor(MOTORS.slider)
    time.sleep(0.5) # give the motor time to settle

def dump(bracket):
    _dump_bracket(bracket)
