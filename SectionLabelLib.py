#$Id$
#$Revision$
#$Date$
#$URL$

from ErrorReporter import showError
from Constants import tagSection, sectionTypes

class SectionLabelException(Exception): pass

TEST = True
DEBUG = False

class SectionLabel:
    """Class encapsulating the label for a specific section of an Act."""
    def __init__(self,labelList=None,numberings=None):
        """Constructs a SectionLabel object from the list of tuples (sectionType, sectionlabelstring).  The type can be specified either by 2-character tags, as returned by the code param parser, or by the full name of the section type."""
        self.numberings = []
        if labelList != None:
            for tag, labelString in labelList:
                if tag in tagSection: sectionType = tagSection[tag] #decode the short version of the section name.
                else: sectionType = tag
                if sectionType == "section":self.numberings.append(SectionNumbering(sectionType=sectionType,labelString=labelString))
                elif sectionType == "definition": self.numberings.append(DefinitionNumbering(sectionType=sectionType,labelString=labelString))
                elif sectionType == "formuladefinition": self.numberings.append(FormulaNumbering(sectionType=sectionType,labelString=labelString))
                else: self.numberings.append(Numbering(sectionType=sectionType,labelString=labelString))
                pass
            pass
        elif numberings != None: self.numberings = [c for c in numberings]
        return
    #def setNumberings(self,numberings): self.numberings = numberings #these object should be immutable after creation!
    def getNumberings(self): return self.numberings
    def __add__(self,sl):
        """Creates a new sectionLabel by adding on the specified sectionLabel."""
        return SectionLabel(numberings=self.getNumberings() + sl.getNumberings())
    def __getitem__(self,n):
        """Create a SectionLabel which is a slice of the current label."""
        if type(n) == slice: return SectionLabel(numberings=self.numberings[n])
        return SectionLabel(numberings=[self.numberings[n]])
    def __len__(self):
        return len(self.numberings)
    def __eq__(self,sl):
        if sl == None: return False
        if len(self) != len(sl): return False
        for c in range(0,len(self)):
            if self.numberings[c] != sl.numberings[c]: return False
            pass
        return True
    def __ne__(self,sl): return not self.__eq__(sl)
    def getSubLabels(self):
        """Returns the list of non-empty initial-sublabels of this label (including the label itself)."""
        return [self[:n] for n in xrange(len(self),0,-1)]
    def quasiEqual(self,sl):
        """Returns True if the last numberings are quasiEqual and the remaining numberings are actually equal.  Used for testing whether imputed section labels are being computed accurately (since impused section labels will not know what term is being defined in a definition section)"""
        if sl == None: return False
        if len(self) != len(sl): return False
        if len(self) == 0: return True
        if not self.numberings[-1].quasiEqual(sl.numberings[-1]): return False
        if self[:-1] != sl[:-1]: return False
        return True
    def containsSection(self,sl):
        if len(self) > len(sl): return False
        for c in range(0,len(self)):
            if self.numberings[c] != sl.numberings[c]: return False
            pass
        return True
    def __hash__(self):
        return hash( tuple(n.getTuple() for n in self.numberings) ) #TODO: have this calculated only once, and then stored for future use?
    def addLabel(self,labelType,labelString):
        """Creates a new sectionLabel by appending the specified labelString."""
        newSL = SectionLabel(labelList = [(labelType,labelString)])
        return self + newSL
    def __str__(self): return self.getIDString()
    def __repr__(self):
        return self.getDisplayString()
    def getIDString(self):
        """Returns a string that can be used match against reference to sections in the text of the instrument."""
        return u"".join(n.getIDString() for n in self.numberings)
    def getDisplayString(self):
        """Returns a string representation for the section label for debugging purposes."""
        return u"".join(n.getDisplayString() for n in self.numberings)
    def indentLevel(self): return sum(n.indentIncrement() for n in self.numberings)
    def hasLastEmptyDefinition(self):
        """Returns True if one of the SectionLabel's numberings is an empty definition."""
        if len(self.numberings) == 0: return False
        if isinstance(self.numberings[-1],DefinitionNumbering) and self.numberings[-1].labelString == "": return True
        return False
    pass

