#!/usr/bin/env python3
"""
Write system/blockMeshDict for a floating body in the Day 3 tank (5 m long, 0.5 m deep).

    python3 makeBodyMesh.py --shape box                          # 2D box 0.2 x 0.1316 m
    python3 makeBodyMesh.py --shape boxPlate --plateWidth 0.3    # 2D box with a heave plate
    python3 makeBodyMesh.py --shape cylinder                     # 2D horizontal cylinder, axis along y
    python3 makeBodyMesh.py --shape box3D                        # 3D box 0.2 x 0.2 x 0.1316 m
    python3 makeBodyMesh.py --shape sphere                       # 3D sphere

How it works
  1. The tank is cut by planes x = const, y = const, z = const into blocks.
  2. Blocks inside the body are left out: that hole is the box (or box + plate).
  3. For cylinder and sphere the hole is a square (cube) of 0.4 m, filled with an
     O-grid: one block from each side of the square to the curved surface.
  4. A block face used by one block only is a boundary face. Its position gives
     the patch (inlet, outlet, bottom, atmosphere, wall1, wall2, otherwise box).

Read system/blockMeshDict afterwards: it is a normal blockMeshDict. No packages needed.
"""
import argparse
import itertools
import math

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--shape", default="box", choices=["box", "boxPlate", "cylinder", "box3D", "sphere"])
ap.add_argument("--plateWidth", type=float, default=0.30, help="plate width in x [m]")
ap.add_argument("--plateThickness", type=float, default=0.02, help="plate thickness [m]")
ap.add_argument("--plateGap", type=float, default=0.0,
                help="gap between box bottom and plate [m]: 0 = attached, else at least 0.03")
ap.add_argument("--radius", type=float, help="default 0.1 (cylinder), 0.1146 (sphere)")
ap.add_argument("--dx", type=float, help="cell size near the surface [m], default 0.025 (2D), 0.05 (3D)")
ap.add_argument("--out", default="system/blockMeshDict")
ap.add_argument("--properties", metavar="DIR",
                help="box, boxPlate: also update DIR/massProperties and DIR/lines_v2_bodyC.txt")
a = ap.parse_args()

X0, X1, Z0, Z1 = -2.5, 2.5, -0.5, 0.5
HB, DRAFT, TOP = 0.1, 0.0786, 0.053
is3D = a.shape in ("box3D", "sphere")
curved = a.shape in ("cylinder", "sphere")
dx = a.dx or (0.05 if is3D else 0.025)
dz = min(dx, 0.04) if is3D else dx
R = a.radius or (0.1146 if a.shape == "sphere" else 0.1)
if curved and not 0.03 <= R <= 0.17:
    ap.error("radius must be 0.03 .. 0.17 m (O-grid square is 0.4 m)")

ys = [-0.1, 0.1]
if curved:
    S = 0.2
    xs, zs = [X0, -S, S, X1], [Z0, -S, S, Z1]
    solids = [(-S, S, -S, S)]
    if is3D:
        ys = [-0.5, -S, S, 0.5]
else:
    solids = [(-HB, HB, -DRAFT, TOP)]
    if a.shape == "boxPlate":
        w, t, g = a.plateWidth / 2, a.plateThickness, a.plateGap
        if not 0.2 < a.plateWidth <= 0.5:
            ap.error("plateWidth must be in (0.2, 0.5] m")
        if not 0.01 <= t <= 0.06 or (g and g < 0.03) or DRAFT + g + t > 0.3:
            ap.error("thickness 0.01 .. 0.06 m, gap 0 or >= 0.03 m, plate above z = -0.3 m")
        solids.append((-w, w, -DRAFT - g - t, -DRAFT - g))
    xs = sorted({X0, X1} | {v for s in solids for v in s[:2]})
    zl = {round(v, 6) for s in solids for v in s[2:]} | {Z0, Z1, 0.2}
    if min(zl - {Z0}) > -0.18:
        zl.add(-0.2)
    zs = sorted(zl)
    if is3D:
        ys = [-0.5, -HB, HB, 0.5]
levels = [xs, ys, zs]


