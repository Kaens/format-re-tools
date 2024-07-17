#!/usr/bin/env python3

"""
FindSigs is meant to discover the identical (and optionally non-zero) byte sequences
across many files, which will often lead to finding an obscure format's signature.

It just replaces the non-same bytes with the value of ZeroOutWith, one by one, iteratively.
It then saves the resulting almost-zeroish binary result file
and the text file with ready sigs and pointers.

Run it with one argument: the folder name (don't drop it into the same folder --
I̶'̶m̶ t̶o̶o̶ l̶a̶z̶y̶ t̶o̶ e̶x̶c̶l̶u̶d̶e̶ i̶t̶ f̶r̶o̶m̶ s̶e̶a̶r̶c̶h̶ who knows if you weren't looking for
files having the same signature as my script!)

Additionally, you could filter the search by its extension below, along with the other parameters.

Conceived and created by Kaens Bard, 2022～2024.
Works on CPython 3.10.5 and PyPy 3.9.
"""

import signal, sys, os, tqdm
from struct import unpack as su

# CHANGE THESE TO FIT YOUR NEEDS:
Ext = "" # "" for any, otherwise style it as ".ext"
MaxOfs = 10000000 # the max offset to look at for matches
SigAtLeast = 2 # the minimum length of a sequence of matching bytes to make a signature from 
AllZeroesGood = False # when the entire sig sequence is zeroes, ignore it — useful for file format detection
ZeroOutWith = 0 # the output .bin will have this character in the positions that aren't a match
ansimin = 2 # how many characters an ansi sequence should have for the 'text' conversion to happen in the DiE sig
def BaseOffset(file):
	"""
	This function will analyse each file to know what offset the matchable block starts from in each file.
	For example, it can be the EntryPoint of an exe file, or a 6000???? jump in an Amiga music module.
	You need to already know something about the format to make use of this, otherwise just return 0.
	Reminder: Intel/Speccy goes "<" (little endian), Amiga/Motorola goes ">" (big endian)
	u_int8 = "c", s_int8 = "b"; u16 = "H", s16 = "h"; u32 = "L", s32 = "l"; u64 = "Q", s64 = "q"
	"<L" is an unsigned int32 pointer (that's 4 bytes long in size) for an Intel-produced binary
	">h" is a signed int16 pointer (size = 2 bytes) for Amiga and other Motorolas

	# An example to get the AddressOfEntryPoint for exe files:
	file.seek(0x3C); pe = su("<L",file.read(4))[0]
	file.seek(pe+6); sn = su("<H",file.read(2))[0]
	file.seek(pe+0x14); sts = pe+su("<H",file.read(2))[0]+0x18
	file.seek(pe+0x28); eprva = su("<L",file.read(4))[0]
	for i in range(sn):
		start = sts+i*0x28; file.seek(start+8)
		vsz = su("<L",file.read(4))[0]; vadr = su("<L",file.read(4))[0]
		rdsz = su("<L",file.read(4))[0]; rdp = su("<L",file.read(4))[0]
		if vadr <= eprva < vadr+rdsz:
			return eprva-vadr+rdp
	return 0
	"""
	return 0

# MAIN CODE

if len(sys.argv) > 1:
	BaseDir = sys.argv[1]
else:
	BaseDir = "."

if type(ZeroOutWith) is str:
	ZeroOutWith = ord(ZeroOutWith[0])
Ext = Ext.lower()

# Ctrl+C processing
Quit = False
def signal_handling(signum,frame):
	global Quit
	Quit = True; print(" Esc key pressed, breaking off")
signal.signal(signal.SIGINT,signal_handling)

def DIESig(bs):
	# creates a Detect-It-Easy signature from bytes
	s = '"'; s1 = ""
	for b in bs:
		if (0x20 <= b < 0x7F) and not (chr(b) in ["'",'"']): # if it's an ansi character (but not a quote or apostrophe)
			s1 += chr(b) # add it to the buffer for 'text' representation
		else: # not an ansi character...
			if len(s1) >= ansimin: # if the size of the 'text' repr collected so far is above threshold
				s += "'"+s1+"'" # add it to the sig
			elif s1 != "":
				for q in s1:
					s += f"{ord(q):02X}"
			s1 = ""; s += f"{b:02X}" # empty the 'text' buffer and add the current hex as hex
	if len(s1) >= ansimin: # the end of the sig has the same effect for 'text' repr. Feels like this can be optimised...
		s += "'"+s1+"'"
	elif len(s1) > 0: # if our 'text' repr has characters but is below threshold, empty it out as hexes
		for q in s1:
			s += f"{ord(q):02X}"        
	del s1; s = s.replace("''",""); s += '"'
	return s

