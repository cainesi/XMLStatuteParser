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


import os
import shutil
import Constants

NEWPAGESDIR = Constants.WIKIDIR
OLDPAGESDIR = Constants.CUR_WIKIDIR
SUBMITPAGESDIR = Constants.SUBMIT_WIKIDIR

EXTRA_LAX=True

newPageList = os.listdir(NEWPAGESDIR)
oldPageList = os.listdir(OLDPAGESDIR)

changePages = []

replacements = [(" ",""), ("&#8217;","'"), ("\xe2\x80\x99","'"),("&#8220;","\""),("&#8221;","\"")]

if EXTRA_LAX: replacements += [("\n",""), ("\t",""), (">","")]

def clean(data):
    for x,y in replacements: data = data.replace(x,y)
    return data

print "Newpages:"

for page in newPageList:
    if page not in oldPageList:
        print page
        changePages.append(page)
        continue
    f = open(os.path.join(OLDPAGESDIR,page))
    oldPageData = f.read()
    f.close()
    f = open(os.path.join(NEWPAGESDIR,page))
    newPageData = f.read()
    f.close()
    
    #remove whitespace:
    oldPageData = clean(oldPageData)
    newPageData = clean(newPageData)

    if oldPageData != newPageData:
        changePages.append(page)
        pass
    pass

deletedPages = []
for page in oldPageList:
    if page not in newPageList:
        deletedPages.append(page)
        pass
    pass

print ""
print "Deleted Pages:"
for page in deletedPages:
    print page
    pass
print ""

print "Changed Pages"
for page in changePages:
    print page
    shutil.copy(os.path.join(NEWPAGESDIR,page),os.path.join(SUBMITPAGESDIR,page))
    pass

