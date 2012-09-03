import XMLStatParse
import sys

fname = sys.argv[1]
section = sys.argv[2]
outfile = "output.xml" if (len(sys.argv) < 4) else sys.argv[3]

f = file(fname,"r"); data = f.read(); f.close()
p = XMLStatParse.ActPruner([("se",section)])
p.feed(data)
t = p.getTree()
d = t.getPrettyXML()
f = file(outfile,"w"); f.write(d.encode("utf-8")); f.close()