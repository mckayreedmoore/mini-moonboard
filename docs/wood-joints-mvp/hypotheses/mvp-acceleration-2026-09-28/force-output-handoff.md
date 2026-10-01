# RF force-output handoff

`fea/wood_joint_reduced_response.py` now uses
`fea/wood_joint_reduced_force_output.py:recover(record, raw_assessed, data)`
for physical connector forces and their DAT print-precision intervals. The
helper checks that each spring endpoint DOF belongs to one scalar `SPRING2`,
that auxiliary nodes are not shared with another structural element, that
endpoint RF values satisfy action/reaction within their printed intervals, and
that active RF-derived forces overlap the `k * deltaU` interval. It then uses
`current_response_run.physical_forces` for connector-axis conversion and radial
clearance reference-force subtraction.

The retained known-answer fixture can be replayed without a solver:

```sh
.venv/bin/python -m fea.wood_joint_reduced_force_output
.venv/bin/python -m fea.wood_joint_reduced_response
```

To reassess an already registered native attempt from its frozen outputs:

```sh
.venv/bin/python - <<'PY'
from fea.wood_joint_reduced_response import assess_directory

report = assess_directory(
    "docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/"
    "reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-01-revised-metadata"
)
print(report["force_output_recovery_audit"]["status"])
PY
```

The prior cycle01 displacement-recovery report is preserved byte-for-byte at
`reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-01-revised-metadata/response-displacement-recovery.json`
(SHA-256 `acf2a2678b97629671dcf26d47a166cad4cad2984d732ff1713535a2d96131b8`).
The updated `response.json` is a read-only reassessment of that cycle's frozen
native output; no new native execution occurred. It reports all 50 body raw and
interval equilibrium checks passing, with maximum raw body-moment residual
`0.5212 N mm`. The contact/tension/radial complementarity checks do not all
pass, so `numerical_checks_passed` is false and `mechanical_acceptance` remains
false. The report records the helper SHA-256 as
`32900ea0729a195b66bd540d81fc79e446caeb4819a660928fbd40bcdc0d60ed`.

These RF intervals bound only printed-number rounding for this linearized
active branch. The recovery requires isolated auxiliary spring DOFs; it does
not apply when an endpoint shares a structural element or multiple spring
components on the same DOF. The RF/KΔU comparison checks output consistency,
not solver accuracy, contact-law validity, connector stiffness, hardware
capacity, joint acceptance, or physical build readiness.


An independent cycle01 model audit additionally checked equation ownership,
boundary conditions and direct loads, which the helper itself does not inspect:
all 3,680 spring endpoint DOFs occur exactly once in the equations, no endpoint
node is fixed, and no endpoint has a nonzero direct load in this zero-gap case.
The RF helper's own isolation status is not a substitute for those model checks.
Repeat the endpoint constraint/load check for any changed model; when radial gap
reference CLOADs are active, match them to the recorded correction loads before
applying this force recovery. The reported half-last-place intervals cover
printed U/RF rounding only, not native residual or formulation error.
