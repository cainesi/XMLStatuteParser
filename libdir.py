# $Id$

import Constants, sys, os

if len(sys.argv)<2: sys.exit(1)
fname = sys.argv[1]
print(os.path.join(Constants.LIBRARYDIR,fname))