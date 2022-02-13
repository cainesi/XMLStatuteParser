# Copyright (C) 2022  Ian Caines
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sys

class StrictException(Exception): pass

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

errorCount = 0

STRICT = False #set to True to force an exception upon any warning message.
def showError(s, header = "WARNING", location = None,color=None):
    global errorCount
    if location is not None:
        while True:
            if hasattr(location, "getSectionLabel"): #work our way up the parent chain till we find something with a getSectionLabel that returns non-None           
                if location.getSectionLabel() is not None:
                    s += "@<" + location.getSectionLabel().getIDString() + ">"
                    #s += "@<" + location.getLocationString() + ">"
                    break
                pass
            if not hasattr(location, "parent"): break
            location = location.parent 
            pass
        pass
    if STRICT: raise StrictException(s)
    else:
        if color is not None: sys.stderr.write(FAIL)
        errorCount += 1
        sys.stderr.write(("[% 5d]"%errorCount) + header + ": <" + s + ">\n")
        if color is not None: sys.stderr.write(ENDC)