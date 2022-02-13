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


import HTMLParser, re
import xsutil #code to interfact with external C-code library
from ErrorReporter import showError

#The module provides code that converts an xml file representing a statute (as found in the Justice Department website) and creates an in-memory representation of it that can be taken as input by the statute parsing code in the Statute module.

# HACK -- the HTMLParser isn't really a xml parser (most notably, not case sensitive) -- should update this to use xml.parsers.expat

class XMLStatException(Exception):
    """Exception thrown by XML-statute parsing code."""
    pass

def attrsToDict(attrs):
    """converts the attrs parameters received by methods of HTMLParser into dictionaries."""
    return dict(attrs)

#examle of the text parsed by following method
#se=&quot;2&quot;,ss=&quot;1&quot;,df=&quot;{producer organization}{association de producteurs}&quot;    
defPat = re.compile("\{(?P<english>[^}]*)\}\{(?P<french>[^}]*)\}$")
def parseCodeParam(code):
    """Parses a (unicode) "code" parameters used in XML statutes into a list of 2-types (level, value).
    Code assuems that any special html-encoded characters in the string have already been unescaped to unicode."""
    levelList = []
    #print code.__repr__()
    codeItems = xsutil.commaSplit(code)
    #print codeItems
    for item in codeItems:
        l = item.split("=")
        if len(l) != 2: raise XMLStatException("Equals Problem: " + str((code,item,l)))
        level = l[0]
        val = l[1]
        #lval = val.split("&quot;") #if quotes are un-escaped
        lval = val.split("\"") #if quotes are escaped -- codes in attributes are apparently automaticall un-escaped
        if len(lval) != 3 or lval[0] != "" or lval[2] != "": raise XMLStatException("Value Problem: " + str((code,item,lval)))
        value = lval[1]
        if level == "df":
            m = defPat.match(value)
            if m == None: raise XMLStatException("Definition Problem: " + str((code,item,value)))
            value = m.group("english")
        if u" to " in value or u" and " in value: value = value.split()[0] #fix certain tag referencing multiple sections (usually for repeals of subsections)
        value = value.strip("()") #sometimes there are stray parentheses around the number (usually also seems to be associated with repealed provisions)
        levelList.append((level, value))
        pass
    #print levelList
    return levelList

def indentString(s):
    """Indents every (\\n-separated) line of a string by one space."""
    return " " + s.replace("\n", "\n ")

