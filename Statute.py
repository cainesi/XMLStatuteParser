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
import Constants, SectionLabelLib
import XMLStatParse
import StatuteItem, langutil, DecoratedText
import RenderContext
import util
from ErrorReporter import showError

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

#Data structures:
# Statutes starts as XML
# XML is fed into Statute object
# Basic parser converts that to a tree structure (XMLStatParse Nodes), with nodes representing tags in the XML structure
# The tree is then recursively walked by the Statute object and sub-trees encapsulated in appropriate StatuteItems (TextItem, FormulaItem, HeadingItem, etc.)
# The structure of StatuteItems is then walked to extract certain data about the overall structure of the statute
#       A) SegmentData - organization of sections into Parts/Divisions/etc
#       B) SectionData - enumeration of sectionLabel items in the structure --- allows relative position of sections to be determined
# (TODO) The statute is bound against other statutes or dictionaries in order to resolve certain cross references, etc. (regs to statutes, etc)
# wikipage/html output is generated

# TODOs:
# - add an index of look-up dictionaries of sectionLabels to the Statute object initialization, and generation of the indices from completed statute.
# - convert to using proper xml parser - xml.parsers.expat (before the conversion gets too annoying! -- this will probably speed things up too, since expat is written in C)
# - bump indent level when one forumladefinition is nested inside another?
# - deal with headings in the statute / division identifications
# - headings in the regulations take the place of some marginalnotes
# - Move marginal notes that are attached to top level sections, when there are subsections in the section, and first subsection is un-noted.

class StatuteException(Exception): pass

