#$Id$
#$Revision$
#$Date$
#$URL$

import re
import sys
from Constants import sectionTypes, formulaSectionTypes, formulaSectionMap, textTypes, tagSection


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
        hash( tuple(n.getTuple() for n in self.numberings) )
        return
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


class Division:
    """class for the recording information about part/division/subdivision in the Act/regulations."""
    def __init__(self,part=None,division=None,subDivision=None):
        self.part = part
        self.division = division
        self.subDivision = subDivision
        if self.part is None:
            self.tuple = ()
            pass
        elif self.division is None:
            self.tuple = (self.part,)
            pass
        elif self.subDivision is None:
            self.tuple = (self.part,self.division)
            pass
        else:
            self.tuple = (self.part, self.division, self.subDivision)
            pass
        pass
    
    def getTuple(self):
        return self.tuple
    
    def __len__(self):
        return len(self.tuple)
    
    def __str__(self):
        titles = ("Part", "Division", "Subdivision")
        return " ".join(["%s %s" % c for c in zip(titles,self.tuple)])

    def labelString(self):
        """Return the string for the final part of the division (eg, for a sub-division, would be just "subdivision xxx")."""
        titles = ("PART", "Division", "Subdivision")
        parts = ["%s %s" % c for c in zip(titles,self.tuple)]
        if len(parts) == 0:
            return None
        return parts[-1]
        

    def __repr__(self):
        return "<Division:"+str(self)+">"

    def __eq__(self,d2):
        if not isinstance(d2,Division):
            raise Exception("Can only compare to Division object")
        if len(self) != len(d2):
            return False
        for x,y in zip(self.getTuple(),d2.getTuple()):
            if x != y:
                return False
            pass
        return True

    def __ne__(self,d2):
        return not self == d2

    def __hash__(self):
        return hash(self.tuple)

    def isSubDivisionOf(self,d2):
        """returns True if this Division is equal to or contained in the second Division object"""
        if not isinstance(d2,Division):
            raise Exception("Can only compare to Division object")
        
        if len(d2) > len(self):
            return False
        
        for c in [x==y for x,y in zip(self.tuple,d2.getTuple())]:
            if c == False:
                return False
            pass
        return True
    
    def getPart(self):
        if len(self) >= 1:
            return Division(part=self.part)
        return None
    def getDivision(self):
        if len(self) >= 2:
            return Division(part=self.part,division=self.division)
        return None
    def getSubDivision(self):
        if len(self) >= 3:
            return Division(part=self.part,division=self.division,subDivision=self.subDivision)
        return None 
    def getChangedDivisions(self,d2):
        """Get a list of slices of d2 that differ from self. E.g., if d2 has a part, division and subdivision, and self and d2 have the save part but different divisions, this would be a 2-element list of d2's division and subdivision."""
        changedDivisions = []
        stup = self.getTuple()
        dtup = d2.getTuple()
        if len(dtup)>=1 and (len(stup) < 1 or dtup[0] != stup[0]):
            changedDivisions.append(d2.getPart())
            changedDivisions.append(d2.getDivision())
            changedDivisions.append(d2.getSubDivision())            
            pass
        elif len(dtup)>=2 and (len(stup)<2 or dtup[1] != stup[1]):
            changedDivisions.append(d2.getDivision())
            changedDivisions.append(d2.getSubDivision())
            pass
        elif len(dtup)>=3 and (len(stup)<3 or dtup[2] != stup[2]):
            changedDivisions.append(d2.getSubDivision())
            pass
        changedDivisions = [c for c in changedDivisions if c is not None]
        return changedDivisions
        
    pass

class DivisionData:
    """class for storing data regarding divisions, including a dictionary linking sectionlabels to divisions, and a dictionary of division titles."""
    def __init__(self):
        self.divisionTitle = {} #dictionary indexed by division label, giving division title
        self.divisionDict = {} #dictionary indexed by sectional label, giving the division the section is in
        return
    def setDivisionTitle(self,division,title):
        self.divisionTitle[division] = title
    def getDivisionTitle(self,division):
        return self.divisionTitle[division]
    def clearDivisionDict(self):
        #discard the information regarding sl assignments
        self.divisionDict = {}
        return
    def assignSL(self,sL, division):
        self.divisionDict[sL] = division
    def getSLAssignment(self,sL):
        if sL not in self.divisionDict:
            return None
        return self.divisionDict[sL]
    def getSLsInDivision(self,division):
        """return an ordered list of sL's in a specified division"""
        #TODO
        return
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
