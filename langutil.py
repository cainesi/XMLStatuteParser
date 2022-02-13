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

"""Module for provides functions for processing statute language (e.g., the applicability provisions of statutes, definitions, cross-references).

How this will work
1) TextParse handles the contents of TextItem blocks --- should we just add this to the TextItem class?  Maybe the parameter it receives should be a TextItem object (so that it has location and statute information?
2) Will have low level methods for doing various sorts of matches, and a few high-level methods that perform collections of matches [and return appropriate  (unevaluated) Decorator objects]
3) Subsequent pass will be needed over all the decorators to "link" them appropriately (assign them to appropriate target instruments, verify that the cited locations in fact exist).
"""

import re
from ErrorReporter import showError
import SectionLabelLib
import DecoratedText

class LangUtilException(Exception): pass

#TODO: make it consistent whether the eating methods should eat initial space or leave no initial space on the string

labelPat = re.compile("(" + "(\d+([a-zA-Z])?(\.\d+)?)(\([^\) ]{1,10}\))*" + "|" + "(\([^\) ]{1,10}\))+" + ")")
connectorPat = re.compile("(?P<connector>to|and( in)?|or|,)")
sectionNamePat = re.compile("(?P<type>section|subsection|paragraph|clause|subclause)s?")
wordPat = re.compile(" *(?P<word>[-a-zA-Z]+)\s*")
punctuationPat = re.compile("(?P<punctuation>\.|,)\s*")
quotePat = re.compile(" *\"(?P<phrase>[^\"]*)\"")

class Fragment(object):
    """class representing a fragment of text, along with it's position in the parent text block."""
    def __init__(self,text,position,toConnected=False,seriesStart=False):
        """Fragment represents a fragment from a larger string.
        text is the extract represented,
        position is the index at which it appears in larger string,
        toConnected indicates whether fragment is connected to prior one by a "to" connection (useful in determining applicability ranges
        """
        self.text = text
        self.position = position
        self.toConnected = toConnected #is True if this Fragment is connection to prior Fragment by a "to" (important to know when calculating applicability ranges)
        self.seriesStart = seriesStart #is True if this is the first Fragment in a series of labels (important to know when determining which section is referred to.
        self.targetSL = None
        self.pinpoint = None
        return
    def getText(self): return self.text
    def getPosition(self): return self.position
    def getStart(self): return self.getPosition() #return start of string in main text
    def getEnd(self): return self.getPosition() + len(self) #return end of string in main text
    def setToConnected(self,toConnected=True): self.toConnected = toConnected; return
    def setSeriesStart(self,seriesStart=True): self.seriesStart = seriesStart; return
    def setPinpoint(self, pinpoint):
        """
        @type pinpoint: SectionLabelLib.Pinpoint
        """
        self.pinpoint = pinpoint
        return
    def getPinpoint(self):
        """
        @rtype: SectionLabelLib.Pinpoint
        """
        return self.pinpoint
    def hasPinpoint(self):
        """
        @rtype: bool
        """
        if self.pinpoint is None: return False
        return True
    def setTargetSL(self, sL): self.targetSL = sL
    def getTargetSL(self):
        """
        @rtype:SectionLabelLib.SectionLabel
        """
        return self.targetSL
    def hasTargetSL(self):
        if self.targetSL is None: return False
        return True
    def isToConnected(self): return self.toConnected #indicates whether fragment is linked to prior one by a "to"
    def isSeriesStart(self):
        """@rtype: bool"""
        return self.seriesStart
    def __len__(self): return len(self.text)
    def __str__(self):
        if self.isToConnected(): return self.getText() + "<+t>"
        return self.getText()

class LabelLocation(object):
    """Class for encapsulating information about where a label points to (locally within the current act, another act, regulations, within a definition."""
    def __init__(self,local=False, actName=None,definition=None,definitionSectionFragment=None,softLocal=False):
        """
        Object can be initialized in three ways: by specifying that reference is local, by giving the name of Act pointed to, or by giving the definition that is being referred to
        @type local: bool
        @type softLocal: bool
        @type actName: str
        @type definition: str
        @type definitionSectionFragment: Fragment
        """
        self.local=False
        self.silent= softLocal #if self.silent = True, indicates that the location was not explicitly stated, so is assumed local
        self.actName = None
        self.definition=None
        self.definitionSectionFragment=None
        if local == True: self.local = True
        elif actName is not None: self.actName = actName
        else:
            if (definition is None) : raise LangUtilException("LabelLocation must specify one of local, actName or definition (in which case definitionSectionFragment is optional).")
            self.definition=definition; self.definitionSectionFragment=definitionSectionFragment
            pass
        return
    def __str__(self):
        if self.local: return "LOCAL"
        elif self.actName is not None: return self.actName
        else: return "\"" + self.definition + "\" in " + self.definitionSectionFragment.getText()
    def isDefinitionRef(self):
        if self.definition is not None: return True
        return False
    def isSilent(self):
        return self.silent
    def isLocal(self): return self.local
    def isActRef(self):
        if self.actName is not None: return True
        return False
    def getActName(self): return self.actName
    def getDefinition(self): return self.definition
    def getDefinitionSectionFragment(self): return self.definitionSectionFragment

