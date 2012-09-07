# $Id$
# $URL$

import os
import XMLStatParse
import RenderContext
from Constants import sectionTypes, formulaSectionTypes, formulaSectionMap, textTypes, knownTextTags, textTriggers
import Constants
import SectionLabelLib
from ErrorReporter import showError
import textutil
from StatutePart import StatutePart

#workflow for parsing statute:
# 1) parse xml into tree structure
# 2) walk the tree-structure to extract section structure and extract particular types of data
#   2a) Labels
#   2b) Definitions
#   2c) Marginal notes
#   2d) Historical notes
#   2e) Tables (?)
# 3) Create various meta data for Statute (e.g., section ordering information)
# 4) Walk structure to detect defined terms / defined term applicability
# 5) Detect cross-references and insert applicable links
# 6) Output wikipages

#TODO:
# bump indent level when one forumladefinition is nested inside another?
# deal with headings in the statute / division identifications
# have every item (etc) know what statute it is a part of
# headings in the regulations take the place of some marginalnotes
# 

class StatuteException(Exception): pass

#####
#
# Items, which represent parts of the parsed statute structure
#
####

class BaseItem(StatutePart):
    """Superclass for all items in the statute structure, with some general purpose methods of handling section labels, etc."""
    def __init__(self, parent, tree, statute = None):
        StatutePart.__init__(self,parent=parent,statute=statute)
        self.tree = tree
        self.items = []
        return
    def getStatute(self): return self.statute #statute with which item is associated
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
        return self.getSubParagraphs(renderContext)
    def getSubParagraphs(self,renderContext):
        paragraphs = []
        for c in self.items: paragraphs += c.getParagraphs(renderContext)
        return paragraphs
    def extractMetaData(self):
        """Extracts meta data from the item's tree, and returns a list of subnodes other than those providing metadata."""
        return [item for item in self.tree]
    def handleSubsections(self, subsecs):
        """Handles the subsections of the section that are left over after extractMetaData has done its work.  Called by items that may have subsections."""
        for child in subsecs:
            if child.tag == "definition": self.items.append(DefinitionItem(parent=self,tree=child)) #this is first, so that definitions are parsed a DefinitionItems rather than generic SectionItems, despite being a sectionType
            elif child.tag in sectionTypes: self.items.append(SectionItem(parent=self,tree=child)) #other types of section, include formuladefinition
            elif child.tag in formulaSectionTypes: self.items.append(SectionItem(parent=self,tree=child))
            elif child.tag == "formulagroup": self.items.append(FormulaItem(parent=self,tree=child)) #top level for a formula --- handled specially so we can extract the formula itself
            elif child.tag == "provision": self.items.append(TextItem(parent=self,tree=child,forceNewParagraph=True)) #provision tags only appear in ITA 211.1, this provides an acceptable way of displaying them
            elif child.tag == "readastext": self.items.append(ReadAsItem(parent=self,tree=child))
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

