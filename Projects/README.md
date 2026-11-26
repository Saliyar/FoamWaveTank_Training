# Student projects - moored floating box in waves

Six group projects, to be done after Days 1-3. Each group project combines one to
four parts. Every part is a study of 12-16 hours that starts from the Day 3 moored
box, solved with `waveIsoFoam` of FoamWaveTank (`sixDoFRigidBodyMotion` + MoorDyn v2,
`moorDynR2` restraint). Each group folder has one problem description
(`<group>.pdf`: the group question on page 1, then one chapter per part), and each
part folder has one ready, tested case (`setup/`). **Read the PDF first.**

| Group | Part | Topic | You vary | How |
|-------|------|-------|----------|-----|
| [P01 Waves Severity](P01_WavesSeverity/P01_WavesSeverity.pdf) | A_WaveHeight | Wave height | H | `constant/waveProperties` |
| | B_WavePeriod | Wave period | T at H = 0.06 m | `constant/waveProperties` |
| [P02 Floating Properties](P02_FloatingProperties/P02_FloatingProperties.pdf) | A_MassDraft | Mass and draft | draft, mass | `python3 setBox.py --draft ..` |
| | B_Inertia | Inertia | Iyy | `constant/dynamicMeshDict` |
| [P03 Floating Shape and Damping](P03_FloatingShapeDamping/P03_FloatingShapeDamping.pdf) | A_BodyShape | Body shape, same mass | box, cylinder, sphere | `SHAPE=sphere ./Allrun` |
| | B_HeavePlate | Heave plate | plate size, gap | `makeBodyMesh.py`, `BODY=box ./Allrun` |
| [P04 Mooring Properties](P04_MooringProperties/P04_MooringProperties.pdf) | A_TautVsCatenary | Taut and catenary mooring | mooring system, line properties | `MOORING=taut ./Allrun` |
| [P05 Extreme Waves](P05_ExtremeWaves/P05_ExtremeWaves.pdf) | A_FocusedWaveSlamming | Focused wave slamming, HOS wave | amplitude, focus point | `Tools/makeFocusedWaveHOS.py` |
| | B_GreenWater | Green water | freeboard, H, T | `python3 setBox.py --height ..` |
| [P06 OpenFOAM parameters](P06_OpenFOAMParameters/P06_OpenFOAMParameters.pdf) | A_TurbulenceModel | Turbulence model | RANS model, inflow level | `TURB=laminar ./Allrun` |
| | B_CourantNumber | Courant number | maxCo, maxAlphaCo | `system/controlDict` |
| | C_MeshRefinement | Mesh refinement | cell size | `MESH=fine ./Allrun` |
| | D_RelaxationZone_HOS | Relaxation zone, HOS wave | zone length and shape | `constant/waveProperties.input` |

Split the parts between the members of a group. Each group gives one presentation
on Friday (10-20 minutes, about 5-6 slides per part, no written report) that ends
with one answer to the group question from all parts together.

## Running

```sh
source <OpenFOAM-v2506>/etc/bashrc
cd Projects/P01_WavesSeverity/A_WaveHeight
cp -r setup H004            # one copy per run, next to setup; keep setup clean
cd H004
#   ... make the change described in the PDF
NP=8 ./Allrun               # default 4 cores; NP=1 is serial
./Allclean                  # back to the clean case
```

On the DTU cluster use `sbatch runSlurm.sh` in the case folder. Options are passed
on with `sbatch --export=ALL,MESH=coarse runSlurm.sh`.

The setups use `waveIsoFoam` from `./Allwmake` of FoamWaveTank (set `SOLVER` for
another build). P05 part A and P06 part D also need HOS-NWT (`HOSNWT=/path/to/HOS-NWT`):
the wave is computed in `HOS/` and imposed in waves2Foam relaxation zones. All
other parts generate the wave at the inlet with OpenFOAM `waveModels`, as on
Day 3. A 23 s run of the default case takes about 35-75 minutes on 8 cores.

## Comparing runs

From a part folder (for example `P01_WavesSeverity/A_WaveHeight`):

```sh
python3 ../../Tools/compareRuns.py setup H004 H010 --plot compare.png --csv compare.csv
```

It prints mean, amplitude, first and second harmonic, maximum and minimum of
motions, tensions, wave gauges and forces. For the mooring lines in ParaView run
`python3 ../../../../Tools/mooringToParaview.py` from a case folder.

## Differences from the Day 3 case

- Parallel by default; fields written every 0.5 s; wave gauges at x = -2 ... 2 m.
- All parts keep the Day 3 mesh-morphing band (`innerDistance 0.075`,
  `outerDistance 0.4`). It held in all test runs, also on the fine mesh, with
  taut lines and with the curved and 3D bodies.
- P06 part A solves k, omega and epsilon with `smoothSolver`.
- P05 part A and P06 part D use waves2Foam relaxation zones (`constant/waveProperties.input`)
  instead of the inlet and outlet boundary conditions.