#TODO: audit the code to make sure the saveState and discard/restoreState calls are balanced.

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
        self.stateCount=0 #counts the number of states that have been saved
        return
    def __len__(self):
        return len(self.text)

    def getDecoratedText(self):
        """
        Returns the DecoratedText that this parser is working on.
        @return:
        @rtype: DecoratedText.DecoratedText
        """
        return self.decoratedText

    def saveState(self):
        """Save the state of the pointer, so we can restore to this point if desired. """
        level = len(self.ptrStack)
        ptr = self.ptr
        self.stateCount += 1
        number = self.stateCount
        state = (ptr,number,level)
        self.ptrStack.append(state)
        return state
    def restoreState(self,state=None):
        """Restore the ptr state to what it was at the corresponding previous save."""
        if state is None:
            self.ptr = self.ptrStack.pop()[0]
            return
        ptr, number, level = state
        if level > len(self.ptrStack):
            raise LangUtilException("Attempt to restore state that no longer exists.")
        if self.ptrStack[level][1] != number:
            raise LangUtilException("Attempt to restore state that has been replaced.")
        self.ptr = self.ptrStack[level][0]
        self.ptrStack = self.ptrStack[:level]
        return
    def discardState(self,state=None):
        """Discard the top saved state, or the specified state and any sub-states (so a subsequent restore we restore to the one before)."""
        if state is None:
            self.ptrStack.pop()
            return
        ptr, number, level = state
        if level > len(self.ptrStack):
            raise LangUtilException("Attempt to restore state that no longer exists.")
        if self.ptrStack[level][1] != number:
            raise LangUtilException("Attempt to restore state that has been replaced.")
        self.ptrStack = self.ptrStack[:level]
        return

    def recordMatch(self,matchType,item):
        """Record the item for of a given matchType.  Program needs to remember what is stored for each matchType (locaction, match object, etc)"""
        if matchType not in self.matches: self.matches[matchType] = []
        self.matches[matchType].append(item)
        return
    def getMatches(self, matchType):
        return self.matches[matchType]
    ###
    #
    # Methods to manipulate underlying DecoratedText
    #
    ###
    def addLinkDecorator(self, fragment):
        """Adds required decorators to the underlying DecoratedText object.
        @type: fragment: Fragment"""
        self.decoratedText.addDecorator(DecoratedText.LinkDecorator(parent=self.decoratedText,start=fragment.getStart(),end=fragment.getEnd(),pinpoint=fragment.getPinpoint()))
        return
    ###
    #
    # Functions to parse/eat parts of text
    #
    ###
    def atEnd(self):
        """Returns True if ptr is at end of string.
        @rtype: bool
        """
        if self.ptr == len(self.text): return True
        return False
    def eatSpace(self):
        """Advance pointer to the first non-space.
        @rtype: None
        """
        while self.ptr < len(self.text) and self.text[self.ptr].isspace(): self.ptr += 1
        return
    def eatWord(self):
        """Eats and returns one word, and advances pointer to end of space following word.
        @rtype: str
        """
        m = wordPat.match(self.text,self.ptr)
        if m is None: return None
        self.ptr = m.end()
        return m.group("word")
    def eatPunctation(self):
        """Eats a punction mark (one of "." and ",") and returns it, or None if no punctuation at current position.
        @rtype: str
        """
        m = punctuationPat.match(self.text,self.ptr)
        if m is None: return None
        self.ptr = m.end()
        return m.group("punctuation")
    def eatParenthetical(self):
        """Eat space and any parentheticals"""
        n = 0
        self.eatSpace()
        if self.text[self.ptr] != "(": return
        pcount = 0
        spaceCount = 0
        foundEnd = False
        for n in xrange(self.ptr,len(self.text)):
            if self.text[n] == "(": pcount += 1
            elif self.text[n] == ")": pcount -= 1
            if pcount == 0: foundEnd = True; break
            if self.text[n].isspace(): spaceCount += 1
            pass
        #return if we never found end, or if parentheses contained no space, then this is not something we can eat.
        if not foundEnd: return
        if spaceCount == 0: return
        #else update pointer to point after end of parentheses
        self.ptr = n + 1
        self.eatSpace()
        return
    def eatConnector(self):
        """Eats and returns a connector (connector may not be at end of string).
        @rtype: str
        """
        con = connectorPat.match(self.ltext, self.ptr)
        if con is None: return None
        if con.end() == len(self): return None
        self.ptr = con.end()
        self.eatSpace()
        return con.group("connector")
    def eatLabelType(self):
        """Eats the string describing a type of label (section, subsection, etc)."""
        namem = sectionNamePat.match(self.ltext[self.ptr:])
        if namem is None: return None
        self.ptr += namem.end()
        self.eatSpace()
        return namem.group("type")

    def n_eatLabelType(self):
        """Eats the string describing a type of label (section, subsection, etc). [new version]
        @rtype: Fragment
        """
        namem = sectionNamePat.match(self.ltext[self.ptr:])
        if namem is None: return None
        oldPtr = self.ptr
        self.ptr += namem.end()
        self.eatSpace()
        return Fragment(text=namem.group("type"),position=oldPtr)

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
        self.eatSpace()
        frag = self.eatLabel()
        if frag is None: self.restoreState(); return None
        self.discardState()
        self.eatSpace()
        if con == "to": frag.setToConnected(True)
        return frag

    def eatQuoteText(self):
        """Eats passage of text surrounded by quotes.
        @rtype: Fragment
        """
        m = quotePat.match(self.ltext,self.ptr)
        if m is None: return None #if not a quote passage, return None
        self.ptr = m.end() #otherwise advance ptr and return the quoted passage
        self.eatSpace()
        return Fragment(text=m.group("phrase"),position=m.start("phrase"))

    variableHeaderPat = re.compile(" *(the descriptions? of|the values? of|determined for)")
    variablePat = re.compile(" *(?P<variable>[A-Z](\.\d+)?)")
    def eatVariable(self):
        """
        @rtype: Fragment
        """
        m = TextParse.variablePat.match(self.text, self.ptr)
        if m is None:
            return None
        varFrag = Fragment(text=m.group("variable"),position=self.ptr)
        self.ptr = m.end()
        self.eatSpace()
        return varFrag

    def eatVariableList(self):
        """Eats a sequence of variables, and returns list of corresponding Fragments.
        @rtype: list of Fragment
        """
        self.saveState() #first block eats header for list of variables and initial variable
        m = TextParse.variableHeaderPat.match(self.ltext, self.ptr)
        if m is None:
            self.restoreState()
            return None
        self.ptr = m.end()
        self.eatSpace()
        vlist = []
        variable = self.eatVariable()
        if variable is None:
            self.restoreState()
            return None
        vlist.append(variable)
        self.discardState()

        self.saveState() #second block eats any additional variables
        con = self.eatConnector()
        variable = self.eatVariable()
        while (con is not None) and (variable is not None):
            vlist.append(variable)
            self.discardState()
            self.saveState()
            con = self.eatConnector()
            variable = self.eatVariable()
            pass
        self.restoreState() #restore state to before the last attempt to eat connector and variable (which failed)
        return vlist


    def eatDefinitionAndSection(self):
        """Eat text of the form ["defined term" in subsection 248(1)].
        @rtype: LabelLocation
        """
        #eat defined term
        self.saveState()
        m = quotePat.match(self.ltext,self.ptr)
        if m is None: self.restoreState(); return None
        defTerm = m.group("phrase")
        self.ptr = m.end()
        self.discardState() #can discard state, because we will definitely use the quotes passage

        #eat section reference, if any
        self.saveState()
        nextWord = self.eatWord()
        if nextWord != "in": self.restoreState(); return LabelLocation(definition=defTerm,definitionSectionFragment=None)
        t = self.eatLabelType()
        if t is None: self.restoreState(); return LabelLocation(definition=defTerm, definitionSectionFragment=None)
        labString = self.eatLabel()
        if labString is None: self.restoreState(); return LabelLocation(definition=defTerm,definitionSectionFragment=None)
        self.discardState()
        return LabelLocation(definition=defTerm, definitionSectionFragment=labString)


    rscPat = re.compile(", chapter (?P<chapter>\d+) of the Revised Statutes of Canada, (?P<year>\d+)")
    def eatChapterAndYear(self):
        """Eats the text of a reference to a chapter of the RSC, as in ", chapter 148 of the Revised Statutes of Canada, 1952"
        @rtype: str
        """
        self.saveState()
        m = TextParse.rscPat.match(self.text, self.ptr)
        if m is None: self.restoreState(); return None
        self.ptr = m.end()
        self.discardState()
        return m.group(0)

    def eatActLocation(self):
        """
        Attempts to eat a description of the location that the sections are drawn from, such as from the list below:
            of this Act
            of that Act
            of the Income Tax Act, chapter 148 of the Revised Statutes of Canada, 1952
            of the Excise Tax Act
            of the Foreign Publishers Advertising Services Act
            of the Bank Act
        If one can be found, it is returned without the leading "of" (and the leading "the", if present), otherwise returns None (i.e., "local" --- "this Act" also causes this to be the return).  Detection of the name is highly heurisical.
        @rtype: LabelLocation
        """
        self.saveState()
        #check for word "of", if not present there's nothing
        nextWord = self.eatWord()
        if nextWord != "of": self.restoreState(); return LabelLocation(local=True, softLocal=True)
        nextWord = self.eatWord()
        if nextWord == "this":
            nextWord = self.eatWord()
            if nextWord == "Act": self.discardState(); return LabelLocation(local=True)
            #TODO: what is used in place of "this Act" in the regulations?
            elif nextWord in ("section","subsection","paragraph","subparagraph"): self.discardState(); return LabelLocation(local=True)
            else: showError("Unknown \"of\" type: this " + nextWord, location = self.decoratedText); self.restoreState(); return LabelLocation(local=True)
        elif nextWord == "that":
            nextWord = self.eatWord()
            if nextWord == "Act": self.discardState(); return LabelLocation(actName="that Act")
            else: showError("Unknown \"of\" type: that " + nextWord, location = self.decoratedText); self.restoreState(); return LabelLocation(local=True)
        elif nextWord != "the":
            showError("Unknown \"of\" type: " + nextWord, location = self.decoratedText)
            self.restoreState(); return LabelLocation(local=True)
            pass
        #At this point, we have found the text "of the"
        nextWord = self.eatWord()
        #handle the case of definition reference
        if nextWord == "definition":
            lloc = self.eatDefinitionAndSection()  #if we find a def & section, return the LabelLocation, otherwise parse it in off chance that it's an act name or seomething
            if lloc is not None: self.discardState(); return lloc
            pass

        actWords = []
        #special cases for references to the "Act" or the "Regulations"
        if nextWord == "Act": self.discardState(); return LabelLocation(actName="Act")
        elif nextWord == "Regulations": self.discardState(); return LabelLocation(actName="Regulations")
        while nextWord is not None:
            actWords.append(nextWord)
            if nextWord == "Act" or nextWord == "Regulations":
                actStr = " ".join(actWords)
                chapStr = self.eatChapterAndYear()
                if chapStr is not None: actStr += chapStr
                self.discardState()
                return LabelLocation(actName=actStr)
            nextWord = self.eatWord()
            pass

        #TODO: add code to handle "Income Tax Application Rules" (and maybe other names ending in "Rules"?)
        #TODO: add code to handle references to "Income Tax Act, chapter 148 of the Revised Statutes of Canada, 1952"
        #TODO: references of the "paragraphs (f) and (h) of the description of B in that definition"
        #TODO: paragraphs (a) to (d), (f) and (g) of the definition "qualified investment" in section 204
        showError("Unknown \"of\" type: no closing \"Act\": " + str(actWords), location = self.decoratedText)
        self.restoreState()
        return LabelLocation(local=True)

    def n_eatActLocation(self):
        """
        Attempts to eat a description of the location that the sections are drawn from, such as from the list below:
            of this Act
            of that Act
            of the Income Tax Act, chapter 148 of the Revised Statutes of Canada, 1952
            of the Excise Tax Act
            of the Foreign Publishers Advertising Services Act
            of the Bank Act
        If one can be found, it is returned without the leading "of" (and the leading "the", if present), otherwise returns None (i.e., "local" --- "this Act" also causes this to be the return).  Detection of the name is highly heurisical.
        @rtype: Fragment
        """
        #TODO - return a more sophisticated representation of the statute

        self.saveState()
        #check for word "of", if not present there's nothing
        #nextWord = self.eatWord()
        #if nextWord != "of": self.restoreState(); return None
        nextWord = self.eatWord()
        if nextWord == "this":
            nextWord = self.eatWord()
            if nextWord == "Act": self.discardState(); return "LOCAL"
            elif nextWord in ("section","subsection","paragraph","subparagraph"): self.restoreState(); return None
            else:
                #showError("Unknown \"of\" type: this " + nextWord, location = self.decoratedText)
                self.restoreState(); return None
        elif nextWord == "that":
            nextWord = self.eatWord()
            if nextWord == "Act": self.discardState(); return LabelLocation(actName="that Act")
            else:
                #showError("Unknown \"of\" type: that " + nextWord, location = self.decoratedText)
                self.restoreState(); return None
        elif nextWord != "the":
            #showError("Unknown \"of\" type: " + nextWord, location = self.decoratedText)
            self.restoreState(); return None
            pass
        #At this point, we have found the text "of the"

        nextWord = self.eatWord()
        #handle the case of definition reference
        if nextWord == "definition":
            self.restoreState(); return None
            pass

        actWords = []
        #special cases for references to the "Act" or the "Regulations"
        if nextWord == "Act": self.discardState(); return LabelLocation(actName="Act")
        elif nextWord == "Regulations": self.discardState(); return LabelLocation(actName="Regulations")
        while nextWord is not None:
            actWords.append(nextWord)
            if nextWord == "Act" or nextWord == "Regulations":
                actStr = " ".join(actWords)
                chapStr = self.eatChapterAndYear()
                if chapStr is not None: actStr += chapStr
                self.discardState()
                return actStr
            nextWord = self.eatWord()
            pass

        #TODO: add code to handle "Income Tax Application Rules" (and maybe other names ending in "Rules"?)
        #TODO: add code to handle the Canada Pension Plan (maybe made a dictionary of all federal public statute names so we can test them at each step?
        #TODO: add code to handle references to "Income Tax Act, chapter 148 of the Revised Statutes of Canada, 1952"
        #TODO: references of the "paragraphs (f) and (h) of the description of B in that definition"
        #TODO: paragraphs (a) to (d), (f) and (g) of the definition "qualified investment" in section 204
        #showError("Unknown \"of\" type: no closing \"Act\": " + str(actWords), location = self.decoratedText)
        self.restoreState()
        return None


    def eatSingleLabelSeries(self):
        """This is one of the key methods of the parser.  Eats a series of labels (e.g., "section 4, 2 and 7 [of the Fiseries Act]") and returns a tuple (location, list of fragments).  The location is "LOCAL" if the location is the local statute. The returns values are both None if there is no match.
        @rtype: LabelLocation, list of Fragment
        """
        labelList = []
        self.saveState()
        ty = self.eatLabelType()
        if ty is None: self.restoreState(); return None, None
        frag = self.eatLabel()
        if frag is None: self.restoreState(); return None, None
        self.discardState()
        while frag is not None:
            labelList.append(frag)
            frag = self.eatConnectorAndLabel()
            pass
        location = self.eatActLocation()
        if len(labelList) > 0: labelList[0].setSeriesStart()
        return location, labelList

    def n_eatSingleLabelSeries(self):
        """This is one of the key methods of the parser.  Eats a series of labels (e.g., "section 4, 2 and 7 [of the Fiseries Act]") and returns a tuple (location, list of fragments).  The location is "LOCAL" if the location is the local statute. The returns values are both None if there is no match.
        @rtype: Fragment, list of Fragment
        """
        labelList = []
        self.saveState()
        labelType = self.n_eatLabelType()
        if labelType is None: self.restoreState(); return None, None
        frag = self.eatLabel()
        if frag is None: self.restoreState(); return None, None
        self.discardState()
        while frag is not None:
            labelList.append(frag)
            frag = self.eatConnectorAndLabel()
            pass
        if len(labelList) > 0: labelList[0].setSeriesStart()
        return labelType, labelList


    def eatLabelSeries(self):
        """This method eats a string of label series, joined by connectors, until it finds no more series, or until it finds a series with a non-soft-local location. Both return values are None if there is no match.
        @rtype: LabelLocation, list of Fragment
        """
        newLoc, newList = self.eatSingleLabelSeries()
        if newLoc is None: return None, None
        labelList = newList
        lastLoc = newLoc
        while newLoc is not None and newLoc.isLocal() and newLoc.isSilent(): #keep reading series until we either cannot find a series, or we find a series with a specified location
            lastLoc = newLoc
            self.saveState()
            cstr = self.eatConnector()  #check for and read connector
            if cstr is None: self.restoreState(); break
            newLoc,newList = self.eatSingleLabelSeries() #check for and read new list
            if newLoc is None: self.restoreState(); break
            labelList += newList
            self.discardState()
            pass
        if newLoc is None: location = lastLoc
        else: location = newLoc
        return location,labelList

    def eatNextLabelSeries(self):
        """Eats to the start of a labelSeries, and then eats and returns the series.  If no valid label series found, advances point to end of string and returns None, None."""
        namem = sectionNamePat.search(self.ltext, self.ptr) #find the first start of a label series
        while namem is not None:
            self.ptr = namem.start()
            loc,labelList = self.eatLabelSeries() #eat series
            if labelList is not None: return loc, labelList #if we found a real series, return it
            self.ptr += 1 #otherwise advance point, and look for next series
            namem = sectionNamePat.search(self.ltext, self.ptr)
            pass
        #if we run out of series start, advance pointer to end of string and return None, None
        self.ptr = len(self.text)
        return None, None

    passageStartPat = re.compile("(the +definitions?|sections?|subsections?|paragraphs?|clauses?|subclauses?|the descriptions? of|the values? of|determined for)")
    def eatToNextPassage(self):
        """Eats text up to the start of the next Passage (starting with a definition, variable or section start)."""
        m = TextParse.passageStartPat.search(self.ltext,self.ptr)
        if m is None: return None
        self.ptr = m.start()
        return

    def eatAllPassages(self):
        """Eats and returns all Passages in the text.
        @rtype: list of Passage
        """
        #TODO, need to specially find passages that immediately follow each other, so that we can set the "nextPassage, used for statute lookup."
        passages = []
        self.saveState()
        nextPassage = Passage.makeNextPassage(self)
        while nextPassage is not None:
            passages.append(nextPassage)
            nextPassage = Passage.makeNextPassage(self)
            pass
        return passages


