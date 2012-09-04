import XMLStatParse
import RenderContext
import sys
from Constants import sectionTypes, formulaSectionTypes, formulaSectionMap, textTypes
import SectionLabelLib

#workflow for parsing statute:
# 1) parse xml into tree structure
# 2) walk the tree-structure to verify consistency and specially process certain types of nodes.
#   2a) Labels
#   2b) Definitions
#   2c) Marginal notes
#   2d) Historical notes
#   2e) Tables (?)
# 3) Verify consistency of section labelling?
# 4) Walk structure to detect defined terms
# 5) Insert cross-references, etc.
# 6) Output wikipages

#Classes used in the processed statute structure:
#class StatuteItem(object):
#    pass

#TODO: labels should be output in wikioutput.
#TODO: correct unnecessary spaces appearing at certain points.
#TODO: marks on Items when they should start a new paragraph
#TODO: fix for definitions where there are multiple defined term strings

STRICT = False
def showError(s, location = None):
    if location != None:
        while True:
            if hasattr(location, "getSectionLabel"): #work our way up the parent chain till we find something with a getSectionLabel that returns non-None
                if location.getSectionLabel() != None:
                    s += "@<" + location.getSectionLabel().getDisplayString() + ">"
                    break
                pass
            if not hasattr(location, "parent"): break
            location = location.parent 
            pass
        pass
    if STRICT: raise StatuteException(s)
    else: sys.stderr.write("WARNING: <" + s + ">\n")

class StatuteException(Exception): pass

#####
#
# Items, which represent parts of the parsed statute structure
#
####

class Paragraph(object):
    """Class for encapsulating a (part of a) paragraph of rendered text, along with logic for determining when paragraphs can be connected, and outputing final results."""
    def __init__(self,text, renderContext,indentLevel = 0,isMarginalNote = False, forceNewParagraph=False, softSpace=False):
        self.text = text
        self.indentLevel = indentLevel
        self.isMarginalNote = isMarginalNote
        self.forceNewParagraph = forceNewParagraph
        self.softSpace = softSpace
        self.renderContext = renderContext
        return
    def merge(self,nextParagraph):
        """Attempted to merge text with the nextParagraph, returns True if successful, else False."""
        if nextParagraph.forceNewParagraph: return False
        if self.isMarginalNote or nextParagraph.isMarginalNote: return False #marginal notes can't be merged
        if self.indentLevel != nextParagraph.indentLevel: return False
        spacer = u""
        if self.softSpace: spacer = (u" " if (len(nextParagraph.text) > 0 and nextParagraph.text[0].isalnum()) else u"")
        else: spacer = u""
        self.text += spacer + nextParagraph.text
        self.softSpace = nextParagraph.softSpace
        return True
    def getRenderedText(self):
        if not self.isMarginalNote:
            return self.renderContext.indentText(self.text, level = self.indentLevel)
        return self.renderContext.renderMarginalNote(self.text)

class BaseItem(object):
    """Superclass for all items in the statute structure, with some general purpose methods of handling section labels, etc."""
    def getIndentLevel(self): return self.parent.getIndentLevel()
    def getSectionLabel(self): return self.parent.getSectionLabel()
    def getRenderedText(self,renderContext,skipLabel=False):
        """Get the text for this item, rendered according to the provided context."""
        paragraphs = self.getParagraphs(renderContext,skipLabel=skipLabel)
        #merge paragraphs, where possible
        mergedParagraphs = [paragraphs[0]]
        for p in paragraphs[1:]:
            if not mergedParagraphs[-1].merge(p): mergedParagraphs.append(p)
            pass
        return "\n".join(p.getRenderedText() for p in mergedParagraphs)
    def getParagraphs(self, renderContext, skipLabel=False):
        """Get list of paragraph text-blocks for this item, rendered according to the current context.  Gets overridden in certain subclasses to reflect different paragraph breakdown (e.g., in TextItems)"""
        return self.subParagraphs(renderContext)
    def getSubParagraphs(self,renderContext):
        paragraphs = []
        for c in self.items: paragraphs += c.getParagraphs(renderContext)
        return paragraphs

