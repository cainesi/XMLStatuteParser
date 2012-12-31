#$Id$
#$Revision$
#$Date$
"""code for providing sophisticated comparison for files."""

import difflib
import sys, os
import Constants


name = sys.argv[1]

#empty comment
#second comment

replacements = [("&#8217;","'"), ("\xe2\x80\x99","'")] #do sort of cleaning newPages.py will do
def clean(data):
    for x,y in replacements: data = data.replace(x,y)
    return data

f = open(os.path.join(Constants.WIKIDIR,name),"r")
newData = clean(f.read())
f.close()
f = open(os.path.join(Constants.CUR_WIKIDIR,name),"r")
oldData = clean(f.read())
f.close()

#diff = difflib.ndiff(oldData.splitlines(),newData.splitlines())#, linejunk = lambda x: x.isspace(),charjunk = lambda x: x.isspace())
#l = [c for c in diff]
#print "".join(l)
hd = difflib.HtmlDiff(wrapcolumn=60)
diffPage = hd.make_file(oldData.splitlines(),newData.splitlines())
f = open("d.html","w")
f.write(diffPage)
f.close()

