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