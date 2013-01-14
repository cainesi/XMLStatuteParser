# $Id$

import sys

class StrictException(Exception): pass

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

STRICT = False #set to True to force an exception upon any warning message.
def showError(s, header = "WARNING", location = None,color=None):
    if location is not None:
        while True:
            if hasattr(location, "getSectionLabel"): #work our way up the parent chain till we find something with a getSectionLabel that returns non-None           
                if location.getSectionLabel() is not None:
                    s += "@<" + location.getLocationString() + ">"
                    break
                pass
            if not hasattr(location, "parent"): break
            location = location.parent 
            pass
        pass
    if STRICT: raise StrictException(s)
    else:
        if color is not None: sys.stderr.write(FAIL)
        sys.stderr.write(header + ": <" + s + ">\n")
        if color is not None: sys.stderr.write(ENDC)