# FoamWaveTank Training

Hands-on exercises for the FoamWaveTank course (4 days). Every exercise is
a complete OpenFOAM case with an `Allrun` (mesh, initial fields, probes,
serial run) and an `Allclean` (resets the case to the state in git).

| Day | Topic | Exercises (`DayN_*/HandsonExercise/`) | Solver |
|-----|-------|----------------------------------------|--------|
| 1 | Waves | `waveFoam/` and `waveIsoFoam/`, each with `01_regularWaves`, `02_irregularWaves`, `03_focusedWave`; `potentialFlowWaves/` | `waveFoam`, `waveIsoFoam`, HOS-NWT + Grid2Grid |
| 2 | Free floating box | `waveIsoFoam/` and `FloatStepper/`, each with `01_freeBoxRegularWaves`, `02_freeBoxFocusedWave`; the same two in `HOS_FloatStepper/` | `waveIsoFoam` + sixDoF; `floatStepper`, `floatStepperWaveIsoFoam`; HOS-NWT + Grid2Grid |
| 3 | Moored floating box | `waveIsoFoam/mooredBox`, `FloatStepper/mooredBox`; `HOS_FloatStepper/mooredBox` and `mooredBoxFocusedWave` | `waveIsoFoam` + sixDoF + MoorDyn; `floatStepper` + MoorDyn; HOS-NWT + `floatStepperWaveIsoFoam` |
| 4 | SWENSE on the moored box | `WaveIsoFoamSWENSE/mooredBox` and `mooredBoxFocusedWave`, `FloatStepperSWENSE/mooredBox` | `waveIsoFoamSWENSE`, `floatStepperSWENSE` |

## Student projects

`Projects/` has 13 projects of 12-16 hours based on the Day 3 moored box, solved
with `waveIsoFoam` + sixDoF + MoorDyn v2 (no SWENSE). Each has a problem
description (PDF) and one tested setup; see [Projects/README.md](Projects/README.md).

## Requirements

- OpenFOAM v2506 (openfoam.com)
- FoamWaveTank (waves2Foam, waveIsoFoam, waveIsoFoamSWENSE, MoorDyn
  restraints, FloatStepper), compiled with `./Allwmake`
- HOS-NWT (https://gitlab.com/lheea/HOS-NWT) on the `PATH` or in `HOSNWT` for Day 1
  `potentialFlowWaves`, Day 2 and 3 `HOS_FloatStepper` and the Day 4 focused wave (needs LAPACK
  and FFTW at run time). The coupled cases also need a `setWaveField` that updates Grid2Grid
  to the start time (`externalWave->step()`).
- Python 3 with numpy (matplotlib for the plots) for the `Tools/` scripts

- Day 2 and Day 3 `waveIsoFoam` cases and the projects use `waveIsoFoam` of
  FoamWaveTank (with moving-mesh support); set `SOLVER=/path/to/waveIsoFoam`
  for another build.

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
  of the coupled cases (Day 1 `potentialFlowWaves/CFD`, Day 2 and 3 `HOS_FloatStepper`). From a CFD case folder:
  `python3 <repo>/Tools/compareHOS_CFD.py`
- `Tools/makeFocusedWaveHOS.py` writes the HOS-NWT wavemaker files (`.cfg`/`.dat`) for a
  focused wave group (Day 1 `potentialFlowWaves/HOS/FocusingWaves`).
- `Tools/mooringToParaview.py` turns the MoorDyn line output (`Mooring/*_Line<N>.out`)
  into a ParaView time series `Mooring/Mooring.pvd` with segment tensions (Day 3, Day 4).
  From a case folder: `python3 ../../../../Tools/mooringToParaview.py` (one frame per saved time folder)
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
- Day 2 and Day 3 `HOS_FloatStepper` run in serial in 12 to 26 minutes including HOS-NWT.
- Day 4 `WaveIsoFoamSWENSE` runs in serial in 16 minutes (regular), 6 with `MESH=coarse`,
  and 10 minutes for the focused wave (needs HOS-NWT).
  `FloatStepperSWENSE` is work in progress: it stops at about 1.5 s.
- Projects: 23 s of a default setup take about 35-75 minutes on 8 cores.
- Day 4 runs the moving-body SWENSE solvers from development builds (see the
  `Allrun` of each case); they will be in FoamWaveTank master before the course.

## Licence

- OpenFOAM cases, scripts and `Tools/`: GNU General Public License v3.0 or later,
  see [LICENSE](LICENSE).
- Text and project PDFs: Creative Commons Attribution 4.0 (CC BY 4.0),
  see [LICENSE-docs.md](LICENSE-docs.md).

To cite this material, use [CITATION.cff](CITATION.cff) ("Cite this repository" on GitHub).

## Credits

The exercises use:

- OpenFOAM v2506 (https://www.openfoam.com)
- waves2Foam: N. G. Jacobsen, D. R. Fuhrman, J. Fredsøe (2012), Int. J. Numer. Meth. Fluids 70, 1073-1088
- isoAdvector (waveIsoFoam): J. Roenby, H. Bredmose, H. Jasak (2016), R. Soc. Open Sci. 3, 160405
- HOS-NWT and Grid2Grid (https://gitlab.com/lheea/HOS-NWT): G. Ducrozet et al. (2012), Eur. J. Mech. B/Fluids 34, 19-34
- MoorDyn: M. Hall, A. Goupee (2015), Ocean Engineering 104, 590-603

Validation data:

- Free floating box (Days 1-2): B. Ren, M. He, P. Dong, H. Wen (2015), Applied Ocean Research 50, 1-12
- Moored box (Day 3 and projects): M. Wu et al. (2019), Energies 12, 1834

OpenFOAM® is a registered trademark of OpenCFD Limited, producer and distributor
of the OpenFOAM software via www.openfoam.com. This offering is not approved or
endorsed by OpenCFD Limited.