class ApplicationParse(TextParse):
    #TODO - handle references to non-current Segments
    #TODO - code to add decorators
    #TODO - code to find single-definition subsections
    """Parser that automatically eats the text to determine the applicability range."""
    initialPat = re.compile("^in|apply in|for the purposes? of")
    initialPatAlt = re.compile(", in") #e.g., 18(5)
    thisPat = re.compile("this (?P<thisType>[a-z]+)")
    def __init__(self, decoratedText):
        TextParse.__init__(self,decoratedText)
        self.thisList = [] #list of areas that are referred to as "this", such as "this section" or "this part"
        self.sectionDict = {}
        self.definitionRefList = [] #contains a list of tuples (definition location, list of labels)
        self.eatStart()
        #repeatedly eat labelSeries and this's, with connectors in between, until we have no more matches
        self.eatApplicationRange()
        return
    def eatStart(self):
        """Finds the spot in the text that corresponds to the start of the applicability range."""
        m = ApplicationParse.initialPat.search(self.ltext)
        if m is None: #try to find an alternate start
            m = ApplicationParse.initialPatAlt.search(self.ltext)
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
        if m.group("thisType") not in ["section","act","subsection","part","division","subdivision"]: showError("Unknown \"thisType\": " + m.group("thisType"),location=self)
        return Fragment(m.group("thisType"),self.ptr+5) #fragment only includes the part of the this-reference after "this"
    def eatApplicationRange(self):
        """Eats a series of "this" references and section label lists. Returns a tuple (list of section label fragments, list of this type fragments)"""
        while True:
            loc, labelList = self.eatLabelSeries()
            if labelList is not None:
                if loc.isLocal():
                    if "LOCAL" not in self.sectionDict: self.sectionDict["LOCAL"] = []
                    self.sectionDict["LOCAL"] += labelList
                elif loc.isActRef():
                    ls = loc.getActName()
                    if ls not in self.sectionDict: self.sectionDict[ls] = []
                    self.sectionDict[ls] += labelList
                    pass
                elif loc.isDefinitionRef():
                    self.definitionRefList.append((loc,labelList))
                else: raise LangUtilException("eatApplicationRange -- should not get here in code.")
            else: #look for a this block
                thisFrag = self.eatThis()
                if thisFrag is None: showError("Could not find label list or this in expected spot in application language.",location=self.decoratedText); break
                else: self.thisList.append(thisFrag)
            con = self.eatConnector()
            if con is None: break
        return
    def showParseData(self):
        print("ApplicationParse Contents: {")
        for loc in self.sectionDict:
            locstr = loc
            print(locstr + " : " + ", ".join(str(c) for c in self.sectionDict[loc]))
            pass
        print(",".join(str(c) for c in self.thisList))
        for loc, labList in self.definitionRefList: print(str(loc) + " : " + str([str(c) for c in labList]))
        print("}")
        return
    def getSectionLabelCollection(self):
        """Returns the SectionLabelCollection object representing the applicability range described in the text.
        (Because of the need to get information on intervals, this code uses the data in the Statutes SectionData object, rather than the StatuteData object.)
        @rtype: SectionLabelLib.SectionLabelCollection
        """
        #TODO: add more data to the StatuteData object so that it can also do what is required by this method (calculating intervals, etc.).
        intervalList = []
        #add "this" intervals
        sdata = self.decoratedText.getStatute().getSectionData() #SectionData object for the Statute
        localLoc = self.decoratedText.getSectionLabel() #current sectionLabel

        thisStrList = [c.getText() for c in self.thisList] #self.thisList is filled with Fragments
        if len(thisStrList) > 0:
            segData = self.decoratedText.getStatute().getSegmentData()
            if "act" in thisStrList: return SectionLabelLib.UniversalSectionLabelCollection(sectionData = sdata) #if applicability says "this Act" just return the universal range
            for area in thisStrList:
                if area in ["section", "subsection", "paragraph", "subparagraph"]:
                    interval = None
                    sL = localLoc
                    if sL is None: showError("Could not find local sectionLabel for collection production.", location = self.decoratedText); continue
                    sL = sL.truncateSectionLabel(area)
                    if sL is not None: interval = SectionLabelLib.SectionLabelInterval(sectionData=sdata,sLList = [sL])
                    else: showError("Could not create truncated interval list for this \"" + area + "\" (" + str(localLoc), location=self.decoratedText)
                    if interval is not None: intervalList.append(interval)
                    else: showError("Could not find this \"" + area + "\"", location=self.decoratedText)
                    pass
                elif area in ["part","division", "subdivision"]:
                    curSegment = segData.getContainingSegment(localLoc) #find the current segment and refine it to the appropriate level
                    if curSegment is None: showError("Could not find segment for SL: " + str(localLoc), location = self.decoratedText); continue
                    if area == "part": curSegment = curSegment.getPart()
                    elif area == "division": curSegment = curSegment.getDivision()
                    elif area == "subdivision": curSegment = curSegment.getSubdivision()
                    if curSegment is None: showError("Could not find current segment [" + area + "] for: " + str(localLoc), location = self.decoratedText)
                    else: #if we found a segment
                        contents = segData.segmentContents[curSegment]
                        intervalList.append(SectionLabelLib.SectionLabelInterval(sectionData=sdata,sLList=contents))
                    pass
                else: showError("Unknown \"this\" type: " + area, location=self.decoratedText)
                pass
            pass
        #add intervals for list of specific sections
        if "LOCAL" in self.sectionDict: localFragments = self.sectionDict["LOCAL"]
        else: localFragments = []

        curLoc = localLoc
        #mark the Fragments in our list with the corresponding target SLs
        for frag in localFragments:
            if frag.isSeriesStart(): curLoc = localLoc #reset curLoc each time we start a new series
            tmpLoc = sdata.getSLFromString(frag.getText(), locationSL = curLoc, errorLocation=self.decoratedText)
            if tmpLoc is None: showError("Could not find SL for fragment: [" + frag.getText() + "]", location = self.decoratedText)
            else: curLoc = tmpLoc; frag.setTargetSL(curLoc)
        #create intervals for each of the Fragments
        nextSLList = []
        for frag in localFragments:
            if not frag.isToConnected(): #if the next frag is *not* to-connected to prior one, add the interval for the preceding list of SLs, and clear the SL list
                if len(nextSLList) > 0:
                    nextInterval = SectionLabelLib.SectionLabelInterval(sectionData=sdata, sLList=nextSLList)
                    intervalList.append(nextInterval)
                    nextSLList = []
                    pass
            if frag.hasTargetSL(): nextSLList.append(frag.getTargetSL())
            pass
        #if the nextSLList is not empty we clear it out producing one more interval
        if len(nextSLList) > 0: nextInterval = SectionLabelLib.SectionLabelInterval(sectionData=sdata, sLList=nextSLList); intervalList.append(nextInterval)
        return SectionLabelLib.SectionLabelCollection(sectionData=sdata,intervalList=intervalList)