def ncells(axis, lo, hi):
    if axis == 1 and not is3D:
        return 1
    if axis == 2 and (hi <= -0.2 or lo >= 0.2):
        return max(1, round((hi - lo) / (2 * dx if is3D else 6 * dx)))
    if a.shape == "box" and axis == 2 and lo == TOP:
        return max(1, math.floor((hi - lo) / dz))      # 5 rows as Day 3 (6 blew up at 15.8 s)
    return max(1, round((hi - lo) / (dz if axis == 2 else dx)))


verts, index = [], {}


def vid(p):
    key = tuple(round(c, 7) for c in p)
    if key not in index:
        index[key] = len(verts)
        verts.append(key)
    return index[key]


def solid(m):
    for x0, x1, z0, z1 in solids:
        if x0 < m[0] < x1 and z0 < m[2] < z1:
            if not is3D or ys[1] < m[1] < ys[2]:
                return True
    return False


CORNERS = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1)]
blocks = []

# 1-2. Cartesian blocks
for ijk in itertools.product(*[range(len(l) - 1) for l in levels]):
    lo = [levels[d][ijk[d]] for d in range(3)]
    hi = [levels[d][ijk[d] + 1] for d in range(3)]
    if solid([(l + h) / 2 for l, h in zip(lo, hi)]):
        continue
    v = [vid([(hi if c[d] else lo)[d] for d in range(3)]) for c in CORNERS]
    blocks.append((v, [ncells(d, lo[d], hi[d]) for d in range(3)]))


# 3. O-grid between the square (cube) and the curved surface
def on_surface(p):
    radial = [0, 1, 2] if is3D else [0, 2]
    length = math.sqrt(sum(p[d] ** 2 for d in radial))
    return [p[d] * R / length if d in radial else p[d] for d in range(3)]


if curved:
    hole = [(-S, S), (-S, S) if is3D else (ys[0], ys[1]), (-S, S)]
    nr = max(4, round((1.2 * S - R) / dx * 1.3))
    for axis in ([0, 1, 2] if is3D else [0, 2]):
        for side in (0, 1):
            u, w = (axis + 1) % 3, (axis + 2) % 3     # u x w points along +axis
            if side == 0:
                u, w = w, u                           # ... and along -axis
            outer = []
            for cu, cw in ((0, 0), (1, 0), (1, 1), (0, 1)):
                p = [0, 0, 0]
                p[axis], p[u], p[w] = hole[axis][side], hole[u][cu], hole[w][cw]
                outer.append(p)
            inner = [on_surface(p) for p in outer]
            blocks.append(([vid(p) for p in inner + outer],
                           [ncells(u, *hole[u]), ncells(w, *hole[w]), nr]))

# 4. Boundary faces (outward)
FACES = [(0, 4, 7, 3), (1, 2, 6, 5), (0, 1, 5, 4), (3, 7, 6, 2), (0, 3, 2, 1), (4, 5, 6, 7)]
used = {}
for v, _ in blocks:
    for f in FACES:
        face = [v[i] for i in f]
        used.setdefault(frozenset(face), []).append(face)
PLANES = [("inlet", 0, X0), ("outlet", 0, X1), ("bottom", 2, Z0),
          ("atmosphere", 2, Z1), ("wall1", 1, ys[0]), ("wall2", 1, ys[-1])]
patches = {name: [] for name, _, _ in PLANES}
patches["box"] = []
for fl in used.values():
    if len(fl) == 1:
        name = "box"
        for pn, d, value in PLANES:
            if all(abs(verts[i][d] - value) < 1e-6 for i in fl[0]):
                name = pn
        patches[name].append(fl[0])

edges, projected = [], []
if a.shape == "cylinder":
    done = set()
    for f in patches["box"]:
        for p, q in zip(f, f[1:] + f[:1]):
            P, Q = verts[p], verts[q]
            if P[1] == Q[1] and frozenset((p, q)) not in done:
                done.add(frozenset((p, q)))
                m = on_surface([(x + y) / 2 for x, y in zip(P, Q)])
                edges.append("arc %d %d (%.8f %g %.8f)" % (p, q, *m))