class SectionItem(BaseItem):
    """Class for a section / subsection / etc."""
    def __init__(self, parent, tree):
        self.parent = parent
        self.tree = tree
        #TODO : extract the section label code from the tree, if present

        if tree.labels == None: self.sectionLabel = None
        else:
            self.sectionLabel = None
            try:self.sectionLabel = SectionLabelLib.SectionLabel(labelList=tree.labels) #contruct a SectionLabel object from the labels parameter of the node, if present
            except Exception,e: showError("Error parsing sectionLabel: ["+ str(e) +"]",location=self)
        #extract marginal note and label, if present
        self.marginalNote = None
        self.labelString = None #string labelling this particular element (e.g., "(ii.1)")
        self.historicalNote = None
        subsecs = self.extractMetaData() #fill in prior variables, leaving any remaining nodes to process
        self.finalizeSectionLabel() 
        
        #handle other subitems, which should all be types of sections or blocks of text
        self.items = []
        self.handleSubsections(subsecs)
        #TODO : confirm consistency of section label code and label constructed from label strings

        pass
    
    def handleSubsections(self, subsecs):
        for child in subsecs:
            if child.tag == "definition": self.items.append(DefinitionItem(parent=self,tree=child)) #this is first, so that definitions are parsed a DefinitionItems rather than generic SectionItems, despite being a sectionType
            elif child.tag in sectionTypes: self.items.append(SectionItem(parent=self,tree=child)) #other types of section, include formuladefinition
            elif child.tag in formulaSectionTypes: self.items.append(SectionItem(parent=self,tree=child))
            elif child.tag == "formulagroup": self.items.append(FormulaItem(parent=self,tree=child)) #top level for a formula --- handled specially so we can extract the formula itself
            elif child.tag in textTypes: self.items.append(TextItem(parent=self,tree=child)) #tags that encapsulate only text
            elif child.tag == "a":
                txt = child.getRawText().strip().lower()
                if txt != "previous version":
                    showError("Unknown <a> tag: ["+txt+"]",location=self)
                pass
            elif isinstance(child,XMLStatParse.TextNode): #raise an exception if we are ignoring any raw text
                if child.getRawText().strip() != "": showError("Text appearing directly in a section: ["+child.getRawText()+"]",location=self)
            else: showError("Unknown tag: [" + repr(child) + "]", location=self)
            pass
        return
    
    def extractMetaData(self):
        """Extract information on section label / marginal note, and returns the list of remaining subitems to be processed."""
        subsecs = [] #TODO: factor this out into a method that can be overriden for definitions
        for child in self.tree:
            if child.tag == "marginalnote": self.marginalNote = child.getRawText().strip()
            elif child.tag == "label": #the final mark for this section (e.g., (ii.1))
                if self.labelString != None: showError("Label encountered after another label. ["+ self.labelString +"]["+child.getRawText().strip()+"]",location=self)
                self.labelString = child.getRawText().strip()
                if len(subsecs) > 0: showError("Label encountered after other text ["+ self.labelString +"]["+str(subsecs)+"]",location=self)
            elif child.tag == "formulaterm": #the letter being defined in a formula definition section
                if self.labelString != None: showError("Formula term label encountered after another label. ["+ self.labelString +"]["+child.getRawText().strip()+"]",location=self)
                self.labelString = child.getRawText().strip()
                if len(subsecs) > 0: showError("Formula term label encountered after other text ["+ self.labelString +"]["+str(subsecs)+"]",location=self)
            elif child.tag == "historicalnote": self.historicalNote = child.getRawText().strip() #TODO: improve handling of historical notes!
            elif isinstance(child,XMLStatParse.TextNode) and child.getRawText() == "": pass #ignore whitespace textnodes
            else:
                subsecs.append(child)
                pass
        return subsecs
    
    def finalizeSectionLabel(self):
        """Method that verifies and/or sets the SectionLabel object for the section by looking at the parent section label and the labelString provided for this object.  If the underlying node did not have a code attribute, a SectionLabel is simply constructed by appending the current label to the parent's SectionLabel."""
        #TODO: Fill this in, so all can have sectionlabels!
        #create imputed SL from parent
        selfType = self.tree.tag  #derive the type of the new Numbering type to add to the label from the tag
        if selfType in formulaSectionMap: selfType = formulaSectionMap[selfType]
        if self.labelString != None: cleanLabel = self.labelString.strip("().")
        else: cleanLabel = u""
        if self.parent != None: imputedSL = self.parent.getSectionLabel().addLabel(selfType, cleanLabel)
        else: imputedSL = SectionLabelLib.SectionLabel(labelList=[(selfType,cleanLabel)])
        
        currentSL = self.getSectionLabel()
        if currentSL != None: #compare with SL derived from the xml tag, if one exists, and show error on mismatch
            if currentSL != imputedSL:
                showError("Inconsistent labelling ["+currentSL.getDisplayString()+"]["+imputedSL.getDisplayString()+"]",location=self)
                pass
        else: #otherwise use the imputed SL
            self.sectionLabel = imputedSL
        return
    
    def getMarginalNote(self):
        return self.marginalNote
    pass

    def getSectionLabel(self): return self.sectionLabel #the section label object pinpointing this provision
    def getLabelString(self): return self.labelString #the top-level string tag labeling this provision (appearing at the start of text)
    def getIndentLevel(self):
        sl = self.getSectionLabel()
        if sl == None: return self.parent.getIndentLevel() #return the parent's level, if there's no section label here
        return sl.indentLevel()
    def getParagraphs(self,renderContext, skipLabel=False):
        #paragraphs of a section consist of the marginal note, the label and paragraphs from any subobjects
        paragraphs = []
        needForce = True #need to explicitly force a new paragraph on a subitem paragraph
        if self.marginalNote != None: paragraphs.append(Paragraph(text=self.marginalNote, renderContext=renderContext, isMarginalNote=True)); needForce = False
        if not skipLabel:
            if self.getLabelString() != None: paragraphs.append(Paragraph(text=renderContext.boldText(self.getLabelString()), renderContext=renderContext,forceNewParagraph=True, indentLevel=self.getIndentLevel(), softSpace=True) ); needForce = False
        paragraphs += self.getSubParagraphs(renderContext)
        if needForce and len(paragraphs) > 0: paragraphs[0].forceNewParagraph = True #force a new paragraphs to start if not already accomplished by label string or marginal note
        return paragraphs