class Numbering(object):
    def __init__(self, sectionType,labelString):
        if sectionType not in sectionTypes: raise SectionLabelException("Not a valid sectionType: ["+sectionType+"]")
        self.sectionType = sectionType
        self.labelString = labelString
        return
    def __eq__(self, n):
        if self.getSectionType() != n.getSectionType(): return False
        if self.getLabelString() != n.getLabelString(): return False
        return True
    def __ne__(self,n): return not self.__eq__(n)
    def quasiEqual(self,n):
        """Returns true if actually equal or if both are definitions.  Used for verifying the consistency of imputed section labels."""
        if self.getSectionType() == "definition" and n.getSectionType() == "definition": return True
        else: return self == n
    def getLabelString(self): return self.labelString
    def getSectionType(self): return self.sectionType
    def getIDString(self): return "(" + self.labelString + ")"
    def getDisplayString(self): return u"["+ unicode(self.sectionType) + u" : <" + unicode(self.labelString) + u">]"
    def indentIncrement(self): return 1
    def getTuple(self): return (self.sectionType, self.labelString)
    
class SectionNumbering(Numbering):
    def __init__(self,sectionType,labelString):
        labelString = labelString.rstrip(".") #strip trailing period off the section label string, since sections are written 4(2), not 4.(2)
        Numbering.__init__(self,sectionType,labelString)
        return
    def getIDString(self): return self.labelString #no parentheses around section number
class DefinitionNumbering(Numbering):
    def getIDString(self): return u"[\"" + self.labelString + u"\"]"
    def indentIncrement(self): return 0
class FormulaNumbering(Numbering):
    def getIDString(self): return u"<" + self.labelString + u">" #return u""
    def indentIncrement(self): return 0 #TODO: should have an increment if this is inside another formula numbering (to make nested formulas clearer)

#####
#
# Code for handling statute divisions (e.g., 
#
#####

validSegmentTypes = ["part","division","subdivision"]
segmentTitleString = {"part":"PART","division":"Division","subdivision":"subdivision"}

class SegmentNumbering:
    """Class for a single segment level."""
    def __init__(self,segmentType,labelString):
        self.segmentType = segmentType
        if self.segmentType not in validSegmentTypes: raise SectionLabelException("Unknown segment numbering type: ["+segmentType+"]")
        self.labelString = labelString
        return
    def getSegmentType(self): return self.segmentType
    def getLabelString(self): return self.labelString
    def getString(self): return segmentTitleString[self.segmentType] + u" " + self.labelString
    def __hash__(self): return hash((self.segmentType,self.labelString))
    def __eq__(self,dn):
        if dn is None: return False
        if dn.segmentType != self.segmentType: return False
        if dn.labelString != self.labelString: return False
        return True
    def __ne__(self,dn): return not self == dn
    def __repr__(self): return "<SegmentNumbering:" + self.segmentType + ":" + self.labelString + ">"
    def __str__(self): return self.getString()
    pass

