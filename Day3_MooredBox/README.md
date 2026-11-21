# Day 3 - Moored floating box

2D box (0.2 m x 0.2 m, draft 0.0786 m, 3.148 kg) moored with four MoorDyn
lines (`Mooring/lines_v2_bodyC.txt`, MoorDyn v2, BODY coupling) in regular
StokesII waves, H = 0.1195 m. Body motion with the OpenFOAM
`sixDoFRigidBodyMotion` solver (Newmark) in `waveIsoFoam`. The tank is 5 m
long (x -2.5 .. 2.5) with relaxation blending over 1 m at each end.

Output: `postProcessing/waveGauges` (10 gauges, x = -2 .. 2),
`postProcessing/sixDoFState`, `postProcessing/box_forces`, and the line
tensions in `Mooring/`.

`endTime` is 23 s (the full experiment window). Serial run time is about
one hour; this will be shortened for the course.