class Statute(object):
    """Class that encapsulating a xml statute in a usable form.
    Based on the XMLStatuteParser, but processes the raw tree output to make it more usable."""
    #def __init__(self,data,verbose=False):
    def __init__(self,statuteName, statuteIndex, verbose=False):
        """
        Initialize Statute object based on it's raw XML representation.
        Metadata about the Statute is stored in following members:
        sectionList/headingList/allItemList - lists of the corresponding top-level items in the Statute.
        segmentData - contain information about the segments (parts / divisions / subdivisions) in the statute and which sections correspond to which segments.
        sectionData - contains information about the sections in the Statute, their text-searchable representations and their orderings.
        instrumentType - gives the type of instrument represented by the object -- currently just "statute" and "regulation"
        @type statuteName: str
        @type statuteIndex: StatuteIndex.StatuteIndex
        @type verbose: bool
        @rtype: None
        """
        self.statuteName = statuteName
        self.statuteIndex = statuteIndex
        self.statuteData = self.statuteIndex.getStatuteData(self.statuteName)
        self.renderContext = RenderContext.HTMLContext
        #self.renderContext = RenderContext.MediaWikiContext
        data = self.statuteData.getRawXML()

        p = XMLStatParse.XMLStatuteParser()
        p.feed(data)
        dataTree = p.getTree()
        if verbose: print "[XML file read]"
        self.instrumentType = None
        self.enablingAuthority = None
        if "statute" in dataTree: #figure out if we are dealing with statute or regulation, and extract the appropriate part of data tree.
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

        return

    #TODO, after testing, make the following part of the initialization (we've separated it out so that object can be assigned before this code is run)
    def doProcess(self):
        self.sectionData = SectionLabelLib.SectionData(statute=self)                #compile information about the ordering of sections
        self.statuteData.setSectionNameDict(self.sectionData.getSectionNameDict())  #store information about available sections
        #TODO: also need to store data for sLDict and linkDict in the statuteData object
        self.definitionData = DefinitionData(statute=self) #compile information about available definitions and their ranges of applicability
        self.definitionData.applyToAll()
        #self.definitionData.displayDefinedTerms()
        #TODO: insert decorations for section cross-references
        self.markSectionReferences() #detect section references in text, and decorate them

        #create cross-link dictionary
        linkDict = self.compileLinkDict()
        self.statuteData.setLinkDict(linkDict)
        self.statuteData.storeIndices()
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
    # Meta-data about the Statute
    #
    ###
    def getStatuteIndex(self):
        """@rtype: StatuteIndex.StatuteIndex"""
        return self.statuteIndex
    def getStatuteData(self):
        """@rtype: StatuteIndex.StatuteData"""
        return self.statuteData
    def getSectionData(self):
        """
        Returns SectionData object for statute, containing list of section labels and their ordering.
        @rtype: SectionLabelLib.SectionData
        """
        return self.sectionData
    def getSegmentData(self):
        """
        Returns segmentData (information of parts/divisions/subdivisions) for the Statute.
        @rtype: SectionLabelLib.SegmentData
        """
        return self.segmentData

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
        """Add headingItem to the appropriate lists of the Statute meta-data (the all-heading and all-item lists).
        @type heading: StatuteItem.HeadingItem
        @rtype: None
        """
        self.headingList.append(heading)
        self.allItemList.append(heading)
        if heading.isLabeled(): self.segmentData.addNewNumbering(heading.getNumbering(), title=heading.getTitleString())
        return
    def addSection(self,section):
        """Add a SectionItem to the appropriate sections.
        @type section: StatuteItem.SectionItem
        @rtype: None
        """
        self.sectionList.append(section)
        self.allItemList.append(section)
        self.segmentData.addSection(section.getSectionLabel())
        return

    def compileLinkDict(self):
        """Compile a dictionary specifying all the links from this Statute.
        Dictionary is indexed by statute name,
        """
        #create master list of source/target for every link in the Statute
        linkList = []
        for section in self.sectionList:
            for subItem in section.itemIterator():
                if isinstance(subItem,StatuteItem.TextItem):
                    sourceSL = subItem.getSectionLabel()
                    dt = subItem.getDecoratedText()
                    pinpoints = dt.getPinpoints()
                    for pin in pinpoints: linkList.append((sourceSL,pin))
                    pass
                pass
            pass

        #produce linkDict from the list of links
        linkDict = {}
        for sourceSL,pin in linkList: #produce the linkDict
            targetStatuteName = pin.getStatuteName()
            targetSL = pin.getSL()
            sourceSL = sourceSL[:1]
            if len(sourceSL) != 1: continue
            targetSL = targetSL[:1]
            if len(targetSL) != 1: continue
            if targetStatuteName not in linkDict: linkDict[targetStatuteName] = {}
            if targetSL not in linkDict[targetStatuteName]: linkDict[targetStatuteName][targetSL] = {}
            linkDict[targetStatuteName][targetSL][sourceSL] = None
        for targetStatuteName in linkDict: #replace the final dict
            for targetSL in linkDict[targetStatuteName]:
                d = linkDict[targetStatuteName][targetSL]
                l = d.keys()
                l.sort(key=lambda x:self.sectionData.sectionStart[x])
                linkDict[targetStatuteName][targetSL] = l
                pass
            pass

        return linkDict

    ###
    #
    # Methods for decorating contents
    #
    ###

    def markSectionReferences(self):
        """Marks all the section references in the Statute."""
        for item in self.itemIterator():
            parent = item.parent
            if isinstance(item,StatuteItem.TextItem):
                dt = item.getDecoratedText()
                #print(dt.getText())
                sr = langutil.SectionReferenceParse(dt)
                sr.addDecorators()
            pass
        return

    ###
    #
    # File / Rendering output methods.
    #
    ###

    def renderPages(self): #TODO: this code is just a stop-gap for testing purposes
        """Renders a page for each top-level sectionItems."""
        #render pages

        for previousItem,sectionItem,nextItem in util.triples(self.sectionList): self.renderSectionPage(sectionItem,previousItem=previousItem,nextItem=nextItem)
        self.renderCurrencyPage()
        self.renderIndexPage()
        return


    def renderSectionPage(self,sectionItem,previousItem,nextItem):
        """Renders the page for a sectionItem (assumed to be top-level).
        @type sectionItem: StatuteItem.SectionItem
        @type previousItem: StatuteItem.SectionItem
        @type nextItem: StatuteItem.SectionItem
        """
        lab = sectionItem.getSectionLabel()[0].getIDString()
        sL = sectionItem.getSectionLabel()
        page = u""

        #header
        # - page title
        page += self.renderContext.renderHeading(self.statuteData.getFullName() + " " + lab,1)
        page += self.renderContext.newLine()

        # - next/previous page
        page += self.nextPreviousBlock(previousItem=previousItem,nextItem=nextItem)
        page += self.renderContext.newLine()
        page += self.renderContext.horizontalLine()
        page += self.renderContext.newLine()

        #page contents
        page += sectionItem.getRenderedText(self.renderContext,skipLabel=True,baseLevel=2) #set base level to 2 so that subsection as flush left
        page += self.renderContext.newLine()

        #footer
        # - citing sections (what objects we take references from should be configurable)
        citeBlock = self.citationsBlock(sectionItem)
        if citeBlock is not None:
            page += self.renderContext.horizontalLine()
            page += self.renderContext.newLine()
            page += citeBlock
            page += self.renderContext.newLine()

        # - citing bulletins

        # - disclaimer
        page += self.renderContext.horizontalLine()
        page += self.renderContext.newLine()
        page += self.disclaimerBlock()

        fname = os.path.join(Constants.PAGEDIR, self.statuteData.getPrefix()) + " " + lab
        f = self.renderContext.openFile(fname=fname)
        f.write(page.encode("utf-8"))
        self.renderContext.closeFile(f)
        return

    def renderCurrencyPage(self):
        """Renders the page giving the currency data for the statute."""
        page = u""
        page += self.renderContext.renderHeading(self.statuteData.getFullName() + ": " + "Currency Information",1)
        page += self.renderContext.newLine()
        page += self.renderContext.horizontalLine()
        page += self.renderContext.newLine()
        s = self.longTitle
        longTitleStr =  self.renderContext.italicText( self.longTitle )
        if s[:3].lower() == "an " or s[:4].lower() == "the ": pass
        else: longTitleStr = "the " + longTitleStr
        if self.isRegulation(): longTitleStr += ", " + self.enablingAuthority + ","
        else: longTitleStr += ", " + self.citationString + ","


        page += "The copy of the " + self.statuteData.getFullName()+ " provided here is based on the " + self.renderContext.renderExternalLink(targetURL=self.statuteData.getXMLUrl(), linkText="XML version") + " of "+ longTitleStr + " downloaded from the website of the Department of Justice at " + self.renderContext.renderExternalLink(targetURL=self.statuteData.getBundleUrl()) + " on " + self.statuteData.getDownloadDate().strftime("%B %-e, %Y") + " (current to " + self.statuteData.getCurrencyDate().strftime("%B %-e, %Y") + ")."
        fname = self.currencyPageName()
        f = self.renderContext.openFile(fname=fname)
        f.write(page.encode("utf-8"))
        self.renderContext.closeFile(f)
        return

    def renderIndexPage(self):
        """Renders the index page for this statute."""
        page = u""
        #header
        # - page title
        page += self.renderContext.renderHeading(self.statuteData.getFullName() + " Table of Contents",1)
        page += self.renderContext.newLine()
        page += self.renderContext.horizontalLine()
        page += self.renderContext.newLine()

        for item in self.allItemList:
            if isinstance(item,StatuteItem.SectionItem):
                sectionItem = item
                sL = sectionItem.getSectionLabel()
                assert isinstance(sL, SectionLabelLib.SectionLabel)
                pin = self.statuteData.getPinpoint(sL)
                title = sectionItem.getTitle()
                if title != "": title = " (" + title + ")"
                page += self.renderContext.renderPinpoint(pin, sL.getIDString() + title )
                page += self.renderContext.newLine()
                pass
            elif isinstance(item,StatuteItem.HeadingItem):
                l = [item.getLabelString(), item.getTitleString()]
                l = [c for c in l if c is not None]
                level = 4
                if item.getNumbering() is not None: level = item.getNumbering().getHeadingLevel()
                title = " -- ".join(l)
                page += self.renderContext.renderHeading(title,level)
                page += self.renderContext.newLine()
                pass
            pass
        page += self.renderContext.horizontalLine()
        page += self.renderContext.newLine()
        page += self.disclaimerBlock()
        fname =  self.indexPageName()
        f = self.renderContext.openFile(fname=fname)
        f.write(page.encode("utf-8"))
        self.renderContext.closeFile(f)
        return

    def nextPreviousBlock(self,previousItem,nextItem):
        """Renders a block of text with backwards / forwards links.
        @type previousItem: StatuteItem.SectionItem
        @type nextItem: StatuteItem.SectionItem
        """
        text = u""
        prevExplanation = None
        nextExplanation = None
        if previousItem is None: previousStr = None
        else:
            prevSL = previousItem.getSectionLabel()
            previousPin = self.statuteData.getPinpoint(prevSL)
            previousStr = self.renderContext.renderPinpoint(previousPin, "(previous section: " + prevSL.getIDString() + ")")
            pass
        if nextItem is None: nextStr = None
        else:
            nextSL = nextItem.getSectionLabel()
            nextPin = self.statuteData.getPinpoint(nextSL)
            nextStr = self.renderContext.renderPinpoint(nextPin, "(next section: " + nextSL.getIDString() + ")") # + nextSL.getIDString() + "]")
            pass
        if previousStr is not None:
            text += previousStr
            if nextStr is not None: text += self.renderContext.newLine()
            pass
        if nextStr is not None:
            text += nextStr
            pass
        return text
    def citationsBlock(self, sectionItem):
        """Returns the block of text representing citations to this section.
        @type sectionItem: StatuteItem.SectionItem
        @rtype: str
        """

        page = u""
        #local citations
        localBlock = self.statuteCiteBlock(sourceStatuteName=self.getStatuteData().getName(),sectionItem=sectionItem)
        if localBlock is not None:
            page += self.renderContext.renderHeading("Other sections citing this section:",2)
            page += self.renderContext.newLine()
            page += localBlock
            page += self.renderContext.newLine()
            pass
        if self.statuteData.getReg() is not None:
            regBlock = self.statuteCiteBlock(sourceStatuteName=self.getStatuteData().getReg(),sectionItem=sectionItem)
            if regBlock is not None:
                if page != u"":
                    page += self.renderContext.renderHeading("Sections of regulations citing this section:",2)
                    page += self.renderContext.newLine()
                    page += regBlock
                    page += self.renderContext.newLine()
                    pass
                pass
            pass

        if page == u"": return None
        return page

    def statuteCiteBlock(self,sourceStatuteName,sectionItem):
        """Renders the block of links representing links from sourceStatuteName to the specified local section of this statute..  Returns None if there are no such links.
        @type sourceStatuteName: str
        @type sectionItem: StatuteItem.sectionItem
        @rtype: unicode
        """
        text = u""
        l = []
        targetSL = sectionItem.getSectionLabel() #get sL representing the target
        sLList = self.statuteIndex.getStatuteData(sourceStatuteName).getLinksToSL(targetSL=targetSL,statuteName=self.statuteData.getName()) #get the list of sL's in the source Statute
        sourceData = self.statuteIndex.getStatuteData(sourceStatuteName)
        for sL in sLList:
            tpin = sourceData.getPinpoint(sL)
            l.append(self.renderContext.renderPinpoint(tpin))
            pass
        if len(l) == 0: return None
        return ", ".join(l)


    def disclaimerBlock(self):
        #TODO: fill in email address
        email = self.renderContext.mailTo("ian.caines@gmail.com")
        disclaimerText = "This material is based on the text of the " + self.statuteData.getName() + ", available from the website of the Department of Justice at " + self.renderContext.renderExternalLink(targetURL=self.statuteData.getBundleUrl()) + " (" + self.renderContext.renderPageLink(pageName=self.currencyPageName(), text="currency information") + "), but has not been produced in affiliation with, or with the endorsement of the Government of Canada.  This material has been produced by programmatic means, has not been reviewed for accuracy, and is likely to contain a variety of errors.  We would appreciate hearing about any errors, or any other suggestions for improvement, at " + email + "." # + renderContext.mailTo("comments@taxwiki.ca") + "."
        return disclaimerText

    #TODO: move page name definitions to SectionData object
    def currencyPageName(self):
        return os.path.join(Constants.PAGEDIR, self.statuteData.getPrefix() + " " + "Currency Information")

    def indexPageName(self):
        return os.path.join(Constants.PAGEDIR, self.statuteData.getPrefix())

