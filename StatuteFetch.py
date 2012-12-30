"""Module for fetching statute xml from justice website and bundling into a file."""

import urllib2, urlparse, re, datetime, pickle

class StatuteFetchException(Exception): pass

currentToPat = re.compile("current to (?P<date>(?P<year>\d\d\d\d)-(?P<month>\d+)-(?P<day>\d+))")
amendedPat = re.compile("last amended on (?P<date>(?P<year>\d\d\d\d)-(?P<month>\d+)-(?P<day>\d+))")
xmlPat = re.compile("<a href=('|\")(?P<url>[^\">]*)('|\")>XML")

def openStatute(fname):
    """Open a statute file and return the dictionary."""
    f = file(fname,"r"); xstat = pickle.load(f); f.close()
    return xstat

def storeStatute(fname, url):
    """Download and store statute to a specified file."""
    xstat = fetchStatute(url)
    f = file(fname,"w"); pickle.dump(xstat,f); f.close()
    return

def isStatuteUpdated(fname):
    """Checks whether a statute has accumulated any further amendments."""
    statDict = openStatute(fname)
    url = statDict["URL"]
    newDict = readStatutePage(url)
    if newDict["AMEND"] > statDict["AMEND"]: return True
    elif newDict["AMEND"] == statDict["AMEND"]: return False
    elif newDict["AMEND"] < statDict["AMEND"]: print("WARNING: Lastest statute has less current amendments than stored."); return True
    else:
        print("WARNING: Lastest statute has less current amendments than stored.")
        return False
    return

def fetchStatute(url,amendDate=None, priorVersion=None):
    """Processes the top url for a statute, and returns a dictionary
    { "DOWNLOAD": download datetime (of the top-level page),
    "CURRENCY": currency date,
    "AMEND": amendment date,
    "XMLDATA": xml representation of statute, as a string,
    "URL": the url of the top page for statute,
    "XMLURL": the url of xml contents of statute}

    if either optional parameter amendDate or priorVersion (a statute dictionary) is given, then will return None unless the posted act reports a more recent amendment date or the contents of the XML have been changed (respectively).
    """
    #TODO - implement handling of priorVersion parameter
    #TODO - zip the xml data in the "DATA" parameter?
    statDict = readStatutePage(url)
    if amendDate != None:
        if statDict["AMEND"] <= amendDate: return None

    statDict["DATA"] = urllib2.urlopen(statDict["XMLURL"]).read()
    return statDict

def readStatutePage(url):
    """Reads the top page for a statute and return a dictionary containing the metadata found there (currency, amendment date, download time.  Basically, everything except the raw xml of the statute."""
    page = urllib2.urlopen(url).read()
    currentm = currentToPat.search(page)
    amendm = amendedPat.search(page)
    if currentm is None: raise StatuteFetchException("Could not find currency date: " + url)
    if amendm is None: raise StatuteFetchException("Could not find amendment date: " + url)
    statDict = {}
    statDict["CURRENCY"] = datetime.date(year=int(currentm.group("year")),month=int(currentm.group("month")),day=int(currentm.group("day")))
    statDict["AMEND"] = datetime.date(year=int(amendm.group("year")),month=int(amendm.group("month")),day=int(amendm.group("day")))
    statDict["DOWNLOAD"] = datetime.datetime.today()
    statDict["URL"] = url
    xmlm = xmlPat.search(page)
    if xmlm is None: raise StatuteFetchException("Could not find url for statute XML: " + url)
    xurl = xmlm.group("url")
    uparse = urlparse.urlparse(url)
    xparse = urlparse.urlparse(xurl)
    if xparse.scheme == '': xparse = xparse._replace(scheme="http")
    if xparse.netloc == '': xparse = uparse._replace(path=xparse.path)
    xurl = urlparse.urlunparse(xparse)
    statDict["XMLURL"] = xurl
    return statDict

#testing
if __name__ == "__main__":
    print("-- ITA --")
    url = "http://laws-lois.justice.gc.ca/eng/acts/I-3.3/"
    print(fetchStatute(url))
    print("-- ITA Regulations --")
    url = "http://laws-lois.justice.gc.ca/eng/regulations/C.R.C.,_c._945/"
    print(fetchStatute(url))