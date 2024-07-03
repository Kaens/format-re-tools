#!/usr/bin/env python3

"""
FindRanges is a somewhat more obscure kind of the Find Signatures script.
It will simply grab all files you specify, from and to the offset you specify,
and output a report file with each byte of it on a separate line,
showing the ranges, the bytemask to filter them by,
and all values that that byte assumes across those files.
It may get a bit RAM-heavy if you go too far.

Run it with one argument: the folder name (don't drop it into the same folder --
I̶'̶m̶ t̶o̶o̶ l̶a̶z̶y̶ t̶o̶ e̶x̶c̶l̶u̶d̶e̶ i̶t̶ f̶r̶o̶m̶ s̶e̶a̶r̶c̶h̶ who knows if you weren't looking for
files having the same signature as my script!)

Filter the search by the file extensions below, along with the other parameters.

Conceived and created by Kaens Bard, 2024.
Works on CPython 3.13.
"""

import signal, sys, os, tqdm

# CHANGE THESE TO FIT YOUR NEEDS:
Ext = "" # "" for any, otherwise style it as ".ext"
MinOfs = 0 # the offset to start with to look for ranges
MaxOfs = 256 # the max offset to look at for ranges

# MAIN CODE

if len(sys.argv) > 1:
	BaseDir = sys.argv[1]
else:
	BaseDir = "."

Ext = Ext.lower()

# Ctrl+C processing
Quit = False
def signal_handling(signum,frame):
	global Quit
	Quit = True; print(" Esc key pressed, breaking off")
signal.signal(signal.SIGINT,signal_handling)

print("Enumerating files...",end='',flush=True)

# prep the file dict (relative-pathed fnames, sizes)
Df = {}

for root,_,files in os.walk(BaseDir):
	for f in files:
		if Quit: break
		if (Ext == "") or (os.path.splitext(f)[1].lower() == Ext):
			fn = os.path.normcase(os.path.join(root,f))
			Df[fn] = os.stat(fn).st_size - MinOfs

print(" done.")
if len(Df) < 2:
	print("At least have 2 files to start the search! Aborting.")
	exit()

print("Processing...")

Hope = Sz = min(min(Df.values()), MaxOfs-MinOfs) #the amount of ranges that aren't 0~255
print(f"First {Hope=}")
if Hope <= 0:
	print("The smallest file has zero length or is smaller than the minimum offset, aborting.")
	exit()
else:
	m = bytearray([0xFF] * Sz) #min
	M = bytearray([0] * Sz) #max
	V = []
	for i in range(0,Sz): V.append(set()) #possible values

for fn in tqdm.tqdm(Df.keys(), ncols=os.get_terminal_size().columns-4,ascii=True):
	if Quit: break
	f = open(fn,'rb'); f.seek(MinOfs); F = f.read(Sz); f.close()
	for i in range(0,Sz): #going through offsets:
		V[i].add(F[i]) #add it to the possible values set
		hopeYet = m[i] != 0 or M[i] != 255
		if F[i] < m[i]: m[i] = F[i] #update min value for the offset
		if F[i] > M[i]: M[i] = F[i] #update max value
		if hopeYet and m[i] == 0 and M[i] == 255:
			Hope -= 1
	if Hope == 0: print("It's all random, no point in continuing."); exit(1)
	while Sz > 0 and m[Sz-1] == 0 and M[Sz-1] == 255: # crop the size of the checked array
		Sz -= 1
del Df

if Quit:
	print("Program terminated."); exit(1)

def hex(x): return f"{x:02X}" #avoids the multiple levels of format {}s
def notMask(aSet): # finds the bitmask that this value will never fit
	b = 0xFF
	for j in (aSet): b &= ~j
	return hex(b)

o = open(f"findranges{os.path.splitext(fn)[1]}.txt","w",encoding="cp437")
o.write(f"   Ranges detected for {os.path.splitext(fn)[1]}\nofs   range  not-mask (possible values)\n")
for i in range(0,Sz):
	V[i] = sorted(V[i])#; print(f"{MinOfs+i:04X}:")
	nm = notMask(V[i])
	if m[i] == 0 and M[i] == 255 and nm == "00": continue
	o.write(f"{MinOfs+i:04X}: {m[i]:02X}-{M[i]:02X}, ~{nm} ({','.join(hex(x) for x in V[i])})\n")
o.close()
print(f"Report complete. {Hope} hopes remain.")