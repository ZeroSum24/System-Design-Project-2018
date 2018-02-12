"""Enum used to track the direction of turn during course correction"""

import sys
from enum import Enum

Turning = Enum('Turning', 'NONE LEFT RIGHT')

# Causes the import statement for this module to export the Enum instead
sys.modules[__name__] = Turning
