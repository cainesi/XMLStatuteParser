# $Id$

"""module for handling text and text decorators, used by the TextItem class in Statute."""

from ErrorReporter import showError
from StatutePart import StatutePart


#####
#
# Piece classes, used to represent the parts of text in a TextItem
#
####

class Piece(StatutePart):
    """Object representing an element in the linked-list of text stored by a TextItem, which also includes logic for linking the Pieces together into a single block of text."""
    def __init__(self,parent,previousPiece=None,nextPiece=None,isSpaced = True, decorator = None):
        StatutePart.__init__(self,parent=parent)
        if previousPiece == None: self.previousPiece = None
        else: self.setPreviousPiece(previousPiece)
        if nextPiece == None: self.nextPiece = None
        else: self.setNextPiece(nextPiece)
        self.isSpaced = isSpaced
        self.decorator = decorator
        return
    def __iter__(self):
        """Iterates over linked list starting from this piece."""
        ptr = self
        while ptr != None:
            yield ptr
            ptr = ptr.nextPiece
            pass
        return
    def objName(self):
        return u"<Piece>"
    def pieceList(self):
        """Returns a list of pieces in this linked list. (allows pieces to be modified during iteration without screwing things up)."""
        return [c for c in self]
    ###
    # Linked list manipulation code
    ###
    def setNextPiece(self,piece):
        """Sets the nextPiece for this piece to the specified piece, and unlinks the existing nextPiece, if any."""
        if self.nextPiece != None: self.nextPiece.previousPiece = None #break back-link from this pieces existing target, if any
        self.nextPiece = piece #set to new target
        if piece.previousPiece != None: piece.previousPiece.nextPiece = None #break forward link piece targetting target, if any
        piece.previousPiece = self  #set new backlink for target
        return
    def setPrevious(self,piece):
        """Sets the previous Piece for this piece."""
        if self.previousPiece != None: self.previousPiece.nextPiece = None
        self.previousPiece = piece
        if piece.nextPiece != None: piece.nextPiece.previousPiece = None
        piece.nextPiece = self
        return
    def removePiece(self,piece):
        """Remove a piece from its linked list, joining the pieces ahead and behind."""
        if self.nextPiece != None: self.nextPiece.previousPiece = self.previousPiece
        if self.previousPiece != None: self.previousPiece.nextPiece = self.nextPiece
        self.nextPiece = None
        self.previousPiece = None
        return
    def replace(self,newPieces):
        """Replace this piece in linked list with the list of pieces in newPieces (which are themselves linked together by this method)."""
        ptr = self.previousPiece
        for p in newPieces: p.setPreviousPiece(ptr); ptr = p
        ptr.setNextPiece(self.nextPiece)
        return
    ###
    # Text combining code
    ###
    def getText(self):
        showError("getText call on piece",location=self) #this shouldn't happen anymore...
        return self.softInitialSpace() + self.getUnspacedText() + self.softTrailingSpace()
    def getUnspacedText(self): return u""
    def softInitialSpace(self): return u" " if self.hasInitialSpace() else u""
    def softTrailingSpace(self): return u" " if self.hasTrailingSpace() else u""
    def hasInitialSpace(self):
        if self.previousPiece == None: return False #don't add space at start of text block
        if self.previousPiece.hasTrailingSpace(): return False #don't add spaced if trailing space already added
        if self.previousEatsSpace(): return False
        if self.isSpaced: return True
        return False
    def hasTrailingSpace(self):
        if self.nextPiece == None: return False
        if not self.nextIsAlnumStart(): return False
        if self.isSpaced: return True
        return False
    @staticmethod
    def isSpacingChar(char):
        if char.isalnum() or char == "(": return True
        return False
    def isAlnumStart(self): return False #does piece start with an alphanumeric character
    def nextIsAlnumStart(self):
        """Returns True if the nextPiece exists and has an alphanumeric start (or other start that results in adding a soft space after current piece)."""
        if self.nextPiece == None: return False
        return self.nextPiece.isAlnumStart()
    def previousEatsSpace(self):
        """Returns true if prior piece in the linked list will "eat" a space that would otherwise be added to this piece. The None at the front of the list eats spaces."""
        if self.previousPiece == None: return True
        return self.previousPiece.eatsFollowingSpace()
    def eatsFollowingSpace(self):
        """Returns True if this piece will "eat" a space that would otherwise be added by the following space."""
        return True
    def getDefinedTerm(self): return None

    ###
    # Code for assemling text into a single block (for text processing) and a list of decorators
    ###
    
    def assembleText(self):
        """Returns a tuple (text, list of decorators) based on this piece and all following pieces in the list."""
        textList = []
        decorators = []
        totLength = 0
        for piece in self:
            text, dec = piece.getTextAndDecorator()
            if piece.hasInitialSpace(): textList.append(u" "); totLength += 1
            if dec != None:
                dec.rightShift(totLength)
                decorators.append(dec)
            textList.append(text)
            totLength += len(text)
            if piece.hasTrailingSpace(): textList.append(u" "); totLength += 1
        return (u"".join(textList),decorators)
    
    def getTextAndDecorator(self):
        """Returns a tuple (text, decorator) based just on this piece.""" #Should pieces be able to have multiple decorators?
        return (self.getUnspacedText(),self.decorator)
    pass

