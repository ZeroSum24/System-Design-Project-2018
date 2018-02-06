"""Log all interpreter errors in a file"""

import sys
import traceback

# Where to log the errors
EFILE = 'errors.txt'

# New exception handler function
def _handler(etype, evalue, trace):
    # Format the exception and write it to the file
    with open(EFILE, 'w') as efile:
        traceback.print_exception(etype, evalue, trace, None, efile)
    # Also call the builtin exception handler (Prints to screen)
    sys.__excepthook__(etype, evalue, trace)

# Override the exception handler
sys.excepthook = _handler