class Segment:
    """class for the recording the full segment data for a portion of the act, composed of a list of SegmentNumberings."""
    def __init__(self,segmentNumberingList):
        self.numberings = segmentNumberingList
        self.confirmNumberings()
        return

    def confirmNumberings(self):
        """Confirm that the numberings for this Segment conform to our expectations (part, division, subdivision) or throw an exception."""
        if len(self.numberings) > 0:
            if self.numberings[0].getSegmentType() != "part": raise SectionLabelException("First element of Segment not part: ["+str(self.numberings)+"]")
        else: return True
        if len(self.numberings) > 1:
            if self.numberings[1].getSegmentType() != "division": raise SectionLabelException("Second element of Segment not division: ["+str(self.numberings)+"]")
        else: return True
        if len(self.numberings) > 2:
            if self.numberings[2].getSegmentType() != "subdivision": raise SectionLabelException("Third element of Segment not subdivision: ["+str(self.numberings)+"]")
        else: return True
        if len(self.numberings) > 3:
            raise SectionLabelException("Excessively long numbering list for Segment object: ["+str(self.numberings)+"]")
        return True

    def __len__(self):
        return len(self.numberings)

    def __iter__(self):
        for n in self.numberings: yield n

    def __eq__(self,s2):
        if s2 is None: return False
        if len(self) != len(s2): return False
        for c in xrange(0,len(self)):
            if self.numberings[c] != s2.numberings[c]: return False
        return True

    def __ne__(self,s2):
        return not self == s2

    def __hash__(self):
        return hash(tuple(hash(c) for c in self))

    def __str__(self): return "(" + " ".join(str(c) for c in self.numberings) + ")"

    def __repr__(self): return "<Segment:"+self.numberings+">"

    def advanceSegment(self,newNumbering):
        """Returns the next Segment following this Segment, that involves the given newNumbering."""
        if newNumbering.getSegmentType() == "part":
            return Segment([newNumbering])
        elif newNumbering.getSegmentType() == "division":
            if len(self) < 1: raise SectionLabelException("Adding division to a length 0 Segment.")
            return Segment([self.numberings[0], newNumbering])
        elif newNumbering.getSegmentType() == "subdivision":
            if len(self) < 2: raise SectionLabelException("Adding subdivision to a Segment of length < 2.")
            return Segment(self.numberings[0:2] + [newNumbering])
        raise SectionLabelException("Cannot add specified numbering to Segment object: ["+str(newNumbering)+"]")

    def isSubSegmentOf(self,s2):
        """returns True if this Segment is equal to or contained in (i.e., is a subset of) the second Segment object"""
        if not isinstance(s2,Segment): raise SectionLabelException("Can only do containment comparison with Segment object")
        if len(s2) > len(self):
            return False
        for c in xrange(0,len(s2)):
            if s2.numberings[c] != self.numberings[c]: return False
        return True

    def isSuperSegmentOf(self,s2):
        """converse of isSubSegmentOf"""
        if not isinstance(s2,Segment): raise SectionLabelException("Can only do containment comparison with Segment object")
        return s2.isSubSegmentOf(self)

    def getPart(self):
        if len(self) >= 1:
            return Segment(self.numberings[:1])
        return None
    def getDivision(self):
        if len(self) >= 2:
            return Segment(self.numberings[:2])
        return None
    def getSubdivision(self):
        if len(self) >= 3:
            return Segment(self.numberings[:3])
        return None
    def getChangedNumberings(self,d2):
        """Get a list of slices of d2 that differ from self. E.g., if d2 has a part, division and subdivision, and self and d2 have the save part but different divisions, this would be a 2-element list of d2's division and subdivision."""
        for c in xrange(0,len(self)):
            if c >= len(d2): return list()
            if self.numberings[c] != d2.numberings[c]: return d2.numberings[c:]
            pass
        return d2.numberings[len(self):]
        
    pass

