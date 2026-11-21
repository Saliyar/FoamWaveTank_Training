# FoamWaveTank Training

Hands-on exercises for the FoamWaveTank course (4 days). Every exercise is
a complete OpenFOAM case with an `Allrun` (mesh, initial fields, probes,
serial run) and an `Allclean` (resets the case to the state in git).

| Day | Topic | Exercises (`DayN_*/HandsonExercise/`) | Solver |
|-----|-------|----------------------------------------|--------|
| 1 | Waves | `01_regularWaves`, `02_irregularWaves`, `03_focusedWave` | `waveIsoFoam` |
| 2 | Floating bodies with FloatStepper | `01_freeBoxRegularWaves`, `02_freeBoxFocusedWave` | `floatStepper`, `floatStepperWaveFoam` |
| 3 | Moored floating box | `mooredBox_waveIsoFoam` | `waveIsoFoam` + sixDoF + MoorDyn |
| 4 | SWENSE on the moored box | `01_mooredBox_waveIsoFoamSWENSE`, `02_mooredBox_floatStepperSWENSE` | `waveIsoFoamSWENSE`, `floatStepperSWENSE` |

## Requirements

- OpenFOAM v2506 (openfoam.com)
- FoamWaveTank (waves2Foam, waveIsoFoam, waveIsoFoamSWENSE, MoorDyn
  restraints, FloatStepper), compiled with `./Allwmake`

## Running an exercise

```sh
source <OpenFOAM-v2506>/etc/bashrc
cd Day1_Waves/HandsonExercise/01_regularWaves
./Allrun          # serial
paraview case.foam
./Allclean        # back to the clean case
```

Logs are written to `log.<application>`; wave gauges, forces and body
motions go to `postProcessing/`.

## Tools

`tools/mooringToParaview.py` turns the MoorDyn line output (`Mooring/*_Line<N>.out`)
into a ParaView time series `Mooring/Mooring.pvd` with segment tensions. A copy is in
each moored-box case (Day 3, Day 4); run `python3 mooringToParaview.py` in the case folder.

## Status (Nov 2026)

- Day 1 runs in serial in 5 to 10 minutes (regular 5.0, irregular 10.3,
  focused 5.3 min on one DTU HPC core).
- Days 2 to 4 are set up with their full physical times (20 s, 15 s, 23 s);
  they take about one hour or more in serial and will be shortened before
  the course.
- Day 4 runs the moving-body SWENSE solvers from development builds (see the
  `Allrun` of each case); they will be in FoamWaveTank master before the course.
