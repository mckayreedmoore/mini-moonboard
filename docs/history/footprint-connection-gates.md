# Footprint changes: connection and floor-contact gates

Research checked 2026-09-05. This supplements the
[joint development plan](hybrid-joint-next-steps.md), not a new rated hardware
schedule. The 2×8 shallow candidate retains two laminated 19.05 mm plywood
layers per leg, 38.1 mm total; no anchors or crash-pad support are credited.
Intended use remains **one climber, 250 lb maximum**. The 150/200 lb cases and
300 lb sensitivity do not establish validated ratings.

## A longer footprint is not a free connection improvement

Moving the foot centre farther toward the leg-side tipping edge improves that
edge's restoring lever arm, but also lengthens and flattens the lower leg.
Recompute the actual member volume, centre of gravity, floor-cut extremes and
connection actions; extending a support polygon alone does not model a leg.
The continuous hockey-stick profile carries bending through its knee and its
four-bolt upper attachment. It is **not a pin-ended two-force strut**.

For an isolated, weightless, straight pin-ended strut at angle `alpha` above the
floor, a compressive vertical component `V` would imply horizontal spreading
`|H| = V cot(alpha)` and axial force `N = V / sin(alpha)`. Thus shallower struts
would increase spreading per unit vertical reaction. This is an illustrative
mechanics relation, **not the current frame's friction requirement or joint
demand**. The actual floor reaction can vary across the flat foot, the upper
joint transmits moment, and the leg has weight. Neither `H/V` nor equal sharing
between the left and right legs follows from the tipping screen.

The actual nominal CAD profiles give the following geometric comparison. The
last column is the illustrative straight-strut ratio above, **not an output
from a joint/contact solve**. Floor coordinates are world Y; positive extension
is toward the leg side, irrespective of viewer camera orientation.

| Foot-centre extension | Lower segment angle above floor | Leg-side extreme floor Y | Ideal straight-strut `cot(alpha)` |
| --- | ---: | ---: | ---: |
| 0 mm / 0 in | 72.716° | 1398.255 mm | 0.3112 |
| 50 mm / 1.97 in | 70.893° | 1449.246 mm | 0.3464 |
| 100 mm / 3.94 in | 69.109° | 1500.331 mm | 0.3817 |
| 150 mm / 5.91 in | 67.366° | 1551.508 mm | 0.4170 |
| 200 mm / 7.87 in | 65.667° | 1602.773 mm | 0.4522 |

The extreme toe moves slightly more than the foot centre because flattening
the fixed-width profile lengthens its floor cut. Independent CAD inspection
found a valid continuous left-leg solid and a single flat full-width floor face
for all five variants, with area `38.1 × 180 / sin(alpha)`; all non-leg parts
remain identical to the shallow baseline. These nominal geometry checks are
not a floor-pressure uniformity or timber-bearing-capacity assertion.

Whole-frame net horizontal force can be small while opposing foot reactions
are large. Consequently `total horizontal load / total vertical load` is only
a global friction-demand screen, not a sufficient sliding check at every foot.
An unanchored analysis must enforce nonnegative local normal pressure and
bounded local friction; it cannot assign tensile floor reactions to keep the
frame standing. Moving the leg toes does not resolve the separate exploratory
case that tips toward the kicker.

## Conditional rigid-leg free body, before a nonlinear model

The following is a transparent equilibrium diagnostic, not a completed FEA or
capacity calculation. Use the repository's world Y/Z plane (Z upward), one
isolated leg, and force units N with lengths mm:

- `J=(y_J,z_J)`: centroid of its four leg/rim bolt centres.
- `F=(y_F,0)`: resultant floor-contact location, **within the actual foot**,
  not automatically the centre or the extreme toe.
- `H,V`: floor force on that leg, positive +Y/upward, with `V >= 0`.
- `W`: that leg's own downward weight at `y_G`.
- `M_J`: joint moment on the leg, positive about +X.

Equilibrium gives:

```text
joint force on leg = (-H, W - V) in (Y, Z)
M_J = -(y_F - y_J) V - z_J H + (y_G - y_J) W
```

This exposes the tradeoff: at fixed reactions and height, adding `delta` to
the floor resultant's Y coordinate changes the first moment term by
`-delta V`. It does **not** predict the final moment, since H, V, W and the
pressure-resultant location also change. Setting `M_J=0` and `W=0` would imply
`H/V = -(y_F-y_J)/z_J`; that is a hypothetical pinned upper joint, not the
actual four-bolt connection and not the lower segment's knee-to-foot angle.
Do not switch between those different mechanisms to select favorable results.

