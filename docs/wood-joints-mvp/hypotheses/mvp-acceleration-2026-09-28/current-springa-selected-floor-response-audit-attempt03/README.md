# Selected-floor SPRINGA frame response audit, attempt 03

This packet defines a read-only response auditor for one proposed 25-bearing /
75-separated floor mask. It pins
`current-springa-selected-floor-branch-screen-attempt02/screen.json` at SHA256
`231b4fa22128bb01ae08f9bf21e6fec9ccb9c7578724781fae01a6f79856ed93`. That
screen labels the mask
`REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH` and says corner demands are
unusable. The mask is a diagnostic proposal for a monotone, zero-gap,
first-bearing reference branch; it is not an accepted support model, general
release/recontact solution, uniqueness result, floor qualification, or
joint-force acceptance.

The auditor accepts only `current_springa_selected_floor_input_model/v1`, binds
the mask to the pinned parent screen, and retains all 200 original floor
tangent source rows: 50 active reaction rows and 150 explicitly inactive zero
actions. It recovers all 1,292 nonlinear SPRINGA carriers and 348 retained
bilateral SPRING2 components; checks every projection/MPC, all 100
compression-only floor normals, the exact transformed source-point floor
reactions, all 50 physical bodies, and global force/moment balance. Numerical
SPRINGA grounds are excluded from physical support actions. Inactive tangent
rows must have no reference equation, native tangent, or nonzero RF; each paired
normal must remain strictly separated. Every one of the 25 selected normals
must remain strictly positive after rounded-output intervals.

The response code imports the unchanged stable recovery kernel from
`current-springa-frame-response-audit-attempt01/response_audit.py`, pinned at
SHA256 `b20dae471e9826a55c40bbeed028375e6d082913e3f3917665514f2763ddd49c`.
It also pins the unchanged controls model and deck. This packet does not
consume native frame output, freeze input, launch CalculiX, or establish
readiness. Earlier selected-floor masks remain separate diagnostic records;
their results do not transfer to this proposed 25/75 mask.

Replay the previously passed native method coupons without launching a solver:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-response-audit-attempt03/verify_method_fixtures.py
```

Check the attempt03 adapter model/deck contract, source-point wrench transform,
and emitted-CLOAD correction. This check launches no native solver and sets
`frame_ready_for_native_run` false:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-response-audit-attempt03/verify_selected_input.py
```

If a parent-owned native response is later supplied, the postprocessor accepts
the model record, native DAT, emitted deck, and terminal execution record. It
does not run CalculiX:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-response-audit-attempt03/response_audit.py MODEL.json MODEL.dat MODEL.inp EXECUTION.json --output RESPONSE.json
```

A passing response report would establish only that this one `a12-rear`
response met the stated numerical and physical-equilibrium checks for the
exact proposed branch and input. It would not establish that the branch is
accepted, usable for corner demands, supported by a qualified floor, or
adequate for any other case.
