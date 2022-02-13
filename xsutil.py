
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


#Module providing clean interface to external c-library of utility functions

import ctypes, os
from Constants import LIBRARYDIR
def setupLibrary():
    global xsutil_dll
    lib = os.path.join(LIBRARYDIR,"xsutillib.so") #TODO: have this point to local directory?
    xsutil_dll = ctypes.cdll.LoadLibrary(lib)
    return
setupLibrary()

def commaSplit(u):
    """method that splits a unicode string into comma separated pieces, ignoring commas appearing in quotes.  Returns a list of the comma-separated pieces."""
    strlen = len(u) #number of unicode characters
    src = u.encode("utf-32")[4:] #convert to unicode byte-string, remove the initial 4-bytes (the endianness-indicator)
    #HACK - we could probably speed this up by not constantly reallocating the arrays each time function called?
    iarray = ( ctypes.c_int * (strlen + 1)) #maximum number of tokens we could possibly see
    tokenStart = iarray()
    tokenEnd = iarray()
    numTokens = ctypes.c_int()
    result = xsutil_dll.linesplit(ctypes.c_char_p(src), strlen, tokenStart, tokenEnd,ctypes.byref(numTokens)); #call to library
    tokens = []
    for n in xrange(0, numTokens.value):
        tokens.append(u[tokenStart[n]:tokenEnd[n]])
        pass
    return tokens

#TODO code for quickly searching all relevant defined terms in text.

class TermSeeker():
    def __init__(self):
        """Initialize the defined term seeker with information on the applicability of defined terms.  Used by the DefinitionData object."""
        return
    def find(self,text,position):
        """Returns a list of all the defined terms that appear in the text, and their positions."""
        return


if __name__ == "__main__":
    #run tests of the methods
    l = commaSplit(u"abcd,dsfdfd\"sdfs,xxxx\",svsd")
    if l != [u'abcd', u'dsfdfd"sdfs,xxxx"', u'svsd']: print("Problem with commaSplit():"); print(l)
    