class DummyStatute(object):
    def __init__(self):
        """Dummy object used for testing by sections that need to declare a parent."""
        return
    def getStatute(self): return self

class DefinitionData(object):
    """Object encapsulating information about defined terms in the Statute and their ranges of applicability. And also code for marking the defined terms in the Statute once applicabilities have been determined."""
    def __init__(self,statute):
        """
        @type statute: Statute
        """
        self.statute = statute
        self.definedTermRanges = {} #dictionary indexed by defined terms, where each entry is a list of (sourceitem, application range)
        self.applicationRange = {} #dictionary indexed by sL, and giving the application range specified by that sL.
        self.scopeDefinedTerms()
        self.definedTermList = self.definedTermRanges.keys() #make a list of defined terms, indexed by decreasing size
        self.definedTermList.sort(key=lambda x: -len(x))
        self.sectionData = self.statute.getSectionData()
        self.statuteData = self.statute.getStatuteData()
        return

    def scopeDefinedTerms(self):
        """Determines the scope for defined terms appearing in the Statute."""
        itemDict = {} # a dictionary of StatuteItems that are parents of definitions, indexed by sectionlabel
        for item in self.statute.itemIterator():
            if isinstance(item,StatuteItem.DefinitionItem):
                parent = item.parent
                parentSL = parent.getSectionLabel()
                if parentSL in self.applicationRange: appRange = self.applicationRange[parentSL]
                else: # if we haven't already processed that item, do so now
                    decoratedText = parent.getInitialTextItem().getDecoratedText()
                    appParse = langutil.ApplicationParse(decoratedText=decoratedText)
                    appRange = appParse.getSectionLabelCollection()
                    self.applicationRange[parentSL] = appRange
                    pass
                definedTerm = item.getDefinedTerm()
                if definedTerm is None: showError("No defined term found in: " + str(item.getSectionLabel()), location = item)
                else:
                    definedTerm = definedTerm.lower()
                    if definedTerm not in self.definedTermRanges: self.definedTermRanges[definedTerm] = []
                    self.definedTermRanges[definedTerm].append((item,appRange))
                    itemDict[parent.getSectionLabel()] = parent
                    pass
                pass
            pass
    def applyToAll(self):
        """Adds Decorators to the entire Statute."""
        for item in self.statute.itemIterator():
            if isinstance(item,StatuteItem.TextItem):
                dt = item.getDecoratedText()
                self.applyToDecoratedText(decoratedText=dt)
                pass
            pass
        return

    def applyToDecoratedText(self,decoratedText):
        """Adds Decorators to the DecoratedText for the applicable definitions.
        @type decoratedText: DecoratedText.DecoratedText
        @rtype: None
        """
        text = decoratedText.getText().lower() #use normalized (lower-case) text for defined term matching
        sL = decoratedText.getSectionLabel()
        position = self.sectionData.getSLPosition(sL)
        hits = self.applyToText(text=text,position=position)
        for start,end,pinpoint in hits:
            ld = DecoratedText.LinkDecorator(parent=decoratedText, start=start,end=end,pinpoint=pinpoint)
            decoratedText.addDecorator(ld)
            pass
        return

    def applyToText(self,text,position):
        """Returns at list of intervals where defined terms were found, and the item of the corresponding
        @type text: str
        @type position: int
        @rtype: list of (int, int, SectionLabelLib.PinPoint)
        """
        #TODO: write a version that works with section labels.
        l = []
        for term in self.definedTermList: #go through defined terms
            for source, appRange in self.definedTermRanges[term]: #go through all definitions for each defined term
                if not appRange.containsPosition(position): continue #if definition not applicable, continue
                ptr = text.find(term)
                while ptr != -1: #otherwise, iterate through all instances
                    #confirm that match occurs at the
                    if not isAWordRange(text,ptr,ptr+len(term)): #if not a valid word range, simply continue
                        ptr = text.find(term,ptr+1)
                        continue
                    sL = source.getSectionLabel()
                    l.append( (ptr, ptr+len(term), self.statuteData.getPinpoint(sL)) )
                    ptr = text.find(term,ptr+1)
                pass
            pass
        return l

    def displayDefinedTerms(self):
        """Prints out a listing of the defined terms."""
        terms = self.definedTermRanges.keys()
        terms.sort()
        for term in terms:
            print(">> " + term + " <<")
            for item,appRange in self.definedTermRanges[term]:
                print(" - " +item.getSectionLabel().getIDString() + " -- " + str(appRange))
            pass
        return

    pass

###
#
# Definition data utility methods
#
###

def isAWordRange(text,start,end):
    """
    Returns true of the text between start and end corresponds to a series of words in the text, possibly with a pluralization at the end.
    @type text: str
    @type start: int
    @type end: int
    @rtype: bool
    """
    if start != 0 and not text[start-1].isspace(): return False #reject if not space before interval
    if end == len(text): return True #return True if at end, followed by space, or by "s" and space.
    if end < len(text) and (not text[end].isalpha()): return True
    if (end+1) < len(text) and text[end] == "s" and (not text[end+1].isalpha()): return True
    return False #otherwise, return False

