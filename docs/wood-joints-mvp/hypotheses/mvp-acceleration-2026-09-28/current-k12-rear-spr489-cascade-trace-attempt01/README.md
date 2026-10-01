# SPR489 cascade replay and direct-scalar coupon input

This packet records a source-pinned replay of the exact SPR489 qghost MPC
dependency closure in K12-rear attempt03, then prepares one source-interpolation
direct-scalar SPRINGA known-answer coupon. All artifacts here are diagnostic or
input-only. This packet contains no native run, freeze, response-force adoption,
floor-support qualification, or joint acceptance.

The closure has 8 rows,
replayed in emitted equation order. The replay converges in
4 substitution sweeps; it takes
10 replacements. No dependent coefficient is
repaired. The independent cutoff deletes
24 terms: row 9360 drops
11, qghost-y row 19433 drops 8, and qghost-z row 19434
drops 5. No selected-floor equation appears in the closure.

At the rejected 0.2 state, the source-faithful replay predicts qghost-y
-2.5581786689e-11 mm and qghost-z 5.35670119373e-12 mm of pruning-induced coordinate
change; the scalar axis projection changes by -1.23401843344e-11 mm. The
recorded strict scalar interval excess is
1.63435693752e-11 mm. The
pruning change is material to the exception but does not fully explain it; this
is a candidate mechanism, not exclusive native causality. The seven-state
printed-U residuals, per-row token radii, coefficient deltas, drop records and
source-loop steps are in `cascade-trace.json`.

The coupon uses the same SPR489 owner order, contact point, unit normal,
stiffness, and actual two 20-node interpolation coefficient sets. It replaces
only the nested interpolation/projection/qghost representation with one direct
scalar equation over the original 80 independent master DOFs. Its first state
has common first-point translation 0.0004342299 mm and serialized
equation q 1.64930000001e-06 mm, with expected endpoint
force 0.433903293063 N. It also includes a negative-q
open state and a +0.01 mm closed control. The direct row retains all 80 source
DOFs; no qghost, projection slave, or interpolated slave node appears in that
row. The manufactured loads, expected nodal actions, force and moment
resultants, and DAT-token q/force intervals are in
`direct-scalar-coupon/model.json` and `analytic-check.json`.

`cascade-source-excerpt.txt` contains the exact relevant source lines from the
hash-pinned CCX 2.23 `cascade.c`. The producer verifies the archive/member
hashes, source input hashes, owner binding, and the equation closure before
writing. Reproduce or check without running CalculiX:

```bash
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-spr489-cascade-trace-attempt01/produce.py --write
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-spr489-cascade-trace-attempt01/produce.py --check
```

The native relative-coordinate sign convention is cross-referenced to the
already run bounded method coupon at
`docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-relative-coordinate-fixture-attempt01`; this packet does not rerun it. Parent owns any later
freeze and native execution.
