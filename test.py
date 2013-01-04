import os, sys
import StatuteIndex
import Constants

#Script to run the parser on every statute provided in the Statutes subdirectory, as a test.


statList = ["apca"]
si = StatuteIndex.StatuteIndex()


for statName in statList: #parse each file in turn
    s = "== " + statName + " =="
    print("=" * len(s))
    #print("==" + (" " * (len(s)-4)))
    print("== " + statName + " ==")
    #print("==" + (" " * (len(s)-4)))
    print("=" * len(s))
    st = si.getStatute(name=statName)
    st.doProcess()
    st.renderPages()
    pass

