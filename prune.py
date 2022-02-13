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

import XMLStatParse
import sys

fname = sys.argv[1]
section = sys.argv[2]
outfile = "output.xml" if (len(sys.argv) < 4) else sys.argv[3]

f = open(fname,"r"); data = f.read(); f.close()
p = XMLStatParse.ActPruner([("se",section)])
p.feed(data)
t = p.getTree()
d = t.getPrettyXML()
f = open(outfile,"w"); f.write(d.encode("utf-8")); f.close()