# Day 4 - SWENSE on the moored box

The Day 3 case (same mesh, box, mooring and wave) with the SWENSE
decomposition: the incident wave is known (Stokes II, or HOS-NWT for the
focused wave) and the solver computes only the complementary field (`Uc`, `pc`) caused by the body. The
complementary flow is solved in `bodyZone`, the cells around the box.

| Case | Body motion | Solver |
|------|-------------|--------|
| `WaveIsoFoamSWENSE/mooredBox` | sixDoFRigidBodyMotion + MoorDyn (as Day 3) | `waveIsoFoamSWENSE` (moving-body version) |
| `WaveIsoFoamSWENSE/mooredBoxFocusedWave` | as above, focused wave from HOS-NWT | `waveIsoFoamSWENSE` (moving-body version) |
| `FloatStepperSWENSE/mooredBox` | FloatStepper + MoorDyn (as Day 2) | `floatStepperSWENSE` |

Serial run times on one core of a DTU HPC node:

| Run | Cells | Time |
|-----|------:|-----:|
| `WaveIsoFoamSWENSE/mooredBox` | 3760 | 16 min |
| the same with `MESH=coarse ./Allrun` | 1088 | 6 min |
| for comparison, Day 3 `waveIsoFoam/mooredBox` with `MESH=coarse` | 1088 | 5 min |
| `WaveIsoFoamSWENSE/mooredBoxFocusedWave` (HOS-NWT + CFD) | 3760 | 10 min |

The focused wave has the Day 2 parameters (crest 0.06 m, Tp 1.2 s, gamma 3.3, focus at
the box at 10 s) in the 0.5 m deep Day 3 tank, with components up to 1.4 Hz. `Allrun`
runs HOS-NWT first: it needs LAPACK and FFTW at run time (on the DTU cluster:
`module load lapack/3.11.0 fftw/3.3.10`), or set `HOSNWT=/path/to/HOS-NWT`.

Wave gauges: `postProcessing/surfaceElevation`, 50 Hz. In these cases `sets` in
`system/controlDict` must be a dictionary `{ }`, not a list `( )`.

Solver builds: until the moving-body SWENSE is merged to master, `Allrun`
uses the development builds; set `SOLVER=...` (or `FWT_DYN` / `FWT_FS`) to
use another build.

`FloatStepperSWENSE` is not yet validated. floatStepperSWENSE requires all moving mesh
points to lie inside `bodyZone`, so its zone comes from `system/topoSetDict`
and its mesh morphing from `constant/dynamicMeshDict` (not the zone of `WaveIsoFoamSWENSE`).

## Mooring lines in ParaView

Use `Tools/mooringToParaview.py` as in the Day 3 README: from a case folder,
`python3 ../../../../Tools/mooringToParaview.py`, then open `Mooring/Mooring.pvd`.
