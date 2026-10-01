# K12-rear normal-law screen with exact-zero U-token intervals

This read-only screen reparses the existing frozen K12-rear all-bearing
response using the sibling zero-U-token auditor copy. It checks the 100
floor-normal SPRINGA laws at all seven accepted times. For each cell,
classification requires a strict projected-`q` interval and strict geometric
elongation interval; active cells also require positive table-force and native
endpoint-force intervals. Inactive cells require both `q` and geometric
elongation strictly below zero, a zero table-force interval, and the original
endpoint RF law/action-reaction check.

The only parser delta is canonical all-zero displacement-token radius. On the
full K12 stream, 91,476 zero U component radii change from `5e-7` to zero,
358,071 nonzero U values/radii stay identical, and all 449,547 RF values/radii
stay identical. The original 32-epsilon geometry guard and constitutive,
equilibrium, and balance checks are untouched.

At the first state, the old parser left `SPR1110` (`floor_base_floor_left_29`)
unclassified because its free projected coordinate printed `0.000000E+00`.
The refined intervals are:

- projected `q`: `[-7.2589015e-8, -7.2589005e-8] mm`;
- endpoint geometric elongation: `[-7.25893635e-8, -7.25886430e-8] mm`;
- SPRINGA table force: `[0, 0] N`;
- endpoint RF center/radius: `0 ± 5e-7 N` (the RF rounding rule is unchanged).

The normal-law inventory is 16 strictly positive and 84 strictly separated
cells at every state. The old first-state screen had 16 positive, 83
separated, and this one unresolved interval; all later state counts were
already 16/84. This closes the parser ambiguity for this output record.

This result does not accept the all-bearing floor support branch, choose a new
floor mask, or supply physical corner demands. It is not a stability, contact
uniqueness, solver-error, floor, or design claim. The native response remains
the existing K12-rear run; this producer did not launch a solver, alter a
freeze or ledger, or modify input geometry.

`produce.py` regenerates `screen.json` from the pinned input, output,
execution, freeze, and original screen hashes recorded there.
