#$Id$

"""Superclass for everything that is part of the Statute Object, allows objects to get back to the statute object and track their parent."""

class StatutePartException(Exception): pass

class StatutePart(object):
    """Superclass for everything that is part of the Statute object.  These objects keep track of their parent and the statute that they are a part of."""
    def __init__(self, parent, statute = None):
        """parent is the object sitting above this object in the structure.  statute is the Statute object of which this object is a part."""
        self.parent = parent
        if statute != None: self.statute = statute
        else:
            if self.parent == None: raise StatutePartException("StatutePart created with neither parent not statute") #TODO: maybe if there is no parent, the parent should be set to the statute?
            else: self.statute = self.parent.getStatute()
    def getLocationString(self):
        """Method to describe the location of the object in the structure, to be overridden in subclasses."""
        return "No Location"
    def getStatute(self): return self.statute
    def hasStatute(self):
        if self.statute is None: return False
        return True