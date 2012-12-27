# $Id$

"""module for handling text and text decorators, used by the TextItem class in Statute.

There are two sets of objects representing two ways of representing text:
Representation 1: text areas are broken up into separate objects (subclasses of Piece) matching the tag division boundaries within the XML representation.  The Piece objects contain logic for consolidating the text (e.g., of a paragraph) into a single block.  The representation is only transitory while the TextItem is being initialized.
Representation 2: The text of each paragraph is consolidated into a single string within the TextItem, along with a set of Decorator objection.  Each decorator records a sort of notation that should be added to the text upon rendering, such as a cross-link --- this lets additional decorations to be added with lots of annoying object division.
 """

# TODO: instead of TextItem objections having a raw string and a list of Decorators, should there instead by a Decorated Text class that encapsulates both? (if so, fix above description)

from ErrorReporter import showError
from StatutePart import StatutePart
import DecoratedText

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
        """Returns a DecoratedText object based on this piece and all following pieces in the list."""
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
        return DecoratedText.DecoratedText(parent=self,text=u"".join(textList),decorators=decorators)
    
    def getTextAndDecorator(self):
        """Returns a tuple (text, decorator) based on *just this* piece.""" #Should pieces be able to have multiple decorators?
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
        decorator = DecoratedText.DefinedTermDecorator(parent=parent,start=1,end=1+len(self.definedTerm),definedTerm=self.definedTerm) #decoration should not include quotes
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
        decorator = DecoratedText.LinkDecorator(parent=parent,start=0,end=len(text),target = target)
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

