import os, sys
import Statute
import Constants

#Script to run the parser on every statute provided in the Statutes subdirectory, as a test.


#fileList = ["apca.xml"] #simplest test
#fileList = ["apca.xml","excise_act.xml"] #test more
#fileList = os.listdir("Statutes") #full test
#fileList = ["apca.xml","excise_act.xml","ita13.xml","ita14.xml"] #representative ita section
#fileList = ["ita14.xml"]
#fileList = ["ita.xml"]
#fileList = ["bank.xml"]
#fileList = ["excise_act.xml"]

#fileList = os.listdir(Constants.STATUTEDIR); fileList = [c for c in fileList if c != "ita.xml"]


if "ita_reg.xml" in fileList: fileList.remove("ita_reg.xml")


if len(sys.argv) > 1: fileList = [sys.argv[1]]

fileList = [c for c in fileList if c[-4:].lower() == ".xml"]

for name in fileList: #parse each file in turn
    print "== " + name + " =="
    f = open(os.path.join(Constants.STATUTEDIR, name),"r"); data = f.read(); f.close()
    st = Statute.Statute(data, verbose=True)
    st.renderPages()
    pass

