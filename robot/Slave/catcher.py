import sys
import traceback

# Where to log the errors
EFILE = 'errors.txt'

# New exception handler function
def _handler(etype, evalue, tb):
    # Format the exception and write it to the file
    with open(EFILE, 'w') as efile:
        traceback.print_exception(etype, evalue, tb, None, efile)
    # Also call the builtin exception handler (Prints to screen)
    sys.__excepthook__(etype, evalue, tb)

# Override the exception handler
sys.excepthook = _handler


