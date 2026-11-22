#!/usr/bin/env python3
"""
Compare runs of the project cases: motions, mooring tension, waves, loads.

    python3 compareRuns.py run1 run2 run3               # table over the last wave periods
    python3 compareRuns.py run1 run2 --plot compare.png --csv compare.csv
    python3 compareRuns.py run1 --start 13.04 --end 23  # chosen time window

Regular waves: the window is the largest whole number of wave periods (at most 5)
before the last common time and after --settle (default 8 s); T is read from
constant/waveProperties or given with --T.
Focused waves: give --start and --end, and use the max / min columns.

Amplitudes are (max - min)/2 in each period, averaged over the periods.
"1st" and "2nd" are harmonic amplitudes at T and T/2. Surge and heave are measured
from the initial centre of gravity, pitch is in degrees.
Needs numpy (matplotlib for --plot).
"""
import argparse
import glob
import os
import re
import numpy as np

DEPTH = 0.5     # water depth [m]


def table(path):
    """Numeric rows of a postProcessing file; brackets are ignored, cut lines dropped."""
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


def restarts(case, obj, name):
    """All time folders of one function object joined (restarted runs)."""
    files = sorted(glob.glob(os.path.join(case, "postProcessing", obj, "*", name)),
                   key=lambda p: float(os.path.basename(os.path.dirname(p))))
    data = None
    for p in files:
        d = table(p)
        if d is None:
            continue
        data = d if data is None else np.vstack([data[data[:, 0] < d[0, 0]], d])
    return data


def read_case(case):
    s = {}
    d = restarts(case, "sixDoFState", "sixDoFRigidBodyState.dat")
    if d is not None:
        s["surge [m]"] = d[:, 0], d[:, 4]
        try:
            z0 = float(re.search(r"centreOfMass\s*\(\s*\S+\s+\S+\s+([-\d.eE+]+)", "".join(
                open(p).read() for p in (os.path.join(case, "constant", n)
                                         for n in ("massProperties", "dynamicMeshDict"))
                if os.path.exists(p))).group(1))
        except AttributeError:
            z0 = d[0, 6]
        s["heave [m]"] = d[:, 0], d[:, 6] - z0
        s["pitch [deg]"] = d[:, 0], d[:, 8]
    for p in glob.glob(os.path.join(case, "Mooring", "*.out")):
        if re.search(r"_(Line|Body|Point)\d+\.out$", p):
            continue
        d = table(p)
        if d is not None and d.shape[1] >= 6:
            s["tension line 1 [N]"] = d[:, 0], d[:, 4]      # seaward line
            s["tension line 3 [N]"] = d[:, 0], d[:, 5]      # leeward line
    d = restarts(case, "waveGauges", "height.dat")
    if d is not None:
        pos = glob.glob(os.path.join(case, "postProcessing", "waveGauges", "*", "height.dat"))[0]
        loc = []
        with open(pos) as f:
            for line in f:
                m = re.match(r"#\s*Location\s+\d+\s*:\s*\((\S+)\s+\S+\s+(\S+)\)", line)
                if m:
                    loc.append(float(m.group(1)))
                elif not line.startswith("#"):
                    break
        for i, x in enumerate(loc):
            s["eta x=%g [m]" % x] = d[:, 0], d[:, 2 * i + 1] - DEPTH     # height above the bottom
    d = restarts(case, "box_forces", "force.dat")
    if d is not None:
        s["Fx [N]"] = d[:, 0], d[:, 1]
        s["Fz [N]"] = d[:, 0], d[:, 3]
    for side in ("Bottom", "Deck", "Front", "Back"):
        d = restarts(case, "force_box" + side, "force.dat")
        if d is not None:
            s["F%s %s [N]" % ("z" if side in ("Bottom", "Deck") else "x", side)] = \
                d[:, 0], d[:, 3 if side in ("Bottom", "Deck") else 1]
        d = restarts(case, "max_box" + side, "surfaceFieldValue.dat")
        if d is not None:
            s["p max %s [Pa]" % side] = d[:, 0], d[:, 1]
        d = restarts(case, "areaAverage_box" + side, "surfaceFieldValue.dat")
        if d is not None and side == "Deck":
            s["wetted fraction Deck"] = d[:, 0], d[:, 2]
    return s


