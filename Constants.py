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

HEADDIR = os.path.expanduser("~/Data")
STATUTEDIR = os.path.join(HEADDIR,"Statutes")  #where statute xml bundles are found
PAGEDIR = os.path.join(HEADDIR,"Pages")  #where the output wikipage should be stored
LIBRARYDIR = os.path.join(HEADDIR,"XMLLibs") #where compile c modules will be located
STATUTEDATADIR = os.path.join(HEADDIR, "StatuteData") #directory for information about statutes, used by StatuteIndex
RAWXMLDIR = os.path.join(HEADDIR,"RawXML")
#TODO: look for "stat_config.txt" in correct location?
#STATUTECONFIGFILE = os.path.join(STATUTEDATADIR,"stat_config.txt")
STATUTECONFIGFILE = "stat_config.txt"
#TODO: implement logging old statutes
OLDSTATUTEDIR = os.path.join(HEADDIR, "OldStatutes") #directory that stores old versions of statutes


#top level tags for ordinary sections handled by SectionItem (other than in formulas)
sectionTypes = set(["section","subsection","paragraph","subparagraph","clause","subclause","subsubclause","definition","formuladefinition"])
formulaSectionTypes = set(["formulaparagraph", "formulasubparagraph","formulaclause","formulasubclause", "formuladefinition"]) #top level tags for sections in formulas, need to have name translated to get correct label
formulaSectionMap = {"formulaparagraph":"paragraph",      #mapping from the formula sections to ordinary section types
                     "formulasubparagraph":"subparagraph",
                     "formulaclause":"clause",
                     "formulasubclause":"subclause",
                     "forumlasubsubclause":"subsubclause",
                     "formuladefinition": "formuladefinition"}
tagSection = {"se": "section",
              "ss": "subsection",
              "p1": "paragraph",
              "p2": "subparagraph",
              "c1": "clause",
              "cs": "subclause",
              "c3": "subsubclause", #is this right?
              "df": "definition",
              "fd": "formuladefinition"}
sectionTag = {(c[1],c[0]) for c in tagSection.items()}


textTypes = set(["text","continuedsectionsubsection","continuedparagraph","continuedsubparagraph","continuedclause","continuedsubclause","continueddefinition", "oath" , "formulaconnector", "continuedformulaparagraph"]) #top level tags for subitems of sections that should be interpreted as text
#list of types of tags that are expected in text blocks, others will generate warnings so we know there may be something that needs special handling
textTriggers = set(["text","oath","formulaconnector","label"])

knownTextTags = set(["text", #ordinary text
                     "emphasis", #italics / bold
                     "repealed", #repealed blocks
                     "sub", #subscripts
                     "sup", #superscript
                     "language", #foreign language (e.g., latin)
                     "label" #appeaers in the "provision" tags in 211.1
                     ])


segmentTypes = set(["part","division","subdivision"])