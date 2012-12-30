#$Id$
__author__ = 'caines'

#Module that encapsulates information about known statutes, sections within them.
#StatuteIndex is initialized from the stat_config.txt file, which tells it what statutes are available and the url locations, and some information about their relationships.
#Meta-data, if any, is then stored in a file [name].data, and a bundle of the xml contents are stored in [name].bundle

#For each Statute, should have: location of the file for that statute, certain metadata about the file (at least: when downloaded, the currency as reported on the justice website, short name of the statute, page-prefix for statute, and relationship to other instruments (e.g., whether the document represents regulations for a specified statute, etc.). A list of sections within the statute.

#Could include code here to automate downloading & archiving of statutes from justice.


import pickle, shutil, re
import Constants

class StatuteIndexException(Exception): pass
linePat = re.compile("(?P<tag>[^:]*):\s*\"(?P<value>[^\"]*)\"")

def storeIndex(index):
    tmpName = Constants.INDEXFILE+".tmp"
    f = file(tmpName,"w"); pickle.dump(index,f); f.close()
    shutil.move(tmpName,Constants.INDEXFILE) #only move file into position once fully written (to avoid leaving a half-written/corrupt index file)
    return

def loadIndex():
    f = file(Constants.INDEXFILE,"r"); index = pickle.load(f); f.close()
    return index

def removeComment(line):
    """Removes the part of line after "#" and returns line."""
    n = line.find("#")
    if n == -1: return line
    return line[:n]

def processLine(line):
    origLine = line
    line = removeComment(line)
    line = line.strip()
    if line == "": return None, None
    m = linePat.match(line)
    if m is None: raise StatuteIndexException("Bad line in " + Constants.STATUTECONFIGFILE +":[" + origLine + "]")
    return (m.group("tag").lower(), m.group("value"))

class StatuteIndex(object):
    """Class for representing list of all the statutes we are handling."""
    def __init__(self):
        self.statuteDataDict = {}
        self.loadConfig() #populate self.statuteDataDict with objects for the statutes of interest
        return
    def loadConfig(self):
        """Processes th stat_config.txt file, and creates a StatuteData object for each of the specified statutes."""
        f = file(Constants.STATUTECONFIGFILE,"r"); lines = [c for c in f]; f.close()
        curStat = None
        lineno = 0
        for line in lines:
            lineno += 1
            tag, value = processLine(line)
            if tag is None: continue
            elif tag == "name":
                if value in self.statuteDataDict: raise StatuteIndexException("Error in " + Constants.STATUTECONFIGFILE +", duplicate definition of name [line:" + str(lineno) + "][" + line + "]")
                curStat = StatuteData(value)
                self.statuteDataDict[value] = curStat
                pass
            elif curStat is None: raise StatuteIndexException("Error in " + Constants.STATUTECONFIGFILE +", value specified before any name [line:" + str(lineno) + "][" + line + "]")
            elif tag == "url": curStat.setUrl = value
            elif tag == "act": curStat.setAct = value
            elif tag == "reg": curStat.setReg = value
            else: raise StatuteIndexException("Error in " + Constants.STATUTECONFIGFILE +", unknown tag type [line:" + str(lineno) + "][" + line + "]")
            return
        return
    def addStatuteData(self, statuteData):
        """Adds a StatuteData object to the index.  Throws exception if we already have a Statute with the specified name."""
        name = statuteData.getName()
        if name in self.statuteDataDict: raise StatuteIndexException("Duplicated StatuteData name: " + name)
        self.statuteDataDict[name] = statuteData
        return
    def getStatuteData(self,name):
        """Returns the StatuteData object for the named statute."""
        return self.statuteDataDict[name]
    def getLinksToSection(self,name,sL):
        """Returns a list of all sections, from any source, linking to a specified sL (or sub-sL of that sL) the named statute."""
        linkList = []
        #TODO - write this
        return linkList


    pass


#TODO - implement a more sophisticated serializer for StatuteData objects?

class StatuteData(object):
    """Class for storing metadata about a statute."""
    def __init__(self,name,prefix=None,url=None,act=None,reg=None):
        """
        name - the name of statute (serves as the key by which it is accessed in all these methods
        prefix - prefix used for pages of this statute, by default equal to name
        url - url where statute can be obtained
        act - the name of the statute that is "the Act" for this instrument (if any)
        reg - the name of the statute that is "the regulations" for this instrument (if any)
        """
        #following contain metadata about the section contents of the statute and should be updated each time the statute is parsed.
        self.name = name
        if self.prefix is None: self.prefix = self.name
        else: self.prefix=prefix
        self.act = act
        self.reg = reg
        self.url = url
        self.sLDict = None #dictionary indexed by sL objects of sections in this statute
        self.sectionNameDict = None #dictionary indexed by the string labels of sections in this statute
        self.linksDict = None #dictionary of external links -- indexed by external statute name, then by target sL, then a list of source sLs in this Statute.



        return
    def __str__(self): return "<StatuteData: name:["+ str(self.name)+"] url:["+str(self.url)+"]>"

    def getName(self): return self.name
    def getPrefix(self): return self.prefix
    def setAct(self,actName):
        if self.act is not None: raise StatuteIndexException("Setting act when act already specified ["+str(self)+"]["+self.act+"]["+actName+"]")
        self.act = actName
    def getAct(self): return self.act
    def setReg(self, regName):
        if self.reg is not None: raise StatuteIndexException("Setting reg when act already specified ["+str(self)+"]["+self.reg+"]["+regName+"]")
        self.reg = regName
    def getReg(self): return self.reg
    def setUrl(self, url):
        if self.url is not None: raise StatuteIndexException("Setting url when act already specified ["+str(self)+"]["+self.url+"]["+url+"]")
        self.url = url
    def getUrl(self): return self.url
    def setSLDict(self,sLDict):
        """Sets the sLDict for this statute."""
        self.slDict = sLDict
        return
    def setSectionNameDict(self,sectionNameDict):
        """Sets the sectionNameDict for this statute."""
        self.sectionNameDict = sectionNameDict
        return
    def setLinks(self, linksDict):
        """Set the linksDict for this Statute."""
        self.linksDict = linksDict
        return
    pass