"""Encapsulates the calculation for the PID Controller"""

from math import sin, cos

def pid_speeds(course, speed, wheel_circum, robot_diameter):
    """Returns the required speeds for all four motors."""
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

    non_driver_speed = _delta_deg(speed_left, speed_right, wheel_circum, robot_diameter)
    speed_front = non_driver_speed
    speed_back = -non_driver_speed

    return [int(speed_left), int(speed_right), int(speed_front), int(speed_back)]

# Distance traveled per degree by a wheel
def _d_deg(wheel_circum):
    return wheel_circum/360

# Distance traveled by each wheel per second in cm
def _dist(velocity, wheel_circum):
    return velocity * _d_deg(wheel_circum)

# The difference in distance traveled by the left and right wheels in cm
def _diff_in_dist(vel_left, vel_right, wheel_circum):
    return _dist(vel_left, wheel_circum) - _dist(vel_right, wheel_circum)

# Angle of base rotation per second in radians
def _omega(vel_left, vel_right, wheel_circum, robot_diameter):
    return _diff_in_dist(vel_left, vel_right, wheel_circum)/robot_diameter

# The distance from the centre of rotation to the centre of the drive axis
def _IC_dist(vel_left, vel_right, robot_diameter):
    return (robot_diameter/2)*((vel_right + vel_left)/(vel_right - vel_left))

# Result of rotating the vector defined by IC_dist through omega in euclidian
# space, only the x coordinate is required in cm (robot_diameter/2 is the
# original y coordinate)
def _omega_to_axis(vel_left, vel_right, wheel_circum, robot_diameter):
    angle = _omega(vel_left, vel_right, wheel_circum, robot_diameter)
    result = _IC_dist(vel_left, vel_right, robot_diameter) * cos(angle)
    result -= robot_diameter/2 * sin(angle)
    return result

# Change is x coordinate is how far the front wheel must move perpendicular to
# the direction of travel (cm)
def _delta(vel_left, vel_right, wheel_circum, robot_diameter):
    start = _IC_dist(vel_left, vel_right, robot_diameter)
    end = _omega_to_axis(vel_left, vel_right, wheel_circum, robot_diameter)
    return start - end

# The number of degrees the front and back wheels must move through in a second.
def _delta_deg(vel_left, vel_right, wheel_circum, robot_diameter):
    if abs(vel_left-vel_right) > 3: # avoiding division by 0 in _IC_dist
        return 360 * _delta(vel_left, vel_right, wheel_circum, robot_diameter)/wheel_circum
    else:
        return 0
