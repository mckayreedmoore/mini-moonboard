# Half-timestep work prefix through 0.013 s

This immutable output capture contains 26 accepted increments through
0.013 s, with no rejected attempts in its status prefix. All 34 input
artifact hashes verified before capture. The live native case continues
independently of this snapshot.

The folder name refers to times before the earlier coarse run's reported
bolt-hole contact onset. It does not assert that this joint has no active
contact, or that the half-timestep contact history has been qualified.

The [manifest](snapshot.json), SHA-256
`cc48eff42c5ef23eaa88d3511a55d024d54adba8373b642fa20a74e0782c2fee`,
pins status, DAT, log, convergence, execution and input-freeze records.
Each was copied through its size at open, with status first; the capture is
not atomic across files. Only complete reports at captured accepted times
may be used. Missing and partial records remain unavailable, not zero.

FRD and CEL were intentionally omitted because this capture serves the
work, monitor-motion and printed-energy comparison. It cannot independently
supply the velocity fields needed for a momentum reconstruction. The exact
candidate comparison times are 0.001 through 0.013 s at 0.001 s spacing,
subject to complete matched output. The capture establishes no timestep
accuracy or mechanical acceptance.