class SectionItem(BaseItem):
    """Class for a section / subsection / etc."""
    def __init__(self, parent, tree, statute=None):
        BaseItem.__init__(self,parent,tree,statute)
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
        self.repealed = False
        subsecs = self.extractMetaData() #fill in prior variables, leaving any remaining nodes to process
        self.finalizeSectionLabel() 
        #handle other subitems, which should all be types of sections or blocks of text
        self.handleSubsections(subsecs)
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
            elif child.tag == "repealed":
                self.repealed = True
                subsecs.append(child) #don't ignore 
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
        if u" to " in cleanLabel or u" and " in cleanLabel: cleanLabel = cleanLabel.split(" ")[0].strip("()") #if label string contains a connector, only look at first part (this typically happen for repealed groups of sections)
        
        if self.parent != None: imputedSL = self.parent.getSectionLabel().addLabel(selfType, cleanLabel)
        else: imputedSL = SectionLabelLib.SectionLabel(labelList=[(selfType,cleanLabel)])
        
        currentSL = self.getSectionLabel()
        if currentSL != None: #compare with SL derived from the xml tag, if one exists, and show error on mismatch
            if not currentSL.quasiEqual(imputedSL):
                showError("Inconsistent labelling, Current:["+currentSL.getDisplayString()+"] Imputed["+imputedSL.getDisplayString()+"]",location=self)
                pass
        else: #otherwise use the imputed SL
            self.sectionLabel = imputedSL
        return
    def getMarginalNote(self):
        return self.marginalNote
    def getSectionLabel(self):
        """Returns this item's sectionLabel, or the parent's, if sectionLabel not yet assigned."""
        if hasattr(self,"sectionLabel"): return self.sectionLabel #the section label object pinpointing this provision
        else: return self.parent.getSectionLabel()
    def getLabelString(self): return self.labelString #the top-level string tag labeling this provision (appearing at the start of text)
    def getIndentLevel(self):
        sl = self.getSectionLabel()
        if sl == None: return self.parent.getIndentLevel() #return the parent's level, if there's no section label here
        return sl.indentLevel()
    def getParagraphs(self,renderContext, skipLabel=False):
        #paragraphs of a section consist of the marginal note, the label and paragraphs from any subobjects.  Label is skipped if "skipLabel" is set to True
        paragraphs = []
        needForce = True #need to explicitly force a new paragraph on a subitem paragraph
        if self.marginalNote != None: paragraphs.append(Paragraph(text=self.marginalNote, renderContext=renderContext, isMarginalNote=True)); needForce = False
        if not skipLabel:
            if self.getLabelString() != None: paragraphs.append(Paragraph(text=renderContext.boldText(self.getLabelString()), renderContext=renderContext,forceNewParagraph=True, indentLevel=self.getIndentLevel(), softSpace=True) ); needForce = False
        paragraphs += self.getSubParagraphs(renderContext)
        if needForce and len(paragraphs) > 0: paragraphs[0].forceNewParagraph = True #force a new paragraphs to start if not already accomplished by label string or marginal note
        return paragraphs
    pass

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
        if len(paragraphs) > 0: paragraphs[0].forceNewParagraph = True #force first paragraph, if any, to start a new paragraph
        return paragraphs
    pass

class FormulaItem(SectionItem):
    """Top level item for a formulagroup node.  Handles the initial formula. These items have "Formula" groups instead of Labels, and are at the same section label as preceding text (but force a new paragraph). The Formula sub-items are handled as ordinary sections."""
    def __init__(self, parent, tree):
        BaseItem.__init__(self,parent,tree) #Hack --- not calling the right initializer for this object, we want SectionItem methods, but not all the initialization
        
        self.marginalNote = None
        self.formulaString = None
              
        subsecs = self.extractMetaData()
        self.handleSubsections(subsecs)
        return
    
    def getFormulaString(self):
        if self.formulaString == None:
            #showError("Formula without formula string",location=self) #this is not an error -- sometimes the variables are discussed in text, or the formula is given is a seperate part of the text from the variables.
            return ""
        return self.formulaString
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

class ReadAsItem(BaseItem):
    """Class representing a read-as text block. """
    def __init__(self, parent, tree):
        BaseItem.__init__(self,parent,tree)
        sections = self.extractSectionSubtree(tree) #the subtree of the sections being read-as
        self.handleSubsections(sections)
        return
    def getSectionLabel(self): return self.parent.getSectionLabel()
    
    def extractSectionSubtree(self,tree):
        """Returns the subtree of a readastext tree that contains section data."""
        sectionPieces = []
        sections = []
        for node in tree:
            if isinstance(node,XMLStatParse.TextNode):
                if node.getRawText().strip() != "": showError("Text found in a readastext: ["+node.getRawText()+"]",location=self)
            elif node.tag == "sectionpiece": sectionPieces.append(node)
            else:
                if node.tag in sectionTypes or node.tag == "formulagroup": sections.append(node)
                else: showError("Bad node found in readastext: ["+node.getTag()+"]",location=self)
            pass
        if len(sectionPieces) > 1: showError("Multiple sectionpieces found in readastext: ["+ str(len(sectionPieces))+"]",location=self)
        elif len(sectionPieces) == 0:
            if len(sections) > 0:
                showError("No sectionpieces found in readas, but direct sections found",location=self)
                return sections
            else: showError("Nothing found in readastext",location=self)
        if len(sections) > 0: showError("Both sections and sectionpieces found in readastext",location=self)
        sectionPiece = sectionPieces[0]
        sections = []
        for node in sectionPiece:
            if isinstance(node,XMLStatParse.TextNode):
                if node.getRawText().strip() != "": showError("Text found in a sectionpiece: ["+node.getRawText()+"]",location=self)
            elif node.tag in sectionTypes: sections.append(node)
            elif node.tag == "formulagroup" or node.tag == "provision": sections.append(node)
            else: showError("Bad node found in sectionpiece: ["+node.getTag()+"]",location=self)
            pass
        if len(sections) < 1: showError("No sections found in sectionpiece: ["+ str(len(sections))+"]",location=self)
        return sections


