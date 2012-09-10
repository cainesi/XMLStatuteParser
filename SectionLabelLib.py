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
                if tag in tagSection: sectionType = tagSection[tag]
                else: sectionType = tag
                if sectionType == "section":self.numberings.append(SectionNumbering(sectionType=sectionType,labelString=labelString))
                elif sectionType == "definition": self.numberings.append(DefinitionNumbering(sectionType=sectionType,labelString=labelString))
                elif sectionType == "formuladefinition": self.numberings.append(FormulaNumbering(sectionType=sectionType,labelString=labelString))
                else: self.numberings.append(Numbering(sectionType=sectionType,labelString=labelString))
                pass
            pass
        elif numberings != None: self.numberings = [c for c in numberings]
        return
    def setNumberings(self,numberings): self.numberings = numberings
    def getNumberings(self): return self.numberings
    def __add__(self,sl):
        """Creates a new sectionLabel by adding on the specified sectionLabel."""
        newSL = SectionLabel()
        newSL.setNumberings(self.getNumberings() + sl.getNumberings())
        return newSL
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
    def getIDString(self):
        """Returns a string that can be used match against reference to sections in the text of the instrument."""
        return u"".join(n.getIDString() for n in self.numberings)
    def getDisplayString(self):
        """Returns a string representation for the section label for debugging purposes."""
        return u"".join(n.getDisplayString() for n in self.numberings)
    def indentLevel(self): return sum(n.indentIncrement() for n in self.numberings)
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
    def getIDString(self): return u""
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
        self.currentSegment = self.currentSegment.advanceSegment(newNumbering)
        print self.currentSegment
        if self.currentSegment in self.segmentList: showError("Repeated Segment seen: ["+str(self.currentSegment)+"]")
        self.segmentList.append(self.currentSegment)
        self.currentPart = self.currentSegment.getPart()
        self.currentDivision = self.currentSegment.getDivision()
        self.currentSubdivision = self.currentSegment.getSubdivision()
        if self.currentSegment not in self.segmentContents: self.segmentContents[self.currentSegment] = set([])
        if self.currentPart not in self.segmentContents: self.segmentContents[self.currentPart] = set([])
        if self.currentDivision not in self.segmentContents: self.segmentContents[self.currentDivision] = set([])
        if self.currentSubdivision not in self.segmentContents: self.segmentContents[self.currentSubdivision] = set([])
        if title is not None:
            self.segmentTitle[self.currentSegment] = title
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

class SectionLabelRange:
    def __init__(self,start,end=None,universal = False):
        """initializes range with start and end points (for comparisons, test labels are truncated to the length of start or end, respective). If end is None, range will match against anything with start as a stem. If universal is True, the range will match all sectionLabels"""
        self.start = start
        self.universal = universal
        if self.universal:
            self.singleton = False
            return
        if end is None or start == end:
            self.singleton = True
            self.end = None
            pass
        else:
            self.singleton = False
            self.end = end
        pass
    
    def __str__(self):
        if self.universal:
            return "[universal]"
        if self.singleton:
            return "[%s]"%self.start
        return "[%s to %s]"%(str(self.start),str(self.end))

    def __repr__(self):
        return "<SectionLabelRange:%s>"%str(self)
    
    def containsSectionLabel(self,sectionLabel):
        if self.universal:
            return True
        sl = sectionLabel
        if self.singleton:
            return sl[:len(self.start)] == self.start
            pass
        if not sl[:len(self.start)] >= self.start:
            return False
        if not sl[:len(self.end)] <= self.end:
            return False
        return True
    
    def possiblyContainsSectionLabel(self,sectionLabel):
        """returns true if it is possible for an extention of this sectionLabel to be in the range"""
        
        if self.universal:
            return True
        if self.isSingleton(): #if a singleton, 
            x = min(len(self.start), len(sectionLabel))
            return sectionLabel[:x] == self.start[:x]
            pass
        xs = min(len(self.start),len(sectionLabel))
        xe = min(len(self.end),len(sectionLabel))
        
        return (sectionLabel[:xs]>=self.start[:xs] and sectionLabel[:xe]<=self.end[:xe])
        
    def isSingleton(self):
        return self.singleton
    
    def addSectionLabel(self,newLabel):
        if not self.singleton:
            raise Exception("attempting to add label to non-singleton range")
        self.singleton = False
        if newLabel< self.start:
            print("problem: adding to a SectionLabelRange below start point")
            self.end = self.start
            self.start = newLabel
            pass
        else:
            self.end = newLabel
            pass
        pass
    pass

    def isUniversal(self):
        return self.universal

class SectionLabelSet:
    def __init__(self,sectionLabelRangeList):
        self.sectionLabelRangeList = sectionLabelRangeList
        pass
    def __len__(self):
        return len(self.sectionLabelRangeList)
    def __str__(self):
        return "[" + ", ".join([str(c) for c in self.sectionLabelRangeList]) + "]"
    def __repr__(self):
        return "<SectionLabelSet:%s>"%str(self)
    def containsSectionLabel(self,sectionLabel):
        for range in self.sectionLabelRangeList:
            if range.containsSectionLabel(sectionLabel):
                return True
            pass
        return False
    def possiblyContainsSectionLabel(self,sectionLabel):
        for range in self.sectionLabelRangeList:
            if range.possiblyContainsSectionLabel(sectionLabel):
                return True
            pass
        return False
    def isUniversal(self):
        for range in self.sectionLabelRangeList:
            if range.isUniversal():
                return True
            pass
        return False
    
    def __cmp__(self,ls2):
        if self.isUniversal():
            if ls2.isUniversal():
                return 0
            else:
                return 1
            pass
        else:
            if ls2.isUniversal():
                return -1
            else:
                return 0
            pass
        pass
        

def makeRangeFromList(sLList):
    list = [c for c in sLList]
    list.sort()
    return SectionLabelRange(start=min(list),end=max(list))
