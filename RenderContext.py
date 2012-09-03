#$Id$
#$Revision$
#$Date$

"""Classes including code for rendering text/links for different contexts, such as HTML pages, and wikipages."""

import re

badStrings = [("&#8217;","'"),("&#8220;","\""),("&#8221;","\""),("&#8212;","--")]

#these characters don't need to be corrected, now that we're using utf-8 encoding on the html pages.
htmlBadStrings = [] #("\xe2\x80\x99","'"), ("\xe2\x80\x94","&mdash;"), ("\xe2\x80\x93","&ndash;"),("\xc3\x97","x")] #, ("\"","&quot;"),("<","&lang;"),(">","&rang;"),("&","&amp;")]

class RenderContext:
    fileExtension = ""
    includesBulletins = True #whether links to bulletins are available in this context
    @staticmethod
    def cleanText(text):
        """method for cleaning text that must appear in links."""
        return text
    @staticmethod
    def cleanPlainText(text):
        """method for cleaning raw text without any formatting."""
        return text    
    @staticmethod
    def documentStart():
        return ""
    @staticmethod
    def documentEnd():
        return ""
    @staticmethod
    def indentText(text, level = 0):
        return ""
    @classmethod
    def renderPlainText(classobj, text, level = 0): #for legacy code referencing renderPlainText
        return classobj.indentText(text,level)
    @staticmethod
    def renderLink(targetSection,targetAnchor=None,linkText=None):
        return ""
    @staticmethod
    def renderExternalLink(targetURL,linkText=None):
        return ""
    @staticmethod
    def renderAnchor(anchorTarget):
        return ""
    @staticmethod
    def renderHeading(text,level):
        return ""
    @staticmethod
    def renderTable(table):
        return ""
    @staticmethod
    def renderTOC():
        """code for a table of contents, if available."""
        return ""
    @staticmethod
    def horizontalLine():
        return ""
    @staticmethod
    def newLine():
        return ""
    @staticmethod
    def italicText(text):
        return ""
    @staticmethod
    def boldText(text):
        return ""
    @staticmethod
    def mailTo(address):
        return ""
    pass

class WikiContext(RenderContext):
    @staticmethod
    def cleanText(text):
        for badString,replacement in badStrings:
            text = re.sub(badString,replacement,text)
            pass
        return text
    @staticmethod
    def cleanPlainText(text):
        """method for cleaning raw text without any formatting."""
        return text   
    @staticmethod
    def indentText(text, level = 0):
        return ">" * level + " " + text
    @staticmethod
    def renderLink(targetSection,targetAnchor=None,linkText=None):
        """renders a link in the current context. targetSection is the section to link to, targetAnchor is the anchor in the section, linkText is the text of the link."""
        targetString = targetSection
        if targetAnchor is not None: targetString += "#" + targetAnchor
        if linkText is None:
            linkText = targetString
            pass
        linkText = WikiContext.cleanText(linkText)
        return "[[%s|%s]]"%(targetString,linkText)
    @staticmethod
    def renderExternalLink(targetURL,linkText=None):
        """renders a link to a url pointing outside of the wiki."""
        if linkText == None: linkText = targetUrl
        return "[[%s|%s]]" % (targetURL, linkText)
    @staticmethod
    def renderAnchor(anchorTarget):
        return "[[#%s]]"%anchorTarget
    @staticmethod
    def renderHeading(text,level):
        text = WikiContext.cleanText(text)
        return "="*level + " " + text + " " + "="*level
    @staticmethod
    def renderTable(table):
        heading = ("||~ " + " ||~ ".join(table[0]) + " ||") if len(table)>=1 else ""
        return "\n".join([heading]+["|| " + " || ".join(row) + " ||" for row in table[1:]])
    @staticmethod
    def renderTOC():
        """code for a table of contents, if available."""
        return "[[toc]]"
    @staticmethod
    def horizontalLine():
        return "----"
    @staticmethod
    def newLine():
        return "\n"
    @staticmethod
    def italicText(text):
        return "//" + text + "//"
    @staticmethod
    def boldText(text):
        return "**" + text + "**"  
    @staticmethod
    def mailTo(address):
        return "[[mailto:%s]]"%address
    pass

class HTMLContext(RenderContext):
    fileExtension = ".html"
    includesBulletins = False #in html, we won't necessarily have bulletins available.
    @staticmethod
    def cleanText(text):
        return text
    @staticmethod
    def cleanPlainText(text):
        """method for cleaning raw text without any formatting."""
        for badString,replacement in htmlBadStrings:
            text = re.sub(badString,replacement,text)
            pass
        return text 
    @staticmethod
    def documentStart():
        return "<html><meta charset=\"utf-8\"></meta>"
    @staticmethod
    def documentEnd():
        return "</html>"
    @staticmethod
    def indentText(text, level = 0):
        return ("<div style=\"padding-left: %dem;\">"%(level*3)) + text + "</div>\n"
    @staticmethod
    def renderLink(targetSection,targetAnchor=None,linkText=None):
        linkUrl = targetSection + HTMLContext.fileExtension
        if targetAnchor is not None: linkUrl += "#" + targetAnchor
        if linkText is None: linkText = targetSection + (targetAnchor if targetAnchor is not None else "")
        linkText = HTMLContext.cleanPlainText(linkText)
        return "<a href=\"%s\">%s</a>" %(linkUrl,linkText)
    @staticmethod
    def renderExternalLink(targetURL,linkText=None):
        """renders a link to a url pointing outside of the wiki."""
        if linkText == None: linkText = targetUrl
        return "<a href=\"%s\">%s</a>" %(linkURL,linkText)
    @staticmethod
    def renderAnchor(anchorTarget):
        return "<a name=\"%s\"></a>"%anchorTarget
    @staticmethod
    def renderHeading(text,level):
        if level == 1: size=6
        elif level == 2: size=5.25
        elif level == 3: size= 4.75
        elif level == 4: size=4.25
        elif level == 0: size = 12
        else: size = 4.0
        text = HTMLContext.cleanPlainText(text)
        return "<font size=\"%.2f\">%s</font>"%(size, text)
    @staticmethod
    def renderTable(table):
        return "<table>\n<tr>" + "</tr>\n<tr>".join(["<td>" + "</td><td>".join(row) + "</td>" for row in table]) + "</tr></table>"
    @staticmethod
    def horizontalLine():
        return "<hr>"
    @staticmethod
    def newLine():
        return "<br>\n"
    @staticmethod
    def italicText(text):
        return "<i>%s</i>"%text
    @staticmethod
    def boldText(text):
        return "<b>%s</b>"%text
    @staticmethod
    def mailTo(address):
        return "<a href=\"mailto:%s\">%s</a>"%(address,address)
    pass
