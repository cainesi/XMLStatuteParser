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

import XMLStatParse, Statute


#FNAME = "Statutes/apca.xml"
FNAME = "Statutes/ita.xml"
f = open(FNAME,"r"); data = f.read(); f.close()
p = XMLStatParse.XMLStatuteParser(data=data)
t = p.getTree() #test 
stat = Statute.Statute(data)

pruner = XMLStatParse.ActPruner([("se","6")],data = data)
print pruner.getPrunedPrettyXML()