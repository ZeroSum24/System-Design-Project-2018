"""Enum holding the states of the robot"""

import sys
from enum import Enum

State = Enum('State', 'LOADING DELIVERY RETURNING PANIC')

# Causes the import statement for this module to export the Enum instead
sys.modules[__name__] = State