# Extremely simplistic, saves a recursive filelist to simplify searches across big file collections
import os
L=[]
exclude=[os.path.join(".","filelist.py"),os.path.join(".","filelist.txt"),os.path.join(".","filelist.py.txt")]
print("Please wait patiently...")
for r,_,fs in os.walk("."):
	for f in fs:
		fn = os.path.join(r,f)
		if fn not in exclude:
			L.append(fn+'\n')

open("filelist.py.txt","w",encoding="utf-8-sig").writelines(L)