#TODO: need a function that advances us to the start of the next Passage point (starting section, subsection, etc... the value, the description, the definition, others?)

class Passage(object):
    """Super class for objects representing a match to some form of cross-reference in the text of the Statute."""
    def __init__(self,decoratedText):
        """
        @type decoratedText: DecoratedText.DecoratedText
        """
        self.decoratedText=decoratedText
        self.targetStatute = None
        self.containerPassage = None #the Passage that says where this passage is located (if any)
        self.followingPassage = None #the Passage immediately following this one, if any
        return

    @staticmethod
    def makeNextPassage(tparse):
        """
        Advances the text parser to eat the next Passage, if any.
        @param tparse:
        @type tparse: TextParse
        @return:
        @rtype: Passage
        """
        tparse.saveState()
        tparse.eatToNextPassage()
        passage = Passage.makePassage(tparse)
        if passage is None:
            tparse.restoreState()
            return None
        return passage

    @staticmethod
    def makePassage(tparse):
        """
        Attempts to eat a Passage at the current position in the textparser.
        @type tparse: TextParse
        @rtype: Passage
        """
        tparse.saveState()
        passage = LabelPassage.makeLabelPassage(tparse)
        if passage is not None:
            tparse.discardState()
            return passage
        passage = DefinitionPassage.makeDefinitionPassage(tparse)
        if passage is not None:
            tparse.discardState()
            return passage
        passage = VariablePassage.makeVariablePassage(tparse)
        if passage is not None:
            tparse.discardState()
            return passage
        tparse.restoreState()
        return None

    @staticmethod
    def makeContainerPassage(tparse):
        """Returns the follower object in the tparse at the current state, or None if None.  May return a passage of type LabelPassage, DefinitionPassage, DescriptionPassage or StatutePassage
        @rtype: Passage
        """
        tparse.saveState()
        word = tparse.eatWord()
        if word is None:
            word = "" #fill in word with an empty string so that following string comparisons work
        if word.lower() == "of":
            #check for StatutePassage
            passage = StatutePassage.makeStatutePassage(tparse)
            if passage is not None:
                tparse.discardState()
                return passage
            pass
        if word.lower() == "of" or word.lower() == "in":
            #check for DefinitionPassage
            passage = DefinitionPassage.makeDefinitionPassage(tparse)
            if passage is not None:
                tparse.discardState()
                return passage
            passage = LabelPassage.makeLabelPassage(tparse)
            if passage is not None:
                tparse.discardState()
                return passage
            passage = VariablePassage.makeVariablePassage(tparse)
            if passage is not None:
                tparse.discardState()
                return passage
        tparse.restoreState()
        return TerminalPassage(tparse.getDecoratedText())

    def parseContainer(self,tparse):
        """Find container for this Passage in the tparse, and add it, eating the applicable text.  If no Container found, then nothing added."""
        container = Passage.makeContainerPassage(tparse)
        if container is None: return
        self.setContainerPassage(container)

    def getContainerPassage(self):
        """
        @rtype: Passage
        """
        return self.containerPassage

    def setContainerPassage(self,passage):
        """
        Set the container Passage for this Passage.
        @param passage:
        @type passage: Passgae
        @return:
        @rtype: None
        """
        self.containerPassage = passage
        return

    def getFollowingPassage(self):
        """
        @return:
        @rtype: Passage
        """
        return self.followingPassage

    def setFollowingPassage(self,passage):
        """
        Sets the following Passage for this Passage.  Information is also stored in all containers.
        @param passage:
        @type passage: Passage
        @return:
        @rtype:
        """
        self.followingPassage = passage
        if self.containerPassage is not None:
            self.containerPassage.setFollowingPassage(passage)
            pass
        return

    def setStatuteName(self,statuteName):
        """
        Sets the name of the Statute for this passage (useful for Passages that do not have a directly containing Statute Passage -- e.g. where Statute is implicitly local.
        @param statuteName:
        @type statuteName: str
        @return:
        @rtype: None
        """
        #TODO
        return

    def getStatute(self):
        """Returns the StatutePassage specifying the Act which this Passage points into, or None if None is specified (i.e., this is a local reference)
        @rtype: str
        """
        if self.containerPassage is None:
            raise LangUtilException("Calling generic getStatutePassage on a Passage without a container, which should never happen.")
        return self.containerPassage.getStatute()

    def getLocationSL(self):
        """Returns the SectionLabel that this Passage points into (e.g., when we are talking about a paragraph of a definition)
        @rtype SectionLabelLib.SectionLabel
        """
        return None


    def __str__(self):
        container = self.getContainerPassage()
        if container is None:
            cstr = ""
        else:
            cstr = " >> " + str(container)
        return "[" + self.passageString() + cstr + "]"

    def passageString(self):
        return "Generic Passage"

    pass

