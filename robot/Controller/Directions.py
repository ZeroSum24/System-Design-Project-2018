import sys
from enum import Enum

Directions = Enum('Directions', 'FORWARD BACKWARD LEFT RIGHT ROT_LEFT ROT_RIGHT')

sys.modules[__name__] = Directions
