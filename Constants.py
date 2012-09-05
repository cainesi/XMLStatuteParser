
ACTFILE = "Statutes/apca.xml"
ITAFILE = "Statutes_all/ita.xml"
REGFILE = "Statutes_all/ita_reg.xml"

#top level tags for ordinary sections handled by SectionItem (other than in formlas)
sectionTypes = set(["section","subsection","paragraph","subparagraph","clause","subclause","subsubclause","definition","formuladefinition" 
                   ]) 
formulaSectionTypes = set(["formulaparagraph", "formulasubparagraph","formulaclause","formulasubclause", "formuladefinition"]) #top level tags for sections in formulas, need to have name translated to get correct label
formulaSectionMap = {"formulaparagraph":"paragraph",      #mapping from the formula sections to ordinary section types
                     "formulasubparagraph":"subparagraph",
                     "formulaclause":"clause",
                     "formulasubclause":"subclause",
                     "forumlasubsubclause":"subsubclause",
                     "formuladefinition": "formuladefinition"}
tagSection = {"se": "section",
              "ss": "subsection",
              "p1": "paragraph",
              "p2": "subparagraph",
              "c1": "clause",
              "cs": "subclause",
              "c3": "subsubclause", #is this right?
              "df": "definition",
              "fd": "formuladefinition"}
sectionTag = {(c[1],c[0]) for c in tagSection.items()}


textTypes = set(["text","continuedsectionsubsection","continuedparagraph","continuedsubparagraph","continuedclause","continuedsubclause","continueddefinition", "oath" , "formulaconnector", "continuedformulaparagraph"]) #top level tags for subitems of sections that should be interpreted as text
#list of types of tags that are expected in text blocks, others will generate warnings so we know there may be something that needs special handling
textTriggers = set(["text","oath","formulaconnector","label"])

knownTextTags = set(["text", #ordinary text
                     "emphasis", #italics / bold
                     "repealed", #repealed blocks
                     "sub", #subscripts
                     "sup", #superscript
                     "language", #foreign language (e.g., latin)
                     "label" #appeaers in the "provision" tags in 211.1
                     ]) 