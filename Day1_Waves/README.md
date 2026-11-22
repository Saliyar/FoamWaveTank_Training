# Day 1 - Waves

2D numerical wave flume (18 m long, 0.5 m deep, about 33 000 cells) with
waves2Foam relaxation zones. The same three cases are given for two solvers:

- `waveFoam/`: `waveFoam` (MULES interface)
- `waveIsoFoam/`: `waveIsoFoam` (isoAdvector interface)

```
x = 0 ---- 3 ----------------------------- 12 --------------- 18 m
    | inlet |          working region       |   outlet zone   |
    | zone  |  gauges x = 4, 6, 8, 10, 12   |   (absorption)  |
```

| Case (in both folders) | Wave | `endTime` |
|------|------|-----------|
| `01_regularWaves` | Stokes 2nd order, H = 0.08 m, T = 1.5 s | 20 s |
| `02_irregularWaves` | JONSWAP, Hs = 0.06 m, Tp = 1.5 s, gamma 3.3, 100 components, random phases | 40 s |
| `03_focusedWave` | NewWave (JONSWAP), crest 0.06 m focused at x = 8 m, t = 15 s | 22 s |

Steps in `Allrun`: `blockMesh` -> `setWaveParameters` (reads
`constant/waveProperties.input`) -> `relaxationZoneLayout` -> `setWaveField`
-> `waveGaugesNProbes` (reads `constant/probeDefinitions`) -> the solver
(`application` in `system/controlDict`).

Surface elevation: `postProcessing/surfaceElevation/0/surfaceElevation.dat`.

Compare the solvers, from the repository root, with `python3 Tools/waveStats.py <waveFoam case> <waveIsoFoam case> --start 12`:
how much wave height does each lose along the tank?

Things to try: change H or T, the length of the relaxation zones, the
number of spectral components or the focus point and time.

## The waves of Day 2, 3 and 4 in the empty tank (cases 04 - 06)

The same tank, mesh, wave generation and gauges as the floating-body cases
of the later days, without the body. Run them on Day 1 to see the incident
wave the box will meet; compare with the Day 2 - 4 gauges upstream of the box.

| Case | Same wave as | Wave | Tank | Solver |
|------|--------------|------|------|--------|
| `04_floatingBoxRegularWaves` | Day 2 `01_freeBoxRegularWaves` | StokesV, H = 0.1 m, T = 1.2 s (OpenFOAM waveModels) | depth 0.4 m, x = 0 .. 8 m | `interIsoFoam` |
| `05_floatingBoxFocusedWave` | Day 2 `02_freeBoxFocusedWave` | NewWave JONSWAP, Tp = 1.2 s, crest 0.06 m at x = 2 m, t = 10 s (waves2Foam) | depth 0.4 m, x = -2 .. 8 m | `waveIsoFoam` |
| `06_mooredBoxRegularWaves` | Day 3 and Day 4 | StokesII, H = 0.1195 m, T = 1.993 s (OpenFOAM waveModels) | depth 0.5 m, x = -2.5 .. 2.5 m | `interIsoFoam` |

The box position is x = 2 m (Day 2) and x = 0 (Day 3, 4); each case has a
gauge there. `04` and `05` use the Day 2 course meshes (7280 and 9520 cells) and take
about 1 minute each in serial; `06` takes about 10 minutes. These meshes damp the waves:
at the box the focused crest of `05` is 0.042 m, against 0.048 m on a 2x finer mesh and
0.06 m nominal (linear focus). Measure the wave here before you judge the Day 2 motions.

Wave statistics at every gauge (mean wave height, crest, trough, period):

```
python3 ../../../Tools/waveStats.py . --start 8        # in a case folder
```

`04` also has the measured gauge record of the experiment
(`Ren2015data/H010WaveGauge`, as in Day 2).

## Potential-flow waves: HOS-NWT and CFD (`HandsonExercise/potentialFlowWaves`)

The same kinds of waves computed first with the potential-flow wave tank
HOS-NWT (`HOS/`) and then in a shorter CFD domain coupled to it with Grid2Grid
(`CFD/`): `RegularWaves`, `IrregularWaves`, `FocusingWaves` and
`WavemakerMotion/{Piston,Flap}`, and the Day 2 - 4 waves
`FloatingBoxRegularWaves`, `FloatingBoxFocusedWave` and `MooredBoxRegularWaves`.
See `potentialFlowWaves/README.md`. HOS-NWT must be installed
(https://gitlab.com/lheea/HOS-NWT).
