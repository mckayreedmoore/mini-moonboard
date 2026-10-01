# Body-restricted force-resultant check

This output-only check evaluates a route for stable global interface force
resultants on the curved A09 pair-021 crop. It uses the v17 documented
`CALC_CHAMP(FORCE='FORC_NODA', GROUP_MA=...)` behavior: assemble the force field
from one selected body, then sum it over that body's contact-node group. The
paired decks separately calculate `BOLT` on `SNODE` and `WOOD` on `MNODE`; the
base and cell-order-reversed runs use byte-identical `.comm` and `.export`
files and the same pinned Code_Aster 17.4 image.

The flat PENTA15/TRIA6 known-answer check is in
[`fea/code_aster_trial/contact_body_force`](../../contact_body_force/README.md).
It recovers the analytic `3000 N` face resultant within `4.7e-13 N`, matching
the opposite `RN` action and same-body cut. That calibrates the sign and
resultant extraction before applying the route to TETRA10.

On the curved TETRA10 crop, the all-state paired audit checks `INST=-1..11`.
Across every state, `BOLT` and `WOOD` interface force resultants oppose within
`1.3e-12 N`; each body balances its own cut within `6.4e-14 N`, and their
first-moment balances are below `1.5e-11 N·mm`. Reversing only the 95 slave
TRIA6 record lines changes each body-force resultant by at most `5.2e-11 N`
and displacement by at most `7.93e-14 mm`. In contrast, the summed contact
`RN` changes by `0.98–7.00 N` at loaded diagnostic states and remains `10.0–
33.7 N` away from the body-restricted force, far outside its existing
`0.118–0.398 N` screen.

The route recovers a stress-derived global force and first moment for this
displacement-controlled crop. It does not independently validate contact
pressure, reproduce the contact residual quadrature, or establish joint
response. Do not compare the two nonmatching faces' first moments as
equal-and-opposite without accounting for their force application locations.

The reproducible preparation and offline audit are:

```sh
.venv/bin/python fea/code_aster_trial/curved_contact/body_restricted_force/prepare_curved_body_force.py
.venv/bin/python fea/code_aster_trial/curved_contact/body_restricted_force/audit_curved_body_force.py
```

The parent ran the prepared cases serially through `run_frozen.py`. Frozen
inputs, source hashes, output tables and audit are preserved in the two
attempt directories linked from the
[candidate-check results](../../../../docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/RESULTS.md).
