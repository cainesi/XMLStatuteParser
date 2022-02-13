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

"""Code to setup directory structure and libraries for parser."""

import Constants
import os

toCreate = [Constants.HEADDIR, Constants.RAWXMLDIR, Constants.STATUTEDIR, Constants.OLDSTATUTEDIR, Constants.STATUTEDATADIR, Constants.PAGEDIR, Constants.LIBRARYDIR ]

#setup directories

for dirName in toCreate: print("Creating " + dirName); os.makedirs(dirName)

#create libraries

print("")
print("Compiling C libraries.")
os.system("./comp")