class SegmentData:
    """Class for storing data regarding divisions, including a dictionary linking sectionlabels to divisions, and a dictionary of division titles.  Allows sections and segment headings to be recorded as they are encountered moving through the Act, and records how the sections are grouped together into Segments (parts, divisions, etc)."""
    def __init__(self, statute):
        self.statute = statute
        self.currentSegment = Segment([]) #the division sections are currently being added to
        self.currentPart = None
        self.currentDivision = None
        self.currentSubdivision = None
        self.segmentList = []
        self.segmentTitle = {} #dictionary indexed by Segment, giving segment's title
        self.containingSegment = {} #dictionary indexed by sectional label, giving the most narrowest Segment the section is in
        self.segmentContents = {} #dictionary providing a set of sections in each segment of the statute
        self.segmentContents[Segment([])] = set([]) #these two entries are dumping grounds for sections that are not in a Segment at all, or do not have a division / subdivision / etc
        self.segmentContents[None] = set([])
        return
    def addNewNumbering(self,newNumbering, title=None):
        """Called when a new heading numbering seen in the court of the statute.  This method computes what new segment must be (based on the latest numbering and the numberings of the preceding segment) and updates the segment information accordingly."""
        self.currentSegment = self.currentSegment.advanceSegment(newNumbering)
        if self.currentSegment in self.segmentList: showError("Repeated Segment seen: ["+str(self.currentSegment)+"]")
        self.segmentList.append(self.currentSegment)
        self.currentPart = self.currentSegment.getPart()
        self.currentDivision = self.currentSegment.getDivision()
        self.currentSubdivision = self.currentSegment.getSubdivision()
        if self.currentSegment not in self.segmentContents: self.segmentContents[self.currentSegment] = set([])
        if self.currentPart not in self.segmentContents: self.segmentContents[self.currentPart] = set([])
        if self.currentDivision not in self.segmentContents: self.segmentContents[self.currentDivision] = set([])
        if self.currentSubdivision not in self.segmentContents: self.segmentContents[self.currentSubdivision] = set([])
        if title is not None: self.segmentTitle[self.currentSegment] = title
        return
    def addSection(self,sectionLabel):
        """Record that the specified sectionLabel exists within the current Segment of the statute (and all enclosing super-Segments)."""
        self.containingSegment[sectionLabel] = self.currentSegment
        self.segmentContents[self.currentPart].add(sectionLabel)
        self.segmentContents[self.currentDivision].add(sectionLabel)
        self.segmentContents[self.currentSubdivision].add(sectionLabel)
        self.segmentContents[self.currentSegment].add(sectionLabel)
        return
    def setSegmentTitle(self,segment,title):
        self.segmentTitle[segment] = title
    def getSegmentTitle(self,segment):
        return self.segmentTitle[segment]
    pass

class SectionData(object):
    def __init__(self,statute):
        """
        Object that encapsulates information about the ordering of sections in the Statute, and various look-up tables so that SectionItems can be located based on the full or partial text representation of the label.
        self.sectionStart - for each sL gives the number of appearance for the label
        self.sectionEnd - for each sL gives the appearance of the last section for which this section is a super-label
        self.stringToSection - for each string representation of a sL gives the corresponding sectionItem

        @type statute: Statute.Statute
        """
        self.statute = statute
        self.sectionList = [si for si in self.statute.sectionIterator()] #this will get us a list of all sections, in order
        self.sectionStart = {}
        self.sectionEnd = {} #the number of the last label under the given label
        self.numberToSL = {} #gives the SL corresponding to a specific label number
        self.stringToSectionItem = {}
        n = 0
        for section in self.sectionList: #asign a number to each section labeling
            sL = section.getSectionLabel()
            if sL in self.sectionStart:  #if we've already seen the sectionLabel
                if sL.hasLastEmptyDefinition(): pass #if there are duplicates because we have multiple empty defs, just ignore (there will be other errors generated, if these are not repealed)
                else: showError("Duplicated sectionLabel ["+str(sL)+"]["+section.getRawText()+"]", location=section)
            else:
                self.sectionStart[sL] = n
                self.sectionEnd[sL] = n+1 #plus one, so we follow the usual python interval-convention
                for superSL in sL.getSubLabels(): self.sectionEnd[superSL] = n+1 #TODO: should we use "parent" members of the section to trace up the list of supersection instead?  (worried that readas provisions might break this in some cases)
                self.numberToSL[n] = sL
                sLString = sL.getIDString()
                if sLString in self.stringToSectionItem: showError("Repeated sectionlabel string representation ["+sLString+"]["+section.getRawText()+"]",location=section)
                else: self.stringToSectionItem[sLString] = section
            n += 1
            pass
        return

    def ltSL(self, sL1, sL2):
        """
        Compare two section labels, returns True if sL1 is earlier than sL2.
        @type sL1: SectionLabel
        @type sL2: SectionLabel
        """
        return self.sectionStart[sL1] < self.sectionStart[sL2]
    def leSL(self,sL1,sL2):
        """
        Compare two section labels, returns True if sL1 is earlier than sL2.
        @type sL1: SectionLabel
        @type sL2: SectionLabel
        """
        return self.sectionStart[sL1] <= self.sectionStart[sL2]
    def cmpSL(self,sL1,sL2):
        if self.leSL(sL1,sL2):
            if self.ltSL(sL1,sL2):return -1
            return 0
        return 1

    def getSectionItemFromString(self,sLString,locationItem=None,locationSL=None):
        """Returns the sectionItem references by the given string.  If location is provided, it will also try to match sectionLabel strings by combining stems from the location label's string with the specified string.  Returns None (and shows an error) if no matches can be found.
        @type sLString: unicode
        @type locationSL: SectionLabel
        @type locationItem: StatuteItem.SectionItem
        @rtype: StatuteItem.SectionItem
        """
        if sLString in self.stringToSectionItem: return self.stringToSectionItem[sLString]
        if locationSL is None:
            if locationItem is None: showError("Could not locate sectionlabel string ["+sLString+"]"); return None
            locationSL = locationItem.getSectionLabel()
            pass
        for subLabel in locationSL.getSubLabels():
            #print(">>" + subLabel.getIDString() + sLString)
            if (subLabel.getIDString() + sLString) in self.stringToSectionItem: return self.stringToSectionItem[subLabel.getIDString() + sLString]
            pass
        showError("Could not find item for ["+sLString+"][hint:"+locationSL.getIDString()+"]")
        return None

    def getSectionInterval(self,sLList):
        return SectionLabelInterval(self,sLList)

    def getSectionCollection(self,sLListList):
        intervals = [self.getSectionInterval(l) for l in sLListList]
        return SectionLabelCollection(self,intervals)

    def getUniversalCollection(self):
        return UniversalSectionLabelCollection(self)

