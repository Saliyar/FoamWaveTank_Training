#!/usr/bin/env python3
"""
Mooring visualisation in ParaView from MoorDyn output.
Based on MooringVisualizationInParaview.py by Sithik Aliyar.

Run it from the case folder after the simulation (or while it runs):

    python3 mooringToParaview.py                 # all output times
    python3 mooringToParaview.py --start 5 --end 20 --dt 0.05

It reads the MoorDyn line files  Mooring/<prefix>_Line<N>.out  (or Mooring/Line<N>.out)
and writes

    Mooring/VTP/mooring_<i>.vtp   one file per time: all lines, node positions,
                                  segment tension (CellData "Tension") and
                                  node height (PointData "z")
    Mooring/Mooring.pvd           time series -> open this in ParaView

In ParaView: open case.foam and Mooring/Mooring.pvd together; the times match.
Requires only numpy.
"""
import argparse
import glob
import os
import re
import sys

import numpy as np


def find_line_files(mooring_dir):
    files = glob.glob(os.path.join(mooring_dir, "*Line*.out"))
    found = {}
    for f in files:
        m = re.search(r"(?:^|_)Line(\d+)\.out$", os.path.basename(f))
        if m:
            found.setdefault(int(m.group(1)), []).append(f)
    lines = {}
    for n, fs in found.items():
        if len(fs) > 1:
            sys.exit("Several output files for Line%d: %s\nKeep one set in Mooring/." % (n, fs))
        lines[n] = fs[0]
    return dict(sorted(lines.items()))


def read_line(filename):
    with open(filename) as fid:
        header = fid.readline().split()
        fid.readline()  # units line: (s) (m) ...
        data = np.loadtxt(fid, ndmin=2)
    col = {name: i for i, name in enumerate(header)}
    nnode = 0
    while "Node%dpx" % nnode in col:
        nnode += 1
    if nnode < 2:
        sys.exit("%s: no NodeNpx/py/pz columns. Set line outputs to 'pt' in the MoorDyn input." % filename)
    pos = np.stack([data[:, [col["Node%dp%s" % (i, c)] for c in "xyz"]] for i in range(nnode)], axis=1)
    ten = None
    for base in (1, 0):  # MoorDyn v2 numbers segments Seg1..SegN, older versions from 0
        names = ["Seg%dTe" % (i + base) for i in range(nnode - 1)]
        if all(n in col for n in names):
            ten = data[:, [col[n] for n in names]]
            break
    if ten is None:
        print("  (no segment tension columns in %s; add 't' to the line outputs)" % os.path.basename(filename))
    return data[:, 0], pos, ten  # time (nt), pos (nt, nnode, 3), tension (nt, nseg)


def write_vtp(filename, t, lines, it):
    out = ['<?xml version="1.0"?>',
           "<!-- MoorDyn mooring lines, time = %g -->" % t,
           '<VTKFile type="PolyData" version="0.1" byte_order="LittleEndian">',
           "  <PolyData>"]
    for n, (_, pos, ten) in lines.items():
        p = pos[it]
        nn = p.shape[0]
        out.append('    <Piece NumberOfPoints="%d" NumberOfLines="%d">' % (nn, nn - 1))
        out.append("      <PointData>")
        out.append('        <DataArray type="Float32" Name="z" format="ascii">')
        out.append(" ".join("%.6g" % v for v in p[:, 2]))
        out.append("        </DataArray>")
        out.append("      </PointData>")
        out.append("      <CellData>")
        out.append('        <DataArray type="Int32" Name="LineID" format="ascii">')
        out.append(" ".join([str(n)] * (nn - 1)))
        out.append("        </DataArray>")
        if ten is not None:
            out.append('        <DataArray type="Float32" Name="Tension" format="ascii">')
            out.append(" ".join("%.6g" % v for v in ten[it]))
            out.append("        </DataArray>")
        out.append("      </CellData>")
        out.append("      <Points>")
        out.append('        <DataArray type="Float32" NumberOfComponents="3" format="ascii">')
        out.extend("%.6g %.6g %.6g" % tuple(x) for x in p)
        out.append("        </DataArray>")
        out.append("      </Points>")
        out.append("      <Lines>")
        out.append('        <DataArray type="Int32" Name="connectivity" format="ascii">')
        out.append(" ".join("%d %d" % (i, i + 1) for i in range(nn - 1)))
        out.append("        </DataArray>")
        out.append('        <DataArray type="Int32" Name="offsets" format="ascii">')
        out.append(" ".join(str(2 * (i + 1)) for i in range(nn - 1)))
        out.append("        </DataArray>")
        out.append("      </Lines>")
        out.append("    </Piece>")
    out += ["  </PolyData>", "</VTKFile>", ""]
    with open(filename, "w") as fid:
        fid.write("\n".join(out))


def write_pvd(filename, entries):
    with open(filename, "w") as fid:
        fid.write('<?xml version="1.0"?>\n<VTKFile type="Collection" version="0.1">\n  <Collection>\n')
        for t, f in entries:
            fid.write('    <DataSet timestep="%.10g" part="0" file="%s"/>\n' % (t, f))
        fid.write("  </Collection>\n</VTKFile>\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case", nargs="?", default=".", help="case folder containing Mooring/ (default .)")
    ap.add_argument("--start", type=float, default=None, help="first time to write (default: first output)")
    ap.add_argument("--end", type=float, default=None, help="last time to write (default: last output)")
    ap.add_argument("--dt", type=float, default=None, help="time between frames (default: every MoorDyn output)")
    args = ap.parse_args()

    mooring_dir = os.path.join(args.case, "Mooring")
    line_files = find_line_files(mooring_dir)
    if not line_files:
        sys.exit("No *Line<N>.out files in %s. Has the simulation run?" % mooring_dir)

    lines = {}
    for n, f in line_files.items():
        lines[n] = read_line(f)
        print("Read %s: %d times, %d nodes" % (os.path.basename(f), lines[n][1].shape[0], lines[n][1].shape[1]))

    # Lines may have a different number of rows if the run is still going: use the common part
    nt = min(v[0].shape[0] for v in lines.values())
    time = lines[min(lines)][0][:nt]

    t0 = time[0] if args.start is None else args.start
    t1 = time[-1] if args.end is None else args.end
    if args.dt is None:
        idx = np.where((time >= t0 - 1e-12) & (time <= t1 + 1e-12))[0]
    else:
        targets = np.arange(t0, t1 + 0.5 * args.dt, args.dt)
        idx = np.unique([np.argmin(np.abs(time - t)) for t in targets])
    if len(idx) == 0:
        sys.exit("No MoorDyn output between t = %g and %g (output covers %g .. %g)" % (t0, t1, time[0], time[-1]))

    vtp_dir = os.path.join(mooring_dir, "VTP")
    os.makedirs(vtp_dir, exist_ok=True)
    for f in glob.glob(os.path.join(vtp_dir, "mooring_*.vtp")):
        os.remove(f)

    entries = []
    for k, it in enumerate(idx):
        name = "mooring_%05d.vtp" % k
        write_vtp(os.path.join(vtp_dir, name), time[it], lines, it)
        entries.append((time[it], "VTP/" + name))
    pvd = os.path.join(mooring_dir, "Mooring.pvd")
    write_pvd(pvd, entries)
    print("Wrote %d VTP files and %s (t = %g .. %g)" % (len(entries), pvd, entries[0][0], entries[-1][0]))



if __name__ == "__main__":
    main()