class TextPiece(Piece):
    def __init__(self,parent, text,previousPiece=None,nextPiece=None):
        Piece.__init__(self,parent=parent, previousPiece=previousPiece, nextPiece=nextPiece, isSpaced=False)
        if "\n" in text: showError("Newline inside text piece.", location = self)
        self.text = text
        return
    def objName(self):
        return u"<TextPiece: [" + self.text + "]>"
    def getUnspacedText(self): return self.text
    def isAlnumStart(self):
        if len(self.text) == 0: return self.nextIsAlnumStart() #empty text pieces should have the effect of the piece on the other side.
        if self.isSpacingChar(self.text[0]): return True
        return False
    def eatsFollowingSpace(self):
        if len(self.text) > 0: return False
        else: return self.previousEatsSpace()
    pass

class DefinedTermPiece(Piece):
    def __init__(self, parent, text, previousPiece=None,nextPiece=None):
        self.definedTerm = text
        decorator = DefinedTermDecorator(parent=parent,start=1,end=1+len(self.definedTerm),definedTerm=self.definedTerm) #decoration should not include quotes
        Piece.__init__(self,parent=parent,previousPiece=previousPiece,nextPiece=nextPiece,decorator = decorator)
        return
    def objName(self):
        return u"<DefinedTermPiece: [" + self.definedTerm + "]>"
    def getDefinedTerm(self): return self.definedTerm
    def getUnspacedText(self): return "\"" + self.definedTerm + "\""
    def isAlnumStart(self): return True
    def eatsFollowingSpace(self): return False
    pass

class LinkPiece(Piece):
    """Class for a link in the text."""
    def __init__(self, parent,text, target = None,previousPiece=None,nextPiece=None):
        decorator = LinkDecorator(parent=parent,start=0,end=len(text),target = target)
        Piece.__init__(self,parent=parent,previousPiece=previousPiece,nextPiece=nextPiece, decorator=decorator)
        self.text=text
        self.target=target
        return
    def objName(self):
        return u"<LinkPiece: [" + self.text + "]>"
    def getUnspacedText(self): return self.text
    def isAlnumStart(self):
        if len(self.text) == 0: return False
        if self.isSpacingChar(self.text[0]): return True
        return False
    def eatsFollowingSpace(self):
        if len(self.text) > 0: return False
        else: return self.previousEatsSpace()
    pass

#####
#
# Decorators for text
#
#####

class Decorator(StatutePart):
    def __init__(self, parent, start, end):
        StatutePart.__init__(self,parent=parent)
        self.start = start
        self.end = end
        return
    def __gt__(self,dec): return self.getStart() > dec.getStart() #ordering based on start positions
    def __lt__(self,dec): return dec > self
    def collide(self,dec):
        """Returns True if the two decorators collide."""
        if self.getStart() < dec.getStart():
            if self.getEnd() > dec.getStart(): return True
            else: return False
        else:
            if self.getStart() < dec.getEnd(): return True
            else: return False
            pass
        pass
    def includes(self,dec):
        """Returns True if this decorator contains the other."""
        if self.getStart() <= dec.getStart() and self.getEnd() >= dec.getEnd(): return True
        return False
    def rightShift(self,delta):
        """Shift the Decorator by amount delta in the text (useful when other text is concatenated onto the start of the underlying string)"""
        self.start += delta
        self.end += delta
    def getStart(self): return self.start
    def getEnd(self): return self.end
    def getDecoratedText(self,renderContext,textPiece=None, textFull=None):
        """Returns the rendered text of this decorator.  Can either supply the full text, in which case the decorator will use it's start and end variables to extract the relevant portion, or the specific piece that should be rendered."""
        if textPiece == None:
            if textFull == None: showError("getDecoratedText called with no text",location=self); return u""
            else: text = textFull[self.getStart():self.getEnd()]
        else:
            if textFull != None:
                if textPiece != textFull[self.getStart():self.getEnd()]: showError("getDecoratedText called with inconsistent textFull and textPiece",location=self)
            text = textPiece
        return text

class LinkDecorator(Decorator):
    def __init__(self, parent,start,end,target):
        Decorator.__init__(self,parent,start,end)
        self.target = target #TODO: do something with the target! (also in DefinedTermDecorator)
        return
    def getDecoratedText(self,renderContext,textPiece=None,textFull=None):
        text = Decorator.getDecoratedText(self,renderContext,textPiece=textPiece,textFull=textFull)
        return text

class DefinedTermDecorator(Decorator):
    def __init__(self, parent,start,end,definedTerm,target=None):
        Decorator.__init__(self,parent,start,end)
        self.target = target
        self.definedTerm = definedTerm
        return
    def getDefinedTerm(self): return self.definedTerm
    def getDecoratedText(self,renderContext,textPiece=None,textFull=None):
        text = Decorator.getDecoratedText(self,renderContext,textPiece=textPiece,textFull=textFull)
        return renderContext.boldText(text)


#####
#
# Various types of targets for Link Items
#
####

class Target(object):
    """Superclass for all types of link targets."""
    def __init__(self, target): pass
    pass

class InternalTarget(Target):
    """Link to another location within the current statutory instrument."""
    def __init__(self, target): pass    
    pass

class ExternalTarget(Target):
    """Target to another statutory instrument (another act, regulations, etc.)"""
    def __init__(self, target): pass
    pass

class ChapterTarget(Target):
    """Target to a chapter for the federal statutes (for historical notes.)"""
    def __init__(self, target): pass
    pass

class BulletinTarget(Target):
    """Target to a bulletin."""
    def __init__(self, target): pass
    pass
