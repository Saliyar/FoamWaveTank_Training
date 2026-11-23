# Day 3 - Moored floating box

2D box (0.2 m x 0.2 m, draft 0.0786 m, 3.148 kg) moored with four MoorDyn
lines (`Mooring/lines_v2_bodyC.txt`, MoorDyn v2, BODY coupling) in regular
StokesII waves, H = 0.1195 m. Body motion with the OpenFOAM
`sixDoFRigidBodyMotion` solver (Newmark) in `waveIsoFoam`, or with FloatStepper
(`floatStepper`, `floaterMeshMotionSolver`). The tank is 5 m long (x -2.5 .. 2.5).

| Folder | Solver | Body motion (`constant/dynamicMeshDict`) | Output |
|--------|--------|--------------------------------------------|--------|
| `waveIsoFoam/mooredBox` | `waveIsoFoam` | `sixDoFRigidBodyMotion` + `moorDynR2` restraint | `sixDoFState`, `box_forces` |
| `FloatStepper/mooredBox` | `floatStepper` | `floaterMeshMotionSolver` (`pisoAddedMass`, update every 4th step) + `moorDynR2` restraint | `floaterMotion` |

Same mesh, box, mooring input and wave in both. `HOS_FloatStepper/` (see below) has the same
box and mooring in HOS-NWT waves.

Output: 10 wave gauges at x = -2 .. 2 (waves2Foam probes in
`postProcessing/surfaceElevation`, 50 Hz) and the line tensions in `Mooring/`, plus
`postProcessing/sixDoFState` and `postProcessing/box_forces` (`waveIsoFoam`) or
`postProcessing/floaterMotion` (`FloatStepper`).

`endTime` is 23 s (the full experiment window). Serial run times on a DTU HPC core:

| Mesh | Cells | Command | `waveIsoFoam` | `FloatStepper` |
|------|------:|---------|---------:|---------:|
| medium (default) | 3760 | `./Allrun` | 12 min | 20 min |
| coarse (quick look) | 1088 | `MESH=coarse ./Allrun` | 6 min | 8 min |

The coarse mesh is for a quick look: its pitch amplitude is about 60 % of the medium-mesh one.

`waveIsoFoam` here needs a build with moving-mesh support. `Allrun` defaults to the development
build on the DTU cluster; elsewhere use `SOLVER=/path/to/waveIsoFoam ./Allrun`
(or `FWT_PLAIN=/path/to/build`, with `bin/` and `lib/`).

## HOS-NWT + FloatStepper (`HandsonExercise/HOS_FloatStepper`)

The same mesh, box, mooring and numerics as `FloatStepper/mooredBox`, with `floatStepperWaveIsoFoam`
and the HOS wave in 1 m relaxation zones at both ends and in the initial field.

| Case | Wave | CFD t = 0 is HOS | `endTime` | HOS + CFD, medium | `MESH=coarse` |
|------|------|-----:|-----:|-----:|-----:|
| `mooredBox` | Day 1 `potentialFlowWaves/HOS/MooredBoxRegularWaves` | 4 s | 23 s | 24 min | 12 min |
| `mooredBoxFocusedWave` | as Day 4 `mooredBoxFocusedWave/HOS`, focus at the box at t = 10 s | 15 s | 15 s | 12 min | 7 min |

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

Without the box the wave is within 5 % (RMS/H) of HOS at all gauges (medium mesh). With it, the
regular-wave amplitudes (t = 13 - 23 s) are 92 % (surge), 93 % (heave) and 89 % (pitch) of
`FloatStepper/mooredBox`. The waves differ: the HOS piston adds a free second harmonic, so H varies
along the tank. The box first settles about 5 mm into the mooring, as in `FloatStepper/mooredBox`.
The table below is for the Stokes II cases: the HOS wave has not been compared with the experiment.

## How good are the results?

Medium mesh, t = 13 - 23 s, against the experiment of Wu et al. (BOX3):

| Quantity | Result |
|----------|--------|
| Surge | good: amplitude 8 - 11 % high |
| Heave | good: amplitude 4 - 6 % high |
| Pitch | known model error: about 80 deg late in phase, peak too high |
| Line tension | fair: amplitude 11 - 17 % low, the sharp peaks of the measurement are missed |

The sign conventions of the experiment are inferred from the data (surge, pitch and load
cell reversed), not documented. Use surge and heave for validation. Why pitch is late is a good question for discussion.

## Mooring lines in ParaView

After the run (or while it runs), in the case folder:

    python3 ../../../../Tools/mooringToParaview.py                 # one frame per saved time folder
    python3 ../../../../Tools/mooringToParaview.py --start 5 --end 20

(or give the case folder as argument: `python3 Tools/mooringToParaview.py <case>`).
The frames follow the time folders the solver wrote (writeInterval in
`system/controlDict`), so mooring and flow have the same times in ParaView.

It reads `Mooring/*_Line<N>.out` (node positions and segment tensions) and
writes `Mooring/VTP/mooring_<time>.vtp` plus the time series `Mooring/Mooring.pvd`.
Open `case.foam` and `Mooring/Mooring.pvd` together in ParaView; the times
match the flow solution. Colour the lines by `Tension` (N per segment) or
`LineID`. Needs only numpy.