def period(case, given):
    if given:
        return given
    try:
        with open(os.path.join(case, "constant", "waveProperties")) as f:
            m = re.search(r"^\s*wavePeriod\s+([\d.]+)", f.read(), re.M)
    except OSError:
        return 1.993
    return float(m.group(1)) if m else 1.993


def stats(t, y, t0, t1, T):
    ok = np.concatenate(([True], np.diff(t) > 0))
    t, y = t[ok], y[ok]
    keep = (t >= t0) & (t <= t1)
    if keep.sum() < 10:
        return None
    tu = np.linspace(t0, t1, 4000, endpoint=False)
    yu = np.interp(tu, t, y)
    r = dict(mean=yu.mean(), max=y[keep].max(), min=y[keep].min())
    n = int(round((t1 - t0) / T))
    if n >= 1 and abs(n * T - (t1 - t0)) < 0.05 * T:
        parts = np.array_split(yu, n)
        r["amp"] = float(np.mean([(p.max() - p.min()) / 2 for p in parts]))
        for k, name in ((1, "1st"), (2, "2nd")):
            r[name] = 2 * abs(np.mean((yu - yu.mean()) * np.exp(-2j * np.pi * k * (tu - t0) / T)))
    return r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cases", nargs="+")
    ap.add_argument("--start", type=float)
    ap.add_argument("--end", type=float)
    ap.add_argument("--settle", type=float, default=8.0, help="ignore the start-up [s] (8)")
    ap.add_argument("--T", type=float, help="wave period [s]")
    ap.add_argument("--plot", help="png file")
    ap.add_argument("--csv", help="csv file")
    a = ap.parse_args()

    data = [(os.path.basename(os.path.normpath(os.path.abspath(c))), c, read_case(c)) for c in a.cases]
    data = [x for x in data if x[2]]
    if not data:
        raise SystemExit("No results found (postProcessing/, Mooring/*.out)")
    tend = a.end if a.end is not None else min(
        max(t[-1] for t, _ in s.values()) for _, _, s in data) - 1e-3

    cols = ("mean", "amp", "1st", "2nd", "max", "min")
    csv = ["case,quantity,t0,t1," + ",".join(cols)]
    for name, case, s in data:
        T = period(case, a.T)
        t1 = min(tend, min(t[-1] for t, _ in s.values()))
        if a.start is not None:
            t0 = a.start
        else:
            t0 = t1 - min(5, max(1, int((t1 - a.settle) / T))) * T
        print("\n%s   window %.2f .. %.2f s   T = %g s" % (name, t0, t1, T))
        print("  %-24s" % "" + "".join("%11s" % c for c in cols))
        for key, (t, y) in s.items():
            r = stats(t, y, t0, t1, T)
            if r:
                print("  %-24s" % key + "".join(
                    "%11.4g" % r[c] if c in r else "%11s" % "-" for c in cols))
                csv.append("%s,%s,%.3f,%.3f," % (name, key, t0, t1)
                           + ",".join("%.6g" % r[c] if c in r else "" for c in cols))
    if a.csv:
        with open(a.csv, "w") as f:
            f.write("\n".join(csv) + "\n")
    if a.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        keys = ["eta x=-1 [m]", "surge [m]", "heave [m]", "pitch [deg]", "tension line 1 [N]"]
        extra = [k for k in ("Fz Deck [N]", "wetted fraction Deck", "Fx Front [N]", "Fz Bottom [N]")
                 if any(k in s for _, _, s in data)]
        keys = [k for k in keys + extra if any(k in s for _, _, s in data)]
        fig, ax = plt.subplots(len(keys), 1, sharex=True, figsize=(10, 1.7 * len(keys)), squeeze=False)
        for axis, key in zip(ax[:, 0], keys):
            for name, _, s in data:
                if key in s:
                    axis.plot(*s[key], lw=0.9, label=name)
            axis.set_ylabel(key, fontsize=8)
            axis.grid(alpha=0.3)
        ax[0, 0].legend(fontsize=8)
        ax[-1, 0].set_xlabel("time [s]")
        ax[-1, 0].set_xlim(a.start if a.start is not None else 0, tend)
        fig.tight_layout()
        fig.savefig(a.plot, dpi=110)
        print("\nWrote", a.plot)


if __name__ == "__main__":
    main()
