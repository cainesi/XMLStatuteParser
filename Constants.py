
ACTFILE = "Statutes/apca.xml"
ITAFILE = "Statutes_all/ita.xml"
REGFILE = "Statutes_all/ita_reg.xml"


sectionTypes = ["section","subsection","paragraph","subparagraph","clause","subclause","subsubclause","definition","formuladefinition"]
formulaSectionTypes = ["formulaparagraph", "formulasubparagraph","formulaclause","formulasubclause", "formuladefinition"]
formulaSectionMap = {"formulaparagraph":"paragraph",
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


textTypes = ["text","continuedsectionsubsection","continuedparagraph","continuedsubparagraph","continuedclause","continuedsubclause","continueddefinition", "oath" , "formulaconnector"]
