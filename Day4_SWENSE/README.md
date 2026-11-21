# Day 4 - SWENSE on the moored box

The Day 3 case (same mesh, box, mooring and wave) with the SWENSE
decomposition: the incident wave is known analytically and the solver
computes only the complementary field (`Uc`, `pc`) caused by the body. The
complementary flow is solved in `bodyZone`, the cells around the box.

| Case | Body motion | Solver |
|------|-------------|--------|
| `01_mooredBox_waveIsoFoamSWENSE` | sixDoFRigidBodyMotion + MoorDyn (as Day 3) | `waveIsoFoamSWENSE` (moving-body version) |
| `02_mooredBox_floatStepperSWENSE` | FloatStepper + MoorDyn (as Day 2) | `floatStepperSWENSE` |

Solver builds: until the moving-body SWENSE is merged to master, `Allrun`
uses the development builds; set `SOLVER=...` (or `FWT_DYN` / `FWT_FS`) to
use another build.

Case 02 is not yet validated. floatStepperSWENSE requires all moving mesh
points to lie inside `bodyZone`, so its zone comes from `system/topoSetDict`
and its mesh morphing from `constant/dynamicMeshDict` (not the zone of case 01).
