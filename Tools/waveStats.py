#!/usr/bin/env python3
"""
Wave statistics at the wave gauges of one or more cases: are the waves the same?

    python3 waveStats.py <case> [<case> ...] [--start t0] [--end t1]

For every gauge it prints the mean zero-upcrossing wave height H, crest and
trough height, mean period T and the largest crest (with its time) in the
time window [t0, t1] (default: the second half of each record). Use it to
check that the same wave reaches the box in Day 1, 2, 3 and 4, e.g.

    python3 Tools/waveStats.py Day1_Waves/HandsonExercise/06_mooredBoxRegularWaves \\
                               Day3_MooredBox/HandsonExercise/waveIsoFoam/mooredBox --start 10

It reads, whichever the case has:
  OpenFOAM interfaceHeight   postProcessing/<name>/<t>/position.dat
                             (eta = interface z - its value at the first time,
                             so the case must start from still water)
  waves2Foam waveGauges      postProcessing/surfaceElevation/<t>/surfaceElevation.dat
  HOS-NWT                    Results/probes.dat with the x positions in prob.inp
Times and positions are those of each case (no mapping). Needs numpy.
"""
import argparse
import glob
import os
import re
import sys

import numpy as np


def _restarts(files):
    """Join records of several start-time folders (restarts), sorted in time."""
    files = sorted(files, key=lambda f: float(os.path.basename(os.path.dirname(f))))
    return files


def read_interface_height(case):
    out = []
    names = sorted({os.path.basename(os.path.dirname(os.path.dirname(f)))
                    for f in glob.glob(os.path.join(case, "postProcessing", "*", "*", "position.dat"))})
    for name in names:
        files = _restarts(glob.glob(os.path.join(case, "postProcessing", name, "*", "position.dat")))
        t, z, x = [], [], None
        for f in files:
            for line in open(f):
                if line.startswith("#"):
                    continue
                vec = re.findall(r"\(([^)]*)\)", line)
                if not vec:
                    continue
                p = np.array([v.split() for v in vec], float)
                if x is None:
                    x = p[:, 0]
                t.append(float(line.split()[0]))
                z.append(p[:, 2])
        if t:
            t, z = np.array(t), np.array(z)
            t, i = np.unique(t, return_index=True)
            z = z[i]
            out.append(("interfaceHeight %s" % name, x, t, z - z[0]))
    return out


def read_waves2foam(case):
    files = _restarts(glob.glob(os.path.join(case, "postProcessing", "surfaceElevation", "*", "surfaceElevation.dat")))
    if not files:
        return []
    x, rows = None, []
    for f in files:
        for line in open(f):
            p = line.split()
            if not p or p[0] == "Time":
                continue
            v = float(p[0])
            if v == -1:
                x = np.array(p[1:], float)
            elif v >= 0:
                rows.append([float(s) for s in p])
    d = np.array(rows)
    d = d[np.unique(d[:, 0], return_index=True)[1]]
    return [("waves2Foam surfaceElevation", x, d[:, 0], d[:, 1:])]


def read_hos(case):
    pf = os.path.join(case, "Results", "probes.dat")
    if not os.path.isfile(pf):
        return []
    rows = []
    for line in open(pf):
        try:
            rows.append([float(s) for s in line.split()])
        except ValueError:
            continue
    d = np.array([r for r in rows if len(r) == len(rows[-1])])
    x = np.loadtxt(os.path.join(case, "prob.inp"), ndmin=2)[:, 0]
    return [("HOS-NWT probes", x, d[:, 0], d[:, 1:])]


def stats(t, e):
    """Mean zero-upcrossing H, crest, trough, T; largest crest and its time."""
    e0 = e - e.mean()
    up = np.where((e0[:-1] < 0) & (e0[1:] >= 0))[0]
    imax = int(np.argmax(e))
    if len(up) < 2:
        return 0, np.nan, np.nan, np.nan, np.nan, e[imax], t[imax]
    H, C, Tr = [], [], []
    for a, b in zip(up[:-1], up[1:]):
        H.append(e[a:b + 1].max() - e[a:b + 1].min())
        C.append(e[a:b + 1].max())
        Tr.append(-e[a:b + 1].min())
    # period from interpolated up-crossing times
    tc = t[up] - e0[up] * (t[up + 1] - t[up]) / (e0[up + 1] - e0[up])
    return len(H), np.mean(H), np.mean(C), np.mean(Tr), np.mean(np.diff(tc)), e[imax], t[imax]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cases", nargs="+", help="case folders (CFD or HOS-NWT)")
    ap.add_argument("--start", type=float, help="start of the time window [s]")
    ap.add_argument("--end", type=float, help="end of the time window [s]")
    a = ap.parse_args()

    found = False
    for case in a.cases:
        sets = read_interface_height(case) + read_waves2foam(case) + read_hos(case)
        if not sets:
            print("%s: no wave gauge output found" % case)
            continue
        found = True
        for name, x, t, eta in sets:
            t0 = t[0] + 0.5 * (t[-1] - t[0]) if a.start is None else a.start
            t1 = t[-1] if a.end is None else a.end
            m = (t >= t0) & (t <= t1)
            print("\n%s  [%s]  t = %.2f .. %.2f s" % (os.path.relpath(case), name, t0, min(t1, t[-1])))
            print("%9s %6s %9s %9s %9s %8s %10s %8s" % ("x [m]", "waves", "H [m]", "crest", "trough", "T [s]",
                                                        "max eta", "at t"))
            for j in range(eta.shape[1]):
                if m.sum() < 3:
                    break
                n, H, c, tr, T, emax, tmax = stats(t[m], eta[m, j])
                print("%9.3f %6d %9.4f %9.4f %9.4f %8.3f %10.4f %8.2f" % (x[j], n, H, c, tr, T, emax, tmax))
    if not found:
        sys.exit(1)


if __name__ == "__main__":
    main()
