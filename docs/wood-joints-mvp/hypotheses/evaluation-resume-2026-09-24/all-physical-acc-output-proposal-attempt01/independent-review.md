# Independent review of all-physical ACC output proposal

This read-only review covers the frozen `results.c` proposal, its source pins,
the pinned input decks, the node-map audit, and the parent emitter fixture. I
did not run CAD or a native solver.

## Review result

The proposal is appropriately scoped as an output-only diagnostic for a later
accepted-state angular-balance audit. Its runtime node map is tied to the
current mesh rather than relying on `nk` alone, and its new hook does not write
solver state arrays. The evidence supports the extracted emitter and the
source-level output contract; it does not establish a full CalculiX build, a
native trajectory, or any mechanics acceptance.

## Provenance and node ownership

All 12 path/hash pairs in `source-pins.json` match the files on disk. The pinned
base `results.c` is SHA-256
`41deef087bdadcdf9bb7a52142c4b6982f8111d3336ab50747c2473f0e11e65c`; applying
the pinned patch reproduces `proposed-results.c` byte-for-byte at SHA-256
`5a9f37af2e120b478be48964e9f29dc862bb3d7b8bf26d9ce33284476ee9438f`.

I independently parsed the pinned mesh and its control-node deck. The mesh
contains 57,643 unique C3D10 elements, with element IDs 1–57,643. Its node rows
and the union of all solid connectivities are both exactly the contiguous set
1–116,162. The pinned nut-control deck declares exactly nodes 116,163–116,170,
and none appears in the solid connectivity. The independently recorded
`node-map-audit.json` agrees. The hook reconstructs the same bitmap from
`kon[ipkon[i] + j]`, requires every physical ID and rejects any control ID in
solid connectivity; the output loop then emits one row per marked ID in
ascending order.

## Hook, framing, and state effects

The helper is called inside the existing `iout == 2`, `nmethod == 4`,
`CCX_WJ_DEP_RESIDUAL_AUDIT=1` branch. It therefore shares the accepted-output
hook used by the existing diagnostics and does not run in solver iterations or
cutbacks. For `mi[1] == 3`, its `mt = mi[1] + 1` stride and `accold[mt*i + 1..3]`
accesses match the established translational acceleration indexing. The
`STATE` record carries step, increment, total time (`ttime + time`), `dtime`,
and expected row count; the `END` repeats step, increment, and count. A static
last-pair guard suppresses a repeated call for the same consecutive
`(step, increment)`. Non-finite physical accelerations or a changed topology
fail fast; all solver inputs are read-only, with only a local bitmap and output
file state written.

The parent’s pinned extracted-helper fixture compiled with warnings as errors
and passed two full states of 116,162 triples each, duplicate suppression,
bad-count/type/connectivity rejection, physical-node NaN rejection, ignored
control-node NaNs, and source-array immutability checks. This compiles and runs
the extracted helper against full mesh connectivity, not the complete
proposed `results.c` or CalculiX executable. The proposal keeps that distinction
clear and retains `PROPOSAL_ONLY_NOT_APPLIED_NOT_COMPILED_NOT_RUN` as the
full-source/native-run status.

Use a fresh run directory: the helper opens the output file in truncate mode on
its first record, then appends subsequent blocks. A downstream parser should
validate exactly one complete `STATE`, all expected unique IDs with finite
triples, and a matching `END` per block; incomplete or I/O-damaged blocks must
not be consumed. The prior reference execution is recorded as failed after an
accepted state, so it supports the existing hook context only; it is not
evidence of a complete output trajectory. Output values retain the case's
solver-consistent unit system rather than embedding unit labels in the CSV.