The current four stations are S=1540, 1620, 1740, 1820 mm, with centroid
S=1680 mm. Their offsets are -140, -60, +60, +140 mm and
`sum(r_i²)=46,400 mm²`. Under an explicitly assumed rigid interface and equal
isotropic in-plane fastener stiffness, the moment-induced force magnitude at
an outer bolt would be `|M_J| × 140 / 46,400`. For example, a **hypothetical**
100 N m pure joint moment gives 302 N at each outer bolt, before vector addition
of direct force divided by four. This is an arithmetic illustration only;
it is neither a computed climbing demand nor allowable bolt capacity. Actual
wood anisotropy, clearance, hole slip, bearing/contact and group action alter
load sharing. Out-of-plane eccentricity adds other moments and bolt axial
forces that this planar diagnostic omits.

AWC's bolted-connection example separately checks fastener yield, net section,
row/group tear-out and spacing effects; simply multiplying a single-bolt
capacity by four is not a sufficient joint check. Its example is not a plywood
leg design table, and the applicable current design basis must be selected for
the actual materials. [AWC bolted-connection design example](https://web-media.awc.org/wp-content/uploads/2021/12/17210649/StructureMag-NDS2015-PracticalSolutions-1611.pdf).

## Next leg/rim joint detail to investigate

Retain through-bolts for detachability provisionally. First evaluate the actual
laminated-plywood-to-lumber lap joint with compression bearing and hole slip;
do not add more or larger bolts solely because the leg becomes longer.
If its demand/resistance or stiffness checks are unfavorable, compare a
designed bearing seat with distributed side plates. A seat can provide a direct
compression path but needs its own attachment, reverse-load behavior, splitting,
edge-distance and tool-access checks. It does not eliminate moment or opening.

| Gate | Required evidence before calling it resolved |
| --- | --- |
| Leg and rim materials | Actual plywood structural designation, layup/strength axes, thickness and defect limits; lumber species/grade and moisture condition; applicable bearing, shear, bending and splitting properties. Birch appearance grade alone is not a structural property set. |
| Two-layer lamination | Selected adhesive approved for the intended load-bearing application and substrate, bondline design, preparation, clamping/pressure, cure and inspection procedure. Include loss of composite action as an uncertainty until justified. |
| Four-bolt connection | Traceable bolt/nut/washer or plate specification, thread extent relative to shear plane, drilled-hole tolerance, end/edge distances in both materials, group action, plywood bearing/delamination and lumber splitting, net section and local plate/head bearing. |
| Changed leg profile | Knee bending/shear, local stress concentration, weak-axis/lateral stability and glue-line demand; full floor cut after angle changes, with tolerances and floor unevenness. |
| Floor and complete frame | Individual reaction/contact-pressure envelopes with unilateral contact and explicit friction assumptions; asymmetric loading and local sliding, not merely a global friction ratio. |
| Rear/backing joints | Existing custom angles and end-grain screws remain unresolved; passing the new leg screen does not validate them. |

APA distinguishes plywood structural ratings, strength axes and bond/exposure
classifications; use the actual panel identification to obtain design properties,
not the isotropic E=7000 MPa comparison assumption.
[APA plywood specification guidance](https://www.apawood.org/engineered-wood-products/plywood-osb/plywood/).
An ordinary woodworking adhesive is not automatically suitable: for example,
Titebond III's manufacturer explicitly excludes structural/load-bearing use.
That product is **not selected for this design**. Obtain an applicable structural
adhesive system and process rather than treating a waterproof designation as
structural qualification. [Titebond III manufacturer limitations](https://www.titebond.com/print/product/e8d40b45-0ab3-49f7-8a9c-b53970f736af).

Manufacturer hardware must match its complete installation, material and load
conditions. Simpson's general notes require washers or equivalent plates under
bolt heads and nuts at wood interfaces. Its catalogue has separate HL heavy
angles and HL strap ties; a family name alone does not select the needed shape,
hole pattern or rating. None is an approved substitute for the current custom
angles. [Simpson connector general notes](https://www.strongtie.com/products/connectors/wood-construction-connectors/technical-notes/general-notes),
[current manufacturer catalogue](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog).

## Completion boundary for this footprint iteration

The useful deliverable is a geometrically checked footprint comparison with
actual inventory/mass and retained failing load cases, plus a selected next
connection-analysis target. It is not a construction release. Preserve the
published bonded-frame FEA as a stiffness reference; do not reuse its numerical
displacements as results for altered legs. Before a joint-capacity conclusion,
obtain the material and hardware inputs above, release perfect ties at the
chosen joint, and verify unilateral contact, force/moment balance and sensitivity
to connection stiffness and clearance. Qualified structural review and a
controlled physical verification procedure remain required construction gates.
