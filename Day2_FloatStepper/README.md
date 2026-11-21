# Day 2 - Floating bodies with FloatStepper

Freely floating box (0.3 m x 0.2 m, 12 kg, surge, heave and pitch free) in
the Ren et al. (2015) wave tank, depth 0.4 m. Body motion with the
FloatStepper algorithm (Roenby et al. 2024, Royal Society Open Science,
https://doi.org/10.1098/rsos.231453).

| Case | Wave | Solver |
|------|------|--------|
| `01_freeBoxRegularWaves` | StokesV, H = 0.1 m, T = 1.2 s (OpenFOAM waveModels) | `floatStepper` |
| `02_freeBoxFocusedWave` | NewWave (JONSWAP, Tp = 1.2 s, crest 0.06 m) focused on the box at t = 10 s (waves2Foam) | `floatStepperWaveFoam` |

Mesh: `blockMesh`, refinement band around the free surface (`refineMesh`),
the box is cut out (`subsetMesh`) and moved to its start position
(`moveDynamicMesh`). Case 02 has the tank extended upstream to x = -2 m for
the inlet relaxation zone.

After case 01: `python3 compareExpNum.py` compares surge, heave and pitch
with the experiment (`Ren2015data/`).
