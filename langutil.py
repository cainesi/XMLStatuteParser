#$Id :$

"""Module for provides functions for processing statute language (e.g., the applicability provisions of statutes, definitions, cross-references)."""

"""How this will work
1) TextParse handles the contents of TextItem blocks --- should we just add this to the TextItem class?  Maybe the parameter it receives should be a TextItem object (so that it has location and statute information?
2) Will have low level methods for doing various sorts of matches, and a few high-level methods that perform collections of matches [and return appropriate  (unevaluated) Decorator objects]
3) Subsequent pass will be needed over all the decorators to "link" them appropriately (assign them to appropriate target instruments, verify that the cited locations in fact exist).
"""

import re
from ErrorReporter import showError
import SectionLabelLib

labelPat = re.compile("(" + "(\d+([a-zA-Z])?(\.\d+)?)(\([^\) ]{1,10}\))*" + "|" + "(\([^\) ]{1,10}\))+" + ")")
connectorPat = re.compile("(?P<connector>to|and( in)?|,)")
sectionNamePat = re.compile("(?P<type>section|subsection|paragraph|clause|subclause)s?")

class Fragment(object):
    """class representing a fragment of text, along with it's position in the parent text block."""
    def __init__(self,text,position,toConnected=False):
        """Fragment represents a fragment from a larger string.
        text is the extract represented,
        position is the index at which it appears in larger string,
        toConnected indicates whether fragment is connected to prior one by a "to" connection (useful in determining applicability ranges
        """
        self.text = text
        self.position = position
        self.toConnected = toConnected
        return
    def getText(self): return self.text
    def getPosition(self): return self.position
    def getStart(self): return self.getPosition() #return start of string in main text
    def getEnd(self): return self.getPosition + len(self) #return end of string in main text
    def setToConnected(self,toConnected): self.toConnected = toConnected; return
    def isToConnected(self): return self.toConnected #indicates whether fragment is linked to prior one by a "to"
    def __len__(self): return len(self.text)
    def __str__(self): return self.getText()

class TextParse(object):
    def __init__(self, decoratedText):
        """Superclass for all the parsing classes. Implements the basic parsing steps which are relied on in subclasses.  One parameter, text, is the text to be handled by the parser.
        :type decoratedText: DecoratedText.DecoratedText
        """
        self.decoratedText=decoratedText
        self.text = decoratedText.getText()
        self.ltext= self.text.lower()
        self.ptr = 0
        self.matches = {} #dictionary of stored matches of the various types
        self.ptrStack = []
        self.eatSpace() #there should never be leading space on the text
        return

    def saveState(self):
        """Save the state of the pointer, so we can restore to this point if desired."""
        self.ptrStack.append(self.ptr)
        return
    def restoreState(self):
        """Restore the ptr state to what it was at the corresponding previous save."""
        self.ptr = self.ptrStack.pop()
        return
    def discardState(self):
        """Discard the top saved state (so a subsequent restore we restore to the one before)."""
        self.ptrStack.pop()
        return
    def recordMatch(self,matchType,item):
        """Record the item for of a given matchType.  Program needs to remember what is stored for each matchType (locaction, match object, etc)"""
        if matchType not in self.matches: self.matches[matchType] = []
        self.matches[matchType].append(item)
        return
    def getMatches(self, matchType):
        return self.matches[matchType]
    def eatSpace(self):
        """Advance pointer to the first non-space."""
        while self.ptr < len(self.text) and self.text[self.ptr].isspace(): self.ptr += 1
        return
    def eatParentheticals(self):
        """Eat space and any parentheticals"""
        self.eatSpace()
        if self.text[self.ptr] != "(": return
        pcount = 0
        spaceCount = 0
        foundEnd = False
        for n in xrange(self.ptr,len(self.text)):
            if self.text[n] == "(": pcount += 1
            elif self.text[n] == ")": pcount -= 1
            if pcount == 0: foundEnd == True; break
            if self.text[n].isspace(): spaceCount += 1
            pass
        #return if we never found end, or if parentheses contained no space.
        if not foundEnd: return
        if spaceCount == 0: return
        #else update pointer to point after end of parentheses
        self.ptr = n + 1
        self.eatSpace()
        return
    def eatConnector(self):
        con = connectorPat.match(self.ltext[self.ptr:])
        if con is None: return None
        self.ptr += con.end()
        self.eatSpace()
        return con.group("connector")
    def eatLabelType(self):
        """Eats the string describing a type of label (section, subsection, etc)."""
        namem = sectionNamePat.match(self.ltext[self.ptr:])
        if namem is None: return None
        self.ptr += namem.end()
        self.eatSpace()
        return namem.group("type")
    def eatLabel(self):
        """Eats and returns one label (e.g., "12(6)(a)")
        @rtype: Fragment
        """
        labm = labelPat.match(self.text[self.ptr:])
        if labm is None: return None
        label = self.text[self.ptr:self.ptr + labm.end()] #get corresponding text from the non-lower text, since capitalization is important
        frag = Fragment(text=label,position=self.ptr)
        self.ptr += labm.end()
        self.eatSpace()
        return frag
    def eatConnectorAndLabel(self):
        """Eats a connector and a label, if possible, returns the Fragment object for the label.
        @rtype: Fragment
        """
        self.saveState()
        con = self.eatConnector()
        if con is None: self.restoreState(); return None
        frag = self.eatLabel()
        if frag is None: self.restoreState(); return None
        self.discardState()
        self.eatSpace()
        if con == "to": frag.setToConnected(True)
        return frag
    def eatLabelSeries(self):
        """Eats a series of labels (e.g., "section 4, 2 and 7")
        @rtype: list of Fragment
        """
        labelList = []
        self.saveState()
        ty = self.eatLabelType()
        if ty is None: self.restoreState(); return None
        frag = self.eatLabel()
        if frag is None: self.restoreState(); return None
        while frag is not None:
            labelList.append(frag)
            frag = self.eatConnectorAndLabel()
            pass
        return labelList
    def eatMultipleSeries(self):
        """Eats a series of label series (e.g., "sections 4, and 7 and paragraph 3(b)
        @rtype: list of Fragment
        """
        l = self.eatLabelSeries()
        if l is None: return None
        labelList = []
        while l is not None:
            labelList += l
            l = self.eatLabelSeries()
            pass
        return labelList
    def addDecorators(self):
        """Adds required decorators to the underlying DecoratedText object."""
        return

