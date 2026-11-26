#!/usr/bin/env python3
"""
Compare SWENSE (waveIsoFoamSWENSE) with plain waveIsoFoam on the Day 3/4 tank.

Wave only (Day 4 WaveOnly): wave height, crest and trough at every gauge against
Stokes II theory (H = 0.1195 m, T = 1.993 s, h = 0.5 m):

    python3 Tools/compareSWENSE.py waves <plain case> <SWENSE case> [more cases] [--plot waves.png]

Moored box (Day 3 waveIsoFoam/mooredBox against Day 4 WaveIsoFoamSWENSE/mooredBox):
mean and amplitude of surge, heave, pitch and line tensions, and the wave at the gauges:

    python3 Tools/compareSWENSE.py moored <plain case> <SWENSE case> [--plot moored.png]

Window: the last 5 wave periods before 23 s (13.04-23 s), or --start / --end.
Amplitudes are (max - min)/2 in each period, averaged. The run time of each case
is read from its solver log. Needs numpy (matplotlib for --plot).
"""
import argparse
import glob
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from waveStats import read_waves2foam  # noqa: E402

H, T, DEPTH, G = 0.1195, 1.993, 0.5, 9.81


def stokes2():
    """Wave length, crest and trough of the Stokes II wave of the tank."""
    w = 2 * np.pi / T
    k = w * w / G
    for _ in range(200):
        k = w * w / (G * np.tanh(k * DEPTH))
    s = np.tanh(k * DEPTH)
    a2 = k * H * H / 16 * (3 - s * s) / s ** 3
    return 2 * np.pi / k, H / 2 + a2, H / 2 - a2


def table(path):
    rows, n = [], None
    with open(path) as f:
        for line in f:
            if line.startswith("#"):
                continue
            w = line.replace("(", " ").replace(")", " ").split()
            try:
                row = [float(x) for x in w]
            except ValueError:
                continue
            if row and (n is None or len(row) == n):
                n = len(row)
                rows.append(row)
    return np.array(rows) if rows else None


def motions(case):
    s = {}
    files = glob.glob(os.path.join(case, "postProcessing", "sixDoFState", "*", "sixDoFRigidBodyState.dat"))
    if files:
        d = np.vstack([table(f) for f in sorted(files, key=lambda p: float(p.split(os.sep)[-2]))])
        d = d[np.unique(d[:, 0], return_index=True)[1]]
        s["surge [m]"] = d[:, 0], d[:, 4] - d[0, 4]
        s["heave [m]"] = d[:, 0], d[:, 6] - d[0, 6]
        s["pitch [deg]"] = d[:, 0], d[:, 8]
    for p in glob.glob(os.path.join(case, "Mooring", "*.out")):
        if re.search(r"_(Line|Body|Point)\d+\.out$", p):
            continue
        d = table(p)
        if d is not None and d.shape[1] >= 6:
            s["tension line 1 [N]"] = d[:, 0], d[:, 4]
            s["tension line 3 [N]"] = d[:, 0], d[:, 5]
    return s


def per_period(t, y, t0, t1):
    """Mean, mean amplitude, max and min over whole periods in [t0, t1]."""
    m = (t >= t0) & (t <= t1)
    if m.sum() < 10:
        return None
    amps = []
    a = t0
    while a + T <= t1 + 1e-9:
        k = (t >= a) & (t < a + T)
        if k.sum() > 2:
            amps.append(0.5 * (y[k].max() - y[k].min()))
        a += T
    return y[m].mean(), np.mean(amps) if amps else np.nan, y[m].max(), y[m].min()


def runtime(case):
    for log in sorted(glob.glob(os.path.join(case, "log.waveIsoFoam*"))):
        last = None
        for line in open(log, errors="ignore"):
            if line.startswith("ExecutionTime"):
                last = line
        if last:
            return float(last.split()[2])
    return np.nan


def cells(case):
    log = os.path.join(case, "log.checkMesh")
    if os.path.exists(log):
        m = re.search(r"cells:\s+(\d+)", open(log, errors="ignore").read())
        if m:
            return int(m.group(1))
    return 0


def label(case):
    return os.path.relpath(case)


