#$Id$

#####
#
# Module for representing a string of text and associated decorations
#
#####

from ErrorReporter import showError
from StatutePart import StatutePart

class DecoratorException(Exception): pass

class DecoratedText(StatutePart):
    def __init__(self,parent,text,decorators=None):
        StatutePart.__init__(self,parent=parent)
        self.text=text
        self.decorators = []
        if decorators is not None:
            for d in decorators: self.addDecorator(d) #add each of the given decorators, if specified
        return
    def addDecorator(self,decorator):
        """Adds a decorator for this Text."""
        n = 0
        decorator.attachToDecoratedText(self)
        #find the first decorator that this one starts after
        insertPoint = len(self.decorators) #find the point were this decorator would be inserted
        for n in xrange(0,len(self.decorators)):
            if self.decorators[n].getEnd() > decorator.getStart(): insertPoint = n; break
        if insertPoint < len(self.decorators) and self.decorators[insertPoint].collide(decorator): #if inserting at the point of existing decorator, and there is an overlap, show error and return
            showError("Decorator collision: " + str(self.decorators[insertPoint])+ "" + "/" + str(decorator) ,location=self)
            return
        self.decorators.insert(insertPoint,decorator) #insert decorator at appropriate sport
        return
    def getText(self):
        """Returns the raw text underlying the DecoratedText."""
        return self.text
    def getDecoratedText(self, renderContext):
        """Returns the items text, with the Decorator objects applied to the applicable portions."""
        self.decorators.sort()
        ptr = 0
        textList = []
        for dec in self.decorators:
            if dec.getStart() < ptr: raise DecoratorException("Decorators out of order!")
            textList.append(self.text[ptr:dec.getStart()])
            textList.append(dec.getDecoratedText(renderContext=renderContext,textFull=self.text)) #TODO: should getDecoratedText on each decoration be told about the end of the previous decoration and the start of the next one --- so it knows how much it can spread out? (e.g., so that links can be spread out to cover whole words?)
            ptr = dec.getEnd()
            pass
        textList.append(self.text[ptr:])
        return u"".join(textList)



class Decorator(StatutePart):
    def __init__(self, parent, start, end):
        StatutePart.__init__(self,parent=parent)
        self.start = start
        self.end = end
        self.decoratedText = None #marks the DecoratedText message that this decorator is attached to
        return
    def __gt__(self,dec): return self.getStart() > dec.getStart() #ordering based on start positions
    def __lt__(self,dec): return dec > self
    def attachToDecoratedText(self,decoratedText):
        """Specify which DecoratedText object this decorator is attached to."""
        self.decoratedText = decoratedText
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
        """Returns the rendered text of this decorator.  Can either supply the full text, in which case the decorator will use it's start and end variables to extract the relevant portion, or the specific piece that should be rendered.
        Default method simply returns raw text."""
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
        text = Decorator.getDecoratedText(self,renderContext,textPiece=textPiece,textFull=textFull) #get the simple text
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
