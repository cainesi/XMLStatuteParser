import XMLStatParse
import RenderContext
import sys

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

#TODO: get label for defintion section (out of first text piece)
#TODO: labels should be output in wikioutput.
#TODO: correct unnecessary spaces appearing at certain points.
#TODO: marks on Items when they should start a new paragraph
#TODO: fix for definitions where there are multiple defined term strings

STRICT = False
def showError(s, location = None):
    if location != None:
        while True:
            if hasattr(location, "getSectionLabel"):
                s += "@<" + str(location.getSectionLabel()) + ">"
                break
            if not hasattr(location, parent): break
            location = location.parent
            pass
        pass
    if STRICT: raise StatuteException(s)
    else: sys.stderr.write("WARNING: <" + s + ">\n")


class StatuteException(Exception): pass
sectionTypes = ["section","subsection","paragraph","subparagraph","clause","subclause","subsubclause"]
textTypes = ["text","continuedsectionsubsection","continuedparagraph","continuedsubparagraph","continuedclause","continueddefinition", "oath" ]

class BaseItem(object):
    """Superclass for all items in the statute structure, with some general purpose methods of handling section labels, etc."""
    def getSectionLevel(self): return self.parent.getSectionLevel()
    def getSectionLabel(self): return self.parent.getSectionLabel()
    def getRenderedText(self,renderContext,skipLabel=False):
        pieces = self.getRenderedPieces(renderContext,skipLabel=skipLabel)
        if pieces[0] == "": pieces = pieces[1:]
        return "\n".join(pieces)
    def getRenderedPieces(self, renderContext, skipLabel=False):
        level = self.getSectionLevel()
        textList = [u""]
        softSpace = False #space should be inserted before next merge, if leading character is alphanumeric
        if not skipLabel:
            txt = self.getRenderedLabel()
            if txt != None: textList[0] += renderContext.boldText(self.getRenderedLabel())
            softSpace = True
            #TODO: should we make the labels just ordinary text, or is it important to handle them specially so they can be carved out when necessary?
            pass
        for c in self.items:
            levtmp = c.getSectionLevel()
            rp = c.getRenderedPieces(renderContext)
            if levtmp != level: #if the level has changed with the next object, then we need to start new paragraph
                textList.append(renderContext.renderPlainText(rp[0],levtmp)) #change this method to "indentText"?
                textList += rp[1:]
                level == levtmp
                softSpace = False
                pass
            elif c.forceNewParagraph():
                textList.append(renderContext.renderPlainText(rp[0],levtmp)) #change this method to "indentText"?
                textList += rp[1:]
                level == levtmp
                softSpace = False
            else: #make a continuation of the trailing paragraph, adding a space if necessary to separate words
                if softSpace and len(rp[0]) > 0 and rp[0][0].isalnum(): textList[-1] += " " + rp[0]
                else: textList[-1] += rp[0]
                textList += rp[1:]
                softSpace = False
                pass
            pass
        #if textList[0] == "": textList = textList[1:]
        return textList
    def forceNewParagraph(self): return False #returns True if the text of this item must start with a new paragraph

class SectionItem(BaseItem):
    """Class for a section / subsection / etc."""
    def __init__(self, parent, tree):
        self.parent = parent
        self.tree = tree
        #TODO : extract the section label code from the tree, if present
        self.sectionLabel = None
        self.sectionLabel = tree.sectionLabel

        #extract marginal note and label, if present
        self.marginalNote = None
        self.labelString = None
        self.historicalNote = None
        subsecs = self.extractMetaData()

        #handle other subitems, which should all be types of sections or blocks of text
        self.items = []
        for child in subsecs:
            if child.tag in sectionTypes: self.items.append(SectionItem(parent=self,tree=child))
            elif child.tag == "definition": self.items.append(DefinitionItem(parent=self,tree=child))
            elif child.tag in textTypes: self.items.append(TextItem(parent=self,tree=child))
            elif child.tag == "a":
                txt = child.getRawText().strip().lower()
                if txt != "previous version":
                    showError("Unknown <a> tag: ["+txt+"]",location=self)
                pass
            elif isinstance(child,XMLStatParse.TextNode): #raise an exception if we are ignoring any raw text
                if child.getRawText().strip() != "": showError("Text appearing directly in a section: ["+child.getRawText()+"]",location=self)
            else: showError("Unknown tag: [" + repr(child) + "]", location=self)
            pass
        #TODO : confirm consistency of section label code and label constructed from label strings
        pass
    
    def extractMetaData(self):
        """Extract information on section label / marginal note, and returns the list of remaining subitems to be processed."""
        subsecs = [] #TODO: factor this out into a method that can be overriden for definitions
        for child in self.tree:
            if child.tag == "marginalnote": self.marginalNote = child.getRawText()
            elif child.tag == "label": self.labelString = child.getRawText()
            elif child.tag == "historicalnote": self.historicalNote = child.getRawText() #TODO: improve handling of historical notes!
            else:
                subsecs.append(child)
                pass
        return subsecs
    
    def getMarginalNote(self):
        return self.marginalNote
    pass

    def getSectionLabel(self): return self.sectionLabel
    def getSectionLevel(self): return len(self.getSectionLabel()) #TODO: there should be multiple length measures for the labels (including / not including defs, etc.)
    def getRenderedLabel(self):
        if self.labelString == None: return None
        return self.labelString
    def forceNewParagraph(self): return True #returns True if the text of this item must start with a new paragraph

