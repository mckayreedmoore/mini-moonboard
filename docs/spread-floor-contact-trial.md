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
