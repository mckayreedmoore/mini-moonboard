# First-iteration log comparison

This is a bounded review of the two first-increment solver listings. The new
live-log prefix used here was captured at 2026-09-25 11:25:14 UTC: size at
open/read 20,559 bytes, SHA-256
`5f45fc48d502335a3541ee9b6672fa8093a4b19f4c18a7923423c8683447b31e`. The
preserved bytes are in
`current-pilot.log-prefix-at-open.log`; `capture.json` records its source,
length, and pins. The old log is terminal and its SHA-256
`5d0284bf6046626b9a079f3cb56c7627633888c2392dbdea37380c360719f8bd` matches
the old execution record's output pin. The paired input-freeze hashes are
`4f5d892d6f6270ae2d645463255a048b8b719331a0906412c4c4b85fd304f367` (old) and
`f054d6b911fb0d9c9b0a183fa007d16d8a34a422904fd5cbcf73634e87797e66` (new).

Both listings reach increment 1 at exactly `0.001 s`, with 93,540 contact
spring elements, 334,914 equations, 16,221,219 nonzero lower-triangle matrix
elements, and
the same printed maximum displacement correction (`1.136587e-05` at node 9,
DOF 2). The first-iteration residual records differ: old prints `0.000000` at
node 116170, DOF 3; new prints `0.388662` at node 5166, DOF 2. Average and
time-average force print `0.000002` old versus `0.000006` new. In the pinned
CalculiX 2.21 source, `nonlingeo.c` calculates the maximum absolute residual
from the active residual vector, sets values below `1e-6` to zero, then prints
six decimal places. The old line therefore means a thresholded residual below
`1e-6`, not an exact zero; the new value is materially larger. On iteration
2, the reported contact-spring counts also diverge (93,862 old; 96,573 new).
The first increment converged after 26 iterations old and 23 new.

The deck/input audit found only the planned step/time-control and output
schedule changes. The new initial/max increments are `0.001 s`; the old
`TIME POINTS` schedule clips its requested `0.0025 s` increment to the same
first `0.001 s` knot. Both listings report the same actual increment and
endpoint. CalculiX 2.21's `checktime.f`/`dyna.c` path uses `TIME POINTS` to
clip increment endpoints; output scheduling also sets the print path. Thus
time-point handling is a possible control-path difference, but a changed
first-step size or ramp endpoint is not evidenced here. The residual assembly
and print code reviewed does not identify a direct `FREQUENCY=1` output-card
effect on the residual. The two executions also use the same declared image
and binary hashes and the same 4-CPU / `OMP_NUM_THREADS=4` / equation-solver-4
settings. Parallel-order variation is plausible, but the logs do not establish
it as the cause. Equal counts and one equal maximum correction do not prove
equal matrix values, active facets, or residual vectors.

The separate first-state scalar comparison
`../every-increment-first-state-comparison-attempt01/comparison.json`
(`e0a13409ab2492e030d5203d850be37adfe0e0cc7d1b8b913ed2b6c0f4e42ffc`) reports
new-versus-old changes at 0.001 s of −0.1337% in q, +0.0362% in maximum
loaded-node displacement, and −0.3161% in carrier rotation. These are close
monitor scalars, not a full-field or contact-state equivalence check. Keep
the first-iteration difference visible and leave its cause unresolved; no
claim of identical first-state mechanics follows from these inputs or logs.

Source semantics were checked against the local official CalculiX 2.21 source
archive, SHA-256
`52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`; relevant
source-file hashes are `nonlingeo.c`
`0be7d7d6037868c364a621e12a3802a703f189b09ba200de95cf2e9d1b211f1b`, `dyna.c`
`de0d9b8c52ddf7e93043f05b60e57b9321525c9b5ffcde073de4c5648bb4d932`,
`checktime.f`
`3fbb3147b4c98393f73cd36e478049b94f7cd97ffe0e93244f6ed528be6c8d74`, and
`checkconvergence.c`
`a9f417fe198b0bc227a28f1f4775382d2bba22a7e436d60ba6d523ab91713e50`. This
review read existing artifacts only; it did not stop or alter the live run,
and it made no native or CAD run.
