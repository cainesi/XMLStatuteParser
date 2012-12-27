#$Id$
__author__ = 'caines'

#Module that encapsulates information about known statutes, sections within them.

#For each Statute, should have: location of the file for that statute, certain metadata about the file (at least: when downloaded, the currency as reported on the justice website, short name of the statute, page-prefix for statute, and relationship to other instruments (e.g., whether the document represents regulations for a specified statute, etc.). A list of sections within the statute.

#Could include code here to automate downloading & archiving of statutes from justice.


import pickle, shutil
import Constants

class StatuteIndexException(Exception): pass


def storeIndex(index):
    tmpName = Constants.INDEXFILE+".tmp"
    f = file(tmpName,"w"); pickle.dump(index,f); f.close()
    shutil.move(tmpName,Constants.INDEXFILE) #only move file into position once fully written (to avoid leaving a half-written/corrupt index file)
    return

def loadIndex():
    f = file(Constants.INDEXFILE,"r"); index = pickle.load(f); f.close()
    return index

class StatuteIndex(object):
    """Class for representing list of all the statutes we are handling."""
    def __init__(self):
        self.statuteDataDict = {}
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
    def __init__(self,name,prefix,fname,url,act=None,reg=None):
        """
        fname - file where xml representation of statute is stored.
        url - url where statute can be obtained
        name - the name of statute (serves as the key by which it is accessed in all these methods
        act - the name of the statute that is "the Act" for this instrument (if any)
        reg - the name of the statute that is "the regulations" for this instrument (if any)
        """
        #following contain metadata about the section contents of the statute and should be updated each time the statute is parsed.
        self.name = name
        self.prefix=prefix
        self.fname = fname
        self.url = url
        self.act = act
        self.reg = reg
        self.sLDict = None #dictionary indexed by sL objects of sections in this statute
        self.sectionNameDict = None #dictionary indexed by the string labels of sections in this statute
        self.linksDict = None #dictionary of external links -- indexed by external statute name, then by target sL, then a list of source sLs in this Statute.
        return

    def getName(self): return self.name
    def getPrefix(self): return self.prefix
    def getAct(self): return self.act
    def getReg(self): return self.reg
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