class LabelPassage(Passage):
    """Class representing a match to a subsection type and a list of labels in text."""
    @staticmethod
    def makeLabelPassage(tparse):
        """Returns the LabelPassage at the current position in tparse, otherwise None. Label passge is one referring to a collection of section labels of some type, e.g., section 1, 2 and 3
        @type tparse: TextParse
        @rtype: LabelPassage
        """
        tparse.saveState()
        ltype, llist = tparse.n_eatSingleLabelSeries()
        if ltype is None:
            tparse.restoreState()
            return None
        tparse.discardState()
        assert(isinstance(ltype, Fragment))
        assert(isinstance(llist,list))
        lp = LabelPassage(decoratedText=tparse.getDecoratedText(),labelType=ltype,labelList=llist)
        lp.parseContainer(tparse) #parse and add container, if one is present
        return lp

    def __init__(self,decoratedText, labelType, labelList):
        """
        @type decoratedText: DecoratedText.DecoratedText
        @type labelType: Fragment
        @type labelList: list of Fragment
        """
        Passage.__init__(self,decoratedText)
        self.labelType = labelType
        self.labelList = labelList
        return

    def passageString(self):
        return "Label:" + self.labelType.getText() + ":" + ", ".join(c.getText() for c in self.labelList) + ""
    pass


