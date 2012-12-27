"""Module for fetching statute xml from justice website and bundling into a file."""

import urllib2, urlparse, re, datetime

class StatuteFetchException(Exception): pass

currentToPat = re.compile("current to (?P<date>(?P<year>\d\d\d\d)-(?P<month>\d+)-(?P<day>\d+))")
amendedPat = re.compile("last amended on (?P<date>(?P<year>\d\d\d\d)-(?P<month>\d+)-(?P<day>\d+))")
xmlPat = re.compile("<a href=('|\")(?P<url>[^\">]*)('|\")>XML")

def fetchStatute(url,amendDate=None, priorVersion=None):
    """Processes the top url for a statute, and returns a dictionary
    { "DOWNLOAD": download datetime,
    "CURRENCY": currency date,
    "AMEND": amendment date,
    "XMLDATA": xml representation of statute, as a string}

    if either optional parameter amendDate or priorVersion (a statute dictionary) is given, then will return None unless the posted act reports a more recent amendment date or the contents of the XML have been changed (respectively).
    """
    #TODO - implement handling of priorVersion parameter
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
    #TODO - construct full url from the original url and any information gleaned from the webpage
    statDict["XMLURL"] = xurl
    statDict["DATA"] = urllib2.urlopen(xmlURL).read()
    return statDict

#testing
if __name__ == "__main__":
    print("-- ITA --")
    url = "http://laws-lois.justice.gc.ca/eng/acts/I-3.3/"
    print(fetchStatute(url))
    print("-- ITA Regulations --")
    url = "http://laws-lois.justice.gc.ca/eng/regulations/C.R.C.,_c._945/"
    print(fetchStatute(url))