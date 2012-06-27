import XMLStatParse


class Statute(object):
    def __init__(self,data):
        p = XMLStatParse.XMLStatuteParser()
        p.feed(data)
        dataTree = p.getTree()
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
        return
    
    def processStatuteContents(self,tree):
        return
    
    def report(self):
        print "Title: " + self.longTitle + " (a/k/a " + self.shortTitle + ") " + self.chapter
        
