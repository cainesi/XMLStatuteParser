#$Id$
__author__ = 'caines'

#Module that encapsulates information about known statutes, sections within them.
#StatuteIndex is initialized from the stat_config.txt file, which tells it what statutes are available and the url locations, and some information about their relationships.
#Meta-data, if any, is then stored in a file [name].data, and a bundle of the xml contents are stored in [name].bundle

#For each Statute, should have: location of the file for that statute, certain metadata about the file (at least: when downloaded, the currency as reported on the justice website, short name of the statute, page-prefix for statute, and relationship to other instruments (e.g., whether the document represents regulations for a specified statute, etc.). A list of sections within the statute.

#Could include code here to automate downloading & archiving of statutes from justice.

#TODO: rename this StatuteMetaData, and include the DefinitionData object?

import pickle, shutil, re, os, datetime
import Constants, StatuteFetch, Statute, SectionLabelLib
from ErrorReporter import showError

class StatuteIndexException(Exception): pass
linePat = re.compile("(?P<tag>[^:]*):\s*\"(?P<value>[^\"]*)\"")

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
        self.statuteList = []
        self.loadConfig() #populate self.statuteDataDict with objects for the statutes of interest
        return
    def loadConfig(self):
        """Processes th stat_config.txt file, and creates a StatuteData object for each of the specified statutes."""
        f = open(Constants.STATUTECONFIGFILE,"r"); lines = [c for c in f]; f.close()
        curStat = None
        lineno = 0
        for line in lines:
            lineno += 1
            tag, value = processLine(line)
            #print((tag, value))

            if tag is None: continue
            elif tag == "name":
                if value in self.statuteDataDict: raise StatuteIndexException("Error in " + Constants.STATUTECONFIGFILE +", duplicate definition of name [line:" + str(lineno) + "][" + line + "]")
                curStat = StatuteData(index=self,name=value)
                self.statuteDataDict[value] = curStat
                self.statuteList.append(curStat.getName())
                pass
            elif curStat is None: raise StatuteIndexException("Error in " + Constants.STATUTECONFIGFILE +", value specified before any name [line:" + str(lineno) + "][" + line + "]")
            elif tag == "url": curStat.setUrl(value)
            elif tag == "act": curStat.setAct(value)
            elif tag == "reg": curStat.setReg(value)
            elif tag == "fileonly": curStat.setFileOnly()
            elif tag == "nocheck": curStat.setNoCheck()
            elif tag == "rawname": curStat.setRawName(value)
            else: raise StatuteIndexException("Error in " + Constants.STATUTECONFIGFILE +", unknown tag type [line:" + str(lineno) + "][" + line + "]")
            pass
        return
    def addStatuteData(self, statuteData):
        """Adds a StatuteData object to the index.  Throws exception if we already have a Statute with the specified name."""
        name = statuteData.getName()
        if name in self.statuteDataDict: raise StatuteIndexException("Duplicated StatuteData name: " + name)
        self.statuteDataDict[name] = statuteData
        return
    def getStatuteList(self):
        return [c for c in self.statuteList]
    def getStatuteData(self,name):
        """Returns the StatuteData object for the named statute.
        @type name: str
        @rtype: StatuteData"""
        return self.statuteDataDict[name]
    def getStatute(self,name):
        """Returns the Statute object representing the parsed statute.
        @rtype: Statute.Statute
        """
        return Statute.Statute(statuteName=name,statuteIndex=self)
    def __getitem__(self,name):
        """Allow StatuteData objects to be fetched with [] notation.
        @type statuteName: str
        @type statuteIndex: StatuteIndex
        @rtype: StatuteData
        """
        return self.getStatuteData(name)
    def getLinksToSection(self,name,sL):
        """Returns a list of all sections, from any source, linking to a specified sL (or sub-sL of that sL) the named statute."""
        linkList = []
        #TODO - write this
        return linkList
    pass


#TODO - implement a more sophisticated serializer for StatuteData objects?

