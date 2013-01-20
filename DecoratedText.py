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
        """Initializer for Decorated Text."""
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
            #special case when we are adding decorator that nearly exactly overlaps with an existing DefinedTermDecorator that doesn't have a pinpoint.
            tookPin = self.decorators[insertPoint].takePinpoint(decorator)
            if tookPin: pass;# showError("Pinpoint inherited to:[" + self.getDText(self.decorators[insertPoint]) + "]", location=self)
            else:
                oldDec = self.decorators[insertPoint]
                if abs(decorator.getStart()-oldDec.getStart())< 2 and oldDec.getEnd() > decorator.getEnd(): pass
                else: showError( "Decorator collision, old:[" + self.getDText(self.decorators[insertPoint]) + "], new:[" + self.getDText(decorator) +"]" ,location=self)
            return
        self.decorators.insert(insertPoint,decorator) #insert decorator at appropriate sport
        return
    def getText(self):
        """Returns the raw text underlying the DecoratedText."""
        return self.text
    def getDText(self,decorator):
        """Returns the text underlying the decorator.
        @type decorator: Decorator
        @rtype: str"""
        return self.text[decorator.getStart():decorator.getEnd()]

    def getRenderedText(self, renderContext):
        """Returns the items text, with the Decorator objects applied to the applicable portions."""
        self.decorators.sort()
        ptr = 0
        textList = []
        for dec in self.decorators:
            if dec.getStart() < ptr: raise DecoratorException("Decorators out of order!")
            textList.append(self.text[ptr:dec.getStart()])
            textList.append(dec.getRenderedText(renderContext=renderContext,textFull=self.text)) #TODO: should getDecoratedText on each decoration be told about the end of the previous decoration and the start of the next one --- so it knows how much it can spread out? (e.g., so that links can be spread out to cover whole words?)
            ptr = dec.getEnd()
            pass
        textList.append(self.text[ptr:])
        return u"".join(textList)
    def getDefinedTerms(self):
        """Returns a list of defined terms in the DecoratedText.
        @rtype: list of str
        """
        terms = []
        for dec in self.decorators:
            if isinstance(dec,DefinedTermDecorator): terms.append(dec.getDefinedTerm())
            pass
        return terms


class Decorator(StatutePart):
    def __init__(self, parent, start, end):
        StatutePart.__init__(self,parent=parent)
        self.start = start
        self.end = end
        self.decoratedText = None #marks the DecoratedText message that this decorator is attached to
        self.pinpoint = None
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
    def hasPinpoint(self):
        if self.pinpoint is None: return False
        return True
    def getPinpoint(self):
        """Returns the Pinpoint for the decorator, if any.
        @rtype: SectionLabelLib.Pinpoint"""
        return self.pinpoint
    def takePinpoint(self, decorator):
        """Take Pinpoint object from specified decorator in appropriate circumstances. Returns True on success.
        @rtype: bool"""
        return False
    def getRenderedText(self,renderContext,textPiece=None, textFull=None):
        """Returns the rendered text of this decorator.  Can either supply the full text, in which case the decorator will use it's start and end variables to extract the relevant portion, or the specific piece that should be rendered.
        Default method simply returns raw text."""
        if textPiece is None:
            if textFull is None: showError("getDecoratedText called with no text",location=self); return u""
            else: text = textFull[self.getStart():self.getEnd()]
        else:
            if textFull is not None:
                if textPiece != textFull[self.getStart():self.getEnd()]: showError("getDecoratedText called with inconsistent textFull and textPiece",location=self)
            text = textPiece
        return text

class LinkDecorator(Decorator):
    def __init__(self, parent,start,end,pinpoint):
        """Object representing a link to a pinpoint location.
        @type start: int
        @type end: int
        @type pinpoint: SectionLabelList.Pinpoint
        @return:
        """
        Decorator.__init__(self,parent,start,end)
        self.pinpoint = pinpoint
        return
    def getRenderedText(self,renderContext,textPiece=None,textFull=None):
        text = Decorator.getRenderedText(self,renderContext,textPiece=textPiece,textFull=textFull) #text to be decorated
        if self.pinpoint is None: return text #return plain text, unless we have a target #TODO, maybe we should mark the text as a failed decorator?
        return renderContext.renderPinpoint(pinpoint=self.pinpoint,text=text)

class DefinedTermDecorator(Decorator):
    def __init__(self, parent,start,end,definedTerm,pinpoint=None):
        Decorator.__init__(self,parent,start,end)
        self.pinpoint = pinpoint
        self.definedTerm = definedTerm
        return
    def getDefinedTerm(self): return self.definedTerm
    def addPinpoint(self,pinpoint):
        """Sets the pinpoint for the defined term.  Shows a warning if a pinpoint has previously been set."""
        if self.pinpoint is not None: showError("Adding Pinpoint to DefinedTermDecorator when there was already pinpoint.", location=self)
        self.pinpoint = pinpoint
        return
    def takePinpoint(self, decorator):
        """Take Pinpoint object from specified decorator in appropriate circumstances (decorator missing, nearly perfect overlap). Returns True on success.
        @rtype: bool"""
        #TODO, I think this is just a stopgap for replacing the DefinedTermDecorator
        if self.hasPinpoint(): return False
        if not decorator.hasPinpoint(): return False
        if abs(self.start-decorator.getStart()) > 1: return False
        if abs(self.end-decorator.getEnd()) > 1: return False
        self.addPinpoint(decorator.getPinpoint())
        return True
    def getRenderedText(self,renderContext,textPiece=None,textFull=None):
        text = Decorator.getRenderedText(self,renderContext,textPiece=textPiece,textFull=textFull) #get the simple text
        if self.pinpoint is None: return renderContext.boldText(text)
        return renderContext.renderPinpoint(pinpoint=self.pinpoint,text=text)

