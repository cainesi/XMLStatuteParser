#$Id :$

"""Module for provides functions for processing statute language (e.g., the applicability provisions of statutes, definitions, cross-references)."""

"""How this will work
1) TextParse handles the contents of TextItem blocks --- should we just add this to the TextItem class?  Maybe the parameter it receives should be a TextItem object (so that it has location and statute information?
2) Will have low level methods for doing various sorts of matches, and a few high-level methods that perform collections of matches [and return appropriate  (unevaluated) Decorator objects]
3) Subsequent pass will be needed over all the decorators to "link" them appropriately (assign them to appropriate target instruments, verify that the cited locations in fact exist).
"""

import re
from ErrorReporter import showError

labelPat = re.compile("(" + "(\d+([a-zA-Z])?(\.\d*)?)(\([^\) ]{1,10}\))*" + "|" + "(\([^\) ]{1,10}\))+" + ")")
connectorPat = re.compile("(?P<connector>to|and|,)")
sectionNamePat = re.compile("(?P<type>section|subsection|paragraph|clause|subclause)s?")

class Fragment(object):
    """class representing a fragment of text, along with it's position in the parent text block."""
    def __init__(self,text,position):
        self.text = text
        self.position = position
        return
    def getText(self): return self.text
    def getPosition(self): return self.position
    def __len__(self): return len(self.text)


class TextParse(object):
    def __init__(self, text):
        self.text = text
        self.ltext= text.lower()
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
    def recordMatch(self,matchType,text):
        if matchType not in self.matches: self.matches[matchType] = []
        self.matches[matchType].append(text)
        return
    def getMatches(self, matchType):
        return self.matches[matchType]

    def eatSpace(self):
        """Advance pointer to the first non-space."""
        while self.ptr < len(self.text) and self.text[self.ptr].isspace(): self.ptr += 1
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
        """Eats and returns one label (e.g., "12(6)(a)")"""
        labm = labelPat.match(self.text[self.ptr:])
        if labm is None: return None
        label = self.text[self.ptr:self.ptr + labm.end()] #get corresponding text from the non-lower text, since capitalization is important
        self.ptr += labm.end()
        self.eatSpace()
        return label

    def eatLabelSeries(self):
        """Eats a series of labels (e.g., "section 4, 2 and 7")"""
        return


if __name__ == "__main__":
    #various tests for patern matching
    s = "12(14)(a)"
    print("[["+s+"]]")
    t = TextParse(s)
    print(t.eatLabel())
    s ="Subsection 4.1"
    print("[["+s+"]]")
    t = TextParse(s)
    print(t.eatLabelType())
    print(t.eatLabel())
    pass