#objects for the in-memory tree representation of the xml file
class Node(object):
    def __init__(self, tag, attrs, rawText):
        self.tag = tag
        self.attrs = attrs
        self.labels = None #the raw list of label tuples
        if "code" in self.attrs: self.labels = parseCodeParam(self.attrs["code"])
        else: self.labels = None
        
        self.rawText = rawText #the text used -- so we can reconstruct the initial xml structure with minimal changes
        self.children = []
        return
    def __len__(self): return len(self.children)
    def __getitem__(self,n):
        """Get nth subobject of the Node, if n is a string, else returns the first subnode with tag n, if n is a strong"""
        if isinstance(n,int): return self.children[n]
        elif isinstance(n, str) or isinstance(n,unicode):
            n = n.lower() #parsed tag names are all lower case
            for c in xrange(0,len(self.children)):
                if isinstance(self.children[c], Node) and self.children[c].tag == n: return self.children[c]
                pass
            raise KeyError("KeyError: " + unicode(n))
        raise XMLStatException("Node getitem only works with int, string or unicode")
    def __contains__(self, tag):
        for c in xrange(0,len(self.children)):
            if isinstance(self.children[c],Node) and self.children[c].tag == tag: return True
            pass
        return False
    def __str__(self):
        l = []
        l.append( "<" + self.baseStr() + ">" + str(self.attrs) )
        for n in xrange(0, len(self.children)):
            l.append( ("% 2d. "%n) + self.children[n].baseStr() )
        return "\n".join(l)
    def __repr__(self):
        return "<" + self.baseStr() + ">"
    def __iter__(self):
        """Return an iterator over the *children* of this node."""
        return self.children.__iter__()
    def treeWalk(self):
        """Returns an iterator over a depth-first walk of the items under this node."""
        for child in self.children:
            yield child
            for c in child.treeWalk():
                yield c
            pass
        return
    def baseStr(self):
        return "[Node: " + self.tag + "]"
    def getTag(self):
        return self.tag
    def getXML(self):
        """Returns XML representation of Node.
        This consists of the Node's tag's rawText, plus the xml of children, plus (if the tag was not a startend tag) the closing tag text."""
        #TODO: check how this interacts with startend tags
        if self.rawText[-2] == "/" and len(self.children) > 0: raise XMLStatException("[XMLStat NOTICE Unexpected children: %s]"%self.rawText)
        return self.rawText + "".join(c.getXML() for c in self.children) + ("</" + self.rawText[1:1+len(self.tag)] + ">" if self.rawText[-2] != "/" else "")
    def getPrettyXML(self):
        """Similar to getXML, but includes newlines and indentation in xml output, to make it easier to read."""
        if self.rawText[-2] == "/" and len(self.children) > 0: raise XMLStatException("[XMLStat NOTICE Unexpected children: %s]"%self.rawText)
        return self.rawText + ("\n" if len(self.children)>0 else "") + "\n".join(indentString(c.getPrettyXML()) for c in self.children)+ ("\n</" + self.rawText[1:1+len(self.tag)] + ">" if self.rawText[-2] != "/" else "")

    def addChild(self,node):
        """Add a child node to this Node."""
        self.children.append(node)
        return
    def getRawText(self):
        """Returns the plain text contents of the Node (and any subnodes), stripping leading/trailing spaces on internal text chunks.  Therefore the rawText will not necessarily have the correct spacing, since it will not have implied spaces from tags."""
        return "".join(c.getRawText() for c in self.children)
    def getSpacedRawText(self):
        """Returns the plain text contents of Node (and subnode), including implied spaces where a tagged piece of text is immediately next to an alphanumeric character."""
        l = [c.getSpacedRawText() for c in self.children]
        total = "."
        for s in l:
            if len(s) == 0: continue
            if total[-1].isalnum() and s[0].isalnum(): total += " " + s
            else: total += s
            pass
        return total[1:]
        
    def englishMarginalText(self):
        """Returns the subtext of this node included in DefinedTermEn tags, otherwise returns None."""
        if self.tag != "marginalnote": raise XMLStatException("Can only call englishMarginalText on MarginalNote items. [" + self.__repr__() + "]")
        isEnglish = False
        addSpace = False
        margTxt = u""
        for i in self:
            if i.tag == "definedtermen":
                isEnglish = True
                margTxt += " " + i.getRawText().strip()
                addSpace = True
            elif isinstance(i,TextNode): margTxt += (" " if addSpace else "") + i.getRawText().strip(); addSpace = False
        if isEnglish: return margTxt.strip()
        else: return None
    pass
    
class BaseNode(Node):
    """Class for the top-level object in XML tree structure.  The parser seeds its tree with one of these."""
    def __init__(self):
        Node.__init__(self,"","",None)
        return
    def getXML(self): return "".join(c.getXML() for c in self.children)
    def getPrettyXML(self): return "".join(c.getPrettyXML() for c in self.children)
    def baseStr(self): return "[Base node]"

