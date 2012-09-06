#$Id$

"""Superclass for everything that is part of the Statute Object, allows objects to get back to the statute object and track their parent."""

class StatutePart(object):
    """Superclass for everything that is part of the Statute object.  These objects keep track of their parent and the statute that they are a part of."""
    def __init__(self, parent, statute = None):
        self.parent = parent
        if statute != None: self.statute = statute
        else: self.statute = self.parent.getStatute()
    def getStatute(self): return self.statute