class StatuteData(object):
    """Class for storing metadata about a statute."""
    def __init__(self,index,name,prefix=None,url=None,act=None,reg=None, fileOnly=False):
        """
        name - the name of statute (serves as the key by which it is accessed in all these methods
        prefix - prefix used for pages of this statute, by default equal to name
        url - url where statute can be obtained
        act - the name of the statute that is "the Act" for this instrument (if any)
        reg - the name of the statute that is "the regulations" for this instrument (if any)
        fileOnly - if True, this statute should only be loaded from disk, not the internet
        """
        #following contain metadata about the section contents of the statute and should be updated each time the statute is parsed.
        self.index = index
        self.name = name
        self.prefix = prefix
        if self.prefix is None: self.prefix = self.name #set prefix to name, if not otherwise set
        else: self.prefix=prefix
        self.act = act
        self.reg = reg
        self.url = url
        self.fileOnly = fileOnly
        self.bundle = None #the statute bundle for this statute, is set once loaded
        self.rawName = None #filename where XML content can be located on disk (only useful if fileOnly is set)
        self.noCheck = False #if True, then url will not be check if xml already available locally
        self.indexLoaded = False #Set to True once indexes have been loaded from file, if loading is successful
        self.sLDict = None #dictionary indexed by sL objects of sections in this statute
        self.sectionNameDict = None #dictionary indexed by the string labels of sections in this statute, and pointing to SLs
        self.linksDict = None #dictionary of external links -- indexed by external statute name, then by target sL, then a list of source sLs in this Statute.
        return
    def __str__(self): return "<StatuteData: name:["+ str(self.name)+"] url:["+str(self.url)+"]>"
    def getName(self): return self.name
    def getPrefix(self): return self.prefix
    def setAct(self,actName):
        if self.act is not None: raise StatuteIndexException("Setting act when act already specified ["+str(self)+"]["+self.act+"]["+actName+"]")
        self.act = actName
        return
    def getAct(self): return self.act
    def setReg(self, regName):
        if self.reg is not None: raise StatuteIndexException("Setting reg when act already specified ["+str(self)+"]["+self.reg+"]["+regName+"]")
        self.reg = regName
        return
    def getReg(self): return self.reg
    def setUrl(self, url):
        if self.url is not None: raise StatuteIndexException("Setting url when act already specified ["+str(self)+"]["+self.url+"]["+url+"]")
        self.url = url
        return
    def getUrl(self): return self.url
    def setRawName(self,rawName):
        self.rawName = rawName
        return
    def setFileOnly(self, fileOnly = True):
        """Set fileOnly (i.e., not to be fetched from url) flag for this statute, default to True."""
        self.fileOnly = fileOnly
        return
    def setNoCheck(self, noCheck = True):
        """Set noCheck (i.e., not to check url if statute available locally) flag for statute, default to True."""
        self.noCheck = noCheck
        return
    def getBundleName(self):
        """Returns the filename that should contain the bundle for this statute, if it exists."""
        return os.path.join(Constants.STATUTEDIR, self.name + ".bundle")
    def getBundleBackupName(self):
        """Returns the filename for a current back of the statue bundle."""
        return os.path.join(Constants.OLDSTATUTEDIR,self.name + ".bundle" + "-" + datetime.datetime.today().strftime("%Y-%m-%d+%Hh-%Mm-%Ss"))
    def getRawXML(self): self.getBundle(); return self.bundle["XMLDATA"]
    def getURL(self): self.getBundle(); return self.bundle["URL"]
    def getAmendDate(self): self.getBundle(); return self.bundle["AMEND"]
    def getCurrencyDate(self): self.getBundle(); return self.bundle["CURRENCY"]
    def getDownloadDate(self): self.getBundle(); return self.bundle["DOWNLOAD"].date()
    def getBundle(self, forceFetch = False):
        """Returns bundle for the statute.  If bundle had to be loaded from url, a copy is saved to local file.  When fetching, checks if a more recent version is posted.
        forceFetch - force retrieving XML from url
        updateCheck - if statute has been retrieved from file, check if update version online (default True)
        """
        if self.bundle is not None: return self.bundle

        fname = self.getBundleName()
        #try to open file:
        bundle = None
        try:
            bundle = StatuteFetch.openStatute(fname)
        except IOError:
            if self.fileOnly: #if file not available *and* we only want file, then package from rawXML if possible, otherwise raise exception.
                if self.rawName is None: raise StatuteIndexException("Error on forced read from file [" + self.name + "]")
                showError("Not statute file, attempting to package raw XML ["+self.name+"].",header="LOADING")
                self.bundle = StatuteFetch.packageFile(os.path.join(Constants.RAWXMLDIR,self.rawName),fname)
                return self.bundle
            pass
        readNew = False #have we read new XML data from the internet?
        if (bundle is None) or forceFetch: #nothing so far, so definitely need to read from url (or being forced to)
            showError("No file, fetching from url ["+self.name+"].",header="LOADING")
            bundle = StatuteFetch.fetchStatute(self.getUrl())
            showError("Statute loaded from url.", header="LOADING")
            readNew = True
            pass
        elif not self.noCheck: #we have the bundle locally, only check url if updateCheck is set
            showError("File present, checking for update ["+self.name+"].",header="LOADING")
            newData = StatuteFetch.readStatutePage(self.getUrl())
            if StatuteFetch.isStatDictUpdated(bundle,newData): showError("Update found, loading from url ["+self.name+"].",header="LOADING"); bundle = StatuteFetch.fetchStatute(self.getUrl()); readNew = True
            else: showError("No update found.", header="LOADING")
            pass
        else: pass
        if readNew: #if we have read a new statute from url, output a copy of bundle to back directory
            StatuteFetch.storeStatute(fname,sdict=bundle)
            StatuteFetch.storeStatute(self.getBundleBackupName(),sdict=bundle)
            pass
        self.bundle = bundle
        return self.bundle

    ###
    #
    # Methods for working with Statute metadata
    #
    ###

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
    def setIndices(self, sLDict=None,sectionNameDict=None,linksDict=None):
        """Set all the indices for statute at once, and store to file."""
        #TODO
        self.storeIndices()
        return
    def getIndexName(self):
        """Returns the filename where indices for this statute are stored."""
        return os.path.join(Constants.STATUTEDATADIR, self.name + ".index")
    def storeIndices(self):
        """Causes the index information in the file to be stored to the appropriate file."""
        f = file(self.getIndexName,"wb"); pickle.dump((self.slDict,self.sectionNameDict,self.linksDict),f); f.close()
        return
    def loadIndices(self):
        """Loads all the indices for the statute from the disk. If no indices file is found, sets the indices to empty dictionaries, and shows a warning."""
        if not os.path.exists(self.getIndexName()):
            showError("["+self.name+"] Could not find index file for statute")
        else:
            try:
                f = file(self.getIndexName(),"rb"); self.slDict, self.sectionNameDict, self.linksDict = pickle.load(f); f.close()
            except IOError:
                showError("["+self.name+"] Error opening index file for statute")
                pass
            pass
        if self.slDict is None: showError("["+self.name+"] No slDict, setting to {}"); self.slDict = {}
        if self.sectionNameDict is None: showError("[" + self.name + "] No sectionNameDict, setting to {}"); self.sectionNameDict = {}
        if self.linksDict is None: showError("[" + self.name + "] No linksDict, setting to {}"); self.linksDict = {}
        return
    def getSLFromString(self,sLString,locationSL=None,errorLocation=None):
        """Returns the SL (if any) represented by the string in the Statute.  If locationSL is specified, and the sLString is not found in the label dictionary, then additional searches are made pre-pending portions of locationSL.
        @rtype: SectionLabelLib.SectionLabel
        """
        if self.sectionNameDict is None: showError("Call to getSLFromString before self.sectionNameDict is set. Loading indices.",location=errorLocation); self.loadIndices()
        if sLString in self.sectionNameDict: return self.sectionNameDict[sLString]
        if locationSL is None: showError("Could not locate sectionlabel string ["+sLString+"] in statute ["+ self.name + "]",location=errorLocation); return None

        for subLabel in locationSL.getSubLabels():
            #print(">>" + subLabel.getIDString() + sLString)
            if (subLabel.getIDString() + sLString) in self.sectionNameDict: return self.sectionNameDict[subLabel.getIDString() + sLString]
            pass
        showError("Could not locate sectionlabel string ["+sLString+"] in statute ["+ self.name + "] [hint:"+locationSL.getIDString()+"]",location=errorLocation)
        return None
    def getPinpointFromString(self, sLString, locationSL,errorLocation=None):
        """Returns a Pinpoint object for the given sectionLabel string in this statute.  Returns None, None, None if nothing found.
        @type sLString: str
        @type locationSL: SectionLabelLib.SectionLabel
        @rtype: SectionLabelLib.Pinpoint
        """
        sL = self.getSLFromString(sLString=sLString, locationSL=locationSL,errorLocation=errorLocation)
        if sL is None: return None
        return SectionLabelLib.Pinpoint(statuteName=self.name, sL=sL, page=self.getPageName(sL),anchor=self.getAnchor(sL))
    def getPageName(self,sL):
        """
        @type sL: SectionLabelLib.SectionLabel
        @rtype: str
        """
        return self.prefix + " " + sL[0].getIDString()
    def getAnchor(self,sL):
        """
        @type sL: SectionLabelLib.SectionLabel
        @type: str
        """
        return sL[1:].getIDString()
    def pinpointFragmentList(self, fragmentList, locationSL,errorLocation=None):
        """
        Takes a list of fragments, determines their sectionlabels, and marks them with pinpoints in place.
        @type fragmentList: list of langutil.Fragment
        @type locationSL: SectionLabelLib.SectionLabel
        """
        originalSL = locationSL
        curSL = locationSL
        for frag in fragmentList:
            if frag.isSeriesStart(): curSL = originalSL #if this is the start of a new series, we should rest the location hint
            pinpoint = self.getPinpointFromString(sLString=frag.getText(),locationSL = curSL,errorLocation=errorLocation)
            if pinpoint is not None:
                curSL = pinpoint.getSL()
                frag.setPinpoint(pinpoint)
                pass
            pass
        return
    pass


if __name__ == "__main__":
    si = StatuteIndex()
    print("Available statutes: " + str(si.statuteDataDict.keys()))