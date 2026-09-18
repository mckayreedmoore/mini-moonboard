# Unpinned whole-frame floor contact: feasibility prototype

This experiment adapts the frozen 60 mm mesh of `2x8-foot100` rather than
changing the CAD or overwriting the bonded, fixed-floor comparison. It is
**not a completed unanchored validation or a joint-capacity calculation**.

## What is implemented

- Keep the original 62,020-node quadratic tetrahedral timber mesh and its
  perfectly bonded internal interfaces. No steel or fastener compliance is
  introduced.
- Extract the actual six-node exterior floor faces: 16 on each leg and 213
  across the kicker-side timber. Pair them with three separate, fully fixed
  ground-brick top faces. Only the ground nodes are restrained; **no frame XY
  pins, weak support springs, ballast, anchors or numerical damping** are used.
- Use an intended compression-only face-to-face linear penalty law, a nominal
  normal penalty of 10,000 N/mm³ and tangent
  penalty of 100 N/mm³. Assumed friction coefficients are sensitivities, not
  measured floor properties or a selected minimum installation coefficient.
- Attempt gravity preload, followed by the existing five-node 1.2 kN downward
  load in a second geometrically nonlinear static step. Both complete steps
  are required before a final-load equilibrium result may be reported.

CalculiX's face-to-face formulation requires element-face surfaces for both
sides, supports an opening interface with linear pressure-overclosure, and
uses a separate friction stick slope. The implementation follows those
documented distinctions rather than converting the old `FEET` node set into
bilateral supports. [Official CalculiX 2.21 HTML manual archive](https://www.dhondt.de/ccx_2.21.htm.tar.bz2).
The installed solver used here is CalculiX 2.21. Actual local contact pressure,
including any numerical tensile excursions, still requires an output audit;
the selected law alone is not evidence that every computed point satisfies it.

## Gravity and evidence checks

The mesh is **undrilled timber only**, not the drilled timber-plus-angle
inventory used in the previous rigid-body sweep. Its CAD volume is
306,605,478.65 mm³ and mass is **183.963287 kg** at 600 kg/m³. Fasteners,
angles, holds, glue and LEDs receive no mass credit. The corresponding weight
is about 1804.064 N, not the full 195.573 kg candidate's weight.

In consistent N/mm/s units the density is `6e-10` tonne/mm³ and gravitational
acceleration is 9806.65 mm/s². Gravity applies only to the timber element set;
the ground bricks do not contribute a constrained-body gravity reaction.

Gauss integration of the actual C3D10 geometry gives 183.963277 kg, differing
from CAD by approximately 0.000010 kg. The integrated centroid differs from
the CAD centroid `(4.267980, 745.153756, 1137.150551)` mm by less than
0.00002 mm. The calculation explicitly handles the different final two
mid-edge node orders in Abaqus C3D10 and Gmsh tetra10. A straight-tetrahedron
volume/centroid test and invalid mid-edge ordering test check that conversion.

Source/deck identity is verified before adaptation. Consistent integrated
nodal volume weights are retained so gravity moments can be checked at
**deformed**, not only initial, coordinates. The output auditor requires all
wood displacements and every ground-node reaction at the final time of both
steps, then checks global force within 0.1 N and moment within 1 N mm.
Per-patch nonnegative normal resultant and aggregate Coulomb bounds are
necessary checks, **not substitutes for pointwise contact-pressure/friction
validation**. The latter remains an acceptance gate before a contact result
can be called resolved.

Physical floor gaps are computed from deformed wood-node coordinates. A zero
reported contact-opening field alone is not used to establish no lift-off.
Global ground resultants are not divided by four to invent bolt loads.

## Contact-law smoke test

A two-C3D8 model places a 100 mm wood cube on a larger fixed ground brick.
A second toy replaces the wood cube with six conforming C3D10 tetrahedra;
the ground remains C3D8. Both use the same contact/friction parameters and no
wood constraints. Both gravity steps complete, including final nodal output,
and their 0.6 kg mass, ground reaction, deformed gravity moment, physical gap
and necessary aggregate friction bound are checked.

The brick toy balances its 5.883990 N weight within 0.000001 N and 0.00011 N mm.
The quadratic toy balances within 1e-12 N and 0.000000224 N mm. Their small
negative physical gaps are finite penalty penetration, not tensile support:
about 5.9e-8 mm for the brick and 4.1e-8–6.2e-8 mm for the quadratic toy.
These smoke checks establish that the selected law can run without frame XY
pins in simple examples; they do **not** validate the whole frame or establish
pointwise local friction compliance for the frame.

## Whole-frame outcome

The initial μ=0.3 run did not accept its first gravity increment within the
bounded trial. It was deliberately stopped rather than allowing an unbounded
nonlinear calculation. This is **unresolved numerical/contact feasibility**,
not a demonstrated tipping, sliding, joint-strength or material failure.
No 1.2 kN climbing-load result was reached or accepted by that run.

Two further bounded trials also accepted no gravity increment. Neither
increasing assumed friction to 0.5 nor reducing both penalty slopes by a
factor of ten produced an accepted step within the allotted experiments.
No structural/material recommendation follows from their runtime stops.

| Assumed μ | Normal / tangent penalty, N/mm³ | Last recorded first-increment iteration | Stop | Accepted increments |
| --- | ---: | ---: | --- | ---: |
| 0.3 | 10,000 / 100 | 24 | Deliberate manual runtime stop | 0 |
| 0.5 | 10,000 / 100 | 20 | Deliberate manual runtime stop | 0 |
| 0.5 | 1,000 / 10 | 16 | Automatic 240-second solve timeout | 0 |

[Published trial summaries, convergence histories, logs and toy evidence](../fea/results/floor_contact/report.json)
retain these outcomes explicitly. The trial summaries retain pre-launch deck
hashes; early runs did not capture all code hashes at launch. Publication
source digests identify the re-audit code, not retroactively frozen execution
provenance. Full whole-frame input decks and nodal integration weights remain
under the ignored generation directory for reproduction.

The ground pressure/gap distribution, friction, penalty sensitivity and local
equilibrium must still be checked if a later run converges. A solver exit code
or global reaction balance alone is not an accepted local contact solution.

## Next numerical step

Follow-up: the [unchanged actual-leg coupon](foot-contact-diagnosis.md)
completed both load steps with a permanent, explicitly reported upper XY
guide. This narrows the diagnosis but is not an unanchored frame result.
Its recovered nodal contact fields also do not establish local Coulomb
compliance. The original bounded trials above remain unchanged evidence.

The [earlier-recovery experiment](floor-contact-recovery.md) subsequently
reached CalculiX's built-in contact softening/cutback procedure four times,
but still accepted no gravity increment in 600 seconds. Merely reaching that
procedure earlier did not resolve startup within the bounded experiment.

The [temporary-guide/release experiment](floor-contact-continuation.md)
separates guided preload from fully released gravity and climbing load.
Guided convergence is never counted as an unanchored solution; all three
complete steps must pass their equilibrium audits, with no guide forces in
the final two steps. Current released-gravity convergence still fails the
independent moment audit.

Before a broad whole-frame load sweep, isolate the quadratic floor-contact
mesh and unloaded rigid-body modes with a small representative leg/foot
model. Compare penalty/increment settings without supplying artificial
supports. A model that needs extra restraints must disclose their reactions
and cannot be presented as the unanchored board. Once equilibrium is robust,
test friction and mesh sensitivity, asymmetric loading and the previously
failing exploratory directions.

If the limiting problem is an unpressurized initial tangential rigid-body mode,
a separately labelled preload/release experiment could temporarily guide the
frame during gravity and then **remove every guide before evaluating gravity
alone and the climbing load**. That is not implemented here. Such a continuation
would need zero final guide reactions, actual free contact equilibrium and
sensitivity to the initial guides/friction history; leaving guides active is
not an acceptable replacement for the unanchored model.

Aggregate leg/rim actions can then be obtained from each leg's contact
resultant and moment together with its own gravity free body. Because internal
interfaces remain bonded, these would still be **conditional aggregate joint
actions**, not four individual bolt forces or connection capacities. Actual
joint opening, slip, bearing, plywood/glue properties and rated hardware need
their own model and review.

## Reproduce

The existing solver Docker image is reused; no new dependency or host solver
installation is needed. Raw files remain under ignored
`fea/generated/floor-contact/`, separate from historical results.

The preparation step requires the generated `2x8-foot100` 60 mm bulk INP and
its matching JSON, not just the committed result summary. On a fresh checkout,
first generate that reference using the
[bulk FEA reproduction commands](physical-footprint-results.md#matched-bulk-fea)
at the end of that report (the 60 mm solve is sufficient). Build the existing
image with `docker build -t mini-moonboard-fea:box-v1 -f fea/Dockerfile .` if it
is not already present. The floor preparation verifies the generated input
identity, and the contact run checks its integrated mass against CAD.

```sh
uv run python -m fea.floor_contact --prepare
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 python3 fea/floor_contact_toy.py
# Repeat the toy with --quadratic.
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 python3 fea/floor_contact.py --mu .3
# Separate sensitivity: --mu .5; neither coefficient is measured floor data.
# Lower-penalty trial: --mu .5 --stiffness 1000 --max-seconds 240.
uv run python -m fea.floor_contact_record
uv run pytest -q tests/test_floor_contact.py
```

The quadrature unit test runs in the existing image when it is available and
is explicitly skipped otherwise; the pure deck/output tests require no Docker.
