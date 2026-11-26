# Day 4 - SWENSE: waves only, and the moored box

SWENSE splits the solution into a known incident wave (Stokes II, or HOS-NWT for the
focused wave) and a complementary field (`Uc`, `pc`) caused by the body. The solver
computes only the complementary field, in `bodyZone` (the cells around the box,
|x| < 0.5 m). Everywhere else the wave is the incident wave, so it does not lose
height or reflect on the way to the body.

All cases use the Day 3 tank (5 m long, 0.5 m deep), the Day 3 wave (Stokes II,
H = 0.1195 m, T = 1.993 s), the same gauges (x = -2 ... 2 m) and the same meshes
(`MESH=coarse | medium | fine ./Allrun`). The solver is `waveIsoFoamSWENSE` from
`./Allwmake` of FoamWaveTank (set `SOLVER=...` for another build).

| Case | What | Solver |
|------|------|--------|
| `WaveOnly/waveIsoFoam` | empty tank, wave generated at the inlet (as Day 3) | `waveIsoFoam` |
| `WaveOnly/waveIsoFoamSWENSE` | empty tank, SWENSE | `waveIsoFoamSWENSE` |
| `WaveIsoFoamSWENSE/mooredBox` | Day 3 moored box, sixDoFRigidBodyMotion + MoorDyn | `waveIsoFoamSWENSE` |
| `WaveIsoFoamSWENSE/mooredBoxFocusedWave` | the same box in a focused wave from HOS-NWT | `waveIsoFoamSWENSE` |

Compare SWENSE with plain waveIsoFoam (plots and tables of our runs are in `Results/`):

    # wave only, from Day4_SWENSE/HandsonExercise/WaveOnly
    python3 ../../../Tools/compareSWENSE.py waves waveIsoFoam waveIsoFoamSWENSE --plot waves.png
    # moored box, from Day4_SWENSE/HandsonExercise
    python3 ../../Tools/compareSWENSE.py moored ../../Day3_MooredBox/HandsonExercise/waveIsoFoam/mooredBox \
                                                WaveIsoFoamSWENSE/mooredBox --plot moored.png

## Result 1: wave only

Wave height at the 10 gauges against Stokes II theory, t = 13.04-23 s
(`Results/waveOnly_SWENSE_vs_plain.png`, `Results/waveOnly_table.txt`):

| Mesh | Cells | plain waveIsoFoam: RMS error of H | SWENSE: RMS error of H | Run time plain / SWENSE |
|------|------:|------:|------:|------:|
| coarse | 1100 | 6.4 % | **2.0 %** | 17 s / 36 s |
| medium | 3800 | 6.0 % | **1.9 %** | 41 s / 104 s |
| fine | 15200 | 7.3 % | **2.2 %** | 3 min / 19 min |

The plain solver shows a standing-wave pattern along the tank (H between 0.88 and 1.13
of theory): part of the wave is reflected at the outlet, and a finer mesh does not
remove it. SWENSE keeps H within about 3 % at every gauge on every mesh: SWENSE on
1100 cells is closer to theory than plain waveIsoFoam on 15200 cells.

## Result 2: moored box in regular waves

Amplitudes over the last 5 periods (13.04-23 s), `Results/mooredBox_SWENSE_vs_plain.png`,
`Results/mooredBox_table.txt`. How much the result changes from the medium (3760 cells)
to the coarse mesh (1088 cells):

| Amplitude | plain waveIsoFoam | SWENSE |
|-----------|------:|------:|
| surge | -2.8 % | **+0.5 %** |
| heave | -5.3 % | **-0.8 %** |
| pitch | **-40 %** | **-1.5 %** |
| tension line 1 | +5.6 % | +4.2 % |
| tension line 3 | -5.8 % | +1.3 % |

On the medium mesh SWENSE and plain agree within 1 % in surge and 5 % in heave; pitch
is 24 % lower with SWENSE, line 1 tension 11 % higher. Plain waveIsoFoam on the
medium mesh was validated against Wu et al. (2019) on Day 3; pitch was the weak
quantity there too (about 80 deg late in phase). SWENSE gets nearly the same answer
on the coarse mesh as on the medium mesh, the plain solver does not.

Run times (serial, one core of a DTU HPC node): plain 4 min (coarse) and 9 min (medium),
SWENSE 6 min and 17 min. The focused wave case (HOS-NWT + SWENSE, medium) takes 10 min;
the group focuses at the box at about 10 s (crest about 0.07 m) and the box pitches up to 10 deg.

## Settings

- Wave only (`WaveOnly/waveIsoFoamSWENSE`): the settings validated for pure waves in the
  FoamWaveTank tutorial `waveIsoFoamSWENSE_coarse`: `pcAtmosphereConsistent yes`,
  `incidentHydrostatic discrete`, `alphaHExact true` (`constant/waveProperties`) and
  `alphaIExactReset yes` (`system/controlDict`). Without them the wave height error of
  SWENSE was 13.6 % on the coarse mesh, worse than plain waveIsoFoam.
- Moored box (`WaveIsoFoamSWENSE/*`): the settings validated for the moving body
  (adaptive time step, `bodyZone` cut 5 cell rows below the atmosphere, level
  correction off). With the pure-wave settings above, the medium-mesh moored box
  diverged at 11.8 s, so they are not used with the moving body.
- Regular-wave cases: `incidentResidualMax 0.2`. Stokes II is a second-order theory;
  at H/L = 0.03 its free-surface residual is 13 % of omega H/2, above the default
  check of 0.005, and the solver stops without this line. A wave theory that satisfies
  the free-surface conditions exactly (`streamFunction`) is a good extension: on the
  coarse wave-only case it gave 1.7 % instead of 2.0 %.
- The SWENSE log line `SWENSE check` prints max|alpha1 - alphaI| and max|Uc| every step.
  With a body (or on a coarse mesh) Uc is not zero inside `bodyZone`: that is the
  complementary flow the solver computes.

The focused wave has the Day 2 parameters (crest 0.06 m, Tp 1.2 s, gamma 3.3, focus at
the box at 10 s) with components up to 1.4 Hz. `Allrun` runs HOS-NWT first: it needs
LAPACK and FFTW at run time (on the DTU cluster `module load lapack/3.11.0 fftw/3.3.10`),
or set `HOSNWT=/path/to/HOS-NWT`.

Wave gauges: `postProcessing/surfaceElevation`, 50 Hz. In the SWENSE cases `sets` in
`system/controlDict` must be a dictionary `{ }`, not a list `( )`.

A FloatStepper version of SWENSE (`floatStepperSWENSE`) is in development and not yet
in FoamWaveTank master, so it is not part of Day 4.

## Mooring lines in ParaView

Use `Tools/mooringToParaview.py` as in the Day 3 README: from a case folder,
`python3 ../../../../Tools/mooringToParaview.py`, then open `Mooring/Mooring.pvd`.
