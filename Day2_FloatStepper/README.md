# Day 2 - Floating bodies with FloatStepper

Freely floating box (0.3 m x 0.2 m, 12 kg, surge, heave and pitch free) in
the Ren et al. (2015) wave tank, depth 0.4 m. The same two tutorials are run
with two body-motion solvers, and with the wave from HOS-NWT:

- `FloatStepper/`: the FloatStepper algorithm (Roenby et al. 2024, Royal Society
  Open Science, https://doi.org/10.1098/rsos.231453), `floaterMeshMotionSolver`
  with its added-mass model.
  `FloatStepper/BestSetup/` has the two tutorial cases unchanged (full mesh, added mass
  every step) for anyone who wants the full-accuracy set-up; they need hours or
  several cores (see its README).
- `waveIsoFoam/`: `waveIsoFoam` with the OpenFOAM `sixDoFRigidBodyMotion`
  solver (Newmark). The mesh motion, the box boundary conditions
  and the output differ; the box is cut out directly at x = 2 m.
- `HOS_FloatStepper/`: FloatStepper with the incident wave from HOS-NWT through Grid2Grid (see below).

| Case (in both folders) | Wave | `FloatStepper/` | `waveIsoFoam/` |
|------|------|------|------|
| `01_freeBoxRegularWaves` | StokesV, H = 0.1 m, T = 1.2 s (OpenFOAM waveModels) | `floatStepper` | `waveIsoFoam` |
| `02_freeBoxFocusedWave` | NewWave (JONSWAP, Tp = 1.2 s, crest 0.06 m) focused on the box at t = 10 s (waves2Foam) | `floatStepperWaveFoam` | `waveIsoFoam` |

## Course set-up: serial runs, `./Allrun`

| Case | Cells | `endTime` | Serial run time |
|------|------:|----------:|----------------:|
| `waveIsoFoam/01_freeBoxRegularWaves` | 7160 | 20 s | 10 min |
| `waveIsoFoam/02_freeBoxFocusedWave` | 9400 | 15 s | 11 min |
| `FloatStepper/01_freeBoxRegularWaves` | 7160 | 15 s | 15 min |
| `FloatStepper/02_freeBoxFocusedWave` | 9400 | 12 s | 15 min |

Times are from one core of a DTU HPC node. All four use a graded `blockMesh` (the box is cut
out with `subsetMesh`; in `FloatStepper/` at x = 2.3 m and then moved to x = 2 m) and waves2Foam
wave gauges at 50 Hz (`postProcessing/surfaceElevation`). Case 02 has the tank extended upstream
to x = -2 m for the inlet relaxation zone.

- `waveIsoFoam/`: Laplacian mesh motion (`constant/dynamicMeshDict`); the 6-DoF body is the
  boundary condition of `box` in `0.orig/pointDisplacement`. The box motion is in `log.waveIsoFoam`.
- `FloatStepper/`: added mass updated every 4th step (`MaddUpdateFreq 4`).

`waveIsoFoam` here needs a build with moving-mesh support. `Allrun` defaults to the development
build on the DTU cluster; elsewhere use `SOLVER=/path/to/waveIsoFoam ./Allrun`
(or `FWT_PLAIN=/path/to/build`, with `bin/` and `lib/`).

## HOS-NWT + FloatStepper (`HandsonExercise/HOS_FloatStepper`)

The same box, mesh and numerics as `FloatStepper/02_freeBoxFocusedWave` (`floatStepperWaveFoam`),
with the Day 1 HOS waves in both relaxation zones and in the initial field.

| Case | Wave (as Day 1 `potentialFlowWaves/HOS`) | CFD t = 0 is HOS | `endTime` | HOS + CFD, serial |
|------|------|-----:|-----:|-----:|
| `01_freeBoxRegularWaves` | `FloatingBoxRegularWaves` | 5 s | 14 s | 26 min |
| `02_freeBoxFocusedWave` | `FloatingBoxFocusedWave`, focus at the box at t = 10 s | 15 s | 12 s | 17 min |

`./Allrun` runs HOS-NWT first (3-4 min, skipped if `HOS/Results` is complete). It needs LAPACK
and FFTW at run time (on the DTU cluster: `module load lapack/3.11.0 fftw/3.3.10`);
`HOSNWT=/path/to/HOS-NWT ./Allrun` to use another build. `./Allclean` also deletes the HOS result.

The coupling is the one of Day 1 `potentialFlowWaves`, with two differences for a floating body:

- `referenceTime` is chosen so that the waves are upstream and the water at the box is almost
  calm (< 0.6 mm) at CFD t = 0. Day 1 starts inside the developed wave, which would give the
  box at rest an impulsive start.
- The box centre is at HOS x = 9 m (`referencePosition`), and both relaxation zones are outside
  the morphing mesh around the box.

`setWaveField` warns that Tsoft is non-zero and that it starts from still water. Ignore this for
`externalSource`: the warning is always printed, and the HOS field is set. `Allrun` stops if
`setWaveField` is a build that does not update Grid2Grid to the start time.

Gauges against HOS, after the run: `python3 ../../../../Tools/compareHOS_CFD.py`

Without the box the wave is within 0.4 % (RMS/H) of HOS at x = -1 m. On this coarse mesh it loses
about 10 % of its height on the way to the box, so compare with the gauges, not only with the input.

Compared with `FloatStepper/`: regular waves (t = 7.8 - 14 s, amplitudes) surge +12 %, heave +13 %,
pitch -2 %; focused wave (t = 8 - 12 s, ranges) surge -4 %, heave +9 %, pitch +4 %. The waves are
not identical: HOS is nonlinear and has a wavemaker. `compareExpNum.py` does not apply here,
because the phase of the wave differs.

## How accurate is the course set-up?

Regular waves, t = 7.2 - 10 s, amplitude as a share of `FloatStepper/BestSetup`:

| | Surge | Heave | Pitch |
|---|---:|---:|---:|
| `waveIsoFoam` | 93 % | 99 % | 90 % |
| `FloatStepper` | 85 % | 102 % | 68 % |

Heave is good. Pitch is far below the measurement: 43 % of it with `waveIsoFoam`, 32 % with
`FloatStepper`, and 47 % even with the best set-up. The coarse mesh also damps the focused wave
(crest about 13 % lower at the box than on a 2x finer mesh, see Day 1 case 05). Use `BestSetup`
for accuracy; use the course set-up to learn the method.

After case 01: `python3 compareExpNum.py` compares surge, heave and pitch
with the experiment (`Ren2015data/`).