class DefinitionPassage(Passage):
    @staticmethod
    def makeDefinitionPassage(tparse):
        """
        Returns DefinitionPassage at the current position in tparse, otherwise None.  DefinitionPassage is one referring to the defintion of a defined term (e.g. the definition "blah blah"...)
        @type tparse: TextParse
        @rtype: DefinitionPassage
        """
        #TODO: fix so that can handle list of definitions, as in 66(16) (should be able to factor things out to have a single methods that parses a list of labels/variables/definitions?)
        tparse.saveState()
        w= tparse.eatWord()
        if w is None or w.lower() != "the":
            tparse.restoreState()
            return None
        w = tparse.eatWord()
        if w is None or w.lower() != "definition":
            tparse.restoreState()
            return None
        qfrag = tparse.eatQuoteText()
        if qfrag is None:
            tparse.restoreState()
            return None
        df = DefinitionPassage(decoratedText=tparse.getDecoratedText(), definitionFrag=qfrag)
        df.parseContainer(tparse)
        return df
    def __init__(self,decoratedText,definitionFrag):
        """
        @type decoratedText: DecoratedText.DecoratedText
        @param definitionFrag:
        @type definitionFrag: Fragment
        """
        Passage.__init__(self,decoratedText)

        self.definitionFragment = definitionFrag
        self.definedTerm = self.definitionFragment.getText().lower()
        return
    def passageString(self):
        return "Definition: \"" + self.definedTerm + "\""

