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
- HOS-NWT (https://gitlab.com/lheea/HOS-NWT) on the `PATH` for Day 1
  `potentialFlowWaves` (needs LAPACK and FFTW at run time)
- Python 3 with numpy (matplotlib for the plots) for the `Tools/` scripts

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

Post-processing scripts shared by all days live in `Tools/`.

- `Tools/compareHOS_CFD.py` plots the CFD wave gauges against the HOS-NWT probes
  of the coupled case (Day 1 `potentialFlowWaves/CFD`). From a CFD case folder:
  `python3 <repo>/Tools/compareHOS_CFD.py`
- `Tools/makeFocusedWaveHOS.py` writes the HOS-NWT wavemaker files (`.cfg`/`.dat`) for a
  focused wave group (Day 1 `potentialFlowWaves/HOS/FocusingWaves`).
- `Tools/mooringToParaview.py` turns the MoorDyn line output (`Mooring/*_Line<N>.out`)
  into a ParaView time series `Mooring/Mooring.pvd` with segment tensions (Day 3, Day 4).
  From a case folder: `python3 ../../../Tools/mooringToParaview.py` (one frame per saved time folder)

## Status (Nov 2026)

- Day 1 runs in serial in 5 to 10 minutes (regular 5.0, irregular 10.3,
  focused 5.3 min on one DTU HPC core).
- Days 2 to 4 are set up with their full physical times (20 s, 15 s, 23 s);
  they take about one hour or more in serial and will be shortened before
  the course.
- Day 4 runs the moving-body SWENSE solvers from development builds (see the
  `Allrun` of each case); they will be in FoamWaveTank master before the course.