class TextItem(BaseItem):
    """Class for a blob of text, possibly with embedded links and other decorations.  Is called on nodes of the tree which just embed text, and not further subsection.
    Text inside the TextItem is stored as a linked list of Piece objects."""
    def __init__(self,parent,tree,forceNewParagraph = False):
        BaseItem.__init__(self,parent,tree)
        self.forceNewParagraph = forceNewParagraph #force this TextItem to start a new paragraph
        self.firstPiece = textutil.Piece(self,isSpaced=False) #dummy piece to start linked list
        self.lastPiece = self.firstPiece
        self.processTree(self.tree)
        self.text, self.decorators = self.firstPiece.assembleText()
        
        self.definedTerms = [] #list of defined terms appearing in this text block
        #for p in self.firstPiece:  #TODO: instead of this, need to extract defined terms from the applicable decorators
        #    if p.getDefinedTerm() != None: self.definedTerms.append(p.getDefinedTerm())
        
        return
    
    @staticmethod
    def isWrittenText(stack):
        for tag in stack:
            if tag in textTriggers: return True
        return False
        
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
                self.addPiece(textutil.DefinedTermPiece(parent=self,text=item.getRawText().strip()))
            elif item.tag == "xrefexternal":
                self.addPiece(textutil.LinkPiece(parent=self,text=item.getRawText(),target=None))
            elif item.tag =="xrefinternal":
                self.addPiece(textutil.LinkPiece(parent=self,text=item.getRawText(),target=None))
            elif isinstance(item,XMLStatParse.TextNode):  #TextNode correspond to text in the xml file.  Only include if we are inside aof <Text> tags.
                txt = item.getRawText().strip() #to strip off leading/trailing spaces / new lines
                if txt == "": continue
                if self.isWrittenText(stack): self.addPiece(textutil.TextPiece(parent=self,text=txt))
                else:
                    showError("Unprocessed text: [TXT: "+ txt + "][STACK: "+str(stack)+"]",location=self) #if we are ignoring non-trivial text, raise an exception so we know there is more to handle.
                pass
            elif item.tag in sectionTypes or item.tag in formulaSectionTypes: showError("Found a section label in text: ["+item.tag+"]",location=self)
            else:
                if item.tag not in knownTextTags: showError("Unknown tag found in text: ["+item.tag+"]", location=self)
                self.processTree(tree=item,stack=stack) #otherwise recurse down to the contents of this item.
        stack.pop()
        return
    def getDecoratedText(self, renderContext):
        """Returns the items text, with the Decorator objects applied to the applicable portions."""
        #self.decorators.sort() #todo, write code so that decorator list always sorted and never has overlaps?
        ptr = 0
        textList = []
        for dec in self.decorators:
            if dec.getStart() < ptr: raise StatuteException("Decorators out of order!")
            textList.append(self.text[ptr:dec.getStart()])
            textList.append(dec.getDecoratedText(renderContext=renderContext,textFull=self.text))
            ptr = dec.getEnd()
            pass
        textList.append(self.text[ptr:])
        return u"".join(textList)
    def getParagraphs(self, renderContext):
        """Return the rendered text of this item bundled into a list of Paragraph objects."""
        indentLevel = self.getIndentLevel() 
        return [Paragraph(text=self.getDecoratedText(renderContext),renderContext=renderContext,indentLevel=indentLevel,forceNewParagraph=self.forceNewParagraph)]
    def getDefinedTerms(self):
        return self.definedTerms
    pass

