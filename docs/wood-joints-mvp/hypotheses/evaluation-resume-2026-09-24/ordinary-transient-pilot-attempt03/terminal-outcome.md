# Terminal outcome

Attempt03 reached the 600 s runtime bound and was stopped by the parent
launcher. Elapsed time including shutdown was 606.732 s; return code 137
records that stop, not an out-of-memory failure. All frozen inputs remained
unchanged. The first increment at 0.0025 s converged after thirteen iterations.
The next increment did not converge before the runtime bound, so the requested
0.025 s pilot remains incomplete.

The one complete monitor sample gives q = 6.989744242963423e-6 mm, maximum
loaded-node displacement 5.553280450705837e-6 mm, and maximum nut-controller
rotation 3.434742355982487e-9 rad. None of the sampled motion limits was
reached. The first-increment snapshot is preserved separately for independent
energy, work and momentum audits; it is not a terminal execution bundle.

Native output reports an initial energy-balance discrepancy of 0.032926%.
This is a solver diagnostic requiring independent accounting. The first large
increment crosses amplitude knots, so its discrete time-integration work and
impulse must be distinguished from the exact continuous piecewise-linear ramp.
This very small, inertia-dominated response does not establish clearance
seating, quasistatic stiffness, strength, thread qualification or full-frame
behavior. The design geometry and adoption criteria remain unchanged.
