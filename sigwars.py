#!/usr/bin/env python3

# CHANGE THESE TO FIT YOUR NEEDS
Ext = "" # "" for any, otherwise style it as ".ext"
Ofs = 0x00
Sz = 0x04

"""
Signature Wars is something rather niche
If:
  - you have a collection of files whose format you're reversing;
  - you have a strong suspicion that files of multiple subformats (clones, custom rewrites) are in it;
  - you can kinda tell already where the difference is,
then this can be of use to you.

It will look at the given range in each file in a folder given with the extension given,
and collect all the variations of the contents of this range.

Say, your files have signatures "MED0, MED2, MMD1, MMD2, MMD3"
but they're all OctaMED music modules and have the ".med" extension.
You don't want that, now, do you? The formats may well be different in unexpected ways.
Or some idiot has edited the signature to say "Archon" instead. The file may still play, or it may not.
Yes, Archon from 1995, the DM2 producer, I'm looking at you.

So you run this script on that folder, and in the sigwars.med.txt you see something like this:
MED0
  - file 1.med, file 3.med
MED1
  - file 2.med, file 5.med
MMD3
  - file 0.med, file 4.med, file 6.med

Useful? Useful.

With minimal edits (like json.dumps(L)), this can be made machine-readable for further automation.

---
Conceived and created by Kaens bard, 2022.
Works just fine in python 3 or pypy 3.
"""

import os, sys

# The default folder:
if len(sys.argv)>1:
	BaseDir = sys.argv[1]
else:
	BaseDir = "."
# CHANGE UNTIL HERE

def DIESig(bs):
	# creates a Detect It Easy signature from bytes
	ansimin = 2 # how many characters an ansi sequence should have for the 'text' conversion to happen
	s = '"'; s1 = ""
	for b in bs:
		if (0x20 <= b < 0x7F) and not (chr(b) in ["'",'"']):
			s1 += chr(b)
		else:
			if len(s1) >= ansimin:
				s += "'"+s1+"'"
			elif s1 != "":
				for q in s1:
					s += f"{ord(q):02X}"
			s1 = ""; s += f"{b:02X}"
	if len(s1) >= ansimin:
		s += "'"+s1+"'"
	elif len(s1)>0:
		for q in s1:
			s += f"{ord(q):02X}"        
	del s1; s = s.replace("''",""); s += '"'
	return s

L=[]
c = 0
for r,_,ns in os.walk(BaseDir):
	for n in ns:
		if Ext == "" or os.path.splitext(n)[1].lower() == Ext.lower():
			fn = os.path.normcase(os.path.join(r,n))
			f = open(fn,"rb")
			f.seek(Ofs)
			i = f.read(Sz)
			f.close()
			sig = DIESig(i)
			old = False
			for c in range(len(L)):
				if L[c][0] == sig:
					old = True; break
			if not old:
				L.append((sig,[fn]))
			else:
				L[c][1].append(fn)

o = open("sigwars"+Ext+".txt","w",encoding="utf-8-sig")
for k,vs in L:
	o.write(k+"\n  - ")
	o.write(', '.join(v for v in vs))
	o.write("\n\n")
o.close()