class DefinitionItem(SectionItem):
    """Special subclass for handling definitions.
    (By overriding extractMetaData, provides special handling for the marginal notes, which have a different format within definitions, as well as for labels, which are indicated by a definedtermen tag within the definition)."""
    def __init__(self, parent, tree):
        SectionItem.__init__(self,parent, tree)
        #extract labelString from first TextItem in the definition
        for item in self.items:
            if isinstance(item,TextItem) and item.labelString != None: self.labelString = item.labelString; break
            pass
        return 
    
    def extractMetaData(self):
        """Extract information on section label / marginal note, and returns the list of remaining subitems to be processed."""
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
    def getRenderedLabel(self):
        if self.labelString == None: return None
        return "\"" + self.labelString + "\""
    pass


class TextItem(BaseItem):
    """Class for a blob of text, possibly with embedded links and other decorations.
    Text inside the TextItem is stored as a linked list of Piece objects."""
    def __init__(self,parent,tree):
        self.parent = parent
        self.tree = tree
        self.labelString = None
        self.pieces = [] #TODO: replace this with linked list of TextPiece objects
        self.processTree(self.tree)
        return
    
    def processTree(self,tree,stack=None):
        if stack == None: stack = [] #create stack on initial call
        if len(stack) > 100: raise StatuteException("Stackoverflow")
        stack.append(tree.tag)
        for item in tree: #iterate over the subitems
            if item.tag == "definedtermen":
                if self.labelString == None: self.labelString = item.getRawText()
                else: showError("Found definition label where label already exists: ["+self.labelString+ "]["+item.getRawText()+"]", location = self)
            elif item.tag == "xrefexternal":
                self.pieces.append(" ")
                self.pieces.append(LinkItem(parent=self,text=item.getRawText(),target=None))
                self.pieces.append(" ")
            elif isinstance(item,XMLStatParse.TextNode):  #TextNode correspond to text in the xml file.  Only include if we are inside aof <Text> tags.
                txt = item.getRawText().strip()
                if "text" in stack: self.pieces.append(item.getRawText().strip())
                else:
                    if txt != "": showError("Unprocessed text: ["+ txt + "]["+str(stack)+"]",location=self) #if we are ignoring non-trivial text, raise an exception so we know there is more to handle.
                pass
            else:
                self.processTree(tree=item,stack=stack) #otherwise recurse down to the contents of this item.
        stack.pop()
        return
    
    def getRenderedPieces(self, renderContext):
        #TODO: Need to do more sophisticated processing, so that different types of text can be appropriately rendered       
        return ["".join(unicode(c) for c in self.pieces)]
    pass

class Piece(object):
    def __init__(self,parent,previousPiece=None,nextPiece=None):
        self.parent = parent
        self.previousPiece = previousPiece
        self.nextPiece = nextPiece
        return
    #TODO: code for manipulating the linked list
    pass

class DefinedTermPiece(BaseItem):
    pass

class BoldItem(BaseItem):
    """Item representing text that should be presented in bold --- mainly quoted defined terms."""
    pass

class LinkItem(BaseItem):
    """Class for a link in the text."""
    def __init__(self, parent,text, target = None):
        self.parent=parent
        self.text=text
        self.target=target
        return
    pass
    def __unicode__(self):
        return self.text

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
        #TODO: Fill this in
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
