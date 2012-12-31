import XMLStatParse, Statute


#FNAME = "Statutes/apca.xml"
FNAME = "Statutes/ita.xml"
f = open(FNAME,"r"); data = f.read(); f.close()
p = XMLStatParse.XMLStatuteParser(data=data)
t = p.getTree() #test 
stat = Statute.Statute(data)

pruner = XMLStatParse.ActPruner([("se","6")],data = data)
print pruner.getPrunedPrettyXML()