#!/usr/bin/env python3
"""
Mooring visualisation in ParaView from MoorDyn output.
Based on MooringVisualizationInParaview.py by Sithik Aliyar.

Standalone: needs only Python 3 and numpy, works from any folder.

    cd <case>;  python3 <path>/Tools/mooringToParaview.py
    python3 <path>/Tools/mooringToParaview.py <case-folder>

By default it writes one mooring frame for every time folder the solver saved
(i.e. at the controlDict writeInterval), so the mooring and the flow fields have
the same times in ParaView. If there are no time folders (e.g. deleted, or the
case is decomposed and not reconstructed, processor0 is checked first) the
times come from writeInterval in system/controlDict.

Options:  --start/--end <t>  limit the window,  --dt <s>  own interval,
          --all  every MoorDyn output time.

It reads the MoorDyn line files  Mooring/<prefix>_Line<N>.out  (or Mooring/Line<N>.out)
and writes

    Mooring/VTP/mooring_<time>.vtp  one file per time: all lines, node positions,
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


def time_folders(case):
    """Names of the time folders the solver wrote (case or processor0)."""
    for d in (case, os.path.join(case, "processor0")):
        if not os.path.isdir(d):
            continue
        names = []
        for n in os.listdir(d):
            if os.path.isdir(os.path.join(d, n)):
                try:
                    names.append((float(n), n))
                except ValueError:
                    pass
        if names:
            return sorted(names), d
    return [], None


def controlDict_times(case, t_last):
    """Write times from system/controlDict when no time folders exist."""
    cd = os.path.join(case, "system", "controlDict")
    if not os.path.isfile(cd):
        return []
    txt = re.sub(r"//.*", "", open(cd).read())

    def get(key, default=None):
        m = re.search(r"^\s*%s\s+([^;\s]+)\s*;" % key, txt, re.M)
        return m.group(1) if m else default

    try:
        interval = float(get("writeInterval"))
        t0 = float(get("startTime", "0"))
        t1 = float(get("endTime", t_last))
    except (TypeError, ValueError):
        return []
    if get("writeControl", "timeStep") == "timeStep":
        interval *= float(get("deltaT", "0"))
    if interval <= 0:
        return []
    t1 = min(t1, t_last)
    n = int(np.floor((t1 - t0) / interval + 1e-6))
    return [(t0 + k * interval, "%g" % (t0 + k * interval)) for k in range(n + 1)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case", nargs="?", default=".", help="case folder containing Mooring/ (default: current folder)")
    ap.add_argument("--start", type=float, default=None, help="first time to write")
    ap.add_argument("--end", type=float, default=None, help="last time to write")
    ap.add_argument("--dt", type=float, default=None,
                    help="own frame interval instead of the solver write times")
    ap.add_argument("--all", action="store_true", help="every MoorDyn output time (many files)")
    args = ap.parse_args()

    case = os.path.abspath(args.case)
    mooring_dir = os.path.join(case, "Mooring")
    line_files = find_line_files(mooring_dir)
    if not line_files:
        sys.exit("No Mooring/*Line<N>.out files in %s\n"
                 "Run this from the case folder after the simulation, or give the case folder:\n"
                 "    python3 mooringToParaview.py <case-folder>" % case)

    lines = {}
    for n, f in line_files.items():
        lines[n] = read_line(f)
        print("Read %s: %d times, %d nodes" % (os.path.basename(f), lines[n][1].shape[0], lines[n][1].shape[1]))

    # Lines may have a different number of rows if the run is still going: use the common part
    nt = min(v[0].shape[0] for v in lines.values())
    time = lines[min(lines)][0][:nt]
    md_dt = np.median(np.diff(time)) if nt > 1 else 0.0

    # Frame times: (time value, label used in the file name)
    if args.all:
        frames = [(t, "%g" % t) for t in time]
        print("Frames: every MoorDyn output")
    elif args.dt is not None:
        t0 = time[0] if args.start is None else args.start
        t1 = time[-1] if args.end is None else args.end
        frames = [(t, "%g" % t) for t in np.arange(t0, t1 + 0.5 * args.dt, args.dt)]
        print("Frames: every %g s" % args.dt)
    else:
        frames, where = time_folders(case)
        if frames:
            print("Frames: the %d time folders in %s" % (len(frames), where))
        else:
            frames = controlDict_times(case, time[-1])
            if not frames:
                sys.exit("No time folders and no writeInterval in system/controlDict; use --dt or --all")
            print("Frames: writeInterval from system/controlDict (%d times)" % len(frames))

    # Keep frames inside the MoorDyn record and the requested window
    tol = 0.5 * md_dt + 1e-9
    lo = time[0] if args.start is None else args.start
    hi = time[-1] if args.end is None else args.end
    frames = [(t, name) for t, name in frames
              if time[0] - tol <= t <= time[-1] + tol and lo - 1e-9 <= t <= hi + 1e-9]
    if not frames:
        sys.exit("No frame times inside the MoorDyn output (%g .. %g s)" % (time[0], time[-1]))

    vtp_dir = os.path.join(mooring_dir, "VTP")
    os.makedirs(vtp_dir, exist_ok=True)
    for f in glob.glob(os.path.join(vtp_dir, "mooring_*.vtp")):
        os.remove(f)

    entries = []
    worst = 0.0
    for t, label in frames:
        it = int(np.argmin(np.abs(time - t)))
        worst = max(worst, abs(time[it] - t))
        name = "mooring_%s.vtp" % label
        write_vtp(os.path.join(vtp_dir, name), t, lines, it)
        entries.append((t, "VTP/" + name))
    pvd = os.path.join(mooring_dir, "Mooring.pvd")
    write_pvd(pvd, entries)
    print("Wrote %d files in %s (t = %g .. %g)" % (len(entries), vtp_dir, entries[0][0], entries[-1][0]))
    print("Largest gap between a frame and the nearest MoorDyn output: %.3g s" % worst)
    print("Open in ParaView:  %s  (together with case.foam)" % pvd)


if __name__ == "__main__":
    main()