class VariablePassage(Passage):
    @staticmethod
    def makeVariablePassage(tparse):
        """
        Returns DescriptionPassage at the current position in tparse, otherwise None. DescriptionPassage is a passage referring to one or more variables in a formula (e.g., (the description of|the value of|determined for) A (and|or|to) (G) in (section|subsection etc) or (the definition "...")...
        @type tparse: TextParse
        @rtype: VariablePassage
        """
        vlist = tparse.eatVariableList()
        if vlist is None: return None
        dp = VariablePassage(decoratedText=tparse.getDecoratedText(),varFragList=vlist)
        dp.parseContainer(tparse)
        return dp
    def __init__(self,decoratedText,varFragList):
        """
        @type decoratedText: DecoratedText.DecoratedText
        @type varFragList: list of Fragment
        """
        Passage.__init__(self,decoratedText)
        self.variableFragments = varFragList
        self.variables = [c.getText() for c in self.variableFragments]
        return
    def passageString(self):
        return "Variables: " + ", ".join(self.variables) + ""

class StatutePassage(Passage):
    @staticmethod
    def makeStatutePassage(tparse):
        """
        Returns StatutePassage at at the current position in tparse, otherwise None. StatutePassage is one referring to an Statute (e.g., the Blah Blah Act(, revised statutes of Canada...)
        @type tparse: TextParse
        @rtype: StatutePassage
        """
        actName = tparse.n_eatActLocation()
        if actName is None:
            return None
        return StatutePassage(decoratedText=tparse.getDecoratedText(),statuteName=actName)

    def __init__(self,decoratedText,statuteName):
        """
        @type decoratedText: DecoratedText.DecoratedText
        @type statuteName: str
        """
        Passage.__init__(self,decoratedText)

        self.statuteName = statuteName
        self.statuteFragment=None
        return

    def getStatute(self):
        return self.statuteName

    def passageString(self):
        return "Statute: " + self.statuteName + ""

class TerminalPassage(StatutePassage):
    """Passage representing the "Statute" if not Statute is otherwise specified.  Will look to the "next" Passage for the Statute, if specified, otherwise defaults to "LOCAL". """
    def __init__(self,decoratedText):
        """
        @param decoratedText:
        @type decoratedText: DecoratedText.DecoratedText
        @return:
        @rtype:
        """
        Passage.__init__(self,decoratedText)
        return

    def getStatute(self):
        """
        This Passage type occurs where there is not a terminating Statute Passage.  It looks to the following Passage for teh Statute and otherwise indicated local.
        @return:
        @rtype: str
        """
        follower = self.getFollowingPassage()
        if follower is None:
            return "LOCAL"
        return follower.getStatute()

    def passageString(self):
        return "Terminal:hasFollower=" + ("True" if (self.getFollowingPassage() is not None) else "False")


class SectionReferenceParse(TextParse):
    """Finds all the local/external section references in text."""
    def __init__(self, decoratedText):
        """
        @type decoratedText: DecoratedText.DecoratedText
        """
        TextParse.__init__(self,decoratedText)
        self.sectionDict = {} #list of fragments for internal references
        self.definitionRefList = []
        self.eatAllSectionReferences()
        return
    def eatAllSectionReferences(self):
        """Eat all the label series in the text, and store in sectionDict dictionary."""
        loc, labList = self.eatNextLabelSeries()
        while loc is not None:
            if loc.isLocal():
                if "LOCAL" not in self.sectionDict: self.sectionDict["LOCAL"] = []
                self.sectionDict["LOCAL"] += labList
                pass
            elif loc.isActRef():
                ls = loc.getActName()
                if ls not in self.sectionDict: self.sectionDict[ls] = []
                self.sectionDict[ls] += labList
                pass
            elif loc.isDefinitionRef():
                self.definitionRefList.append((loc,labList))
                pass
            loc, labList = self.eatNextLabelSeries()
            pass
        return

    def addDecorators(self):
        """Add decorators to the underlying DecoratedText for the labels identified by the parser."""

        #TODO - extend to non-local references (will need code in StatuteData to redirect to correct data object).- So far implemented for references to the "Act" from regulations
        if len(self.sectionDict) == 0:
            return
        statData = self.decoratedText.getStatute().getStatuteData()
        for actName in self.sectionDict:
            if actName == "LOCAL": #add decorators for local references
                statData.pinpointFragmentList(fragmentList=self.sectionDict["LOCAL"],locationSL=self.decoratedText.getSectionLabel(),errorLocation=self.decoratedText)
                for frag in self.sectionDict["LOCAL"]:
                    if frag.hasPinpoint(): self.addLinkDecorator(frag)
                    #for frag in self.sectionDict["LOCAL"]: print(frag.getText() + "--" + (str(frag.getPinpoint()) if frag.hasPinpoint() else "NONE" ))
                pass
            if actName == "Act": #add decorators for "Act" references
                actStat = statData.getAct()
                if actStat != None:
                    actData = self.decoratedText.getStatute().getStatuteIndex().getStatuteData(actStat)
                    actData.pinpointFragmentList(fragmentList=self.sectionDict["Act"],locationSL=None,errorLocation=self.decoratedText)
                    for frag in self.sectionDict["Act"]:
                        if frag.hasPinpoint(): self.addLinkDecorator(frag)
                else:
                    showError("\"Act\" is referenced, but not act specified for statute.", location = self.decoratedText)
            if actName == "Regulations" in self.sectionDict: #add decorators for "Reg" references
                #TODO: fill this in
                pass
            if actName not in ("LOCAL","Act","Regulations"):
                #TODO: fill this in, cross-references to all other statutes
                pass
            pass
        return

    def showParseData(self):
        for loc in self.sectionDict:
            locstr = loc
            if len(self.sectionDict[loc]) > 0: print(locstr + " : " + ", ".join(c.getText() for c in self.sectionDict[loc]))
            pass
        for loc, labList in self.definitionRefList: print(str(loc) + " : " + str([str(c) for c in labList]))
        return