class DefinitionItem(SectionItem):
    """Special subclass for handling definitions.
    (By overriding extractMetaData, provides special handling for the marginal notes, which have a different format within definitions, as well as for labels, which are indicated by a definedtermen tag within the definition)."""
    def __init__(self, parent, tree):
        SectionItem.__init__(self,parent, tree)
        self.definedTerms = [] #collect list of all terms defined in this definition section
        for item in self.items: 
            if isinstance(item,TextItem): self.definedTerms += item.getDefinedTerms()
            pass
        return 
    
    def extractMetaData(self):
        """Extract information on section label / marginal note, and returns the list of remaining subitems to be processed.
        This overrides the normal meta-data extraction, since definitions shouldn't have labels but have differently tagged marginal notes.
        """
        subsecs = [] #TODO: factor this out into a method that can be overriden for definitions
        for child in self.tree:
            if child.tag == "marginalnote":
                tmp = child.englishMarginalText()
                if tmp != None and self.marginalNote != None: showError("Multiple marginal notes: [" + self.marginalNote + "][" + tmp +"]",location=self)
                self.marginalNote = tmp
            #elif child.tag == "definedtermen": self.labelString = child.getRawText()
            elif child.tag == "historicalnote": self.historicalNote = child.getRawText() #I don't think there should ever be historical notes to definition sections.
            else:
                subsecs.append(child)
                pass
        return subsecs
    def getParagraphs(self,renderContext, skipLabel = False):
        paragraphs =  self.getSubParagraphs(renderContext)
        if len(paragraphs) > 0: paragraphs[0].forceNewParagraph = True
        return paragraphs
    
    pass

