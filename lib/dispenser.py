import ev3dev.ev3 as ev3
from ev3dev.ev3 import Motor
import time
import imp
from collections import namedtuple
from double_map import DoubleMap
import utilities as util

##### Setup #####

# Read config file
with open('dispenser.conf') as f:
    _CONFIG = imp.load_source('config', '', f)

_PORTMAP = DoubleMap(_CONFIG.port_map)

MOTORS = namedtuple('motors', 'dumper slider')(
    ev3.MediumMotor(_PORTMAP['dumper']),
    ev3.MediumMotor(_PORTMAP['slider'])
)

def _selectBracket(bracket):
    if bracket == 1:
        _runSlider(0)
    elif bracket == 2:
        _runSlider(100)
    elif bracket == 3:
        _runSlider(175)
    elif bracket == 4:
        _runSlider(260)
    elif bracket == 5:
        _runSlider(325)

def _runSlider(pos):
    _motorSetup(MOTORS.slider, pos)
    _raiseDumper()
    _motorDebrief(MOTORS.slider, pos)

    # making sure the motor touches the end
    MOTORS.slider.run_timed(speed_sp=-100, time_sp=300)
    _waitForMotor(MOTORS.slider)

def _raiseDumper():
    _motorSetup(MOTORS.dumper, 145)
    time.sleep(2) # wait for 2 seconds for the letter to slide out
    _motorDebrief(MOTORS.dumper, 145)

def _motorSetup(motor, pos):
    motor.stop_action=Motor.STOP_ACTION_HOLD
    # solving a wierd bug, where the motor doesn't move w/o this line
    motor.run_timed(speed_sp=500, time_sp=500)
    motor.run_to_rel_pos(position_sp=pos, speed_sp=500)
    _waitForMotor(motor)

def _motorDebrief(motor, pos):
    motor.stop_action=Motor.STOP_ACTION_COAST
    motor.run_to_rel_pos(position_sp=-pos, speed_sp=500)
    _waitForMotor(motor)

def _waitForMotor(motor):
    time.sleep(0.1)         # Make sure that motor has time to start
    while motor.state==["running"]:
        time.sleep(0.1)

def dump(bracket):
    _selectBracket(bracket)
