#$Id$

#Module providing clean interface to external c-library of utility functions

import ctypes
def setupLibrary():
    global xsutil_dll
    lib = "/Users/caines/Program/Python/XMLStatute/xsutillib.so" #TODO: have this point to local directory?
    xsutil_dll = ctypes.cdll.LoadLibrary(lib)
    return
setupLibrary()

def commaSplit(u):
    """method that splits a unicode string into comma separated pieces, ignoring commas appearing in quotes.  Returns a list of the comma-separated pieces."""
    strlen = len(u) #number of unicode characters
    src = u.encode("utf-32")[4:] #convert to unicode, remove the initial 4-bytes (the endianness-indicator)
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

if __name__ == "__main__":
    #run tests of the methods
    l = commaSplit(u"abcd,dsfdfd\"sdfs,xxxx\",svsd")
    if l != [u'abcd', u'dsfdfd"sdfs,xxxx"', u'svsd']: print("Problem with commaSplit():"); print(l)
    