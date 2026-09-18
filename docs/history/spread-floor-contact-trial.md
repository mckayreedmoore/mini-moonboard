# Spread-leg unanchored contact trial

This is numerical development evidence, not a structural release. The tested
geometry has 300 mm additional leg extension and predates the owner's compact
rear-envelope preference. It cannot qualify the preferred zero-extension legs.

## First bounded run

- Geometry: spread-pattern 2×6, +300 mm, 40 mm leg mesh, E=7000 MPa.
- Model: authenticated existing solid mesh with separate joint springs;
  connector stiffness 1000 N/mm. This is not the later long-bolt hardware trial.
- Floor: three ground blocks, only their bottom nodes fixed; timber floor
  nodes are not fixed. MORTAR contact permits separation and frictional slip.
- Assumptions: friction coefficient 0.2, normal penalty 100 N/mm³, tangent
  penalty 1 N/mm³; these are not measured floor properties.
- Planned loading: gravity first; then A12, 250 lb at 2× weight plus 300 N
  in the model's positive Y direction. This single trial is not the full
  climber/load-direction matrix.
- Outcome: exit 124 after 600.884 seconds. Only the first increment of the
  gravity step completed, at step time 0.05. The second increment was still
  iterating. Neither full gravity nor the climber-load endpoint was obtained.
- Decision: **incomplete numerical trial**. No stability, contact, joint or
  strength conclusion can be drawn from this timeout.

The [raw archive](../fea/results/spread-floor-contact/untied-mu02-k1000.tar.gz)
includes the prepared input, solver outputs, terminal run record, launch source
snapshots and their hashes. The runner refuses to overwrite existing evidence.

```sh
uv run python -m fea.run_spread_floor_contact \
  --output /tmp/new-spread-contact-trial.tar.gz --max-seconds 600
uv run pytest -q tests/test_spread_floor_contact.py \
  tests/test_run_spread_floor_contact.py tests/test_spread_floor_audit.py
```

The separate endpoint auditor checks external force and deformed-coordinate
moment balance, consistent quadratic-element gravity and connector interpolation.
It deliberately rejects missing endpoints. It does not establish local contact
traction/gap/friction consistency, mesh/penalty sensitivity or structural safety.
No endpoint acceptance report exists for this timed-out run.

## Next comparison

Complete the zero-extension leg response comparison first. Use its actual
geometry for the next floor-contact case. Before spending a larger native
runtime budget, assess whether the retained whole-frame mesh can be reduced
without losing load-path or contact fidelity. A shorter or smaller solve is
useful only if the same physical questions remain represented.

## Compact candidate: completed gravity endpoint

The next native trial uses the authenticated zero-extension 2×6 mesh, the same
friction/penalty/material assumptions, 1000 N/mm joint springs and initial/
maximum step increments of 0.5. Its runtime limit is 1800 seconds. The model
still represents assumed springs, not the new resolved joint geometry.

The complete gravity endpoint at time 1 passed the independent global checks:

| Check | Measured maximum | Numerical limit |
| --- | ---: | ---: |
| Absolute force residual component | 0.000009 N | 0.1 N |
| Absolute moment residual component | 0.223467 N·mm | 1 N·mm |
| Connector interpolation error | 0.000000105 mm | 0.00001 mm |
| Wood displacement magnitude | 1.241617 mm | No acceptance limit assigned |

The [gravity-only snapshot](../fea/results/spread-floor-contact/compact-gravity-audit-v1.tar.gz)
contains copied raw output, deck/input, consistent gravity weights, the audit
and its source snapshots. It was captured after gravity completed while the
climber step was still running. It is **not a completed climber-load analysis**.
The partial audit keeps top-level `global_checks_passed` and
`qualified_for_design` false; only `requested_endpoint_checks_passed` is true.
Local contact traction/gap/friction consistency is also not approved.

```sh
uv run pytest -q tests/test_spread_floor_audit.py
# On an extracted audit directory containing weights.json:
uv run python -m fea.spread_floor_audit /path/to/extracted/audit \
  --gravity-only --output /tmp/new-gravity-assessment.json
```

Do not use this gravity result as a load rating, a floor-friction measurement,
or acceptance of the service-load step. The latter must reach its own endpoint
and undergo separate global and local contact checks.

## Compact trial terminal outcome

The [complete bounded-run archive](../fea/results/spread-floor-contact/compact-mu02-k1000-ramp05.tar.gz)
records timeout exit code 124 after 1800.913 seconds. Gravity completed in two
increments. The first climber increment at step size 0.5 was unsuccessful after
19 iterations; the convergence log records two iterations of its second attempt
before timeout. No climber increment completed. The earlier gravity snapshot
therefore remains the only assessed endpoint from this trial.

The archive preserves `run.json`, raw solver output and hashed launch sources.
Its terminal status is `INCOMPLETE OR FAILED NUMERICAL TRIAL; NOT PHYSICAL
INSTABILITY EVIDENCE`; solver completion, global-run equilibrium and local
contact acceptance remain false. This timeout does not establish physical
instability or support a displacement or load rating under climber load.

Next numerical work must examine the failed increment and attempt a bounded
smaller load ramp while retaining the same physical contact question. A completed
climber endpoint still needs global equilibrium/interpolation and local
traction, gap and friction audits. The [separate-body joint mesh](compact-joint-mesh.md)
and [raw-rim boundary map](compact-rim-boundary.md) prepare local joint work;
neither supplies the missing accepted parent field or calibrated joint stiffness.
