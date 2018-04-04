"""Enum holding the directions used to command the robot"""

import sys
from enum import Enum

# I think only ROT_LEFT and ROT_RIGHT are used in practice
Directions = Enum('Directions', 'FORWARD BACKWARD LEFT RIGHT ROT_LEFT ROT_RIGHT')

# Causes the import statement for this module to export the Enum instead
sys.modules[__name__] = Directions
