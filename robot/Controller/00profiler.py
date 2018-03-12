#!/usr/bin/env python3

# Runs on the robot to gather profile results
import cProfile
import control_loop as c

# The entry point of the program goes in the first string
cProfile.runctx('c.main()', globals(), locals(), 'Profile.prof')

