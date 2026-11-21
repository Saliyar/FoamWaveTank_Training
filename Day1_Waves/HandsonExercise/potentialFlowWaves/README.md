# Day 1 - Potential-flow waves (HOS-NWT) and CFD coupling (Grid2Grid)

The waves are first computed with the potential-flow solver **HOS-NWT** in a
20 m long, 0.5 m deep numerical wave tank with a wavemaker at x = 0 and an
absorbing beach from x = 15 m. The **CFD** case then solves only a part of
that tank (HOS x = 4 to 14 m) with `waveIsoFoam`. **Grid2Grid** reads the HOS
modes and supplies the wave in the relaxation zones and as the initial field.

```
HOS-NWT  x = 0 (wavemaker) ------------------------------------------ 15 ---- 20 m
                        4 |=========== CFD ===========| 14            beach
CFD      x =            0 |inlet 2.5|  gauges 3..7  |7.5 outlet| 10 m
```

| Folder | Wave | HOS | CFD time window |
|--------|------|-----|-----------------|
| `RegularWaves` | regular, H = 0.08 m, T = 1.5 s, piston | `type: regular` | HOS t = 10 to 30 s |
| `IrregularWaves` | JONSWAP, Hs = 0.06 m, Tp = 1.5 s, gamma 3.3 | `type: analytical spectrum` | HOS t = 10 to 40 s |
| `FocusingWaves` | focused group, A = 0.06 m at x = 9 m, t = 25 s | `type: file` (`focusedWave.cfg/.dat`) | HOS t = 15 to 30 s |
| `WavemakerMotion/Piston` | regular, H = 0.08 m, T = 2 s, piston wavemaker | `type: regular`, `piston` | HOS t = 10 to 30 s |
| `WavemakerMotion/Flap` | the same wave from a flap (hinged 0.1 m above the bottom) | `type: regular`, `hinged` | HOS t = 10 to 30 s |

The waves of the floating-box days (the same waves as Day 1 cases `04` - `06`):

| Folder | Wave | HOS | CFD time window |
|--------|------|-----|-----------------|
| `FloatingBoxRegularWaves` | Day 2a: H = 0.1 m, T = 1.2 s, depth 0.4 m | `type: regular` | HOS t = 15 to 35 s |
| `FloatingBoxFocusedWave` | Day 2b: NewWave JONSWAP, Tp = 1.2 s, A = 0.06 m (0.4 - 2 Hz), depth 0.4 m, focused at HOS x = 9 m, t = 25 s (CFD x = 5 m, t = 10 s) | `type: file` | HOS t = 15 to 30 s |
| `MooredBoxRegularWaves` | Day 3 and 4: H = 0.1195 m, T = 1.993 s, depth 0.5 m | `type: regular` | HOS t = 10 to 30 s |

These three HOS cases use x-filtering 0.6 (steep waves). The HOS amplitude
of `MooredBoxRegularWaves` is 0.0576 m, not H/2: the nonlinear HOS wave is
higher than the linear one, and 0.0576 m gives the mean H = 0.1195 m of Day 3
at the probes (`Tools/waveStats.py`). In this shallow-water wave (Ursell
number 16) the piston also makes a free second harmonic, so H varies between
0.110 and 0.132 m along the tank; HOS-NWT has no second-order wavemaker
correction for this.

`CFD/FloatingBoxRegularWaves` uses dx = 0.0125 m (nx 800) and maxCo 0.25:
this short, steep wave (ka = 0.16) lost 15 % of its height over 4 m with the
standard settings (dx = 0.025 m, maxCo 0.5) and still loses about 8 % (RMS
difference to HOS 4 - 9 % of H). It runs in about 25 minutes.

Each case has the same name under `HOS/` and `CFD/`.

## Running

```
cd HOS/RegularWaves && ./Allrun          # HOS-NWT: Results/probes.dat, Results/modes_HOS_SWENSE.dat
cd ../../CFD/RegularWaves && ./Allrun    # runs the HOS case first if its Results are missing
python3 ../../../../../Tools/compareHOS_CFD.py   # CFD gauges against the HOS probes
```

- HOS-NWT must be on the `PATH`, or set `HOSNWT=/path/to/HOS-NWT`.
  Source and binaries are at https://gitlab.com/lheea/HOS-NWT.
- `Allrun` in `HOS/` checks that HOS-NWT reached the end time. HOS-NWT stops
  with exit code 0 when its time step collapses, so a short `Results/` would
  otherwise look fine.

## The coupling, in `CFD/<case>/constant/`

- `Grid2Grid.dict`: the path to the HOS modes file (relative to the CFD case)
  and the vertical grid used to rebuild the HOS velocity.
- `waveProperties.input`: `externalForcing Grid2Grid` and the mapping
  `x_HOS = x_CFD - referencePosition`, `t_HOS = t_CFD + referenceTime`. CFD x = 0 is
  HOS x = 4 m. The CFD starts at HOS t = `referenceTime`, when the waves already
  fill the domain, and `setWaveField` takes that field as the initial condition.
  Both relaxation zones use `waveType externalSource` with `Tsoft 0`.
- Gauges at CFD x = 3 to 7 m are the HOS probes x = 7 to 11 m in `HOS/<case>/prob.inp`.

## Things to try

- Compare HOS and CFD (`Tools/compareHOS_CFD.py`): phase, crest height, and the
  start-up transient in the first wave periods.
- `WavemakerMotion`: compare `Results/wmk_motion.dat` (stroke at the free surface) of
  the piston and the flap for the same wave, and the waves at the probes.
- `FocusingWaves`: move the focus with `Tools/makeFocusedWaveHOS.py --xf --tf --A`
  (run in `HOS/FocusingWaves`). In the CFD, `referenceTime` sets when the CFD
  starts relative to the focus.
- Change `referencePosition` / `referenceTime` and see what the CFD receives.
- Steeper waves: the HOS run may stop ("minimum time step reached"). The
  `WavemakerMotion` cases need x-filtering (`filtering coefficients: x: 0.6`) for
  this. Try 0.8 or 1.0 with the flap; H = 0.1 m at T = 2 s does not run with the flap.
