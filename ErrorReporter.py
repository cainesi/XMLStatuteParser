# $Id$

import sys

class StrictException(Exception): pass

STRICT = False
def showError(s, header = "WARNING", location = None):
    if location is not None:
        while True:
            if hasattr(location, "getSectionLabel"): #work our way up the parent chain till we find something with a getSectionLabel that returns non-None           
                if location.getSectionLabel() is not None:
                    s += "@<" + location.getSectionLabel().getDisplayString() + ">"
                    break
                pass
            if not hasattr(location, "parent"): break
            location = location.parent 
            pass
        pass
    if STRICT: raise StrictException(s)
    else: sys.stderr.write(header + ": <" + s + ">\n")