# prep the cache list
Lc = []

print("Enumerating files...",end='',flush=True)

# prep the file dict (relative-pathed fnames, sizes) and another for base offsets
Df = {}
Db = {}
base = 0

for root,_,files in os.walk(BaseDir):
	for f in files:
		if Quit: break
		if (Ext == "") or (os.path.splitext(f)[1].lower() == Ext):
			fn = os.path.normcase(os.path.join(root,f))
			ofs = BaseOffset(open(fn,'rb'))
			if ofs > 0: base = ofs
			Df[fn] = os.stat(fn).st_size-ofs
			Db[fn] = ofs

print(" done.")
if len(Df) < 2:
	print("At least have 2 files to start the search! Aborting.")
	exit()

print("Processing...")

Hope = Sz = min(min(Df.values()), MaxOfs) #the amount of potential matches, starts as the smallest (filesize - base offset)
print(f"First {Hope=}")
if Hope == 0:
	print("The smallest file has zero length, aborting.")
	exit()
else:
	B = bytearray([0] * Sz) #buffer 
	M = bytearray([1] * Sz) #match mask
	F = bytearray([0] * Sz) #current file 

First = True
oldfn = ""

for fn in tqdm.tqdm(Df.keys(), ncols=os.get_terminal_size().columns-4,ascii=True):
	if Quit or Hope <= 0:
		break
	f = open(fn,'rb'); f.seek(Db[fn]); F = f.read(Sz); f.close()
	if First:
		B[:] = F; First = False
	else: # compare against the previous files
		for i in range(Sz):
			if M[i] and F[i] != B[i]: # If there's hope for this byte but it doesn't match
				M[i] = 0 # mask it out
				Hope -= 1 # and take the hope for it away
				if Hope == 0:
					print("No hope. Breaking off at "+fn+ "; prev. "+oldfn)
					break
		while Sz > 0 and not M[Sz-1]: # crop the size of the checked array
			Sz -= 1
	oldfn = fn

if Quit:
	print("Program terminated.")
elif Hope > 0:
	o = open("findsigs"+os.path.splitext(fn)[1]+".txt","w",encoding="cp437")
	SusLen = 0 # running sig suspect length
	SusCnt = 0 # counting sigs
	AllZeroes = 0 # counting the ill-advised sigs too
	Hope = 0 # our hope - counting just the sig-like bytes here
	# add one mismatch at the end to simplify the following algo if a signature continues until the last byte
	Sz += 1
	if len(B) == Sz: B.append(0); M.append(0) # not necessary if there were tailing mismatches trimmed
	for i in range(Sz):
		if M[i]: # if it's a match
			SusLen += 1 # simply add the running length for it
		else: # if it's not, or no longer, a match
			if SusLen >= SigAtLeast: # if the length of uninterrupted signature found thus far is over threshold...
				Hope += SusLen # the hope byte count now includes this signature
				Sus = B[i-SusLen:i] # apprehend the suspect 
				if sum(Sus) > 0 or AllZeroesGood: # avoiding stupid (all zeroes) results, or not
					SusCnt += 1 # we have found a signature we can give the user
					if base > 0:
						o.write(f"{DIESig(Sus)}, base+0x{i-SusLen:02X}\n")
					else:
						o.write(f"{DIESig(Sus)}, 0x{i-SusLen:02X}\n")
				else:
					AllZeroes += 1
			SusLen = 0 # anyway, get ready to find another sig
			B[i] = ZeroOutWith # and erase the mismatch byte in the binary 
	o.close() # the file with signatures
	Sz -= 1 # ignore the final dummy byte
	open("findsigs"+os.path.splitext(fn)[1]+".matches","wb").write(b''.join([b'x' if b else b'.' for b in M[:Sz]]))
	open("findsigs"+os.path.splitext(fn)[1]+".bin","wb").write(B[:Sz])
	print(f"  {Hope} hopes rest in {SusCnt} sequences among {len(Df)} files.",end="")
	if not AllZeroesGood and AllZeroes > 0:
		print(f" 0-sequences ignored: {AllZeroes}.")
	else:
		print("") 
elif Hope == 0:
	print("  There were no matches at all.")