def waves(cases, t0, t1, plot):
    L, crest, trough = stokes2()
    print("Stokes II theory: H = %.4f m, crest %.4f m, trough %.4f m, L = %.3f m" % (H, crest, trough, L))
    print("Window %.2f - %.2f s\n" % (t0, t1))
    data = []
    for c in cases:
        sets = read_waves2foam(c)
        if not sets:
            sys.exit("%s: no postProcessing/surfaceElevation" % c)
        _, x, t, eta = sets[0]
        data.append((c, x, t, eta))
    x = data[0][1]
    head = "%7s" % "x [m]" + "".join("  %-26s" % label(c)[-26:] for c, *_ in data)
    print(head)
    print("%7s" % "" + "".join("  %8s %8s %8s" % ("H/Hth", "crest", "trough") for _ in data))
    Hx = []
    for j in range(len(x)):
        line = "%7.2f" % x[j]
        row = []
        for c, xc, t, eta in data:
            m = (t >= t0) & (t <= t1)
            e = eta[m, j]
            hh, cc, tt = [], [], []
            a = t0
            while a + T <= t1 + 1e-9:
                k = (t[m] >= a) & (t[m] < a + T)
                if k.sum() > 2:
                    hh.append(e[k].max() - e[k].min())
                    cc.append(e[k].max())
                    tt.append(-e[k].min())
                a += T
            row.append(np.mean(hh) / H)
            line += "  %8.3f %8.4f %8.4f" % (np.mean(hh) / H, np.mean(cc), np.mean(tt))
        Hx.append(row)
        print(line)
    Hx = np.array(Hx)
    print("\nRMS error of H over all gauges, and cost:")
    for i, (c, *_) in enumerate(data):
        print("  %-40s %6.1f %%   %6d cells   %7.0f s" % (label(c)[-40:], 100 * np.sqrt(np.mean((Hx[:, i] - 1) ** 2)),
                                                       cells(c), runtime(c)))
    if plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        pick = [int(np.argmin(abs(x - v))) for v in (-2, -0.25, 2)]
        fig, ax = plt.subplots(len(pick) + 1, 1, figsize=(10, 2.4 * (len(pick) + 1)))
        w = 2 * np.pi / T
        k = 2 * np.pi / L
        for a, j in zip(ax, pick):
            tt = np.linspace(t0, t1, 2000)
            for c, xc, t, eta in data:
                m = (t >= t0) & (t <= t1)
                a.plot(t[m], eta[m, j], label=label(c))
            a.axhline(crest, color="k", ls=":", lw=0.8)
            a.axhline(-trough, color="k", ls=":", lw=0.8, label="Stokes II crest / trough")
            a.set_ylabel("eta [m], x = %.2f" % x[j])
        ax[0].legend(fontsize=7, loc="upper right")
        for i, (c, *_) in enumerate(data):
            ax[-1].plot(x, Hx[:, i], "o-", label=label(c))
        ax[-1].axhline(1, color="k", lw=0.8)
        ax[-1].set_xlabel("x [m]")
        ax[-1].set_ylabel("H / H_theory")
        ax[-1].legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(plot, dpi=130)
        print("plot:", plot)


def moored(cases, t0, t1, plot):
    print("Window %.2f - %.2f s\n" % (t0, t1))
    S = [(c, motions(c)) for c in cases]
    keys = [k for k in ("surge [m]", "heave [m]", "pitch [deg]", "tension line 1 [N]", "tension line 3 [N]")
            if all(k in s for _, s in S)]
    print("%-20s" % "" + "".join("  %-30s" % label(c)[-30:] for c, _ in S))
    print("%-20s" % "" + "".join("  %9s %9s %9s" % ("mean", "amplitude", "max") for _ in S))
    for k in keys:
        line = "%-20s" % k
        ref = None
        for c, s in S:
            r = per_period(*s[k], t0, t1)
            line += "  %9.4f %9.4f %9.4f" % (r[0], r[1], r[2])
            if ref is None:
                ref = r
        print(line)
    if len(S) > 1:
        print("\nAmplitude of each case relative to the first:")
        for k in keys:
            r0 = per_period(*S[0][1][k], t0, t1)
            print("  %-20s" % k + "".join("  %+7.1f %%" % (100 * (per_period(*s[k], t0, t1)[1] / r0[1] - 1))
                                         for _, s in S[1:]))
    print("\nCost:")
    for c, _ in S:
        print("  %-40s %6d cells   %7.0f s" % (label(c)[-40:], cells(c), runtime(c)))
    print("\nWave at the gauges (the scattered wave of the box is included):")
    waves(cases, t0, t1, None)
    if plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(len(keys), 1, figsize=(10, 2.2 * len(keys)), sharex=True)
        for a, k in zip(ax, keys):
            for c, s in S:
                t, y = s[k]
                a.plot(t, y, label=label(c), lw=1)
            a.axvspan(t0, t1, color="0.9")
            a.set_ylabel(k)
        ax[0].legend(fontsize=7, loc="upper left")
        ax[-1].set_xlabel("t [s]")
        fig.tight_layout()
        fig.savefig(plot, dpi=130)
        print("plot:", plot)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mode", choices=("waves", "moored"))
    ap.add_argument("cases", nargs="+")
    ap.add_argument("--start", type=float, default=23 - 5 * T)
    ap.add_argument("--end", type=float, default=23.0)
    ap.add_argument("--plot")
    a = ap.parse_args()
    (waves if a.mode == "waves" else moored)(a.cases, a.start, a.end, a.plot)


if __name__ == "__main__":
    main()
