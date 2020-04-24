import os
import os.path
import sys


def infer_program_name():
    """Get current progam name.

    See https://docs.python.org/3/using/cmdline.html#interface-options
    """
    prog_name = os.path.basename(sys.argv[0])
    if prog_name == "-c":
        prog_name = sys.argv[:30] + "..."
    elif prog_name == "-m":
        prog_name = sys.argv[1]
    # Not handled: sys.argv[0] == "-"
    return os.fsencode(prog_name)
