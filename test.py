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

import os, sys
import StatuteIndex
import Constants

#Script to run the parser on every statute provided in the Statutes subdirectory, as a test.


#statList = ["apca"]
statList=["ITA"]
#statList=["IT Reg"]
#statList=["ITA", "IT Reg"]

si = StatuteIndex.StatuteIndex()


for statName in statList: #parse each file in turn
    s = "== Parsing: " + statName + " =="
    print("=" * len(s))
    #print("==" + (" " * (len(s)-4)))
    print(s)
    #print("==" + (" " * (len(s)-4)))
    print("=" * len(s))
    st = si.getStatute(name=statName)
    st.doProcess()
    st.renderPages()
    pass