class ApplicationParse(TextParse):
    """Parser that automatically eats the text to determine the applicability range."""
    initialPat = re.compile("^in|apply in|^for the purposes of|apply for the purposes of")
    thisPat = re.compile("this (?P<thisType>[a-z]+)")
    def __init__(self, decoratedText):
        TextParse.__init__(self,decoratedText)
        self.thisList = [] #list of areas that are referred to as "this", such as "this section" or "this part"
        self.sectionList = []
        self.eatStart()
        #repeatedly eat labelSeries and this's, with connectors in between, until we have no more matches
        self.eatApplicationRange()
        return
    def eatStart(self):
        """Finds the spot in the text that corresponds to the start of the applicability range."""
        m = ApplicationParse.initialPat.search(self.ltext)
        if m is None: return None
        self.ptr=m.end()
        self.eatSpace()
        return m.group(0)
    def eatThis(self):
        """Eats the word "this" and the type of item "this" is referring to (section, division, etc.)"""
        m = ApplicationParse.thisPat.match(self.ltext[self.ptr:])
        if m is None: return None
        self.ptr += m.end()
        self.eatSpace()
        return Fragment(m.group("thisType"),self.ptr+5)
    def eatApplicationRange(self):
        """Eats a series of "this" references and section label lists. Returns a tuple (list of section label fragments, list of this type fragments)"""
        while True:
            l = self.eatLabelSeries()
            if l is not None: self.sectionList += l
            else: #look for a this block
                thisFrag = self.eatThis()
                if thisFrag is None: showError("Could not find label list or this in expected spot in application language.",location=self.decoratedText); break
                else: self.thisList.append(thisFrag)
            con = self.eatConnector()
            if con is None: break
        return
    def showParseData(self):
        print(",".join(str(c) for c in self.sectionList))
        print(",".join(str(c) for c in self.thisList))
        return
    def getSectionLabelCollection(self):
        """Returns the SectionLabelCollection object describing the applicability range described in the text."""
        return



def doTests():
    import DecoratedText
    import Statute
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text="12.3(14)(a)")
    t = TextParse(s)
    lab = t.eatLabel()
    if lab != s: print "Error 1: [" + s.getText() + "] [" + str(lab) + "]"
    s =DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text="Subsection 4.1")
    t = TextParse(s)
    labt = t.eatLabelType()
    lab = t.eatLabel()
    if labt != "subsection": print "Error 2: [" + s.getText() + "] [" + str(labt) + "]"
    if lab != "4.1": print "Error 3: [" + s.getText() + "] [" + str(lab) + "]"
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text="The following definitions apply in this section and in subsection 47(3), paragraphs 53(1)(j) and 110(1)(d) and (d.01), this Part and subsections 110(1.1), (1.2), (1.5), (1.6) and (2.1).")
    t = ApplicationParse(s)
    t.showParseData()
    return

if __name__ == "__main__":
    #various tests for pattern matching
    doTests()