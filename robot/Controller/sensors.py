"""Wrapper around sensor input for the robot"""

import ev3dev.ev3 as ev3
import Colors

_LEFT = ev3.ColorSensor('in2')
_RIGHT = ev3.ColorSensor('in4')
_ULTRA_SONIC = ev3.UltrasonicSensor('in1')
if not _LEFT.connected:
    raise AssertionError('Left sensor not connected')
if not _RIGHT.connected:
    raise AssertionError('Right sensor not connected')
_LEFT.mode = 'COL-COLOR'
_RIGHT.mode = 'COL-COLOR'

def read_color():
    """Convert colors sensor output into members of the Colors Enum"""
    return (Colors(_LEFT.value()+1), Colors(_RIGHT.value()+1))

def sonar_poll():
    """Read the sonar sensor"""
    return _ULTRA_SONIC.distance_centimeters
