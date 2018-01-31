import sys
from enum import Enum

Colors = Enum('Colors', 'NONE BLACK BLUE GREEN YELLOW RED WHITE BROWN')

sys.modules[__name__] = Colors
