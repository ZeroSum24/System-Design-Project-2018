import ev3dev.ev3 as ev3
from ev3dev.ev3 import Motor
import time
import imp
from collections import namedtuple
from double_map import DoubleMap
import utilities as util
from functools import partial

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
        _run_to_dump(0)
    elif bracket == 2:
        _run_to_dump(100)
    elif bracket == 3:
        _run_to_dump(175)
    elif bracket == 4:
        _run_to_dump(260)
    elif bracket == 5:
        _run_to_dump(325)

def _stop_bracket(bracket):
    if bracket == 1:
        _run_to_stop(54)
    elif bracket == 2:
        _run_to_stop(137)
    elif bracket == 3:
        _run_to_stop(212)
    elif bracket == 4:
        _run_to_stop(298)

def _base_run_to(pos, in_between_action = None):

    if in_between_action is None:
        in_between_action = lambda: None

    _motor_setup(MOTORS.slider, pos)
    in_between_action()
    _motor_debrief(MOTORS.slider, pos)

    # making sure the motor touches the end
    MOTORS.slider.run_timed(speed_sp=-100, time_sp=300)
    _wait_for_motor(MOTORS.slider)

def _run_to_dump(pos):
    func = partial(_base_run_to, pos, in_between_action = _raise_dumper)
    return func()

def _raise_dumper():
    _motor_setup(MOTORS.dumper, 145)
    time.sleep(2) # wait for 2 seconds for the letter to slide out
    _motor_debrief(MOTORS.dumper, 145)

def _run_to_stop(pos):
    func = partial(_base_run_to, pos, in_between_action = _scan_letter)
    return func()

def _scan_letter():
    # to be implemented
    time.sleep(2)

def _motor_setup(motor, pos):
    motor.stop_action=Motor.STOP_ACTION_HOLD
    # solving a wierd bug, where the motor doesn't move w/o this line
    motor.run_timed(speed_sp=500, time_sp=500)
    motor.run_to_rel_pos(position_sp=pos, speed_sp=500)
    _wait_for_motor(motor)

def _motor_debrief(motor, pos):
    motor.stop_action=Motor.STOP_ACTION_COAST
    motor.run_to_rel_pos(position_sp=-pos, speed_sp=500)
    _wait_for_motor(motor)

def _wait_for_motor(motor):
    time.sleep(0.1)         # Make sure that motor has time to start
    while motor.state==["running"]:
        time.sleep(0.1)

def dump(bracket):
    _dump_bracket(bracket)

def stop(bracket):
    _stop_bracket(bracket)
