# FloatStepper best setup (tutorial mesh and settings)

The two Day 2 cases exactly as in the FloatStepper tutorial (Roenby et al. 2024,
Ren et al. 2015 benchmark), for those who want the full-accuracy set-up:

| Case | Cells | `MaddUpdateFreq` |
|------|-------|------------------|
| `01_freeBoxRegularWaves` | 145,600 (free-surface band dx = dz = 0.005 m) | 1 (added mass every step) |
| `02_freeBoxFocusedWave` | 182,600 | 1 |

The cases in the parent folder use 1/20 of the cells and a cheaper added-mass update
to run in about 15 minutes in serial (to 15 s and 12 s).
The `BestSetup` cases need hours in serial (about 2.8 s per time step
for 40,000 cells, more for these meshes), so run them in parallel:

    NPROCS=16 ./Allrun        # decomposePar + mpirun floatStepper -parallel

`system/decomposeParDict` is set for 16 subdomains; `NPROCS` overrides it.
On the DTU cluster `OMPI_MCA_pml` is set with literal quotes by the module and
Open MPI rejects it: use `export OMPI_MCA_pml=ob1 OMPI_MCA_btl=self,vader` first
(single node).
