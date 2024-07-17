#!/usr/bin/env python3

"""
FindRanges is a somewhat more obtuse kind of the Find Signatures script.
It will simply grab all files you specify, from and to the offset you specify,
and output a report file with each byte of it on a separate line,
showing the ranges and all values that that byte assumes across those files.

Run it with one argument: the folder name (don't drop it into the same folder --
I̶'̶m̶ t̶o̶o̶ l̶a̶z̶y̶ t̶o̶ e̶x̶c̶l̶u̶d̶e̶ i̶t̶ f̶r̶o̶m̶ s̶e̶a̶r̶c̶h̶ who knows if you weren't looking for
files having the same signature as my script!)

Filter the search by the file extension below to limit what files it'll look at.
The base offset, max size, signedness, and number of iterations are also set up below.

You really want to take a look at the getVariables() function. And maybe adjust it, too,
if you're researching a format where you sort of know where some structures are, but want to
add some strict sanity-checks from the available bulk of files in it.
If you know and have programmed the size and items count that are different between files
(like pattern sizes in module music), you will only be able to see info across the range
of the smallest of them, so make it count :)

It's a good idea to edit a separate copy of the script when you're tuning it to a file type.

Feel free to edit everything else if you're analysing chunked structures or whatever else~~
I just designed this to be a simple tool, after all.

Conceived and created by Kaens Bard, 2024.
Works on CPython 3.13.
"""

import array, signal, sys, os, tqdm
from struct import unpack as su

# CHANGE THESE TO FIT YOUR NEEDS:
Ext = "" # "" for any, otherwise style it as ".ext"
Signed = False # True if you want to look into signed int8 (it's a different picture, try both!)
# These 4 variables ↓ may need changing file by file depending on
#the structures being researched. Do so from getVariables.
# ↓ the base offset to start looking from. Set to 0 if you don't know anything about the files yet.
BaseOfs = 0
# ↓ the single structure size. Set to a manageable value (0x100?) and Items to 1 if unknown.
# The output report length directly depends on this one.
Sz = 0x200
# ↓ the number of structures you're researching. Set to 1 if unknown.
# Affects the report length, drastically because it's how many times Sz bytes will be read.
Items = 1

# After these settings, (Sz × Items) bytes will be read from the BaseOffset position.

def getVariables(file):
	global BaseOfs, Sz, Items
	"""
	This function will analyse a file and find the base offset the researched block starts from.
	Returns 0 if all good and a negative value if not all was.
	It can also be used to find the structure size and the number of structures, if you're in mid-research.
	For example, it can be the EntryPoint of an exe file, or a 6000???? jump in an Amiga music module.
	You need to already know something about the format to make use of this, otherwise just return 0.
	Shifts the file position.
	Reminder: Intel/Speccy goes "<" (little endian), Amiga/Motorola goes ">" (big endian)
	u_int8 = "B", s_int8 = "b"; u16 = "H", s16 = "h"; u32 = "L", s32 = "l"; u64 = "Q", s64 = "q"
	"<L" is an unsigned int32 pointer (that's 4 bytes long in size) for an Intel-produced binary
	">h" is a signed int16 pointer (size = 2 bytes) for Amiga and other Motorolas
	"""

	"""
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
			BaseOfs = eprva-vadr+rdp
	"""

	"""
	# An example to research the instruments of Loudness Sound System .LDS (Adlib game music):
	#(uses known info from previous research, like the offsets or data sizes)
	file.seek(0xF) # instrument record ("patch") number, offset known
	Items = su("<H",file.read(2))[0] # read number of patches, which is stored as uint16le
	BaseOfs = 0x11 # after the patch count
	Sz = 0x2E # structure size known 
	"""
	# Debug your solution to ensure it shows the right values:
	#print(f"\n--getAttr--  {t=:04X}, {file.tell():04X} - {t:02X} div {Sz:02X}, {Items=:02X}\n")

	#Everything went well!
	return 0


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

# prep the file dict (relative-pathed fnames, sizes without base offsets)
Df = []; base = 0

