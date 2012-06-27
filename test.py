import XMLStatParse, Statute
import os, sys
#Script to run the parser on every statute provided in the Statutes subdirectory, as a test.


fileList = os.listdir("Statutes")
fileList = [c for c in fileList if c[-4:].lower() == ".xml"]

for name in fileList: #parse each file in turn
    print "== " + name + " =="
    f = file(os.path.join("Statutes", name),"r"); data = f.read(); f.close()
    st = Statute.Statute(data)
    pass

