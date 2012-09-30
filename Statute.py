# $Id$
# $URL$

import os
import XMLStatParse
import RenderContext
import StatuteItem
import Constants
import SectionLabelLib

#workflow for parsing statute:
# 1) parse xml into tree structure
# 2) walk the tree-structure to extract section structure and extract particular types of data
#   2a) Labels
#   2b) Definitions
#   2c) Marginal notes
#   2d) Historical notes
#   2e) Tables (?)
# 3) Create various meta data for Statute (e.g., section ordering information)
# 4) Walk structure to detect defined terms / defined term applicability
# 5) Detect cross-references and insert applicable links
# 6) Output wikipages

#TODO:
# - convert to using proper xml parser - xml.parsers.expat (before the conversion gets too annoying! -- this will probably speed things up too, since expat is written in C)
# - bump indent level when one forumladefinition is nested inside another?
# - deal with headings in the statute / division identifications
# - headings in the regulations take the place of some marginalnotes
# - Move marginal notes that are attached to top level sections, when there are subsections in the section, and first subsection is un-noted.

class StatuteException(Exception): pass


class Statute(object):
    """Class that encapsulating a xml statute in a usable form.
    Based on the XMLStatuteParser, but processes the raw tree output to make it more usable."""
    def __init__(self,data,verbose=False):
        """
        Initialize Statute object based on it's raw XML representation.
        Metadata about the Statute is stored in following members:
        sectionList/headingList/allItemList - lists of the corresponding top-level items in the Statute.
        segmentData - contain information about the segments (parts / divisions / subdivisions) in the statute and which sections correspond to which segments.
        sectionData - contains information about the sections in the Statute, their text-searchable representations and their orderings.
        instrumentType - gives the type of instrument represented by the object -- currently just "statute" and "regulation"
        """
        p = XMLStatParse.XMLStatuteParser()
        p.feed(data)
        dataTree = p.getTree()
        if verbose: print "[XML file read]"
        self.instrumentType = None
        self.enablingAuthority = None
        if "statute" in dataTree:
            self.instrumentType = "statute"
            self.mainPart = dataTree["statute"]
        elif "regulation" in dataTree:
            self.instrumentType = "regulation"
            self.mainPart = dataTree["regulation"]
        else:
            raise StatuteException("Cannot find any instrument in file.")
        
        self.sectionList = None #list of the top level section items in the Statute
        self.headingList = None #list of all headings in the Statute
        self.allItemList = None #list of all headings and sections in the order they occurred (useful for making TOC for statute)
        self.segmentData = SectionLabelLib.SegmentData(statute=self)
        self.identTree = self.mainPart["identification"]
        self.contentTree = self.mainPart["body"]
        self.processStatuteData(self.identTree) #extract meta-data about the statute from the xml
        self.processStatuteContents(self.contentTree) #extract the contents of the statute
        self.sectionData = SectionLabelLib.SectionData(statute=self)
        return

    ###
    #
    # General utility methods
    #
    ###


    def titleString(self):
        """String giving the title of the statute (mainly for debugging)."""
        return ": " + self.longTitle + " (a/k/a " + self.shortTitle + ") " + self.getCitationString()

    def isRegulation(self):
        """True if this object represents a regulation."""
        if self.instrumentType == "regulation": return True
        return False

    def isStatute(self):
        """True if this object represents a statute."""
        if self.instrumentType == "statute": return True
        return False

    def getTypeString(self):
        if self.instrumentType == "statute" or self.instrumentType == "regulation": return self.instrumentType
        else: raise StatuteException("No typeString because instrument has no type.")
    
    def getCitationString(self):
        """Returns the citation for the instrument (e.g., the chapter # for a consolidated act)"""
        return self.citationString
    
    def reportString(self):
        """Outputs the name of the statute and a list of its sections."""
        return self.titleString() + "\n" + ", ".join(c.labelString for c in self.sectionList)
    
    def __repr__(self):
        """@rtype: unicode"""
        return "<" + self.titleString() + ">"

    def itemIterator(self):
        """Returns an iterator over all the Items in the structure.
        @rtype: StatuteItem.BaseItem
        """
        for sec in self.sectionList:
            for item in sec.itemIterator(): yield item
        return

    def sectionIterator(self):
        """
        Returns an iterator over the SectionItems in the structure.
        @rtype: StatuteItem.SectionItem
        """
        for item in self.itemIterator():
            if isinstance(item,StatuteItem.SectionItem): yield item
        return

    ###
    #
    # Content processing methods.
    #
    ###

    def processStatuteData(self,tree):
        """Process the "identification" portion of the XML to gather data about the statute (title, etc)."""
        self.shortTitle = tree["shorttitle"].getRawText().strip()
        self.longTitle = tree["longtitle"].getRawText().strip()
        if self.instrumentType == "statute":
            self.citationString = tree["chapter"].getRawText().strip()
        elif self.instrumentType == "regulation":
            self.citationString = tree["instrumentnumber"].getRawText().strip()
            self.enablingAuthority = tree["enablingauthority"].getRawText().strip()
            #determine page name prefix for pages of this instrument
        #TODO - have a global mapping that lets us override this where desired
        self.pagePrefix = self.shortTitle
        return


    def processStatuteContents(self,tree):
        self.sectionList = [] #list of top level sections contained in statute
        self.headingList = []
        self.allItemList = []
        #iterate over subitems and add all sections to self.sectionList
        for node in tree:
            if node.tag == "": continue #top level textnodes are ignored
            #if item is a type of section
            elif node.tag == "section":
                self.processSection(node)
            #if item is a type of heading
            elif node.tag == "heading":
                self.processHeading(node)
            #other cases
            else: print "Unknown tag seen at top level: [" + node.tag + "]"
            pass
        #TODO structures pointing to sections by name, organizing them, etc.
        return

    def processSection(self,node):
        """Processes the Node for an act section (as well as subsection, etc), and add to the Statute's structure of sections."""
        #call process section on the item, with a fake parent, then extract the item and add it to the Statute's section list
        section = StatuteItem.SectionItem(parent=None,tree=node, statute=self) #TODO: instead make parent=self, so statute determined automatically?
        self.addSection(section)
        return

    def processHeading(self,node):
        """Process the Node for a heading."""
        #close off prior heading at same level or above
        #create the heading object and add to list
        hitem = StatuteItem.HeadingItem(parent=None,statute=self,tree=node)
        self.addHeading(hitem)
        return
    def addHeading(self,heading):
        """Add headingItem to the appropriate lists of the Statute meta-data (the all-heading and all-item lists)."""
        self.headingList.append(heading)
        self.allItemList.append(heading)
        if heading.isLabeled(): self.segmentData.addNewNumbering(heading.getNumbering(), title=heading.getTitleString())
        return
    def addSection(self,section):
        self.sectionList.append(section)
        self.allItemList.append(section)
        self.segmentData.addSection(section.getSectionLabel())
        return


    ###
    #
    # File output methods.
    #
    ###

    def renderPages(self): #TODO: this code is just a stop-gap for testing purposes
        for sec in self.sectionList:
            self.renderPage(sec)
        return
    def renderPage(self,sec):
        lab = sec.getSectionLabel()[0].getIDString()
        f = file(os.path.join(Constants.PAGEDIR, self.pagePrefix) + " " + lab,"w")
        f.write(sec.getRenderedText(RenderContext.WikiContext,skipLabel=True).encode("utf-8"))
        f.close()
        pass    

    pass

def processAct(url):
    """Method to grab the statute found at a specific url and automatically process it into wiki pages.  Ultimately it should automatically include any regulations"""
    #TODO
    return