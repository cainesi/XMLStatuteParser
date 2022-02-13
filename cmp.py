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