class FormulaItem(SectionItem):
    """Top level item for a formula group.  Handles the initial formula. These items have "Formula" groups instead of Labels, and are at the same section label as preceding text (but force a new paragraph). The Formula sub-items are handled as ordinary sections."""
    def __init__(self, parent, tree):
        self.parent = parent
        self.tree = tree
        
        self.marginalNote = None
        self.formulaString = None
              
        subsecs = self.extractMetaData()
        self.items = []
        self.handleSubsections(subsecs)
        return
    
    def getFormulaString(self): return self.formulaString
    def separateLabelLine(self): return True #the "label" of the formula should be pushed to its own line (as well as starting a new paragraph)
    
    def extractMetaData(self):
        """Extract information on section label / marginal note, and returns the list of remaining subitems to be processed."""
        subsecs = [] #TODO: factor this out into a method that can be overriden for definitions
        for child in self.tree:
            if child.tag == "marginalnote": self.marginalNote = child.getRawText().strip()
            elif child.tag == "formula":
                if self.formulaString != None: showError("formulaString encountered after another. ["+ self.formulaString +"]["+child.getRawText().strip()+"]",location=self)
                self.formulaString = child.getRawText().strip()
                if len(subsecs) > 0: showError("formulaString encountered after other text ["+ self.formulaString +"]["+str(subsecs)+"]",location=self)
            #elif child.tag == "historicalnote": self.historicalNote = child.getRawText().strip() #TODO: improve handling of historical notes!
            elif isinstance(child,XMLStatParse.TextNode) and child.getRawText() == "": pass #ignore whitespace textnodes
            else:
                subsecs.append(child)
                pass
            pass
        return subsecs
    
    def getIndentLevel(self): return self.parent.getIndentLevel()
    def getSectionLabel(self): return self.parent.getSectionLabel()
    def getParagraphs(self,renderContext, skipLabel = False):
        paragraphs = []
        paragraphs.append(Paragraph(text=renderContext.boldText(self.getFormulaString()), renderContext=renderContext,forceNewParagraph=True, indentLevel=self.getIndentLevel()) )
        followers = self.getSubParagraphs(renderContext)
        if len(followers) > 0: followers[0].forceNewParagraph = True
        return paragraphs + followers

class TextItem(BaseItem):
    """Class for a blob of text, possibly with embedded links and other decorations.  Is called on nodes of the tree which just embed text, and not further subsection.
    Text inside the TextItem is stored as a linked list of Piece objects."""
    def __init__(self,parent,tree):
        self.parent = parent
        self.tree = tree
        self.definedTerms = [] #list of defined terms appearing in this text block
        self.firstPiece = Piece(self) #dummy piece to start linked list
        self.lastPiece = self.firstPiece
        self.processTree(self.tree)
        for p in self.firstPiece:
            if p.getDefinedTerm() != None: self.definedTerms.append(p.getDefinedTerm())
        return
    
    def addPiece(self,piece):
        """Adds a new piece after the current last piece."""
        self.lastPiece.setNextPiece(piece)
        self.lastPiece = piece
        return
    
    def processTree(self,tree,stack=None):
        if stack == None: stack = [] #create stack on initial call
        if len(stack) > 100: raise StatuteException("Stackoverflow")
        stack.append(tree.tag)
        for item in tree: #iterate over the subitems
            if item.tag == "definedtermen":
                self.addPiece(DefinedTermPiece(parent=self,text=item.getRawText().strip()))
            elif item.tag == "xrefexternal":
                self.addPiece(LinkPiece(parent=self,text=item.getRawText(),target=None))
            elif isinstance(item,XMLStatParse.TextNode):  #TextNode correspond to text in the xml file.  Only include if we are inside aof <Text> tags.
                txt = item.getRawText().strip() #to strip off leading/trailing spaces / new lines
                if txt == "": continue
                if "text" in stack: self.addPiece(TextPiece(parent=self,text=txt))
                elif "oath" in stack: self.addPiece(TextPiece(parent=self,text=txt))
                elif "formulaconnector" in stack: self.addPiece(TextPiece(parent=self,text=txt))
                else:
                    showError("Unprocessed text: [TXT: "+ txt + "][STACK: "+str(stack)+"]",location=self) #if we are ignoring non-trivial text, raise an exception so we know there is more to handle.
                pass
            elif item.tag in sectionTypes or item.tag in formulaSectionTypes: showError("Found a section label in text: ["+item.tag+"]",location=self)
            else:
                self.processTree(tree=item,stack=stack) #otherwise recurse down to the contents of this item.
        stack.pop()
        return
    def getParagraphs(self, renderContext):
        pieceIterator = iter(self.firstPiece)
        indentLevel = self.getIndentLevel()
        paragraphs = []
        try: #get the paragraph for the initial piece to populate list
            firstPiece = pieceIterator.next()
        except StopIteration:
            return [] #there were no Pieces to iterate over, so there are no paragraphs to return
        firstParagraph = Paragraph(text=firstPiece.getText(renderContext),renderContext=renderContext,indentLevel=indentLevel)
        paragraphs = [firstParagraph]
        for piece in pieceIterator:
            nextParagraph = Paragraph(text=piece.getText(renderContext),renderContext=renderContext,indentLevel=indentLevel)
            if not paragraphs[-1].merge(nextParagraph): paragraphs.append(nextParagraph) #either merge or add paragraph
        return paragraphs
    def getDefinedTerms(self):
        return self.definedTerms
    pass

