# Day 1 - Waves

2D numerical wave flume (18 m long, 0.5 m deep, about 33 000 cells) with
`waveIsoFoam` (isoAdvector interface + waves2Foam relaxation zones).

```
x = 0 ---- 3 ----------------------------- 12 --------------- 18 m
    | inlet |          working region       |   outlet zone   |
    | zone  |  gauges x = 4, 6, 8, 10, 12   |   (absorption)  |
```

| Case | Wave | `endTime` |
|------|------|-----------|
| `01_regularWaves` | Stokes 2nd order, H = 0.08 m, T = 1.5 s | 20 s |
| `02_irregularWaves` | JONSWAP, Hs = 0.06 m, Tp = 1.5 s, gamma 3.3, 100 components, random phases | 40 s |
| `03_focusedWave` | NewWave (JONSWAP), crest 0.06 m focused at x = 8 m, t = 15 s | 22 s |

Steps in `Allrun`: `blockMesh` -> `setWaveParameters` (reads
`constant/waveProperties.input`) -> `relaxationZoneLayout` -> `setWaveField`
-> `waveGaugesNProbes` (reads `constant/probeDefinitions`) -> `waveIsoFoam`.

Surface elevation: `postProcessing/surfaceElevation/0/surfaceElevation.dat`.

Things to try: change H or T, the length of the relaxation zones, the
number of spectral components or the focus point and time.

## Potential-flow waves: HOS-NWT and CFD (`HandsonExercise/potentialFlowWaves`)

The same kinds of waves computed first with the potential-flow wave tank
HOS-NWT (`HOS/`) and then in a shorter CFD domain coupled to it with Grid2Grid
(`CFD/`): `RegularWaves`, `IrregularWaves`, `FocusingWaves` and
`WavemakerMotion/{Piston,Flap}`. See `potentialFlowWaves/README.md`. HOS-NWT
must be installed (https://gitlab.com/lheea/HOS-NWT).
