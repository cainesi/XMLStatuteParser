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
    def isSuperSectionLabelOf(self,sl):
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
    def getIDString(self):
        """Returns a string that can be used match against reference to sections in the text of the instrument."""
        return u"".join(n.getIDString() for n in self.numberings)
    def getDisplayString(self):
        """Returns a string representation fo the section label for debugging purposes."""
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
    def getIDString(self): return u"[" + self.labelString + u"]"
    def indentIncrement(self): return 0
class FormulaNumbering(Numbering):
    def getIDString(self): return u""
    def indentIncrement(self): return 0
#
#class SectionLabel:
#    """class for handling sectionlabels that appear in DoJ statutes --- each section number is internally represented as a tuple of tuples of integers, together with information about how to translate back and forth to a string represenation. tuples are created in such a way that tuple comparison gives the correct ordering."""
#    def __init__(self,struct=None,numberings=None):
#        """SectionLabel(struct) returns the label object for the structure rooted at struct (only
#        used for calculating the label), raises exception if no Label."""
#        self.struct = struct
#        
#        self.ignoredNumberings = False #this is set to true if there were parts of the rawNumberings that were ignored
#        
#        #if no numberings provided (usual case) calculate them from structure
#        if numberings == None:
#            s = self.struct.divLabel()
#            if s == None:
#                raise Exception("Attempting to get label for a label-less item: %s"%struct.nodeString())
#            self.raw = s
#            if s[:2] != "se":
#                raise Exception("Not a section label: %s"%s)
#            l = s.split("-")
#            self.numberings = []   
#            for c in l: 
#                n = makeNumberingFromDivData(c)
#                if n.isTerminator():
#                    self.ignoredNumberings = True
#                    break
#                self.numberings.append(n)
#                pass
#            pass
#        #if numberings provided, then this is a synthetic label
#        else:
#            self.raw = ""
#            #make copy of list
#            self.numberings = [c for c in numberings]
#            pass
#        
#        self.refreshTuple()
#        
#        #set the definition string if the final part of the numbering is "df" (this means that we are at the top of the definition, and the quoted defined term should be at the start of the text). This is not needed with ITALib2
#        #if self.terminalType() == "df" and not self.ignoredNumberings:
#        #    self.setDefinedTerm(struct.getRawDefinedTerm())
#        return
#    
#    def __eq__(self,sl):
#        """returns equal if other object is a SectionLabel with the same numberings."""
#        if not isinstance(sl,SectionLabel):
#            return False
#        if len(self) != len(sl):
#            return False
#        for n in xrange(0,len(self)):
#            if self[n] != sl[n]:
#                return False
#            pass
#        return True
#    
#    def __ne__(self,sl):
#        return not self == sl
#    
#    def __cmp__(self,sl):
#        #returns a numberings-wise comparison between sectionlabels, numberings with different tags are compared alphabetically by tag
#        if not isinstance(sl,SectionLabel):
#            raise Exception("Can only compare SectionLabel to other SectionLabels: %s" % sl.__repr__())
#        for n in xrange(0,min(len(self),len(sl))):
#            if self[n].getTag() != sl[n].getTag():
#                return cmp(self[n].getTag(),sl[n].getTag())
#            else:
#                if self[n] > sl[n]:
#                    return 1
#                elif self[n] < sl[n]:
#                    return -1
#                pass
#            if len(self)> len(sl):
#                return 1
#            elif len(self) < len(sl):
#                return -1
#            return 0
#        
#        #if self.tuple > sl.getTuple():
#        #    return 1
#        #elif self.tuple < sl.getTuple():
#        #    return -1
#        ##TODO: reflect self.ignoredTerms
#        #
#        #else:
#        #    return 0
#    
#    def __str__(self):
#        return "".join(str(c) for c in self.numberings)
#    
#    def __repr__(self):
#        return "<SectionLabel:%s>" % "-".join(["%s%s"%(c.getTag(),str(c)) for c in self.numberings])
#    
#    def __len__(self):
#        return len(self.numberings)
#    
#    def __getitem__(self,n):
#        #if we are passed a slice, return the section label with just those numberings
#        if type(n)== slice:
#            return SectionLabel(self.struct,self.numberings[n])
#        return self.numberings[n]
#
#    def __hash__(self):
#        return hash(self.tuple)
#    
#    def getParentSectionLabel(self):
#        if len(self) == 0:
#            raise Exception("No parent for a SectinLabel of length zero.")
#            pass
#        return SectionLabel(numberings=self.numberings[:-1])
#
#    def refreshTuple(self):
#        self.tuple = tuple(c.getTuple() for c in self.numberings)
#        pass
#    
#    def getNumberings(self):
#        return tuple(self.numberings)
#    
#    def getTuple(self):
#        return self.tuple
#    
#
#    def isSubsection(self,sl):
#        """self.isSubsection(sl) returns true if self is a subsection of sl"""
#        t = sl.getTuple()
#        if len(t) < len(self.tuple):
#            return False
#        for c in zip(self.tuple,t):
#            if c[0] != c[1]:
#                return False
#            pass
#        #if first label has ignored numbering, then second label needs to have ignored numbering and be same length to be subsection
#        if self.ignoredNumberings and not (sl.ignoredNumberings and len(t)==len(self.tuple)):
#            return False
#        return True
#
#    def isProperSubsection(self,sl):
#        """self.isProperSubsection(sl) returns true if self is a proper subsection of sl (ie, self is a
#        subsection which is shorter, or it is a subsection of the same length, but only sl has ignoredNumberings"""
#        t = sl.getTuple()
#        if len(t) > len(self.tuple):
#            return self.isSubsection(sl)
#        elif len(t) == len(self.tuple):
#            return self.isSubsection(sl) and (sl.ignoredNumberings) and (not self.ignoredNumberings)
#        else:
#            return False
#
#    #specifial functions for dealing with definition labels
#    def isDefinition(self):
#        """returns true if this item labels part of a definition"""
#        for c in self.numberings:
#            if c.getTag() == "df":
#                return True
#            pass
#        return False
#    
#    def isDefinitionTop(self):
#        """returns true if this label is for the top of a definition"""
#        return (self.numberings[-1].getTag() == "df")
#    
#    
#    def getDefinedTerm(self):
#        """getDefinedTerm() returns the term being defined by a definition label"""
#        for c in self.numberings:
#            if c.getTag() == "df":
#                tup = c.getTuple()
#                # if tuple is the empty tuple, definition has not been set yet, return None
#                if tup == ():
#                    return None
#                return tup[0]
#            pass
#        raise Exception("Attempting to get defined term for non-definition section: %s"%self.raw)
#    
#    def linkTo(self,renderContext,text=None,sectionType = "Section"):
#        """return a wiki-link to this label"""
#        #create link
#        linkStart = self.linkSectionString(sectionType=sectionType)
#        defaultText = linkStart
#        if len(self)==1:
#            linkEnd=None
#        else:
#            ss = self.linkSubsectionString()
#            defaultText += ss
#            linkEnd = ss
#            pass
#        if text == None:
#            text = defaultText
#        
#        return renderContext.renderLink(targetSection=linkStart, targetAnchor = linkEnd,linkText=text)
#        #return "[[%s%s|%s]]"%(linkStart,linkEnd,text)
#    
#    def anchor(self,renderContext):
#        if len(self) < 2:
#            raise Exception("Seeking anchor for top-level label")
#        else:
#            return renderContext.renderAnchor(self.linkSubsectionString())
#        pass
#    
#    def linkSectionString(self,sectionType = "Section"):
#        """returns the string for the section title, for use in link"""
#        return sectionType + " " + str(self.numberings[0])
#    
#    def linkSubsectionString(self):
#        l = [str(c) for c in self.numberings[1:]]
#        s = "".join(l)
#        return s
#    
#    def getKey(self):
#        """returns a key for the SectionLabel. Ideally, this should be unique among SectionLabels."""
#        return "-".join(["[%s:%s]"%(c.getTag(),c.__str__()) for c in self.numberings])
#    
#    #methods that are now unneeded with the ITALib-2 approach
#    def getRaw(self):
#        return self.raw
#    
#    def missingPriorLabel(self):
#        """if this is SectionLabel following a missing label, then this function returns the hypothetical missing label"""
#        if len(self.numberings)<2:
#            raise Exception("trying to get prior label for depth < 2 label")
#        first = self.numberings[0]
#        tmpsecond = self.numberings[1]
#        tup = tmpsecond.getTuple()
#        #TODO, we assume that what we need to insert is subsection (1), but, hypothetically, there could be a section w/o
#        #subsection (1) (starting at 2, etc) --- need to check raw text to deal with that?
#        if not (tup[0] > 1 or len(tup)>1 or len(self.numberings)>2):
#            raise Exception("seeking prior label for bad label:%s"%str(self))
#            pass
#        newtup = (1,)
#        second = makeNumberingFromTuple(typeTag = tmpsecond.getTag(),tuple=newtup)
#        return SectionLabel(struct = self.struct,numberings = [first,second])
#    
#    def setDefinedTerm(self,s):
#        """setDefinedTerm(s) sets the string of the defined term for the definition."""
#        for c in self.numberings:
#            if c.getTag()=="df":
#                c.setDefinedTerm(s)
#                break
#            pass
#        self.refreshTuple()
#    
#    
#    def hasIgnoredNumberings(self):
#        return self.ignoredNumberings
#
#    def terminalType(self):
#        if len(self.numberings) == 0:
#            return ""
#        return self.numberings[-1].getTag()
#    
#
#class Numbering:
#    """superclass for the various numbering types--- these are immutable, except for the hack that the defined term can be added afterwards"""
#    maxLevel = 1000 #non-restrictive default limits
#    minLevel = 0
#    hint = None
#    def __init__(self,labelStr = None, divData = None, tuple = None):
#        if labelStr != None:
#            m = self.__class__.labelPattern.match(labelStr)
#            if m == None:
#                raise ParseException("No match for %s: %s" %(self.getTag(),labelStr))
#            try:
#                self.tuple = self.labelToTuple(labelStr)
#            except Exception:
#                raise ParseException()
#            pass
#        elif divData != None:
#            try:
#                self.tuple = self.divDataToTuple(divData)
#            except Exception:
#                raise ParseException()
#            pass
#        elif tuple != None:
#            self.tuple = tuple
#            pass
#        else:
#            raise Exception("creating Numbering with no parameters")
#        pass
#
#    def __eq__(self,n2):
#        """tests for equality between numberings--- numberings are equal if they have the same tag and the same tuple.  Numberings are not equal with any object that is not a Numbering instance."""
#        if not isinstance(n2,Numbering):
#            return False
#        if self.getTag() == n2.getTag() and self.getTuple() == n2.getTuple():
#            return True
#        return False
#    
#    def __ne__(self,n2):
#        return not self == n2
#    
#    def __hash__(self):
#        return hash((self.getTag(),self.getTuple()))
#    
#    def __lt__(self,n2):
#        if not isinstance(n2,Numbering):
#            raise Exception("Can only compare Numbering to other Numberings: %s, %s"%(self.__repr__(),n2.__repr__()))
#        if self.getTag() != n2.getTag():
#            raise Exception("Cannot compare Numberings of different types: %s, %s"%(self.__repr__(),n2.__repr__()))
#        return self.getTuple() < n2.getTuple()
#    
#    def __gt__(self,n2):
#        if not isinstance(n2,Numbering):
#            raise Exception("Can only compare Numbering to other Numberings: %s, %s"%(self.__repr__(),n2.__repr__()))
#        return n2 < self
#    
#    def isNextAfter(self,n2):
#        if self.getTag() != n2.getTag():
#            return False
#        if len(self.tuple) < 1 or len(n2.getTuple()) < 1:
#            return False
#        if self.tuple[0] == n2.getTuple()[0] + 1:
#            return True
#        elif self.tuple[0] == n2.getTuple()[0]:
#            return self > n2
#        else:
#            return False
#            
#    
#    def isTerminator(self):
#        """indicates whether this numbering represents a termination of the sectionlabel even though there was more div-data to process.  Overridden in appropriate subclasses."""
#        return False
#
#    def setDefinedTerm(self,s):
#        if self.getTag() != "df":
#            raise Exception("Attempting to set definition of non definition numbering: %s/%s"%(s,self.raw))
#        self.tuple = (s,)
#
#    def getTuple(self):
#        return self.tuple
#    
#    def getTag(self):
#        """Returns a 2-character tag identifying the numbering type (based on the codes used in div tag id fields).  Implemented by subclasses."""
#        return ""
#    
#    def __str__(self):
#        if self.getTuple() == None:
#            return ""
#        return self.tupleToStr(self.tuple)
#    
#    def __repr__(self):
#        return "<%s: %s>"%(self.getTag(), self.tupleToStr(self.getTuple()) if self.getTuple() is not None else "None")
#
#    def getMaxLevel(self):
#        return self.__class__.maxLevel
#    def getMinLevel(self):
#        return self.__class__.minLevel
#    def isInitial(self):
#        """Can this numbering be the first numbering of a level of that type.  Generally true if the corresponding tuple is (1,).  Needs to be overridden in some subclasses."""
#        if self.getTuple() == (1,):
#            return True
#        return False
#    def isFormula(self):
#        """returns true if the numbering is top level for the definition of a formula variable (generally false)."""
#        return False
#    def isFollower(self):
#        """Return True if this type of numbering can follow other numbering types on the same level.  Generally False."""
#        return False
#    def isFarFollower(self):
#        """Return True if this type of numbering can follow other numbering type on the same level, after a hiatus at a lower level.  Generally the same as isFollower()."""
#        return self.isFollower()
#    def penalty_ordering(self):
#        return 150
#    def penalty_contiguous(self):
#        return 50
#    def penalty_ignored(self):
#        """penalty for ignoring a potential numbering of this type"""
#        return 100
#    def hasHint(self):
#        if self.hint == None: return False
#        return True
#    def getHint(self):
#        return self.hint
#
#class ParseException(Exception):
#    pass
#
#class SENumbering(Numbering):
#    """Class for base section numbering. E.g. 5, 14.02"""
#    maxLevel = 0
#    hint = "section"
#    labelPattern = re.compile("\d+(\.\d*)?")
#    def getTag(self):
#        return "se"
#    @staticmethod
#    def divDataToTuple(s):
#        #se elements are numbers, separated by periods (at most 2 numbers), numbers after the period are individual digits
#        ss = s.strip("_")
#        l = ss.split("_")
#        if len(l)<1 or len(l)>2:
#            raise Exception("SE element with wrong number of elemens: %s"%s)
#        lout = []
#        lout.append(int(l[0]))
#        if len(l)>1:
#            lout += [int(c) for c in list(l[1])]
#        return tuple(lout)
#    @staticmethod
#    def tupleToStr(t):
#        if len(t)<=1:
#            return "%s"%t[0]
#        return "%s.%s"%(t[0], "".join(str(c) for c in t[1:]))
#    @staticmethod
#    def labelToTuple(labelStr):
#        l = labelStr.split(".")
#        if len(l)>2:
#            raise ParseException("too many period separated parts in label")
#        ll = [l[0]] #part before period is a number
#        if len(l) > 1: #part after, if any, is individual digits
#            ll += list(l[1])
#            pass
#        lln = [int(c) for c in ll] #convert to integers
#        return tuple(lln)
#    pass
#
#class SSNumbering(Numbering):
#    """Class for subsection numbering. E.g (3), (7.2), (8.03)"""
#    hint="subsection"
#    labelPattern = re.compile("\(\d+(\.\d*)?\)")
#    def getTag(self):
#        return "ss"
#    @staticmethod
#    def divDataToTuple(s):
#        #ss elements are numbers (in parens), separated by a period and then numbers (each digit is a separate index)
#        ss = s.strip("_")
#        l = ss.split("_")
#        if len(l)<1 or len(l)>2:
#            raise Exception("SS element with wrong number of elemens: %s"%s)
#        lout = []
#        lout.append(int(l[0]))
#        if len(l)>1:
#            lout += [int(c) for c in list(l[1])]
#        return tuple(lout)
#    @staticmethod
#    def tupleToStr(t):
#        if len(t)<=1:
#            return "(%s)"%t[0]
#        return "(%s.%s)"%(t[0], "".join(str(c) for c in t[1:]))
#    @staticmethod
#    def labelToTuple(labelStr):
#        if labelStr[0] != "(" or labelStr[-1] != ")":
#            raise ParseException()
#        labelStr = labelStr[1:-1]
#        l = labelStr.split(".")
#        if len(l)>2:
#            raise ParseException("too many period separated parts in label")
#        ll = [l[0]] #part before period is a number
#        if len(l) > 1: #part after, if any, is individual digits
#            ll += list(l[1])
#            pass
#        lln = [int(c) for c in ll] #convert to integers
#        return tuple(lln)
#
#
#class P1Numbering(Numbering):
#    """Class for lower case letter numbering in statute. E.g. (a), (d), (h.02)"""
#    hint = "paragraph"
#    labelPattern = re.compile("\([a-z]{1,2}(\.\d*)?\)")
#    def getTag(self):
#        return "p1"
#    @staticmethod
#    def divDataToTuple(s):
#        #p1 elemenets are letter, followed by a period and then numbers (each digit is a separate index)
#        ss = s.strip("_")
#        l = ss.split("_")
#        if len(l)<1 or len(l)>2:
#            raise Exception("P1 element with wrong number of elemens: %s"%s)
#        lout = []
#        lout.append(a2i[l[0].lower()])
#        if len(l)>1:
#            lout += [int(c) for c in list(l[1])]
#        return tuple(lout)
#    @staticmethod
#    def tupleToStr(t):
#        if len(t)<=1:
#            return "(%s)"%i2a[t[0]]
#        return "(%s.%s)"%(i2a[t[0]], "".join(str(c) for c in t[1:]))
#    @staticmethod
#    def labelToTuple(labelStr):
#        if labelStr[0] != "(" or labelStr[-1] != ")":
#            raise ParseException()
#        labelStr = labelStr[1:-1]
#        l = labelStr.split(".")
#        if len(l)>2:
#            raise ParseException("too many period separated parts in label")
#        ll = [ a2i[l[0]] ]
#        if len(l)>1:
#            ll += list(l[1])
#            pass
#        return tuple([int(c) for c in ll])
#
#
#class P2Numbering(Numbering):
#    """Class for lower case roman numerals. E.g. (ii), (iv), (xx.3)"""
#    hint = "subparagraph"
#    labelPattern = re.compile("\([ivxlcdm]+(\.\d*)?\)")
#    def getTag(self):
#        return "p2"
#    @staticmethod
#    def divDataToTuple(s):
#        #p2 tuples are roman numerals, followed by a period and then numbers (each digit is a separate index)
#        ss = s.strip("_")
#        l = ss.split("_")
#        if len(l)<1 or len(l)>2:
#            raise Exception("P2 element with wrong number of elemens: %s"%s)
#        lout = []
#        lout.append(n2i[l[0].lower()])
#        if len(l)>1:
#            lout += [int(c) for c in list(l[1])]
#        return tuple(lout)
#    @staticmethod
#    def tupleToStr(t):
#        if len(t)<=1:
#            return "(%s)"%i2n[t[0]]
#        return "(%s.%s)"%(i2n[t[0]], "".join(str(c) for c in t[1:]))
#    @staticmethod
#    def labelToTuple(labelStr):
#        if labelStr[0] != "(" or labelStr[-1] != ")":
#            raise ParseException()
#        labelStr = labelStr[1:-1]
#        l = labelStr.split(".")
#        if len(l)>2:
#            raise ParseException("too many period separated parts in label")
#        ll = [ n2i[l[0]] ]
#        if len(l)>1:
#            ll += list(l[1])
#            pass
#        return tuple([int(c) for c in ll])
#
#
#class C1Numbering(Numbering):
#    """Class for capital letter numberings. E.g. (A), (C), (H.02)"""
#    hint = "clause"
#    labelPattern = re.compile("\([A-Z]{1,2}(\.\d*)?\)")    
#    def getTag(self):
#        return "c1"
#    @staticmethod
#    def divDataToTuple(s):
#        #c1 elements are capital letters, followed by period separated numbers
#        ss = s.strip("_")
#        l = ss.split("_")
#        if len(l)<1 or len(l)>2:
#            raise Exception("C1 element with wrong number of elemens: %s"%s)
#        lout = []
#        lout.append(a2i[l[0].lower()])
#        if len(l)>1:
#            lout += [int(c) for c in list(l[1])]
#        return tuple(lout)
#    @staticmethod
#    def tupleToStr(t):
#        if len(t)<=1:
#            return "(%s)"%i2a[t[0]].upper()
#        return "(%s.%s)"%(i2a[t[0]].upper(), "".join(str(c) for c in t[1:]))
#    @staticmethod
#    def labelToTuple(labelStr):
#        if labelStr[0] != "(" or labelStr[-1] != ")":
#            raise ParseException()
#        labelStr = labelStr[1:-1]
#        l = labelStr.split(".")
#        if len(l)>2:
#            raise ParseException("too many period separated parts in label")
#        ll = [ a2i[l[0].lower()] ]
#        if len(l)>1:
#            ll += list(l[1])
#            pass
#        return tuple([int(c) for c in ll])
#
##Xn numberings are added by me, and not reflected in the div tags
#class X1Numbering(Numbering):
#    """Formula for capital roman numerals. E.g. (II), (XI), (CVI.2)"""
#    hint = "subclause"
#    labelPattern = re.compile("\([IVXLCDM]+(\.\d*)?\)")    
#    def getTag(self):
#        return "X1"
#    @staticmethod
#    def divDataToTuple(s):
#        #X1 elements are capital roman numerals, followed by period separated numbers
#        raise ParseException("X1 cannot be derived from divData")
#        return ()
#    @staticmethod
#    def tupleToStr(t):
#        if len(t)<=1:
#            return "(%s)"%i2n[t[0]].upper()
#        return "(%s.%s)"%(i2n[t[0]].upper(), "".join(str(c) for c in t[1:]))
#    @staticmethod
#    def labelToTuple(labelStr):
#        if labelStr[0] != "(" or labelStr[-1] != ")":
#            raise ParseException()
#        labelStr = labelStr[1:-1]
#        l = labelStr.split(".")
#        if len(l)>2:
#            raise ParseException("too many period separated parts in label")
#        ll = [ n2i[l[0].lower()] ]
#        if len(l)>1:
#            ll += list(l[1])
#            pass
#        return tuple([int(c) for c in ll])
#
#class SSCNumbering(SENumbering):
#    """Class for sub-sub-clause numbering. Just like top level numbering, but at a higher level."""
#    maxLevel = 1000
#    minLevel = 5
#    hint = "subsubclause"
#    def getTag(self):
#        return "ssc"
#    pass
#
#class VRNumbering(Numbering):
#    """Class for formula variables. E.g. A, B, C.1"""
#    labelPattern = re.compile("[A-Z](\.\d*)?")    
#    def getTag(self):
#        return "vr"
#    @staticmethod
#    def divDataToTuple(s):
#        #VR elements are capital letters, followed by period separated numbers
#        raise ParseException("VR cannot be derived from divData")
#        return ()
#    @staticmethod
#    def tupleToStr(t):
#        if len(t)<=1:
#            return "%s" % (i2a[t[0]].upper(),)
#        return "%s.%s"%(i2a[t[0]].upper(), "".join(str(c) for c in t[1:]))
#    @staticmethod
#    def labelToTuple(labelStr):
#        l = labelStr.split(".")
#        if len(l)>2:
#            raise ParseException("too many period separated parts in label")
#        ll = [ a2i[l[0].lower()] ]
#        if len(l)>1:
#            ll += list(l[1])
#            pass
#        return tuple([int(c) for c in ll])
#    def penalty_ordering(self):
#        return 20
#    def penalty_contiguous(self):
#        return 20
#    def isFarFollower(self):
#        """Allow formula variables to appear at the same level of paragraphs, after a break.  As in reg 2401."""
#        return True
#    def isFormula(self):
#        """Return true because this numbering type is for the definition of variables."""
#        return True
#    def penalty_ignored(self):
#        """penalty for ignoring a potential numbering of this type"""
#        return 60
#    
#class DFNumbering(Numbering):
#    """Class for definition numbering. E.g. \"capital gains\""""
#    labelPattern = re.compile("(&#8220;(?!&#8220;)(?P<dterm1>.*?)&#8221;|" + "\"(?P<dterm2>.*?)\")")
#    hint = "definition"
#    def getTag(self):
#        return "df"
#    @staticmethod
#    def divDataToTuple(s):
#        #This function just fills in the empty tuple. The actual definition string needs to be filled
#        #later on a second pass (looking at the contents of the item)
#        return ()
#    @staticmethod
#    def tupleToStr(t):
#        if len(t) == 0:
#            return "( **DEFINITION TO BE FILLED IN** )"
#        return "(\""+t[0]+"\")"
#    @staticmethod
#    def labelToTuple(labelStr):
#        m = DFNumbering.labelPattern.match(labelStr)
#        if m.group("dterm1") != None:
#            return (m.group("dterm1"),)
#        elif m.group("dterm2") != None:
#            return (m.group("dterm2"),)
#        else:
#            raise ParseException("no defined term in definition: %s"%(labelStr,))
#    
#    def isInitial(self):
#        #any definition can be initial
#        return True
#    pass
#    def isNextAfter(self,n2):
#        if n2.getTag() != self.getTag():
#            return False
#        return self > n2
#
#    def __eq__(self,n2):
#        """tests for equality between numberings--- note that this does *not* agree with the ordering on SectionLabels
#        since numberings are only equal if they have the same type"""
#        if self.getTag() == n2.getTag() and self.getTuple()[0] == n2.getTuple()[0]:
#            return True
#        return False
#    
#    def __hash__(self):
#        return hash((self.getTag(),self.getTuple()))
#    
#    def __lt__(self,n2):
#        if not isinstance(n2,Numbering):
#            raise Exception("Can only compare Numbering to other Numberings: %s, %s"%(self.__repr__(),n2.__repr__()))
#        if self.getTag() != n2.getTag():
#            raise Exception("Cannot compare Numberings of different types: %s, %s"%(self.__repr__(),n2.__repr__()))
#        def1 = self.getTuple()[0].lower()
#        def2 = n2.getTuple()[0].lower()
#        
#        return (def2[0].isdigit() and not def1[0].isdigit()) or (def1 < def2) or (def1 == def2 and self.getTuple() < n2.getTuple())
#    
#    #__gt__ depends on __lt__, so is automatically handled
#    def penalty_ordering(self):
#        return 10
#    def penalty_contiguous(self):
#        return 1
#    def penalty_ignored(self):
#        """penalty for ignoring a potential numbering of this type"""
#        return 60
#
#class TerminalNumbering(Numbering):
#    """type of numbering that terminates a sectionlabel (inserted where there are various odd things in the div tag id field --- needed for compatability with old code)"""
#    def __init__(self,labelStr = None, divData = None, tuple = None):
#        self.tuple = ()
#        pass
#    
#    def getTag(self): #should never be needed for these numberings
#        return "XXX"
#    def getTuple(self):
#        return None
#    def isTerminator(self):
#        return True
#    @staticmethod
#    def divDataToTuple(s):
#        return None
#    @staticmethod
#    def tupleToStr(t):
#        return ""
#    @staticmethod
#    def labelToTuple(labelStr):
#        raise ParseException("Attempting to get labelToTuple for TerminalNumbering")
#    pass
#
#class NoteNumbering(Numbering):
#    """Class for Note numbering. These are just paragraphs that start with "NOTE:" and represent historical notes."""
#    maxLevel = 1
#    minLevel = 1
#    labelPattern = re.compile("NOTE:")
# 
#    def getTag(self):
#        return "nt"
#    def getTuple(self):
#        return ("NOTE:",)
#    @staticmethod
#    def divDataToTuple(s):
#        raise ParseException("Attempting to create NoteNumbering from divData: %s"%(s,))
#    @staticmethod
#    def tupleToStr(t):
#        return "NOTE:"
#    @staticmethod
#    def labelToTuple(labelStr):
#        return ("NOTE:",)
#    
#    def isInitial(self):
#        return True
#    def isFollower(self):
#        return True
#    def isNextAfter(self,n2):
#        if n2.getTag() != self.getTag():
#            return False
#        return self > n2   
#
#class RSENumbering(Numbering):
#    """Class for base section numbering. E.g. 5, 14.02, 1000A.2"""
#    hint = "section"
#    maxLevel = 0
#    labelPattern = re.compile("\d+[A-Z]?(\.\d*)?")
#    parsePat = re.compile("(?P<initialDigits>\d+)(?P<letter>[A-Z])?(\.(?P<finalDigits>\d+))?")
#    def getTag(self):
#        return "rse"
#    @staticmethod
#    def divDataToTuple(s):
#        #se elements are numbers, separated by periods (at most 2 numbers), numbers after the period are individual digits
#        ss = s.strip("_")
#        l = ss.split("_")
#        if len(l)<1 or len(l)>2:
#            raise Exception("SE element with wrong number of elemens: %s"%s)
#        lout = []
#        lout.append(int(l[0]))
#        if len(l)>1:
#            lout += [int(c) for c in list(l[1])]
#        return tuple(lout)
#    @staticmethod
#    def tupleToStr(t):
#        s = "%s%s"%(str(t[0][0]),"".join(i2a[c].upper() for c in t[0][1:]))
#        if len(t)>1:
#            s += ".%s" % "".join(str(c) for c in t[1])
#            pass
#        return s
#    @staticmethod
#    def labelToTuple(labelStr):
#        m = RSENumbering.parsePat.match(labelStr)
#        if m is None:
#            raise Exception("Not an RSE numbering")
#        l = []
#        l1 = []
#        l1.append(int(m.group("initialDigits")))
#        if m.group("letter") is not None:
#            l1.append(a2i[m.group("letter").lower()])
#            pass
#        l.append(tuple(l1))
#        if m.group("finalDigits") is not None:
#            l2 = [int(c) for c in list(m.group("finalDigits"))]
#            l.append(tuple(l2))
#            pass
#        return tuple(l)
#
#    def isNextAfter(self,n2):
#        if self.getTag() != n2.getTag():
#            return False
#        if len(self.tuple) < 1 or len(n2.getTuple()) < 1:
#            return False
#        if n2 > self:
#            return False
#        elif (len(self.tuple) == 1) and (len(self.tuple[0]) == 1) and (self.tuple[0][0] % 100 == 0):
#            return True #a multiple of 100 can always be initial
#        elif self.tuple[0][0] == n2.getTuple()[0][0] + 1:
#            return True
#        elif self.tuple[0][0] == n2.getTuple()[0][0]:
#            return self > n2
#        else:
#            return False
#    
#    def isInitial(self):
#        if len(self.tuple) == 1 and len(self.tuple[0]) == 1 and self.tuple[0][0] == 1:
#            return True
#        return False
#
#class RSSNumbering(Numbering):
#    """Class for regulation subsection numbering. E.g (3), (7a.2), (8.03), 12ab"""
#    hint = "subsection"
#    labelPattern = re.compile("\(\d+([a-z]*)(\.\d*)?\)")
#    parsePat = re.compile("\((?P<initialDigits>\d+)(?P<letters>[a-z]*)(\.(?P<finalDigits>\d*))?\)")
#    def getTag(self):
#        return "rss"
#    @staticmethod
#    def divDataToTuple(s):
#        pass
#    @staticmethod
#    def tupleToStr(t):
#        s = "(%s%s"%(t[0][0], "".join(i2a[c] for c in t[0][1:]))
#        if (len(t)>1):
#            s += ".%s)"%("".join(str(c) for c in t[1:]))
#            pass
#        else:
#            s += ")"
#        return s
#    @staticmethod
#    def labelToTuple(labelStr):
#        m = RSSNumbering.parsePat.match(labelStr)
#        if m is None:
#            raise Exception("Not a regulation subsection")
#        l1 = []
#        l1.append(int(m.group("initialDigits")))
#        if m.group("letters") is not None:
#            l1 += [a2i[letter] for letter in list(m.group("letters"))]
#            pass
#        l2 = [tuple(l1)]
#        if m.group("finalDigits") is not None:
#            l2 += [int(digit) for digit in list(m.group("finalDigits"))]
#            pass
#        return tuple(l2)
#    
#    def isNextAfter(self,n2):
#        if self.getTag() != n2.getTag():
#            return False
#        if len(self.tuple) < 1 or len(n2.getTuple()) < 1:
#            return False
#        if self.tuple[0][0] == n2.getTuple()[0][0] + 1:
#            return True
#        if self.tuple[0][0] % 100 == 0:  #section labels in the regulations can jump to multiples of 100
#            return True
#        elif self.tuple[0][0] == n2.getTuple()[0][0]:
#            return self > n2
#        else:
#            return False
#    
#    def isInitial(self):
#        if len(self.tuple) == 1 and len(self.tuple[0]) == 1 and self.tuple[0][0] == 1:
#            return True
#        return False
#
#class RP1Numbering(Numbering):
#    """Class for lower case letter numbering used in regulations. E.g. (a), (ab), (d), (h.02), (e.1a)"""
#    hint = "paragraph"
#    labelPattern = re.compile("\([a-z]{1,3}(\.\d+([a-z]+)?)?\)")
#    parsePat = re.compile("\((?P<initialLetters>[a-z]{1,3})(\.(?P<digits>\d+)(?P<finalLetters>[a-z]+)?)?\)")
#    def getTag(self):
#        return "rp1"
#    @staticmethod
#    def divDataToTuple(s):
#        #p1 elemenets are letter, followed by a period and then numbers (each digit is a separate index)
#        ss = s.strip("_")
#        l = ss.split("_")
#        if len(l)<1 or len(l)>2:
#            raise Exception("P1 element with wrong number of elemens: %s"%s)
#        lout = []
#        lout.append(a2i[l[0].lower()])
#        if len(l)>1:
#            lout += [int(c) for c in list(l[1])]
#        return tuple(lout)
#    @staticmethod
#    def tupleToStr(t):
#        s = "(%s" % "".join(i2a[c] for c in t[0])
#        if len(t) > 1:
#            s += ".%s"% "".join(str(c) for c in t[1])
#        if len(t) > 2:
#            s += "%s)"%("".join(i2a[c] for c in t[2]))
#            pass
#        else:
#            s += ")"
#        return s
#    @staticmethod
#    def labelToTuple(labelStr):
#        m = RP1Numbering.parsePat.match(labelStr)
#        if m is None:
#            raise Exception("Not a regulation RP1")
#            pass
#        l = []
#        l1 = [a2i[c] for c in list(m.group("initialLetters"))]
#        l.append(tuple(l1))
#        if m.group("digits") is not None:
#            l2 = [int(c) for c in list(m.group("digits"))]
#            l.append(tuple(l2))
#            pass
#        if m.group("finalLetters") is not None:
#            l3 = [a2i[c] for c in list(m.group("finalLetters"))]
#            l.append(tuple(l3))
#            pass
#        return tuple(l)
#    
#    def isNextAfter(self,n2):
#        if self.getTag() != n2.getTag():
#            return False
#        if len(self.tuple) < 1 or len(n2.getTuple()) < 1:
#            return False
#        if self < n2:
#            return False
#        if self.tuple[0] == n2.getTuple()[0]:
#            return True
#        pairs = zip(self.tuple[0],n2.getTuple()[0])
#        for x,y in pairs:
#            if x != y:
#                if x == y + 1:
#                    return True
#                else:
#                    return False
#                pass
#            pass
#        #at this point, initial tuples match up to the minimum length. they are not equal, so they are different lengths
#        if len(self.tuple[0])<len(n2.getTuple()[0]):
#            return False
#        if self.tuple[0][len(n2.getTuple()[0])] == 1:
#            return True
#        else:
#            return False
#    def isInitial(self):
#        if len(self.tuple) == 1 and len(self.tuple[0]) == 1 and self.tuple[0][0] == 1:
#            return True
#        return False
#
##numberings to use for statutes
#numberingTypes = [SENumbering, SSNumbering, P1Numbering, P2Numbering, C1Numbering, SSCNumbering, DFNumbering,X1Numbering,VRNumbering,NoteNumbering]
#
##numberings to use for regulations
#regulationNumberingTypes = [RSENumbering,RSSNumbering, RP1Numbering,P2Numbering,C1Numbering, SSCNumbering,X1Numbering,DFNumbering,VRNumbering,NoteNumbering]
#
#def makeValidNumberings(labelStr = None, piece = None,nTypes=numberingTypes):
#    valid = []
#    if labelStr == None:
#        if piece == None:
#            raise Exception("Attempting to makeValidNumberings without a string or piece")
#        labelStr = piece.getLeadingStr()
#        if labelStr == None:
#            return []
#        pass
#    for numberingType in nTypes:
#        try:
#            n = numberingType(labelStr)
#            valid.append(n)
#        except ParseException:
#            pass
#        pass
#    return valid


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
    """class for storing data regarding divisions, including which a dictionary linking sectionlabels to divisions, and a dictionary of division titles."""
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