for root,_,files in os.walk(BaseDir):
	for f in files:
		if Quit: break
		if (Ext == "") or (os.path.splitext(f)[1].lower() == Ext):
			fn = os.path.normcase(os.path.join(root,f))
			Df.append(fn)

print(" done.")
if len(Df) < 2:
	print("At least have 2 files to start the search! Aborting.")
	exit()

print("Processing...")

Hope = Sz
mSz = sys.maxsize; MSz = -1; mItems = sys.maxsize; MItems = -1

m = array.array('i',(0xFF for x in range(Sz))) #min
M = array.array('i',(-0xFF for x in range(Sz))) #max
hopeYet = array.array('i',(True for x in range(Sz))) #whether to even check
V = []
for i in range(0,Sz): V.append(set()) #possible values

for fn in tqdm.tqdm(Df, ncols=os.get_terminal_size().columns-4,ascii=True):
	if Quit: break

	f = open(fn,'rb')
	res = getVariables(f)
	if res < 0: print(f"\nFilename {fn}: attributes error {res}! {BaseOfs=}\n"); continue
	fszb = f.seek(0,2) - BaseOfs
	if fszb <= 0:
		print("The file is smaller than the base offset, aborting.")
		exit()
	else:
		mSz = min(Sz,mSz); MSz = max(Sz,MSz); mItems = min(Items,mItems); MItems = max(Items,MItems)

	#print(f"In {fn}, there are {Items:02X}h items") #debug
	f.seek(BaseOfs); F = f.read(Sz*Items); f.close()
	if Signed:
		F = [int.from_bytes(F[i:i+1], byteorder='little', signed=True) for i in range(len(F))]
	#print(f"{fn}: read {len(F):04X} bytes") #debug
	for item in range(Items):
		#print(f"in {fn}: structure {item:02X}:",end='') #debug
		for i in range(Sz): #going through offsets:
			try:
				b = F[item*Sz+i]
			except IndexError: # out of range because some file's smaller than this
				continue
			except Exception as e:
				print(f" {fn}, {Items:02X} items: b = F[({BaseOfs:02X}+) {item:02X} * {Sz:02X} + {i:02X}]. Error: {str(e)}"); exit()
			V[i].add(b) #add it to the possible values set
			if Signed:
				hopeYet = m[i] != -128 or M[i] != 127
			else:
				hopeYet = m[i] != 0 or M[i] != 255
			if b < m[i]: m[i] = b #update min value for the offset
			if b > M[i]: M[i] = b #update max value
			if hopeYet and (
				((not Signed) and m[i] == 0 and M[i] == 255)
				or (Signed and m[i] == -128 and M[i] == 127)):
					Hope -= 1
		#print('') #debug
	if Hope <= 0: print("It's all completely random, alas."); exit()
del Df

if Quit:
	print("Program terminated."); exit(1)

def hex(x): return f"{x:02X}" #avoids the multiple levels of format {}s
def notMask(aSet): # finds the bitmask that this value will never fit
	b = 0xFF
	for j in (aSet): b &= ~j
	return hex(b)

o = open(f"findranges{os.path.splitext(fn)[1]}.txt","w",encoding="cp437")
if Signed:
	o.write(f"   Ranges detected for {os.path.splitext(fn)[1]}\nofs   range   (possible values)\n")
else:
	o.write(f"   Ranges detected for {os.path.splitext(fn)[1]}\nofs   range  not-mask (possible values)\n")
for i in range(Sz):
	V[i] = sorted(V[i])#; print(f"{MinOfs+i:04X}:")
	if Signed:
		o.write(f"{i:04X}: {m[i]:02X}..{M[i]:02X} ({','.join(hex(x) for x in V[i])})\n")
	else:
		nm = notMask(V[i])
		o.write(f"{i:04X}: {m[i]:02X}..{M[i]:02X}, ~{nm} ({','.join(hex(x) for x in V[i])})\n")
o.write(f"\n\n Structure sizes in [{mSz:02X} - {MSz:02X}]; item counts in [{mItems:02X} - {MItems:02X}]\n")
o.close()
print(f"Report complete. {Hope} hopes remain.")