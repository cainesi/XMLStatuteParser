#$Id$
#$Revision$
#$Date$

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