class TextNode(Node):
    """A class to represent information other than tags included in an XML file.  I.e., all the raw text."""
    def __init__(self,text,original = None):
        """text is the unicode text that should be output in other contexts.  original is the original text used used in the node, where different (e.g., if originally escaped characters have been converted)."""
        if original != None: Node.__init__(self, "", {}, original)
        else: Node.__init__(self,"",{}, text)
        self.text = text
        self.original = original
        return
    def __str__(self): return "[Textnode: " + self.text + "]"
    def __repr__(self): return "<" + self.baseStr() + ">"
    def __len__(self): return 0
    def __getitem__(self,n): raise XMLStatException("TextNode does not have subitems.")
    def __iter__(self): raise XMLStatException("Cannot iterate over subitems of TextNode.")
    def baseStr(self): return "[Textnode: " + self.text[:40].__repr__() + "]"
    def getXML(self):
        if self.original != None: return self.original
        return self.text
    def getPrettyXML(self): return self.getXML()
    def getRawText(self):
        """Returns the raw text in the node, except that if the node is nothing but whitespace, returns empty string."""
        #TODO: maybe should just strip off trailing newlines?
        if self.text.strip() == u"": return u""
        return self.text
    def getSpacedRawText(self): return self.getRawText()
    def addChild(self,node): raise XMLStatException("Cannot add children to TextNode.")
    pass
        
class PINode(object):
    """Class for holding a processor directive.  ** Not currently used **"""
    def __init__(self, data):
        self.data = data
        return
    def __str__(self): return "[PI: " + self.data + "]"
    def baseStr(self): return "[PI]"
    def getXML(self): return "<?" + self.data +">"
    pass

class XMLStatuteParser(HTMLParser.HTMLParser):
    """Object to parse the Statute XML file into a structure of nested dictionaries."""
    def __init__(self, data=None):
        HTMLParser.HTMLParser.__init__(self)
        #setup the parser
        self.tree = BaseNode() #base of the tree object
        self.stack = [self.tree] #stack of Node objects leading to the Node to which the next object should be added
        if data != None: self.feed(data)
        return
    def reset(self):
        HTMLParser.HTMLParser.reset(self)
        self.tree = BaseNode()
        self.stack = [self.tree]
        return
    def feed(self,data):
        """Decodes the input string to unicode, assuming it is UTF-8, to avoid internal problems with HTMLParser.
        (In particular, the internal workings of the parser can sometimes cause a straight cast to unicode, which fails if the data contains non-ASCII characters.  See http://bugs.python.org/issue3932)."""
        HTMLParser.HTMLParser.feed(self,data.decode("utf-8"))
        return
    def inBody(self):
        for c in self.stack:
            if c.tag == "body": return True
            pass
        return False
    def handle_starttag(self,tag,attrs):
        rawText = self.get_starttag_text()
        newNode = Node(tag, attrsToDict(attrs), rawText)
        self.stack[-1].addChild(newNode)
        self.stack.append(newNode)
        return
    def handle_endtag(self,tag):
        while self.stack[-1].getTag() != tag: self.stack.pop() #implicitly code any open tags that do not match the one being closed
        self.stack.pop() #remove the node explicitly being closed
        return
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        self.handle_endtag(tag)
        return
    def handle_data(self,data):
        newNode = TextNode(data)
        self.stack[-1].addChild(newNode)
        return
    def handle_entityref(self,name):
        #handle certain entities by converting them into plain ascii text
        if name == "amp": self.handle_data("&")
        elif name =="gt": self.handle_data(">")
        else: showError("Entity Reference: [%s]" %name, header ="XMLStat Warning")
        return
    def handle_charref(self,name):
        print showError("Char Reference: [%s]"%name, header ="XMLStat Warning")
        return
    def handle_comment(self,data):
        #ignore comments
        return
    def handle_decl(self,decl):
        print showError("Declaration: [%s]" %decl, header ="XMLStat Warning")
        return
    def handle_pi(self,data):
        if len(self.stack) != 1: showError("Processing Instruction: [%s]" % data, header ="XMLStat Warning") #ignore top-level processing instructions
        return
    def getTree(self):
        return self.tree
    pass
    
