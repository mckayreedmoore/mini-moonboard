# Eccentric contact-wrench control

Four nonlinear controls completed on 2026-09-08. They establish a limited reuse
basis for CalculiX 2.21 face-to-face penalty **contact-wrench output under
compression**, not a frame, connection or material capacity.

## Model and checks

Two separate 100 mm cubes use 54 nodes and twelve straight-sided quadratic
C3D10 tetrahedra. Each interface has two triangular faces. The lower bottom is
fixed XYZ. The upper top is fixed X/Y and moves downward from 0.001 mm at X=0
to 0.002 mm at X=100, producing eccentric compression. All actuator reactions
are included; there are no applied nodal forces or gravity. Both cubes use the
existing diagnostic E=7000 MPa and Poisson ratio 0.3.

Independent top and bottom reaction wrenches are compared with the solver's
six-component contact wrench about the global origin. Moments use deformed
positions. Checking each body separately prevents global force-only balance
from hiding incorrect contact moment transfer. The eccentric moment about the
face center must be nonzero; force times the geometric center is not substituted
for the reported moment.

Every accepted increment must satisfy the unchanged 0.1 N force and 1 N·mm
moment limits. Checks also cover prescribed motion, fixed supports, both contact
faces, integration-point counts, nonnegative pressure, zero local frictional
traction and the linear pressure/penetration law. DAT output must match every
completed status-file increment.

## Results

| Penalty, N/mm³ | Maximum increment | Endpoints | Final normal contact force | Largest moment residual, all checks/endpoints | Final maximum penetration |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 10,000 | 0.25 | 8 | 551.3073 N | 0.1313 N·mm | 0.000007277 mm |
| 10,000 | 0.125 | 10 | 551.3073 N | 0.0585 N·mm | 0.000007277 mm |
| 100,000 | 0.25 | 8 | 553.1503 N | 0.1244 N·mm | 0.000000731 mm |
| 100,000 | 0.125 | 10 | 553.1503 N | 0.0589 N·mm | 0.000000731 mm |

All 36 endpoints pass. Increasing penalty tenfold changes final reaction by
approximately 0.33% and reduces penetration roughly tenfold. Halving the maximum
increment leaves final normal force unchanged at printed precision; small moment
differences remain in the archived comparison. This is neither a mesh convergence
study nor a measurement of wood contact stiffness.

## Scope and next step

These controls remain compressive. They do **not** validate separation/recontact,
friction, actual panel-edge geometry, the retained common-edge bond, floor contact
or real bolt compliance. Nor do they overturn earlier rejected results in other
configurations or justify relaxing the frame's equilibrium limits.

Next is a separately identified direct-load model using the
[verified panel-edge faces](timber-contact-plan.md), with explicit opening/closing
checks and bounded penalty/increment sensitivity. Nonlinear contact results
cannot be assembled from the old linear basis solves. Any recovered force still
belongs to the ideal rim/common-edge aggregate until the actual fastener load
path is represented and checked.

## Reproduction and evidence

[Summary and 28 compressed replay artifacts](../fea/results/panel-contact-coupon/summary.json)
preserve each input, deck, launch, log, DAT, status and execution record. Exact
reconstruction and source hashes are checked before publication. Omitted auxiliary
outputs are identified explicitly.

```bash
uv run pytest -q tests/test_panel_contact_coupon.py tests/test_panel_contact_audit.py \
  tests/test_publish_panel_contact_coupon.py tests/test_panel_contact_coupon_evidence.py
```

Fresh preparation uses `python -m fea.panel_contact_coupon prepare --penalty
10000 --increment .25 --directory <fresh-case-path>`; launch uses `solve
--directory <fresh-case-path>`. The four combinations are 10000/100000 and
.25/.125. Use the [recorded Docker environment](../fea/release-toolchain/README.md),
two OpenMP threads and the enforced 60-second per-run limit. Existing attempts
are not overwritten. Publication expects the four named case directories under
`fea/generated/panel-contact-series`.

An exploratory run omitted CNUM and could not pass complete-output auditing.
It and its launcher snapshot remain locally preserved, outside the accepted
series. All four accepted runs explicitly request CNUM. No material, hardware,
CAD or historical accepted result changed.

The focused suite has 37 passing tests. Independent correctness, testing and
boundary reviews found no substantial remaining defects. These are numerical
reviews, not professional structural approval.
