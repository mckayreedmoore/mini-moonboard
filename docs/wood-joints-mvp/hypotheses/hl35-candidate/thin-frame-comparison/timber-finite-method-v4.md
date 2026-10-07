# Finite current timber cut recovery

The [frozen method receipt](timber-finite-method-v4.json) issues a separate
consumer for an admitted finite-motion state. Nineteen fixtures and Ruff
pass, and independent review found no remaining blocker. No finite candidate
field has been consumed. All eighteen completion gates remain open and every
release remains false.

The producer is
[`scripts/thin_bolted_timber_finite_checks.py`](../../../../../scripts/thin_bolted_timber_finite_checks.py),
SHA256 `c22215fc4016aa618827ec17a78063d7344a01ce335207b9d650cc35b740de83`.
Its API requires a released field byte hash and an explicit, independently
reviewed SHA256 for the new finite admission helper:

```python
consume(field_path, released_field_sha256, admission_sha256=reviewed_gate_sha256)
```

The fixed admission path is `scripts/thin_bolted_finite_state_audit.py`, with
`audit_finite_state(immutable_bytes)`, schema
`thin_bolted_independent_finite_admission/v1` and acceptance key
`independent_finite_current_support_load_and_equilibrium_checks_pass`.
Missing, malformed or wrong gate hashes are rejected. The same immutable byte
payload supplies the audit and consumption. Its exact raw hash, complete
state/case/accessory identity and gate source hash must match the receipt.
The source field and gate are rehashed before return. No old gate fallback
or identity relabeling is permitted.

Each material cut is selected using its reference station. Forces and free
spatial couples act at each host's separate **current** point. The cut datum
and material basis follow the frozen finite map's current centerline and
geodesic directors. The exported per-span two-Gauss gravity ports remain the
actual discrete load model. No old affine continuous-force integral is
substituted. Every selected component witness retains its complete
simultaneous signed force and moment; independently located maxima are not
combined.

The eighty-two finished wood spans, seventy physical shaft geometry/thread
references and 140 own captures are reused. Each current wood resultant
includes both bearing point arms and its own capture/director couples.
Per-point current grain angles accompany explicit body/root diameter
sensitivities for the NDS dowel-bearing material parameter. Average foundation
patch pressure is a diagnostic, with allowable patch/connection utilization
unavailable. Actual `Dr`, `Fyb`, conforming product and delivered runout/body
lengths remain unverified. Classic equal/opposite or symmetric yield patterns
are not inferred from the distributed finite field.

The [two parent-queried recess sections](timber-leg-recess-sections-v4.json)
are geometry-only inputs, SHA256
`94fd730a72bdb93efc5d654913a162bb9a9715af342e91ebb11e873006969574`.
Their exact net centroids and cross-inertia matrices are transported to the
current material frame. The consumer recovers the same-cut centroid moment,
mean axial stress and normal-stress gradient at those stations. Net centroids
and inertias at other saved cuts remain unavailable. Exact trimmed-boundary
normal-stress extrema, shear, torsion, local fracture and stability require
separate methods. No CAD query or repeated geometry inventory occurs here.

Average `Ft`/`Fc` components reuse the authenticated DF-L No. 2 material and
NDS2024 duration inputs. CD1.6 arithmetic is conditional on an authenticated
live-load case; permanent-only CD0.9 arithmetic remains separate. No duration
increase is applied to the ideal direct-wood washer annulus. The finite own
capture force/couple is preserved separately from actual pressure, washer
spreading and head/nut/thread/prying resistance.

After the parent supplies a reviewed gate hash and an admitted field, reproduce
with a new result path in an existing output directory:

```sh
UV_CACHE_DIR=/tmp/thin-timber-uv-cache uv run python -m scripts.thin_bolted_timber_finite_checks \
  --field PATH --field-sha256 RELEASED_FIELD_SHA256 \
  --admission-sha256 REVIEWED_GATE_SHA256 --out DISTINCT_RESULT_PATH
```

Gross beam `A/I/J` remain an unbounded stiffness scenario. The seat/void
effects, complete distributed yielding, oblique end/edge and connected group
fracture, splitting, adjustments, shear/stability, actual axial hardware
resistance, demand bounds and complete case coverage remain open. This record
issues the consumer method; it supplies no candidate acceptance or physical
release.