class ActPruner(HTMLParser.HTMLParser):
    """Prunes an xml Act object, so that it only contains the section indicated by the provided label list (corresponding to output of the codeParse method) and the "identification" section.  It does this by keeping track of which tags in the stack have already been written out.  When a new tag is added, a check is done of whether it is one that should be written.  If so, then that tag, and any as yet unwritten tags on the stack, are all added to the tree at once."""
    def __init__(self, labels,data=None):
        HTMLParser.HTMLParser.__init__(self)
        #setup the parser
        self.tree = BaseNode() #base of the tree object
        self.tree.forceAddToTree=False
        self.tree.isWritten=True
        self.stack = [self.tree] #stack of Node objects leading to the Node to which the next object should be added        
        self.labels = labels
        if data != None: self.feed(data)
        return
    def feed(self,data):
        """Converts input string to unicode, to avoid internal problems with HTMLParser.
        (In particular, the internal workings of the parser can sometimes cause a cast to unicode, which fails if the data contains non-ASCII characters.  See http://bugs.python.org/issue3932)."""
        HTMLParser.HTMLParser.feed(self,data.decode("utf-8"))
        return
    def checkForceAddToTree(self,node):
        """Checks whether the Node at top of stack is one that should force writing to the tree for itself, sub-nodes and containing nodes."""
        if node.tag == "identification": return True
        elif node.labels == None: return False
        else:
            if len(self.labels) > len(node.labels): return False
            for n in xrange(0, len(self.labels)):
                if node.labels[n] != self.labels[n]: return False
            return True
            pass
    def forceAddToTree(self):
        """Return True if the node at the top of the stack is one that should be written in the final structure (because it or a parent has forceAddToTree set)."""
        for c in self.stack:
            if c.forceAddToTree: return True
        return False
    def flushStack(self):
        """Adds all currently un-added nodes from the stack to the self.tree structure, and marks them as written."""
        #check if top of the stack is forceAddToTree, and if so flush everything to the tree.
        if self.forceAddToTree():
            for n in xrange(len(self.stack)-1,-1,-1):
                if self.stack[n].isWritten: return #return once we've found something already written
                self.stack[n].isWritten = True #mark node as written, and add to the stack element above --- this will eventually add the chain onto the stack.
                self.stack[n-1].addChild(self.stack[n])
            pass
        return
    def handle_starttag(self,tag,attrs):
        rawText = self.get_starttag_text()
        newNode = Node(tag, attrsToDict(attrs), rawText)
        newNode.isWritten = False #whether Node has been written
        newNode.forceAddToTree = self.checkForceAddToTree(newNode) #whether presence of node forces writing
        #self.stack[-1].addChild(newNode)
        self.stack.append(newNode)
        self.flushStack() #add any required Nodes to the tree
        return
    def handle_endtag(self,tag):
        while self.stack[-1].getTag() != tag: self.stack.pop() #implicitly code any open tags that do not match the one being closed
        self.stack.pop() #remove the node explicitly being closed
        return
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        self.handle_endtag(tag)
        return
    def handle_data(self,data, original = None):
        newNode = TextNode(data, original)
        if self.forceAddToTree(): self.stack[-1].addChild(newNode)
        return
    def handle_entityref(self,name):
        #handle certain entities by converting them into plain ascii text
        original = "&" + name + ";"
        if name == "amp": self.handle_data("&", original=original)
        else:
            self.handle_data(original)
            print showError("Entity Reference: [%s]" %name, header="XMLStat Warning") #report that we are seeing an entity reference that is not handled
        return
    def handle_charref(self,name):
        original = "&#" + name + ";"
        if False:
            #handle char refs that are converted
            pass
        else:
            self.handle_data(original)
            print showError("Char Reference: [%s]" %name, header="XMLStat Warning")
        return
    def handle_comment(self,data):
        #ignore comments for the moment
        return
    def handle_decl(self,decl):
        print showError("Declaration: [%s]" %decl, header="XMLStat Warning")
        return
    def handle_pi(self,data):
        if len(self.stack) != 1: print showError("Processing Instruction: [%s]" % data, header="XMLStat Warning") #ignore top-level processing instructions
        return
    def getTree(self):
        return self.tree
    def getPrunedXML(self):
        return self.tree.getXML()
    def getPrunedPrettyXML(self):
        return self.tree.getPrettyXML()
    pass

    
