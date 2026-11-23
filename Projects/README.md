# Student projects - moored floating box in waves

Thirteen projects of 12-16 hours, to be done after Days 1-3. All start from the
Day 3 moored box, solved with `waveIsoFoam` of FoamWaveTank
(`sixDoFRigidBodyMotion` + MoorDyn v2, `moorDynR2` restraint). Each folder has the
problem description (`<project>.pdf`) and one ready, tested case (`setup/`).
**Read the PDF first.**

| # | Project | You vary | How |
|---|---------|----------|-----|
| 1 | [Wave height](01_WaveHeight/01_WaveHeight.pdf) | H | `constant/waveProperties` |
| 2 | [Wave period](02_WavePeriod/02_WavePeriod.pdf) | T at H = 0.06 m | `constant/waveProperties` |
| 3 | [Relaxation zone, HOS wave](03_RelaxationZone_HOS/03_RelaxationZone_HOS.pdf) | zone length and shape | `constant/waveProperties.input` |
| 4 | [Mass and draft](04_MassDraft/04_MassDraft.pdf) | draft, mass | `python3 setBox.py --draft ..` |
| 5 | [Inertia](05_Inertia/05_Inertia.pdf) | Iyy | `constant/dynamicMeshDict` |
| 6 | [Taut and catenary mooring](06_TautVsCatenary/06_TautVsCatenary.pdf) | mooring system | `MOORING=taut ./Allrun` |
| 7 | [Focused wave slamming, HOS wave](07_FocusedWaveSlamming/07_FocusedWaveSlamming.pdf) | amplitude, focus point | `Tools/makeFocusedWaveHOS.py` |
| 8 | [Green water](08_GreenWater/08_GreenWater.pdf) | freeboard, H, T | `python3 setBox.py --height ..` |
| 9 | [Turbulence model](09_TurbulenceModel/09_TurbulenceModel.pdf) | RANS model, inflow level | `TURB=laminar ./Allrun` |
| 10 | [Body shape, same mass](10_BodyShape/10_BodyShape.pdf) | box, cylinder, sphere | `SHAPE=sphere ./Allrun` |
| 11 | [Courant number](11_CourantNumber/11_CourantNumber.pdf) | maxCo, maxAlphaCo | `system/controlDict` |
| 12 | [Mesh refinement](12_MeshRefinement/12_MeshRefinement.pdf) | cell size | `MESH=fine ./Allrun` |
| 13 | [Heave plate](13_HeavePlate/13_HeavePlate.pdf) | plate size, gap | `makeBodyMesh.py`, `BODY=box ./Allrun` |

## Running

```sh
source <OpenFOAM-v2506>/etc/bashrc
cd Projects/01_WaveHeight
cp -r setup H004            # one copy per run, next to setup; keep setup clean
cd H004
#   ... make the change described in the PDF
NP=8 ./Allrun               # default 4 cores; NP=1 is serial
./Allclean                  # back to the clean case
```

On the DTU cluster use `sbatch runSlurm.sh` in the case folder. Options are passed
on with `sbatch --export=ALL,MESH=coarse runSlurm.sh`.

The setups use `waveIsoFoam` from `./Allwmake` of FoamWaveTank (set `SOLVER` for
another build). Projects 3 and 7 also need HOS-NWT (`HOSNWT=/path/to/HOS-NWT`):
the wave is computed in `HOS/` and imposed in waves2Foam relaxation zones. All
other projects generate the wave at the inlet with OpenFOAM `waveModels`, as on
Day 3. A 23 s run of the default case takes about 35-75 minutes on 8 cores.

## Comparing runs

From a project folder:

```sh
python3 ../Tools/compareRuns.py setup H004 H010 --plot compare.png --csv compare.csv
```

It prints mean, amplitude, first and second harmonic, maximum and minimum of
motions, tensions, wave gauges and forces. For the mooring lines in ParaView run
`python3 ../../../Tools/mooringToParaview.py` from a case folder.

## Differences from the Day 3 case

- Parallel by default; fields written every 0.5 s; wave gauges at x = -2 ... 2 m.
- All projects keep the Day 3 mesh-morphing band (`innerDistance 0.075`,
  `outerDistance 0.4`). It held in all test runs, also on the fine mesh, with
  taut lines and with the curved and 3D bodies.
- Project 9 solves k, omega and epsilon with `smoothSolver`.
- Projects 3 and 7 use waves2Foam relaxation zones (`constant/waveProperties.input`)
  instead of the inlet and outlet boundary conditions.