#####
#
# Paragraph class, used for formatted text output from Items
#
####

class Paragraph(object):
    """Class for encapsulating a (part of a) paragraph of rendered text, along with logic for determining when paragraphs can be connected, and outputing final results."""
    def __init__(self,text, renderContext,indentLevel = 0,isMarginalNote = False, forceNewParagraph=False, softSpace=False):
        """text - the raw text of the paragraph
        renderContext
        indentLevel - level to which the text should be indented
        isMarginalNote - True if this paragraph should be rendered as a marginal note
        forceNewParagraph - True if this paragraph should not be added to the end of the prior paragraph, even if at the same leve
        softSpace - True if a space should be added to the end of this paragraph before merging with a alphanumeric-started paragraph."""
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
        #TODO - when merging a length-0 paragraph, we should presumably maintain our softSpace rule (or do an "or"?).  There shouldn't be length-0 paragraphs though.
        if self.softSpace: spacer = (u" " if (len(nextParagraph.text) > 0 and nextParagraph.text[0].isalnum()) else u"")
        else: spacer = u""
        self.text += spacer + nextParagraph.text
        self.softSpace = nextParagraph.softSpace
        return True
    def getRenderedText(self):
        if not self.isMarginalNote:
            return self.renderContext.indentText(self.text, level = self.indentLevel)
        return self.renderContext.renderMarginalNote(self.text)


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
        self.instrumentType = None
        self.enablingAuthority = None
        if "statute" in dataTree:
            self.instrumentType = "statute"
            self.mainPart = dataTree["statute"]
        elif "regulation" in dataTree:
            self.instrumentType = "regulation"
            self.mainPart = dataTree["regulation"]
        else:
            raise StatuteException("Cannot find any instrument in file.")
        
        self.sectionList = None #list of the top level section items in the Statute
        self.identTree = self.mainPart["identification"]
        self.contentTree = self.mainPart["body"]
        self.processStatuteData(self.identTree)
        self.processStatuteContents(self.contentTree)
        return
    
    def processStatuteData(self,tree):
        """Process the "identification" portion of the XML to gather data about the statute (title, etc)."""
        self.shortTitle = tree["shorttitle"].getRawText().strip()
        self.longTitle = tree["longtitle"].getRawText().strip()
        if self.instrumentType == "statute":
            self.citationString = tree["chapter"].getRawText().strip()
        elif self.instrumentType == "regulation":
            self.citationString = tree["instrumentnumber"].getRawText().strip()
            self.enablingAuthority = tree["enablingauthority"].getRawText().strip()
        #determine page name prefix for pages of this instrument
        #TODO - have a global mapping that lets us override this where desired
        self.prefix = self.shortTitle
        return

    def titleString(self):
        """String giving the title of the statute."""
        print ": " + self.longTitle + " (a/k/a " + self.shortTitle + ") " + self.getCitationString()
    
    def getTypeString(self):
        if self.instrumentType == "statute": return "Statute"
        elif self.instrumentType == "regulation": return "Regulation"
        else: raise StatuteException("No typeString because instrument has no type.")
    
    def getCitationString(self):
        return self.citationString
    
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
        #TODO structures pointing to sections by name, organizing them, etc.
        return

    def processSection(self,item):
        """Processes the Node for an act section (as well as subsection, etc), and add to the Statute's structure of sections."""
        #call process section on the item, with a fake parent, then extract the item and add it to the Statute's section list
        section = SectionItem(parent=None,tree=item, statute=self) #TODO: instead make parent=self, so statute determined automatically?
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
        lab = sec.getSectionLabel()[0].getIDString()
        f = file(os.path.join(Constants.PAGEDIR, self.prefix) + " " + lab,"w")
        f.write(sec.getRenderedText(RenderContext.WikiContext,skipLabel=True).encode("utf-8"))
        f.close()
        pass    

    pass
