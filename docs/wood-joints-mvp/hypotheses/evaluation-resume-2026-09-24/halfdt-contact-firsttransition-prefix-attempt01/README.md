# Half-timestep first contact-transition output prefix

The parent captured this immutable output prefix after accepted increment 39
at 0.0195 s, while the same solver was attempting increment 40 at 0.01975 s.
The copied STA records 39 accepted increments and no rejected attempts. The
last accepted increment needed 15 iterations. This is a live-run snapshot,
not a terminal run or an accepted joint response.

`snapshot.json` has SHA-256
`d531ba36a8a6387bc6e12f96fa5093edcf9fde6dd20a12a2bb13b6af9ee9430b`.
It pins DAT, FRD, LOG, STA, CVG, execution metadata, the input freeze, and all
34 frozen input artifacts. The parent verified those 34 artifacts against
freeze `ea24423f587795743d0c1189c798f77d83159208c76d5d1d3a9fa5554eda4f56`
both before and after capture. The source inputs, solver controls and live
process were not changed.

STA was read first. Every other file was copied only to its size at open, so
this is not an atomic multi-file snapshot. Consumers must require complete
blocks at accepted times and treat missing or partial output as unavailable,
not zero. The subsequent trial had begun before capture, but consumers still
must verify each required contact and energy block. Later trial iterations
in LOG are not accepted states. Historical `FROZEN_NOT_EXECUTED` fields describe
input preparation; the separately captured execution record describes this
running diagnostic.

The immediate audit scope is 0.019 and 0.0195 s. The latter has no exact
accepted coarse-run counterpart and cannot be substituted for the coarse
0.020 s state in a timestep-convergence claim. The native energy print alone
is not corrected contact-storage accounting, physical joint acceptance, or
proof of a numerical cause. A later exact-time comparison needs a separately
preserved output prefix.
