# FoamWaveTank Training

Hands-on exercises for the FoamWaveTank course (4 days). Every exercise is
a complete OpenFOAM case with an `Allrun` (mesh, initial fields, probes,
serial run) and an `Allclean` (resets the case to the state in git).

| Day | Topic | Exercises (`DayN_*/HandsonExercise/`) | Solver |
|-----|-------|----------------------------------------|--------|
| 1 | Waves | `waveFoam/` and `waveIsoFoam/`, each with `01_regularWaves`, `02_irregularWaves`, `03_focusedWave`; `potentialFlowWaves/` | `waveFoam`, `waveIsoFoam`, HOS-NWT + Grid2Grid |
| 2 | Free floating box | `waveIsoFoam/` and `FloatStepper/`, each with `01_freeBoxRegularWaves`, `02_freeBoxFocusedWave` | `waveIsoFoam` + sixDoF; `floatStepper`, `floatStepperWaveFoam` |
| 3 | Moored floating box | `waveIsoFoam/mooredBox`, `FloatStepper/mooredBox` | `waveIsoFoam` + sixDoF + MoorDyn; `floatStepper` + MoorDyn |
| 4 | SWENSE on the moored box | `01_mooredBox_waveIsoFoamSWENSE`, `02_mooredBox_floatStepperSWENSE` | `waveIsoFoamSWENSE`, `floatStepperSWENSE` |

## Requirements

- OpenFOAM v2506 (openfoam.com)
- FoamWaveTank (waves2Foam, waveIsoFoam, waveIsoFoamSWENSE, MoorDyn
  restraints, FloatStepper), compiled with `./Allwmake`
- HOS-NWT (https://gitlab.com/lheea/HOS-NWT) on the `PATH` for Day 1
  `potentialFlowWaves` (needs LAPACK and FFTW at run time)
- Python 3 with numpy (matplotlib for the plots) for the `Tools/` scripts

- Day 2 and Day 3 `waveIsoFoam` cases: a `waveIsoFoam` build with moving-mesh support.
  `Allrun` defaults to a development build on the DTU cluster; elsewhere set
  `SOLVER=/path/to/waveIsoFoam`.

## Running an exercise

```sh
source <OpenFOAM-v2506>/etc/bashrc
cd Day1_Waves/HandsonExercise/waveFoam/01_regularWaves
./Allrun          # serial
paraview case.foam
./Allclean        # back to the clean case
```

Logs are written to `log.<application>`; wave gauges, forces and body
motions go to `postProcessing/`.

## Tools

Post-processing scripts shared by all days live in `Tools/`.

- `Tools/compareHOS_CFD.py` plots the CFD wave gauges against the HOS-NWT probes
  of the coupled case (Day 1 `potentialFlowWaves/CFD`). From a CFD case folder:
  `python3 <repo>/Tools/compareHOS_CFD.py`
- `Tools/makeFocusedWaveHOS.py` writes the HOS-NWT wavemaker files (`.cfg`/`.dat`) for a
  focused wave group (Day 1 `potentialFlowWaves/HOS/FocusingWaves`).
- `Tools/mooringToParaview.py` turns the MoorDyn line output (`Mooring/*_Line<N>.out`)
  into a ParaView time series `Mooring/Mooring.pvd` with segment tensions (Day 3, Day 4).
  From a case folder: `python3 ../../../../Tools/mooringToParaview.py` in Day 3,
  `python3 ../../../Tools/mooringToParaview.py` in Day 4 (one frame per saved time folder)
- `Tools/waveStats.py` prints the mean wave height, crest, trough and period at every
  wave gauge of one or more cases (OpenFOAM `interfaceHeight`, waves2Foam gauges or
  HOS-NWT probes), e.g. to check that Day 1 to Day 4 have the same incident wave:
  `python3 Tools/waveStats.py <case1> <case2> --start 10`

## Status (Nov 2026)

- Day 1 `waveFoam/` and `waveIsoFoam/` run in serial in 7 to 16 minutes (regular 7-8,
  irregular 15, focused 8-9 min on one core of a shared DTU HPC node).
- Day 1 empty-tank cases `04` and `05` take about 1 minute each, `06` about 10 minutes.
- Day 2 runs in serial in 10 to 15 minutes per case (`BestSetup` takes hours on many cores).
- Day 3 runs in serial in 12 (`waveIsoFoam`) and 20 minutes (`FloatStepper`), or 6 and 8
  minutes with `MESH=coarse`.
- Day 4 is not updated yet: `waveIsoFoamSWENSE` takes about 70 minutes in serial and
  `floatStepperSWENSE` is work in progress (it stops at about 1.5 s).
- Day 4 runs the moving-body SWENSE solvers from development builds (see the
  `Allrun` of each case); they will be in FoamWaveTank master before the course.
