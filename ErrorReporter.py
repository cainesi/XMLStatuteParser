# $Id$

import sys

STRICT = False
def showError(s, location = None):
    if location != None:
        while True:
            if hasattr(location, "getSectionLabel"): #work our way up the parent chain till we find something with a getSectionLabel that returns non-None
                if location.getSectionLabel() != None:
                    s += "@<" + location.getSectionLabel().getDisplayString() + ">"
                    break
                pass
            if not hasattr(location, "parent"): break
            location = location.parent 
            pass
        pass
    if STRICT: raise StatuteException(s)
    else: sys.stderr.write("WARNING: <" + s + ">\n")