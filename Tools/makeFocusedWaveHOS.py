#!/usr/bin/env python3
"""
Focused wave group for HOS-NWT ("type: file", "format: cfg+dat").

Writes <name>.cfg and <name>.dat: linear wave components with a JONSWAP
amplitude distribution (NewWave: a_n proportional to S(f_n) df, sum a_n = A)
and phases chosen so that all crests meet at x = xf (HOS frame) at t = tf.

    python3 makeFocusedWaveHOS.py                       # defaults below
    python3 makeFocusedWaveHOS.py --A 0.05 --xf 9 --tf 25 --out focusedWave

Run it in the HOS case folder (or give --out with a path). Needs numpy.
Linear focusing only: nonlinear and wavemaker effects shift the real focus a
little in x and t, which is part of the exercise.
"""
import argparse
import numpy as np

G = 9.81


def wavenumber(f, h):
    w = 2 * np.pi * f
    k = w * w / G
    for _ in range(100):
        k = k - (G * k * np.tanh(k * h) - w * w) / (G * np.tanh(k * h) + G * k * h / np.cosh(k * h) ** 2)
    return k


def jonswap(f, Tp, gamma):
    fp = 1.0 / Tp
    sigma = np.where(f <= fp, 0.07, 0.09)
    r = np.exp(-((f - fp) ** 2) / (2 * sigma ** 2 * fp ** 2))
    return f ** -5 * np.exp(-1.25 * (fp / f) ** 4) * gamma ** r


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--A", type=float, default=0.06, help="linear crest amplitude at the focus [m] (0.06)")
    ap.add_argument("--Tp", type=float, default=1.2, help="peak period [s] (1.2)")
    ap.add_argument("--gamma", type=float, default=3.3, help="JONSWAP peak factor (3.3)")
    ap.add_argument("--fmin", type=float, default=0.4, help="lowest frequency [Hz] (0.4)")
    ap.add_argument("--fmax", type=float, default=1.4, help="highest frequency [Hz] (1.4)")
    ap.add_argument("--xf", type=float, default=9.0, help="focus position, HOS x [m] (9)")
    ap.add_argument("--tf", type=float, default=25.0, help="focus time, HOS t [s] (25)")
    ap.add_argument("--depth", type=float, default=0.5, help="water depth [m] (0.5)")
    ap.add_argument("--wavemaker", choices=["piston", "hinged"], default="piston")
    ap.add_argument("--hinge", type=float, default=0.0, help="hinge height above bottom [m] (hinged only)")
    ap.add_argument("--rnum", type=int, default=12, help="df = clock / 2^rnum (12)")
    ap.add_argument("--clock", type=float, default=32.0, help="clock rate [Hz] (32): df = 0.0078 Hz, repeat 128 s")
    ap.add_argument("--out", default="focusedWave", help="file name without extension (focusedWave)")
    a = ap.parse_args()

    df = a.clock / 2 ** a.rnum
    n = np.arange(int(np.ceil(a.fmin / df)), int(np.floor(a.fmax / df)) + 1)
    f = n * df
    S = jonswap(f, a.Tp, a.gamma)
    amp = a.A * S / S.sum()
    k = wavenumber(f, a.depth)
    # HOS-NWT convention: eta(x, t) = sum a_n cos(w_n t - k_n x + phi_n) (phi_n = wave at x = 0);
    # all crests meet at (xf, tf) when w_n tf - k_n xf + phi_n = 0
    phase = k * a.xf - 2 * np.pi * f * a.tf
    phase = np.angle(np.exp(1j * phase))  # wrap to [-pi, pi]

    with open(a.out + ".cfg", "w") as c:
        # cut-offs 0 / 100 Hz: HOS-NWT compares them, made non-dimensional, with the
        # dimensional frequencies and would drop the components; the band is set
        # by the components written in the .dat file instead
        for v in (a.rnum, a.clock, a.depth, 3, "lin", 0.0, 100.0, 1.0, a.wavemaker, a.hinge):
            c.write(" %s \n" % v)
    with open(a.out + ".dat", "w") as d:
        for ni, fi, ai, pi in zip(n, f, amp, phase):
            d.write("%d , %.8e , %.8e , %.8e , %.8e , \n" % (ni, fi, ai, 0.0, pi))

    cg = lambda ff, kk: np.pi * ff / kk * (1 + 2 * kk * a.depth / np.sinh(2 * kk * a.depth))
    slow = a.xf / cg(f[-1], k[-1])
    print("Wrote %s.cfg and %s.dat: %d components %.3f .. %.3f Hz, df = %.5f Hz"
          % (a.out, a.out, len(n), f[0], f[-1], df))
    print("Focus: A = %.3f m at x = %g m, t = %g s (slowest component needs %.1f s to get there)"
          % (a.A, a.xf, a.tf, slow))
    if slow > a.tf:
        print("WARNING: tf is too early for the highest frequencies; increase tf or lower fmax")


if __name__ == "__main__":
    main()
