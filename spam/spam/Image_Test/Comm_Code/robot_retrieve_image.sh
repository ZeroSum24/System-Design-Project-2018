#!/bin/sh
# This is a script to automate access to getting the robot's taken image

maker | scp robot@ev3dev:/home/robot/image_sent.jpg ../imgs/robot_images
