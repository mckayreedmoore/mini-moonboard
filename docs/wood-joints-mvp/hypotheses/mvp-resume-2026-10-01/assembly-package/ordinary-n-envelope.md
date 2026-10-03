# Installed ordinary-N planning envelope

This packet records a completed finite numerical projection of the unadopted
108-stack working proposal. It covers 108 bolt shafts and heads, 108 nuts,
216 washers, 66 purchased-policy screw occupancy cylinders and 24 connector
body enclosures. It does not select a station datum, authorize a dimensional
exception or establish delivered-part fit. Parent executed `attempt01`
successfully. Its status is `conditional_source_datum_diagnostics_only`;
N17 remains open because the current station datum mapping is not adopted.

## Definition and exact remaining ambiguity

The frozen [`ordinary_n_envelope` criterion](../../../criteria.json) requires:

> Check connector and installed hardware against the 139.7 mm local-N envelope from a named datum; document any dimensioned exception.

The recorded direction is `N = (0, -sin(50°), cos(50°))`, in global XYZ;
positive N is rearward from the inclined board. The ordinary limit is an
upper coordinate of 139.7 mm from a named station datum, not a 139.7 mm
bolt-length limit or a direction-independent part-size limit. The recorded
policy reports the minimum coordinate as well; it supplies no separate
accepted frontward bound.