#####
#
# Piece classes, used to represent the parts of text in a TextItem
#
####

class Piece(object):
    def __init__(self,parent,previousPiece=None,nextPiece=None):
        self.parent = parent
        if previousPiece == None: self.previousPiece = None
        else: self.setPreviousPiece(previousPiece)
        if nextPiece == None: self.nextPiece = None
        else: self.setNextPiece(nextPiece)
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
    def getText(self, renderContexte): return u""
    def IsAlnumStart(self): return False #does piece start with an alphanumeric character
    def eatsSpace(self): return True #spaces following this piece should disappear (because )
    def previousEatsSpace(self):
        """Returns True if the previousPiece exists and eats soft leading spaces."""
        if self.previousPiece == None: return True
        return self.previousPiece.eatsSpace()
    def nextIsAlnumStart(self):
        """Returns True if the nextPiece exists and has an alphanumeric start (or other start that results in adding a soft space after current piece)."""
        if self.nextPiece == None: return False
        return self.nextPiece.isAlnumStart()
    def softInitialSpace(self): return (u"" if self.previousEatsSpace() else u" ")
    def softTrailingSpace(self): return (u" " if self.nextIsAlnumStart() else u"")
    def getDefinedTerm(self): return None
    pass

class TextPiece(Piece):
    def __init__(self,parent, text,previousPiece=None,nextPiece=None):
        Piece.__init__(self,parent=parent, previousPiece=previousPiece, nextPiece=nextPiece)
        if "\n" in text: showError("Newline inside text piece.", location = self)
        self.text = text
        return
    def objName(self):
        return u"<TextPiece: [" + self.text + "]>"
    def getText(self,renderContext): return self.text
    def isAlnumStart(self):
        if len(self.text) == 0: return self.nextIsAlnumStart() #empty text pieces should have the effect of the piece on the other side.
        if len(self.text) == 0 or not self.text[0].isalnum(): return False
        return True
    def eatsSpace(self):
        if len(self.text) == 0: return self.previousEatsSpace()
        return False
    pass

class DefinedTermPiece(Piece):
    def __init__(self, parent, text, previousPiece=None,nextPiece=None):
        Piece.__init__(self,parent=parent,previousPiece=previousPiece,nextPiece=nextPiece)
        self.definedTerm = text
        return
    def objName(self):
        return u"<DefinedTermPiece: [" + self.definedTerm + "]>"
    def getText(self,renderContext=None):
        return self.softInitialSpace() + renderContext.boldText("\"" + self.definedTerm + "\"") + self.softTrailingSpace()
    def isAlnumStart(self): return True
    def eatsSpace(self): return True
    def getDefinedTerm(self): return self.definedTerm
    pass

