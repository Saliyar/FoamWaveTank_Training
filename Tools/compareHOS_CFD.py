#!/usr/bin/env python3
"""
Compare the free-surface elevation of a CFD case (waves2Foam gauges) with the
HOS-NWT probes it was coupled to (Grid2Grid).

    cd <CFD case>;  python3 <path>/Tools/compareHOS_CFD.py
    python3 <path>/Tools/compareHOS_CFD.py <CFD-case> [--hos <HOS-case>] [--no-plot]

It reads
  CFD: postProcessing/surfaceElevation/<t>/surfaceElevation.dat (gauge x on line "-1")
  HOS: <HOS-case>/Results/probes.dat and <HOS-case>/prob.inp
  map: constant/waveProperties.input  (referencePosition, referenceTime)
The HOS case is found from constant/Grid2Grid.dict (filePath) unless --hos is given.

For each CFD gauge it takes the HOS probe at the same place (x_HOS = x_CFD -
referencePosition), shifts the HOS time by referenceTime, and prints the RMS
difference relative to the HOS wave height. With matplotlib it also writes
compareHOS_CFD.png in the CFD case. Needs numpy (matplotlib optional).
"""
import argparse
import glob
import os
import re
import sys

import numpy as np


def foam_value(text, key):
    m = re.search(r"^\s*%s\s+([^;]+);" % key, re.sub(r"//.*", "", text), re.M)
    return m.group(1).strip() if m else None


def read_cfd(case):
    files = sorted(glob.glob(os.path.join(case, "postProcessing", "surfaceElevation", "*", "surfaceElevation.dat")),
                   key=lambda f: float(os.path.basename(os.path.dirname(f))))
    if not files:
        sys.exit("No postProcessing/surfaceElevation/*/surfaceElevation.dat in %s (has the case run?)" % case)
    x, rows = None, []
    for f in files:  # restarts write a new time folder: append them
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
    return x, d[:, 0], d[:, 1:]


def read_hos(hos):
    pf = os.path.join(hos, "Results", "probes.dat")
    if not os.path.isfile(pf):
        sys.exit("No %s (run the HOS case first)" % pf)
    rows = []
    for line in open(pf):
        p = line.split()
        try:
            rows.append([float(s) for s in p])
        except ValueError:
            continue
    d = np.array([r for r in rows if len(r) == len(rows[-1])])
    x = np.loadtxt(os.path.join(hos, "prob.inp"), ndmin=2)[:, 0]
    return x, d[:, 0], d[:, 1:]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("case", nargs="?", default=".", help="CFD case folder (default: current folder)")
    ap.add_argument("--hos", help="HOS case folder (default: from constant/Grid2Grid.dict)")
    ap.add_argument("--no-plot", action="store_true", help="only print the numbers")
    a = ap.parse_args()
    case = os.path.abspath(a.case)

    wp = open(os.path.join(case, "constant", "waveProperties.input")).read()
    ref = foam_value(wp, "referencePosition")
    x0 = float(ref.strip("()").split()[0]) if ref else 0.0
    t0 = float(foam_value(wp, "referenceTime") or 0.0)

    hos = a.hos
    if hos is None:
        g = open(os.path.join(case, "constant", "Grid2Grid.dict")).read()
        fp = foam_value(g, "filePath")
        hos = os.path.dirname(os.path.dirname(os.path.join(case, fp)))
    hos = os.path.abspath(hos)

    xc, tc, ec = read_cfd(case)
    xh, th, eh = read_hos(hos)
    print("CFD %s\nHOS %s\nmapping: x_HOS = x_CFD + %g,  t_HOS = t_CFD + %g" % (case, hos, -x0, t0))
    print("%8s %8s %10s %10s %10s" % ("x_CFD", "x_HOS", "H_HOS", "RMS diff", "RMS/H"))

    pairs = []
    for i, x in enumerate(xc):
        j = int(np.argmin(np.abs(xh - (x - x0))))
        if abs(xh[j] - (x - x0)) > 1e-3:
            print("%8.3f   no HOS probe at x_HOS = %g" % (x, x - x0))
            continue
        hos_on_cfd = np.interp(tc + t0, th, eh[:, j], left=np.nan, right=np.nan)
        ok = ~np.isnan(hos_on_cfd)
        H = np.nanmax(hos_on_cfd) - np.nanmin(hos_on_cfd)
        rms = np.sqrt(np.mean((ec[ok, i] - hos_on_cfd[ok]) ** 2))
        print("%8.3f %8.3f %10.4f %10.4f %10.3f" % (x, xh[j], H, rms, rms / H if H > 0 else np.nan))
        pairs.append((x, i, j))

    if a.no_plot or not pairs:
        return
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("(matplotlib not available: no plot)")
        return
    fig, axs = plt.subplots(len(pairs), 1, figsize=(9, 1.9 * len(pairs)), sharex=True, squeeze=False)
    for ax, (x, i, j) in zip(axs[:, 0], pairs):
        ax.plot(th - t0, eh[:, j], "k-", lw=1.2, label="HOS-NWT")
        ax.plot(tc, ec[:, i], "r--", lw=1.0, label="CFD")
        ax.set_xlim(tc[0], tc[-1])
        ax.set_ylabel("eta [m]")
        ax.set_title("x_CFD = %g m (x_HOS = %g m)" % (x, x - x0), fontsize=9, loc="left")
        ax.grid(alpha=0.3)
    axs[0, 0].legend(loc="upper right", fontsize=8)
    axs[-1, 0].set_xlabel("CFD time [s]  (HOS time - %g s)" % t0)
    fig.tight_layout()
    out = os.path.join(case, "compareHOS_CFD.png")
    fig.savefig(out, dpi=120)
    print("Plot: %s" % out)


if __name__ == "__main__":
    main()
