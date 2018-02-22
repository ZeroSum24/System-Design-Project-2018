"""Enum holding the colors detected by the ev3 color sensors"""

import sys
from enum import Enum

Colors = Enum('Colors', 'NONE BLACK BLUE GREEN YELLOW RED WHITE BROWN')

# Causes the import statement for this module to export the Enum instead
sys.modules[__name__] = Colors