class LinkPiece(Piece):
    """Class for a link in the text."""
    def __init__(self, parent,text, target = None,previousPiece=None,nextPiece=None):
        Piece.__init__(self,parent=parent,previousPiece=previousPiece,nextPiece=nextPiece)
        self.text=text
        self.target=target
        return
    def __repr__(self):
        return u"<LinkPiece: [" + self.text + "]>"
    def getText(self,renderContext): return self.softInitialSpace() + self.text + self.softTrailingSpace() #TODO: return context and target appropriate link text
    def isAlnumStart(self):
        if len(self.text) == 0 or not self.text[0].isalnum(): return False
        return True
    def eatsSpace(self): return False
    pass

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

#class MarginalItem(StatuteItem):
#    """Class for a marginal note, attached to a SectionItem."""
#    pass
#
#class NoteItem(StatuteItem):
#    """Class for an historical note attached to the end of a section."""
#    pass

class Statute(object):
    """Class that encapsulating a xml statute in a usable form.
    Based on the XMLStatuteParser, but processes the raw tree output to make it more usable."""
    def __init__(self,data):
        p = XMLStatParse.XMLStatuteParser()
        p.feed(data)
        dataTree = p.getTree()
        self.sectionList = None #list of the top level section items in the Statute
        self.identTree = dataTree["statute"]["identification"]
        self.contentTree = dataTree["statute"]["body"]
        self.processStatuteData(self.identTree)
        self.processStatuteContents(self.contentTree)
        return
    
    def processStatuteData(self,tree):
        """Process the "identification" portion of the XML to gather data about the statute (title, etc)."""
        self.shortTitle = tree["shorttitle"].getRawText().strip()
        self.longTitle = tree["longtitle"].getRawText().strip()
        self.chapter = tree["chapter"].getRawText().strip()
        #determine page name prefix for pages of this instrument
        #TODO - have a global mapping that lets us override this where desired
        self.prefix = self.shortTitle
        return

    def titleString(self):
        """String giving the title of the statute."""
        print "Title: " + self.longTitle + " (a/k/a " + self.shortTitle + ") " + self.chapter
    
    def reportString(self):
        return self.titleString() + "\n" + ", ".join(c.labelString for c in self.sectionList)
    
    def __repr__(self):
        return "<" + self.titleString() + ">"
        
    def processStatuteContents(self,tree):
        self.sectionList = [] #list of top level sections contained in statute
        
        #iterate over subitems and add all sections to self.sectionList
        for item in tree: 
            if item.tag == "": continue #top level textnodes are ignored
            #if item is a type of section
            elif item.tag == "section":
                self.processSection(item)
            #if item is a type of heading
            elif item.tag == "heading":
                self.processHeading(item)
            #other cases
            else: print "Unknown tag seen at top level: [" + item.tag + "]"
            pass
        #build dictionary pointing to the different sections by name
        #TODO
        return

    def processSection(self,item):
        """Processes the Node for an act section (as well as subsection, etc), and add to the Statute's structure of sections."""
        #call process section on the item, with a fake parent, then extract the item and add it to the Statute's section list
        section = SectionItem(parent=None,tree=item)
        self.sectionList.append(section)
        return

    def processHeading(self,item):
        """Process the Node for a heading."""
        #close off prior heading at same level or above
        #create the heading object and add to list
        #TODO: Need to implement this -- requires updating the sectionlabel library first
        return

    def renderPages(self): #TODO: clean this up
        for sec in self.sectionList:
            self.renderPage(sec)
        return
    def renderPage(self,sec):
        lab = sec.labelString
        f = file("Pages/" + self.prefix + " " + lab,"w")
        f.write(sec.getRenderedText(RenderContext.WikiContext,skipLabel=True).encode("utf-8"))
        f.close()
        pass    

    pass
