import ev3dev.ev3 as ev3
from ev3dev.ev3 import Motor
import time
import imp
from collections import namedtuple
from double_map import DoubleMap
from functools import partial
from coroutine import coroutine

##### Setup #####

# Read config file
with open('dispenser.conf') as f:
    _CONFIG = imp.load_source('config', '', f)

_PORTMAP = DoubleMap(_CONFIG.port_map)

MOTORS = namedtuple('motors', 'dumper slider')(
    ev3.MediumMotor(_PORTMAP['dumper']),
    ev3.MediumMotor(_PORTMAP['slider'])
)

def _dump_bracket(bracket):
    if bracket == 1:
        pos = 0
    elif bracket == 2:
        pos = 100
    elif bracket == 3:
        pos = 175
    elif bracket == 4:
        pos = 260
    elif bracket == 5:
        pos = 325

    r = _run_to_dump(pos)
    r.send(None)
    r.send(None)

class stop:
    def __init__(self, bracket):
        if bracket == 1:
            self.pos = 54
        elif bracket == 2:
            self.pos = 132
        elif bracket == 3:
            self.pos = 207
        elif bracket == 4:
            self.pos = 286
        self.__call__()

    def __call__(self):
        self.r = _run_to_stop(self.pos)

    def go_further(self):
        self.r.send(None)

@coroutine
def _base_run_to(pos, in_between_action = None, shifted_return = False):

    if in_between_action is None:
        in_between_action = lambda: None

    _motor_setup(MOTORS.slider, pos, speed = 100)
    _coast()
    yield
    if shifted_return:
        pos -= 70
    in_between_action()
    _coast()
    yield
    _motor_debrief(MOTORS.slider, pos, speed = 100)

    # making sure the motor touches the end
    MOTORS.slider.run_timed(speed_sp=-100, time_sp=500)
    _wait_for_motor(MOTORS.slider)
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
    motor.stop_action=Motor.STOP_ACTION_HOLD
    # solving a wierd bug, where the motor doesn't move w/o this line
    motor.run_timed(speed_sp=500, time_sp=500)
    motor.run_to_rel_pos(position_sp=pos, speed_sp=speed)
    _wait_for_motor(motor)

def _motor_debrief(motor, pos, speed = 500):
    motor.stop_action=Motor.STOP_ACTION_COAST
    # solving a wierd bug, where the motor doesn't move w/o this line
    motor.run_timed(speed_sp=500, time_sp=500)
    motor.run_to_rel_pos(position_sp=-pos, speed_sp=speed)
    _wait_for_motor(motor)

## IN-BETWEEN ACTIONS ##
def _raise_dumper():
    _motor_setup(MOTORS.dumper, 145)
    time.sleep(2) # wait for 2 seconds for the letter to slide out
    _motor_debrief(MOTORS.dumper, 145)

def _drop_letter():
    # shifts slot to one over, to drop letter
    _motor_debrief(MOTORS.slider, 70, speed = 100)
########################

def _wait_for_motor(motor):
    time.sleep(0.1) # Make sure that motor has time to start
    while motor.state==["running"]:
        time.sleep(0.1)

def dump(bracket):
    _dump_bracket(bracket)