The [historical outer-node result](../../../outer-node-result.md#required-revisions)
names the outer post/header-front-bottom corner for its WJ-03 layout. The
[reviewed 24-block projection](../../evaluation-resume-2026-09-24/current-block-n-envelope-attempt01/README.md)
explicitly found no adopted station datum for the reviewed revision. That
historical corner cannot silently become the datum for every current joint.

This producer names diagnostic host datums rather than leaving every
projection at the global origin. Where available, it uses each named host's
recorded `actual_vertex_minimum_N_then_T_then_X` frame origin from
[`source-inventory.json`](../../../source-inventory.json). For a new receiver
without that record, it identifies the reduced member descriptor's
centerline-start point explicitly. Neither choice is an adopted N17 datum.
Each component is compared against every named receiver datum; the report
does not select the most favorable receiver or origin.

The missing criterion definition is therefore **the adopted station-to-host
datum mapping for this 108-stack proposal**. Direction and reference distance
are already defined. Changing an origin changes the measured rearward
coordinate, so numerical projection alone cannot close that missing mapping.

## Numerical comparison and geometry basis

For a point `p` and named datum `d`, the local coordinate is
`n = N · (p - d)`. For an installed finite cylinder with unit axis `a`,
radius `r` and two axial endpoints, its extrema add and subtract
`r × sqrt(1 - (N · a)²)` from the endpoint projections. This is an analytical
projection of that planning cylinder. Regular hex heads and nuts use their
circumscribed cylinders; washer annuli use their outside disks.

World-axis bounding boxes are projected by their eight corners. Their
extrema bound the saved enclosure, not the exact finished shape. A bound
above the ordinary reference is labeled a **conditional enclosure excess**;
it does not prove that the actual part exceeds the reference or collides.
The effective member references and saved bounds remain attached to each
body. Display meshes are not used as collision or fit evidence.

The existing 104 stacks use the frozen working-order lengths and matched
nut/washer routes. Eight corrected top stacks reuse their saved catalog
component cylinders, including the eight 25.4 × 2.5 mm retail rail washers.
Other candidate stacks retain the recorded wood-face position when the
catalog washer-thickness maximum changes the planning under-head point.
The four added knee stacks use the proposed **165.1 mm** stock; the separate
203.2 mm sensitivity and all withdrawal/tool sweeps are excluded from the
installed inventory.

Retained 3/8-inch and 1/2-inch nut/washer dimensions have saved catalog
ranges. Equivalent machine-readable catalog head-height/across-flats bounds
were not found in those packets; their saved modeled head enclosures remain
identified proxies. The 66 Hillman 42605 entries project the recorded
63.5 mm occupied screw cylinders. A complete delivered screw-head/profile
envelope is unavailable. These exact unsupported product facts remain
separate from the missing station-datum adoption.

`comparisons.csv` records component, axis/body, receiver, named datum,
N minimum, N maximum and conditional rearward excess. `envelope.json`
retains the per-component geometry basis, component counts, controlling
rows, dimensioned conditional excesses and unsupported facts. It preserves
all comparisons, including those within the reference. Temporary workspace
is a separate operation scope and is not mixed into this installed result.

## Completed finite diagnostics

The run contains **1,476 receiver-relative comparison rows**, including
component rows and complete five-role stack unions. It reconciles all
108 shafts, 108 heads, 108 nuts, 216 washers, 66 screw cylinders and 24
connector enclosures against the frozen 50-body reference. Every comparison
has a named source datum candidate; none is an adopted station datum.

| Inventory | Minimum N across comparisons (mm) | Maximum N across comparisons (mm) | Largest conditional excess above 139.7 mm | Controlling maximum and named receiver datum |
| --- | ---: | ---: | ---: | --- |
| Complete bolt-stack planning unions | -89.050000 | 1547.326680 | 1407.626680 | `lumber_leg_bolt_left_2` / `lumber_leg_left` and symmetric right pair; source host frame origin |
| Screw occupancy cylinders | -18.256250 | 215.781521 | 76.081521 | Ten `kicker_header_left/right_1..5` cylinders against their named kicker source host frame origins |
| Connector saved enclosures | -95.344782 | 379.281845 | 239.581845 | `knee_outer_left_spine` / `base_post_outer_left` and symmetric right pair; source host frame origin |

These extrema combine different named receiver origins; they are not one
station's dimensions. The large retained leg-bolt coordinate is measured
from its recorded whole-leg frame origin at the foot. It does not mean that
its bolt or head projects 1.4 m rearward from the local joint. This concrete
result shows why a whole-member source origin cannot automatically serve as
the ordinary local joint datum.

The report retains **94 conditional exception-candidate rows** from complete
stack, screw and connector comparisons. This is a count of object/receiver
comparisons, not 94 distinct failed parts or adopted exceptions; component
rows are excluded from that count to avoid counting each stack role again.
All physical-exceedance, datum-adoption, exception-adoption and criterion
acceptance claims remain false. Saved enclosure bounds and incomplete
product profiles also retain the limitations described above.

The exact next definition decision is to name the current station origins
and map each station's connector and installed hardware to those origins.
The N direction and 139.7 mm reference already exist. This packet supplies
dimensioned source-datum diagnostics for that decision without selecting an
origin, approving an exception or altering the formal criterion.

## Parent execution and evidence

The standard-library API is `build(output)`. Use a fresh immediate child of
`rawlocal/ordinary-n-envelope/`; the producer refuses an existing output.
The recorded parent command below has already completed; no further build
is needed for this packet.

```sh
.venv/bin/python -B \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/ordinary-n-envelope.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/rawlocal/ordinary-n-envelope/attempt01
```

The result directory contains `envelope.json`, `comparisons.csv`, a producer
snapshot and `receipt.json`. The receipt binds frozen inputs and output
hashes and checks source bytes again after the calculation. Raw results stay
ignored. Parent owns execution and publication; no CAD, frame/native solve,
test or review run is part of this producer. Formal criterion status,
candidate adoption, delivered conformity and physical release remain unchanged.

Completed output:
[`rawlocal/ordinary-n-envelope/attempt01/`](rawlocal/ordinary-n-envelope/attempt01/).
Parent reported exit 0 and verified all 13 input pins before/after and the
four output hashes recorded in the receipt. No source bytes changed.

| Evidence | SHA-256 |
| --- | --- |
| [Producer](ordinary-n-envelope.py) and saved producer snapshot | `2986919f215d9aaeb857e5d3b9a79b85e148e47cba418c7a14979eb594f0430a` |
| [Envelope result](rawlocal/ordinary-n-envelope/attempt01/envelope.json) | `278407d84e0061ab845ff73fb31dfc5551300a3afb9aa20327a5cca9e6b86ffc` |
| [Comparison CSV](rawlocal/ordinary-n-envelope/attempt01/comparisons.csv) | `efdf6a0062a79850503cbf5f790075ab54cf94fc3a66515b3efc131b3660c978` |
| [Receipt](rawlocal/ordinary-n-envelope/attempt01/receipt.json) | `8cec13103d82b262cdbd9446aefb2227ecc0270ebb241999366bc1be8f690fc2` |

The calculation is complete. Adoption of a current station datum,
dimensional exceptions, delivered hardware conformity and N17 closure are
not established by this run.