if __name__ == "__main__":
    #various tests for pattern matching
    import DecoratedText
    import Statute

    print("\nTEST 1")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text="12.3(14)(a)")
    t = TextParse(s)
    lab = t.eatLabel()
    if lab.getText() != s.getText(): print "Error 1: [" + s.getText() + "] [" + str(lab) + "]"

    print("\nTEST 2")
    s =DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text="Subsection 4.1")
    t = TextParse(s)
    labt = t.eatLabelType()
    lab = t.eatLabel()
    if labt != "subsection": print "Error 2: [" + s.getText() + "] [" + str(labt) + "]"
    if lab.getText() != "4.1": print "Error 3: [" + s.getText() + "] [" + str(lab) + "]"

    print("\nTest 3")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text="The following definitions apply in this section and in subsection 47(3), paragraphs 53(1)(j) and 110(1)(d) and (d.01), this Part and subsections 110(1.1), (1.2), (1.5), (1.6) and (2.1) and subsections 40 and 50 of the Fisheries Act and subsections 60(1), (2) and (3) of the Act and paragraphs 1(1)(a) and (b) of this Act.")
    #print(s.getText())
    t = ApplicationParse(s)
    t.showParseData()

    print("\nTest 4")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text="The following definitions apply in this section and in subsection 47(3), paragraphs 53(1)(j) and 110(1)(d) and (d.01), this Part and subsections 110(1.1), (1.2), (1.5), (1.6) and (2.1) and subsections 40 and 50 of the Fisheries Act and subsections 60(1), (2) and (3) of the Act and paragraphs 1(1)(a) and (b) of this Act and clauses (x), (y) and (z) of the definition \"arbitrary defined term\" in section 42.")
    #print(s.getText())
    t = SectionReferenceParse(s)
    t.showParseData()

    print("\nTest 5")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text="to an official solely for the purposes of section 7.1 of the Federal-Provincial Fiscal Arrangements and Federal Post-Secondary Education and Health Contributions Act;")
    #print(s.getText())
    t = SectionReferenceParse(s)
    t.showParseData()

    print("\nTest 6")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text="Subject to subsections (8) and (8.1), for the purposes of this subsection and subsection (3),")
    #print(s.getText())
    t = ApplicationParse(s)
    t.showParseData()

    print("\nTest 7")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text="The following definitions apply for the purpose of paragraph (1)(b).")
    #print(s.getText())
    t = ApplicationParse(s)
    t.showParseData()

    print("\nTest 8")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text="In this section and paragraph 56(1)(d.1) of the Income Tax Act, chapter 148 of the Revised Statutes of Canada, 1952,")
    t = ApplicationParse(s)
    t.showParseData()

    print("\nTest 9")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text="The following definitions apply in this section and in Part XI.01.")
    t = ApplicationParse(s)
    t.showParseData()

    print("\nTest 10")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text="Notwithstanding any other provision of this Act (other than subsection 18(5.1)), in this subsection and subsections 18(4) to 18(6),")
    t = ApplicationParse(s)
    t.showParseData()

    print("\nTest 11")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text="For the purposes of subsection 13(2), paragraph 13(7)(g), subparagraph 13(7)(h)(iii), subsections 20(4) and (16.1), the description of B in paragraph 67.3(d) and subparagraph 85(1)(e.4)(i) of the Act, the amount prescribed is")
    t = SectionReferenceParse(s)
    t.showParseData()

    st = "contract, other than a contract described in paragraph (1)(d) of this section, or paragraph 12.2(3)(e) of the Income Tax Act, chapter 148 of the Revised Statutes of Canada, 1952, or to which"
    print("\nTest 12:\n[" + st + "]")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text=st)
    t = SectionReferenceParse(s)
    t.showParseData()

    st = "of the Income Tax Act, chapter 148 of the Revised Statutes of Canada, 1952, or to which"
    print("\nTest 13:\n[" + st + "]")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text=st)
    t = TextParse(s)
    print(t.eatActLocation())


    st = "paragraph (i), paragraphs 12(1)(o) and 12(1)(z.5), 18(1)(m), 20(1)(v.1) and 29(1)(b) and 29(2)(b), section 55, subsections 69(6) and 69(7) and paragraph 82(1)(b) of this Act and paragraphs 20(1)(gg) and 81(1)(r) and (s) of the Income Tax Act, chapter 148 of the Revised Statutes of Canada, 1952,"
    print("\nTest 14:\n[" + st + "]")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text=st)
    t = SectionReferenceParse(s)
    t.showParseData()

    st = "paragraph 82(1)(b) of this Act and paragraphs 20(1)(gg) and 81(1)(r) and (s) of the Income Tax Act, chapter 148 of the Revised Statutes of Canada, 1952,"
    print("\nTest 15:\n[" + st + "]")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text=st)
    t = TextParse(s)
    result = LabelPassage.makeLabelPassage(t)
    print result

    st = "paragraphs 20(1)(gg) and 81(1)(r) and (s) of the definition \"blah blah\" of section 2 of the Income Tax Act, chapter 148 of the Revised Statutes of Canada, 1952,"
    print("\nTest 15:\n[" + st + "]")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text=st)
    t = TextParse(s)
    result = LabelPassage.makeLabelPassage(t)
    print result

    st = "the values of A.2 and B.3 in paragraphs 20(1)(gg) and 81(1)(r) and (s) of the definition \"blah blah\" of section 2 of the Income Tax Act, chapter 148 of the Revised Statutes of Canada, 1952,"
    print("\nTest 16:\n[" + st + "]")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text=st)
    to = TextParse(s)
    result = VariablePassage.makeVariablePassage(to)
    print result

    st = "blah blah the values of A.2 and B.3 in paragraphs 20(1)(gg) and 81(1)(r) and (s) of the definition \"blah blah\" of section 2 of the Income Tax Act, chapter 148 of the Revised Statutes of Canada, 1952 and paragraph 82(1)(b) of this Act and paragraphs 20(1)(gg) and 81(1)(r) and (s) of the Happy Camper Act; subsection 14(2)"
    print("\nTest 17:\n[" + st + "]")
    s = DecoratedText.DecoratedText(parent=Statute.DummyStatute(),text=st)
    t = TextParse(s)
    result = t.eatAllPassages()
    for c in result: print c