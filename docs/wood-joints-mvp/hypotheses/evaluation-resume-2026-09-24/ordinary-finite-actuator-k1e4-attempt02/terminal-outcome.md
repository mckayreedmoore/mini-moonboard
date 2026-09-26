# Finite-actuator diagnostic: explicit parent stop

The parent stopped this diagnostic after nine accepted increments through
0.003875 s and 2863.35 seconds of runtime. The launcher records
`process_failed` with native return code 137 because the container was
explicitly stopped; the 10,800-second runtime bound was not reached. All
twelve frozen input artifact hashes remain unchanged.

The first five accepted states provide separately checked force and discrete
actuator-work accounting. Native `allwk` omits the work of the prescribed
actuator target, and the source contact-control path uses that native energy
term. Repeated retries reduced the timestep from 0.0005 s to 0.000125 s;
specific retry causality remains unproven. The parent ended this bounded
method diagnostic to prioritize a force-driven case whose applied-load work
is represented in that native term. No tolerance, restraint, model geometry
or running input was changed to obtain convergence.

The latest physical weighted displacement is 0.0002263059343 mm; none of the
sampled motion stops fired. This result is not bolt seating, an accepted joint
response, a strength failure, or a time-accuracy result. Partial final output
tails remain unknown. The earlier immutable snapshots are preserved.

The [terminal disposition](parent-terminal-disposition.json) records the stop
reason, command, accepted/unaccepted status rows, unchanged input pins and
terminal output hashes. The [energy-work source review](../current-native-stiffness-adaptation-energy-addendum.md)
explains the accounting limit. The next force-driven derivative must pass its
own actual-input audit before execution; it does not inherit joint acceptance.
