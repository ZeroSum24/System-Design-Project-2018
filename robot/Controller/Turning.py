import sys
from enum import Enum

Turning = Enum('Turning', 'NONE LEFT RIGHT')

sys.modules[__name__] = Turning
