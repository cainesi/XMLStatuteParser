import XMLStatParse, Statute

f = file("Statutes/apca.xml","r"); data = f.read(); f.close()
p = XMLStatParse.XMLStatuteParser()
p.feed(data)
t = p.getTree()

stat = Statute.Statute(data)
