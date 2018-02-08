from ev3dev.ev3 import *
import Colors

left = ColorSensor('in2')
right = ColorSensor('in4')
ultra_sonic = UltrasonicSensor('in1')
if not left.connected:
    raise AssertionError('Left sensor not connected')
if not right.connected:
    raise AssertionError('Right sensor not connected')
left.mode = 'COL-REFLECT'
right.mode = 'COL-COLOR'

def read_color():
    return (Colors(left.value()+1), Colors(right.value()+1))

def sonar_poll():
    return ultra_sonic.distance_centimeters


def read_reflect():
    return left.value()


# Original code
'''
MARGIN = 50
BLUE = (40,80,140, colors.BLUE)
GREEN = (30, 50, 30, colors.GREEN)
RED = (220, 30, 30, colors.RED)
YELLOW = (260, 210, 60, colors.YELLOW)
BLACK = (10, 10, 10, colors.BLACK)
WHITE = (290, 230, 250, colors.WHITE)
FLOOR = (100, 130, 150, colors.FLOOR) #change so floor is anything not a color

list_of_colors = [FLOOR, BLUE, RED, GREEN, BLACK, YELLOW, WHITE]

def find_color_manual():
  cs1= ColorSensor("in1")
  cs2= ColorSensor("in2")
  assert cs1.connected, "Connect a single sensor"
  cs1.mode="RGB-RAW"
  assert cs2.connected, "Connect a single sensor"
  cs2.mode="RGB-RAW"
  while True:
    print("Sensor 1: " + str(color_classify(cs1.value(0), cs1.value(1), cs1.value(2))))
    print("Sensor 2: " + str(color_classify(cs2.value(0), cs2.value(1), cs2.value(2))))
    print("")

    print("RED1: " + str(cs1.value(0)))
    print("RED2: " + str(cs2.value(0)))
    print("")
    print("GREEN1: " + str(cs1.value(1)))
    print("GREEN2: " + str(cs2.value(1)))
    print("")
    print("BLUE1: " + str(cs1.value(2)))
    print("BLUE2: " + str(cs2.value(2)))
    print("")
    print("")
    sleep(2)


def color_classify(red, green, blue):
  for option in list_of_colors:
    if option[0] - MARGIN < red and option[0] + MARGIN > red:
      if option[1] - MARGIN < green and option[1] + MARGIN > green:
        if option[2] - MARGIN < blue and option[2] + MARGIN > blue:
          return option[3]
  #return colors.FLOOR

def find_color_auto():
  cs1= ColorSensor("in1")
  cs2= ColorSensor("in2")
  assert cs1.connected, "Connect a single sensor"
  cs1.mode="COL-COLOR"
  assert cs2.connected, "Connect a single sensor"
  cs2.mode="COL-COLOR"
  while True:
    print("Sensor1: " + str(cs1.value()))
    print("Sensor2: " + str(cs2.value()))
    print("")
    print("")
    sleep(2)


find_color_auto()
#find_color_manual()
'''
