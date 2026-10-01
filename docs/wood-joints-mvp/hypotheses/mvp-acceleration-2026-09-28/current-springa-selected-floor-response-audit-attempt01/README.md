# Selected-floor SPRINGA frame response audit, attempt 01

This packet defines a read-only native response auditor for the selected
17-cell floor branch. The selected mask is only the proposed, monotone,
zero-gap reference branch from the parent floor screen. It is not general floor
recontact, uniqueness, friction, or floor qualification.

The auditor accepts only
`current_springa_selected_floor_input_model/v1`, binds the selected and
inactive floor masks to all 200 source tangent rows and the parent screen, and
rejects the prior all-bearing input schema. It recovers all 1,292 nonlinear
SPRINGA carriers and 348 retained bilateral SPRING2 components, checks every
projection/MPC at every increment, audits all 100 compression-only floor
normals, recovers selected exact-floor tangent actions from serialized
equations and emitted source CLOADs, asserts no inactive tangent restraint or
reaction, and checks all 50 physical bodies plus global force/moment balance.
Numerical SPRINGA grounds remain excluded from physical support actions.

Active floor tangent actions are reported for the 34 selected original rows.
The other 166 original rows remain in the source inventory and receive explicit
zero actions only after the input contract proves that they have no reference
node, equation, or native tangent spring. Every accepted increment must show
the same selected 17 cells strictly bearing and the other 83 cells strictly
separated, with rounded endpoint-reaction intervals containing zero at the
inactive normals. `selected_floor_complementarity_passed` is an explicit gate.

The auditor imports the versioned recovery helpers from the prior stable SPRINGA
response audit by absolute path and verifies that module's pinned hash before
use. It does not edit that source or accept its all-bearing response schema.
Read-only known-answer replays are defined in
[`verify_method_fixtures.py`](verify_method_fixtures.py); their report is bound
only in this new packet.

Run the coupon replays from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-response-audit-attempt01/verify_method_fixtures.py
```

The input-only contract check binds the current adapter model and deck to the
pinned 17/83 parent screen, recomputes the selected H/D/S source-point force
and moment map, and verifies emitted-CLOAD transfer. It launches no native
solver and does not claim that the selected branch has been solved:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-response-audit-attempt01/verify_selected_input.py
```

For a later parent-owned selected-floor native result, the auditor accepts the
model record, emitted input deck, native DAT and terminal execution record. It
also requires the adjacent freeze and matching terminal output hashes. It does
not launch CalculiX:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-response-audit-attempt01/response_audit.py MODEL.json MODEL.dat MODEL.inp EXECUTION.json --output RESPONSE.json
```

A passing report means only that this one `a12-rear` response satisfies the
specified numerical and physical-equilibrium checks on this conditional
selected-floor branch. It does not compare joint forces with capacity, qualify
the floor, release any arrangement, or imply the other load cases.
