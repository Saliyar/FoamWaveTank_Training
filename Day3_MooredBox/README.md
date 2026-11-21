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

## Mooring lines in ParaView

After the run (or while it runs), in the case folder:

    python3 mooringToParaview.py                  # every MoorDyn output time
    python3 mooringToParaview.py --dt 0.1         # one frame per 0.1 s
    python3 mooringToParaview.py --start 5 --end 20 --dt 0.05

It reads `Mooring/*_Line<N>.out` (node positions and segment tensions) and
writes `Mooring/VTP/mooring_*.vtp` plus the time series `Mooring/Mooring.pvd`.
Open `case.foam` and `Mooring/Mooring.pvd` together in ParaView; the times
match the flow solution. Colour the lines by `Tension` (N per segment) or
`LineID`. Needs only numpy.
