#!/usr/bin/env python3
"""
This script takes the "diec -dbuj testcase > testcase.txt" testcase.txt many-JSON output and tries to ensure
that everything has detected properly.

Optionally run with 1 parameter to check that 1 file.

Conceived and created by Kaens Bard, 2024.
Works on CPython 3.13 and PyPy 3.10.
"""

ReportFile = "testcase.report.txt"
TestCase = "testcase.txt"
# ↓ heuristics, generics... bad causes for the "multiple detections" alarm
UselessFPs = ['Amiga loadable file','plain text'] 
#UselessFPs = ['Raw Deflate stream','.zlib','Amiga loadable file','plain text']

import os,sys,re,json

if len(sys.argv) > 1:
    TestCase = sys.argv[1]
    ReportFile = f"{os.path.splitext(TestCase)[0]}.report.txt"

D = {} # dictionary holding filenames and jsons

print(f"Parsing {TestCase}...")
fi = open(TestCase,"r",encoding="utf-8")
curblock = []
for a in fi.readlines():
    if len(a) < 2:
        if len(curblock) > 0:
            # remove the ":" from filename = dict key add to dict
            D[os.path.basename(curblock[0][:-1])] = "\n".join((l for l in curblock[1:]))
            curblock = []
    else:
        curblock.append(a.strip()) # removes newlines
fi.close()
print(f"Got {len(D)} files. Writing out the report...")
fo = open(ReportFile,"w",encoding="utf-8-sig")

for f in D:
    if D[f].find("Error: ") >= 0:
        fo.write(f+': '+D[f]+'\n')
        continue
    try:
        j = json.loads(D[f])
        print(f"detects: {len(j['detects'])}")
    except Exception as e:
        je = f"{f}: JSON error: {e}. Could be _log output\n"
        fo.write(je); print(je)
        continue
    for d in j["detects"]:
        if "values" not in d: # this got obsoleted I think
            fo.write(f"{f}: not detected!\n")
        else:
            if(len(d["values"]) > 1):
                multiple = []
                for v in d["values"]:
                    if v["name"] in UselessFPs: continue
                    if v["name"].rfind("(") > 0 and v["name"].rfind(")") > 0:
                        multiple.append(v["name"][v["name"].rfind("(")+1:v["name"].rfind(")")])
                    else:
                        multiple.append(v["name"])
                if(len(multiple) > 1): fo.write(f"{f}: multiple detections: {multiple}\n")
                elif(len(multiple) == 0): fo.write(f"{f}: not detected!\n")

            extFound = False
            for v in d["values"]:
                if v["type"] == "Unknown" and v["name"] == "Unknown":
                    fo.write(f"{f}: not detected!\n")
                shortp = re.compile(r"(^|.+\s)sz:\d+\((-\d+)!\)(\s.*|$)")
                shortg = shortp.match(v["info"])
                if shortg != None:
                    fo.write(f"{f}: short by {shortg.group(2)}\n")
                if not extFound and v["name"].rfind("(") > 0 and v["name"].rfind(")") > 0: # standard extensions/prefixes mentioned
                    exts = []; exts1 = v["name"][v["name"].rfind("(")+1:v["name"].rfind(")")].upper().replace(' ','').split(",")
                    for e in exts1:
                        exts.append(e)
                        if e[0] == '.': exts.append(e[1:]+'.')
                        elif e[-1] == '.': exts.append('.'+e[:-1])
                    for e in exts:
                        if e in f.upper():
                            extFound = True
                            break
                else: extFound = True # for the following line to be true
            if not extFound:
                fo.write(f"{f}: type mismatch with: {','.join(exts1)}\n")


fo.close()
print("Done.")