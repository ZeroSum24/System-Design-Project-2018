"""Junction types"""

# This is probably never used

import sys
from enum import Enum

Junctions = Enum('Junctions', 'NORMAL DESK')

sys.modules[__name__] = Junctions