elif a.shape == "sphere":
    done = set()
    for f in patches["box"]:
        projected.append("project (%d %d %d %d) sphere" % tuple(f))
        for p, q in zip(f, f[1:] + f[:1]):
            if frozenset((p, q)) not in done:
                done.add(frozenset((p, q)))
                edges.append("project %d %d (sphere)" % (p, q))

with open(a.out, "w") as o:
    o.write("// Written by makeBodyMesh.py --shape %s (run it again for another body)\n" % a.shape)
    o.write("FoamFile\n{\n    version 2.0;\n    format  ascii;\n    class   dictionary;\n"
            "    object  blockMeshDict;\n}\n\nscale 1;\n\n")
    if a.shape == "sphere":
        o.write("geometry\n{\n    sphere\n    {\n        type searchableSphere;\n"
                "        centre (0 0 0);\n        radius %g;\n    }\n}\n\n" % R)
    o.write("vertices\n(\n")
    for i, p in enumerate(verts):
        o.write("    (%g %g %g)    // %d\n" % (p + (i,)))
    o.write(");\n\nblocks\n(\n")
    for v, n in blocks:
        o.write("    hex (%s) (%d %d %d) simpleGrading (1 1 1)\n" % (" ".join(map(str, v)), *n))
    o.write(");\n\nedges\n(\n" + "".join("    %s\n" % e for e in edges) + ");\n\n")
    if projected:
        o.write("faces\n(\n" + "".join("    %s\n" % e for e in projected) + ");\n\n")
    o.write("boundary\n(\n")
    for name, fs in patches.items():
        ptype = ("patch" if is3D else "empty") if name.startswith("wall") else "patch"
        o.write("    %s\n    {\n        type %s;\n        faces\n        (\n" % (name, ptype))
        o.write("".join("            (%d %d %d %d)\n" % tuple(f) for f in fs))
        o.write("        );\n    }\n")
    o.write(");\n")
print("%s: %s, %d blocks, about %d cells" %
      (a.out, a.shape, len(blocks), sum(n[0] * n[1] * n[2] for _, n in blocks)))

# 5. Mass properties (plate mass = displaced water, so the draft does not change)
if a.properties:
    if a.shape not in ("box", "boxPlate"):
        ap.error("--properties is for box and boxPlate only")
    mb, zb, ib = 3.148, -0.0126, 0.0167         # Day 3 box
    mass, zg, iyy, ixx, izz = mb, zb, ib, 0.015, 0.021
    if a.shape == "boxPlate":
        bp, tp, ly = a.plateWidth, a.plateThickness, 0.2
        mp, zp = 1000 * bp * tp * ly, -DRAFT - a.plateGap - tp / 2
        mass = mb + mp
        zg = (mb * zb + mp * zp) / mass
        shift = mb * (zb - zg) ** 2 + mp * (zp - zg) ** 2
        ixx = 0.015 + mp * (ly ** 2 + tp ** 2) / 12 + shift
        iyy = ib + mp * (bp ** 2 + tp ** 2) / 12 + shift
        izz = 0.021 + mp * (bp ** 2 + ly ** 2) / 12
    with open(a.properties + "/massProperties", "w") as o:
        o.write("// Written by makeBodyMesh.py --shape %s: plate mass = its displacement\n" % a.shape)
        o.write("mass            %.4g;\ncentreOfMass    (0 0 %.4g);\n"
                "momentOfInertia (%.4g %.4g %.4g);\n" % (mass, zg, ixx, iyy, izz))
    name, text = a.properties + "/lines_v2_bodyC.txt", []
    for line in open(name):
        w = line.split()
        if len(w) > 10 and w[1] == "Coupled":
            line = ("1    Coupled     0      0    %.4f  0       0      0     %.4f"
                    "  0    0       0       0      0\n" % (zg, mass))
        elif len(w) == 9 and w[1] == "Body1":       # fairleads stay on the box
            line = ("%s     Body1     %7.4f  %7.4f  %7.4f  0      0       0      0\n"
                    % (w[0], float(w[2]), float(w[3]), -0.0736 - zg))
        text.append(line)
    open(name, "w").writelines(text)
    print("mass %.3f kg  zG %.4f m  Iyy %.4f kg m2" % (mass, zg, iyy))
