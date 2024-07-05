#!/usr/bin/env python3
"""
This script automates your desperate attempts to find where in the mixed code-data file
the specific info is referenced, allowing you to search with a known endianness, pointer size,
in part of the file, and even have a margin of error in case the pointers are off for any reason.
Run with 1 parameter to check in that file, but it needs tweaking to be effective!
"""

# CHANGE THESE TO FIT YOUR NEEDS:
FileName = "findptrs.tst"
DataAt = 0x13

From = 4 # where we start looking for pointers at, -1 for start of file
To = -1 # after where we stop looking (we try to find all ptrs), -1 for end of file

Jitter = 2 # pointer offset leeway, >= 0 only
# Set to > 0 if the pointers might be offset by this much (like the jmp/bsr command specifics).
# Normally it's good to have it equal to the pointer size.
# Jittery results are displayed with a prepending "~" and an offset suffix (like "~Found [000B]+1").

# Intel/Speccy goes "<" (little endian), Amiga/Motorola goes ">" (big endian)
# u_int8 = "c", s_int8 = "b"; u16 = "H", s16 = "h"; u32 = "L", s32 = "l"; u64 = "Q", s64 = "q"
# "<L" is an unsigned int32 pointer (that's 4 bytes long in size) for an Intel-produced binary
# ">h" is a signed int16 pointer (size = 2 bytes) for Amiga and other Motorolas
Pattern = ">h"
PtrSz = 2 # yes, once more and explicitly, for a non-Pythonic series of checks. L=4, h=2, etc

Rel = 1 # 1 if you're searching for relative pointers (the reason this script exists),
# (eg. when your data is at 10, and the X found at 4 is 6, X is a relative pointer to your data)
# 0 for absolute (from start of file) (which doesn't make much sense to run a whole script for)


import sys,os.path
if len(sys.argv) > 1:
	if os.path.exists(sys.argv[1]):
		FileName = sys.argv[1]
	else:
		print("Error: could not find "+sys.argv[1]+". Did you forget the quotes?")
		exit(-1)

F = open(FileName,'rb').read()

if From == -1:
	From = Jitter #; print('Searching from file start')
if To == -1:
	To = len(F)-PtrSz-Jitter #; print(f'Searching to file end {len(F):08X} at {To:08X}')
if From >= len(F)-PtrSz-Jitter: #; print("From value too big, searching from", Jitter)
	From = Jitter
elif From < Jitter: #; print("From value too little, searching from", Jitter)
	From = Jitter
if To > len(F)-PtrSz-Jitter:
	To = len(F)-PtrSz-Jitter #; print("To value too big, searching from", To)
if To < From:
	To,From = From,To #; print("To value is smaller than From, swapping")
if To-From <= Jitter*2:
	print(f"File too small ({From=}, {To=}, {Jitter=})"); exit()

from struct import unpack

def ptr2ofs(pofs):
	# takes a suggested value from the file (from point pofs) as an offset
	# this offset is further compared to
	try:
		return(unpack(Pattern,F[pofs:pofs+PtrSz])[0])
	except Exception as e:
		print(f"ptr2ofs error at {pofs:08X}:")
		raise

i = From
print(f"Searching in "+FileName+"...")
while i < To:
	for j in range(-Jitter,Jitter+1):
		testing = ptr2ofs(i);
		#print(f"{i:X}{testing:+X}?",end=' ',flush=True)
		if i*Rel+j+testing == DataAt:
			if j == 0:
				print(f"Found [{i:04X}]")
			else:
				print(f"~Found [{i:04X}]{j:+X}")
	i += 1

input("Done. Press <Enter>")