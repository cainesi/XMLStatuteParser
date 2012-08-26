import HTMLParser, re
import Constants, SectionLabelLib
from csv import reader

#code to interfact with external C-code library

"""code to parse an (english) XML statute obtained from the justice department website"""

#To do list:
# finish the pruning code
# handle the sections

# -- when doing this we probably don't need the dynamic-programming labelling system, as we can infer labelling from the XML tagging
#Need code for extracting specific sections/subparts from a big XML document, so we can analyze something big like the ITA!
#Should move this into a separate project


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
    """parses a (unicode) "code" parameters used in XML statutes into a list of 2-types (level, value)"""
    levelList = []
    #codeItems = code.split(",")
    print code.__repr__()
    codeItems = reader([code]).next() #uses CSV module to split line by commas outside quotes -- problem: doesn't work with unicode
    #print code
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
        levelList.append((level, value))
        pass
    return levelList

def indentString(s):
    return " " + s.replace("\n", "\n ")

#objects for the in-memory tree representation of the xml file
class Node(object):
    def __init__(self, tag, attrs, rawText):
        self.tag = tag
        self.attrs = attrs
        self.labels = None
        if "code" in self.attrs:
            #print self.attrs
            self.labels = parseCodeParam(self.attrs["code"])
            #print self.labels
            pass
        self.rawText = rawText #the text used -- so we can reconstruct the initial html structure with minimal changes
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
    def __str__(self):
        l = []
        l.append( "<" + self.baseStr() + ">" + str(self.attrs) )
        for n in xrange(0, len(self.children)):
            l.append( ("% 2d. "%n) + self.children[n].baseStr() )
        return "\n".join(l)
    def __repr__(self):
        return "<" + self.baseStr() + ">"
    def baseStr(self):
        return "[Node: " + self.tag + "]"
    def getTag(self):
        return self.tag
    def getXML(self):
        """Returns HTML representation of object"""
        #TODO: check how this interacts with startend tags
        if self.rawText[-2] == "/" and len(self.children) > 0: raise XMLStatException("[NOTICE Unexpected children: %s]"%self.rawText)
        return self.rawText + "".join(c.getXML() for c in self.children) + ("</" + self.tag + ">" if self.rawText[-2] != "/" else "")
    def getPrettyXML(self):
        if self.rawText[-2] == "/" and len(self.children) > 0: raise XMLStatException("[NOTICE Unexpected children: %s]"%self.rawText)
        return self.rawText + ("\n" if len(self.children)>0 else "") + "\n".join(indentString(c.getPrettyXML()) for c in self.children)+ ("\n</" + self.tag + ">" if self.rawText[-2] != "/" else "")
        return
    def getRawText(self):
        """Returns the plain text contents of the Node (and any subnodes)."""
        return "".join(c.getRawText() for c in self.children)
    def addChild(self,node):
        """Add a child node to this Node."""
        self.children.append(node)
        return
    pass
    
    
class BaseNode(Node):
    """Class for the top-level object in XML tree structure.  The parser seeds its tree with one of these."""
    def __init__(self):
        Node.__init__(self,"","",None)
        return
    def getXML(self): return "".join(c.getXML() for c in self.children)
    def getPrettyXML(self): return "".join(c.getPrettyXML() for c in self.children)
    def baseStr(self): return "[Base node]"

class TextNode(object):
    """A class to represent information other than tags included in an XML file.  I.e., all the raw text."""
    def __init__(self,text,original = None):
        """text is the unicode text that should be output in other contexts.  original is the original text used used in the node, where different (e.g., if originally escaped characters have been converted)."""
        self.text = text
        self.original = original
        return
    def __str__(self): return "[Textnode: " + self.text + "]"
    def baseStr(self): return "[Textnode: " + self.text[:40].__repr__() + "]"
    def getXML(self): 
        if self.original != None: return self.original
        return self.text
    def getPrettyXML(self): return self.getXML()
    def getRawText(self): return self.text
    pass
        
class PINode(object):
    """Class for holding a processor directive.  ** Not currently used **"""
    def __init__(self, data):
        self.data = data
        return
    def __str__(self): return "[PI: " + self.getHTML() + "]"
    def baseStr(self): return "[PI]"
    def getXML(self): return "<?" + self.data +">"


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
        """Converts input string to unicode, to avoid internal problems with HTMLParser.
        (In particular, the internal workings of the parser can sometimes cause a cast to unicode, which fails if the data contains non-ASCII characters.  See http://bugs.python.org/issue3932)."""
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
        else: print "[NOTICE Entity Reference: %s]" %name
        return
    def handle_charref(self,name):
        print "[NOTICE Char Reference: %s]" %name
        return
    def handle_comment(self,data):
        #ignore comments
        return
    def handle_decl(self,decl):
        print "[NOTICE Declaration: %s]" %decl
        return
    def handle_pi(self,data):
        if len(self.stack) != 1: print "[NOTICE Processing Instruction: %s]" % data #ignore top-level processing instructions
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
        """Return True if the node at the top of the stack is one that should be written in the final structure (because it or a parent has forceAddToTree set."""
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
            print "[NOTICE Entity Reference: %s]" %name #report that we are seeing an entity reference that is not handled
        return
    def handle_charref(self,name):
        original = "&#" + name + ";"
        if False:
            #handle char refs that are converted
            pass
        else:
            self.handle_data(original)
            print "[NOTICE Char Reference: %s]" %name
        return
    def handle_comment(self,data):
        #ignore comments for the moment
        return
    def handle_decl(self,decl):
        print "[NOTICE Declaration: %s]" %decl
        return
    def handle_pi(self,data):
        if len(self.stack) != 1: print "[NOTICE Processing Instruction: %s]" % data #ignore top-level processing instructions
        return
    def getTree(self):
        return self.tree
    def getPrunedXML(self):
        return self.tree.getHTML()
    def getPrunedPrettyXML(self):
        return self.tree.getPrettyXML()
    pass

#testing code
if __name__ == "__main__":
    f = file(Constants.ACTFILE,"r"); data = f.read(); f.close()
    if False: #test of parseCode method
        teststr = "se=&quot;2&quot;,ss=&quot;1&quot;,df=&quot;{producer organization}{association de producteurs}&quot;"
        print parseCode(teststr)
    if False: #test parsing of simple xml file
        f = file("Tests/simple_parse.xml","r"); data = f.read(); f.close()
        p = XMLStatuteParser()
        p.feed(data)
        t = p.getTree()
    if True: #test on initial actfile
        p = XMLStatuteParser()
        p.feed(data)
        t = p.getTree()
    pass
    