class SectionLabelInterval(object):
    """Class representing a contiguous interval of sections."""
    def __init__(self, sectionData, sLList):
        self.sectionData = sectionData
        self.start = -1
        self.end = -1
        if len(sLList) > 0:
            self.start = self.sectionData.sectionStart[sLList[0]]
            self.end = self.sectionData.sectionEnd[sLList[0]]
            for sL in sLList[1:]:
                if self.sectionData.sectionStart[sL] < self.start: self.start = self.sectionData.sectionStart[sL]
                if self.sectionData.sectionEnd[sL] > self.end: self.end = self.sectionData.sectionEnd[sL]
                pass
            pass
        return

    def containsSL(self,sL):
        """Returns True if the given section label is contained in the interval, otherwise False.
        @type sL: SectionLabel
        """
        n = self.sectionData[sL]
        if n >= self.start and n < self.end: return True
        return False

    def __len__(self):
        return self.start - self.end

    def __str__(self):
        if self.start == -1: return "<Range: empty>"
        return "<SectionInterval:"+ str(self.sectionData.numberToSL[self.start]) +"---"+ str(self.sectionData.numberToSL[self.end-1]) +">"
    def __contains__(self,sL): return self.containsSL(sL)


class SectionLabelCollection(object):
    """Class representing an arbitrary collection of sections, broken up into intervals."""
    def __init__(self,sectionData,intervalList):
        self.sectionData = sectionData
        self.intervals = intervalList
        return
    def containsSL(self,sL):
        """Returns True if the given section label is contained in the interval, otherwise False.
        @type sL: SectionLabel
        """
        for interval in self.intervals:
            if sL in interval: return True
        return False
    def __str__(self):
        return "<SectionCollection:" + "".join(str(c) for c in self.intervals) + ">"
    def __len__(self): return sum(len(c) for c in self.intervals)
    def __contains__(self,sL): return self.containsSL(sL)

class UniversalSectionLabelCollection(object):
    """Object that the whole range of sections in the Statute."""
    def __init__(self,sectionData): self.sectionData = sectionData; return
    def containsSL(self): return True
    def __str__(self): return "<SectionUniversal>"
    def __len__(self):
        return len(self.sectionData.sectionList) * len(self.sectionData.sectionList) #amount that should be greater than the size of any non-universal collection