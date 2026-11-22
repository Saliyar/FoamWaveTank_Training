#!/usr/bin/env python3
"""
Change draft, mass, inertia or height of the box consistently.

    python3 setBox.py --draft 0.06                     # mass = displacement, inertia ~ mass
    python3 setBox.py --draft 0.06 --iyy 0.0167        # ... with the inertia kept
    python3 setBox.py --height 0.1086                  # lower deck (less freeboard)
    python3 setBox.py                                  # back to the Day 3 box

Assumptions: 2D box 0.2 x 0.2 m; centre of gravity 0.066 m above the keel;
fairleads fixed on the box (5 mm above the keel, at the four corners).
Writes system/boxGeometry, constant/massProperties and the body, fairleads of
Mooring/lines_v2_bodyC.txt.
"""
import argparse

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--draft", type=float, default=0.0786, help="draft [m], 0.04 .. 0.11")
ap.add_argument("--height", type=float, default=0.1316, help="box height [m]")
ap.add_argument("--iyy", type=float, help="pitch inertia about the CoG [kg m2]")
a = ap.parse_args()

top = a.height - a.draft
if not 0.04 <= a.draft <= 0.11 or not 0.018 <= top <= 0.12:
    ap.error("need draft 0.04 .. 0.11 m and freeboard (height - draft) 0.018 .. 0.12 m")

mass = 3.148 * a.draft / 0.0786
zg = 0.066 - a.draft
iyy = a.iyy or 0.0167 * mass / 3.148
gm = a.draft / 2 + 0.2 ** 2 / (12 * a.draft) - 0.066
if gm <= 0:
    ap.error("GM = %.4f m: the box capsizes" % gm)

HEAD = "// Written by setBox.py: draft %g m, height %g m\n" % (a.draft, a.height)
with open("system/boxGeometry", "w") as o:
    o.write(HEAD + "zKeel       %g;\nzDeck       %g;\n" % (-a.draft, top))
with open("constant/massProperties", "w") as o:
    o.write(HEAD + "mass            %.4g;\ncentreOfMass    (0 0 %.4g);\n"
            "momentOfInertia (%.4g %.4g %.4g);\n"
            % (mass, zg, 0.015 * mass / 3.148, iyy, 0.021 * mass / 3.148))

name, out = "Mooring/lines_v2_bodyC.txt", []
for line in open(name):
    w = line.split()
    if len(w) > 10 and w[1] == "Coupled":
        line = "1    Coupled     0      0    %.4f  0       0      0     %.4f  0    0       0       0      0\n" % (zg, mass)
    out.append(line)
open(name, "w").writelines(out)

print("draft %.4f m  freeboard %.4f m  mass %.3f kg  zG %.4f m  Iyy %.4f kg m2  GM %.4f m"
      % (a.draft, top, mass, zg, iyy, gm))
