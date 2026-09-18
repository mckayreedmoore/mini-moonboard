# Floor-runner angle mechanics: actionable disposition

This investigation advances the [complete-wrench review](floor-flush-angle-review.md).
It identifies a published steel basis and the specific limitation that prevents
an independent screw-and-shell calculation from qualifying the existing ML24Z
detail. No hardware or drilling is changed.

## Steel material is now established

[IAPMO ER-280](https://forms.iapmo.org/ues_reports/reports/er_0280.pdf), revised
April 28, 2026 and valid through January 31, 2027, explicitly includes ML angles
in §3.1.13. Section 3.2.1 establishes ASTM A653 SS steel with minimum yield
strength 33 ksi and tensile strength 45 ksi. Its No. 12 base-metal thickness is
0.0975 inch, or **2.4765 mm**. The report includes Z variants.

Use that thickness for a lower-bound steel assessment. The manufacturer's
nominal CAD thickness in [the geometry ledger](ml24z-reference.json) is
2.55524 mm. Substituting the CAD thickness would increase an elastic plate
bending section modulus by **6.46%**. This is a distinction between nominal
geometry and resistance thickness, not evidence of an incorrectly manufactured
part. Keep the CAD archive unchanged.

## Independent screw assessment has a specific applicability obstacle

[ICC-ES ESR-2236](https://cdn-v2.icc-es.org/wp-content/uploads/report-directory/ESR-2236.pdf)
provides SDS25112 steel strengths, withdrawal data and lateral methods. However,
its §4.1.5 NDS steel-to-wood route requires **45 mm minimum penetration**.
The current screw is only 38.1 mm long before the angle is deducted. Therefore
that route cannot qualify this screw/angle assembly, even if its calculated
yield modes pass.

The separate Table 2 tested lateral reference requires Table 4A geometry.
Current base-header holes have adjacent parallel/perpendicular-to-grain offsets
**6.35/38.1 mm**. They do not meet its row/stagger requirements. The report's
§4.1.1 leaves connections outside its description to a separate complete design;
it does not provide missing wood splitting resistance. Catalog ML24Z values
remain usable for their covered installation, but cannot establish arbitrary
local screw demands outside that envelope.

Thus a shell model and isolated nominal screw capacities would still leave the
actual short, closely spaced screw group unsupported. This finding rules out
that proposed shortcut; it does not prove that the factory screw pattern fails.

This obstacle concerns replacing the entire connector resistance with the
generic lateral method. It does **not** invalidate the separately published
withdrawal method or require discarding applicable ML24Z lateral ratings. A
supplemental withdrawal-only check could retain the catalog lateral load path,
provided the catalog load's inherent wrench and the supplemental wrench are
both established. The current total screw forces do not uniquely provide that
decomposition. Dividing unlisted F2 equally among three screws would omit its
concurrent moments and redistribution.

## Actual demand makes the missing evidence finite

From the current saved A12-left report, over all 144 angle screws:

| Quantity | Demand | Screw |
| --- | ---: | --- |
| Maximum withdrawal | 224.341 N | `clip_angle_base_left_beam_3` |
| Concurrent shear there | 445.548 N | same |
| Maximum lateral force | 733.260 N | `clip_single_top_left_1_beam_1` |

Withdrawal is the force on wood opposite the installation axis. Compression
must not be relabeled withdrawal. These loads come from rigid angle bodies;
a flexible shell/contact model would redistribute them. They are demands,
not accepted design values or a proof of failure.

The largest flange moment **projected onto the actual bend line** `u × v` is
only **7.222884 N·m**, also at the left base angle. Its full moment magnitude
or force-parallel 12.052 N·m couple is not the bend-opening moment. A local
steel check must translate the complete wrench to each actual section and
resolve bending, torsion and shear there; this note establishes no steel
failure. The next largest bend-line projection is 6.235409 N·m at
`clip_timber_header_outer_left`.

## Recommended next physical direction

Do not spend six new frame solves on an unchanged connection family whose
complete resistance remains unavailable. First develop one representative
joint with a fully described resistance route:

1. Keep the commercial angle carrying its applicable catalog force directions.
2. Provide separate, explicitly located commercial ties or direct structural
   screws for separation and residual moments, with adequate wood geometry.
3. Model contact and both load paths together. Do not assume the new connector
   takes all separation or that the original angle loses its moment demand.
4. Repeat the local template for each affected station and verify the resulting
   full wrench, fastener geometry and member load introduction.

A compliant direct-screw layout would require a different length/arrangement
and cannot use the current 38.1 mm header depth blindly. No such arrangement
is selected by this note. The exact unresolved input is **resistance of the
actual closely spaced SDS group under its recovered combined loads**, together
with flexible angle/contact response. Steel grade is no longer a missing input.

No external review, physical floor test or manufacturer correspondence is added
as a mandatory project gate. Without a supported local resistance model or a
physically different supported joint, construction release remains unjustified.

## Follow-up: concrete commercial tie layouts

The following are physical alternatives to investigate, not selected parts.
The governing source is [Simpson C-C-2026](https://ssttoolbox.widen.net/content/orplhjaqw1/pdf/C-C-2026.pdf).
Pages 299–301 cover hurricane ties; pages 303–305 cover stud/plate ties.

### Rim or center principal to header: H3, with changed end geometry

H3 detail 7 fastens into the upper top plate only. Its single-plate footprint
is therefore preferable to the ordinary H2.5A double-plate detail. H10A field
bending is limited to 6:12, excluding the present 50° inclined member.
H1A's fixed 2x seat does not fit an 89 mm rim.

However, general note (k), page 288, assumes **3½-inch rafter overhang for
exterior installations**. The available rear/downhill mounting is exterior;
its current flush end does not satisfy this assumption. The front/uphill
header face is covered by the kicker. Consequently **H3 is not a drop-in
remedy**. A concrete next CAD candidate would restore at least the prescribed
overhang at the rear/downhill side, retain a square seat, and put the H3 plate
flange on the rear header face. The overhang must follow the manufacturer's
dimensional convention; do not substitute an unverified slope projection.

Current raw CAD gives rear header Y = −175.7 mm, header Z = 238.9–277 mm and
rim rear cut Y = −175.7 mm up to Z = 334.3981 mm. Unlike the historical
[H3 rejection](round-structural-h3-fit.md), the wing now reaches wood. At the
nominal H3 top height Z = 356.375 mm, the inclined rim edge is approximately
Y = −157.259 mm. Its 39.6875 mm wing extends to Y = −136.0125 mm, leaving
about 21.25 mm of gross overlap. These are necessary envelope facts only;
the manufacturer's actual upper screw holes must lie in that remaining wood.

Two H3s on opposite faces of an 89 mm rim meet the catalog's 63.5 mm minimum
rafter-thickness condition for same-plate-side pairs. A 38.1 mm center principal
does not meet that paired condition. Do not transfer the outer-rim arrangement
to it or infer collision-free staggered nailing without actual hole positions.

Use the exact H3 fastener-specific load table. Page 380 lists eight SD9112
screws as an approved arrangement, but page 382 warns that screw substitutions
may reduce loads. That listing alone does not establish the 210/170 lbf lateral
references associated with the main 2½-inch nail row. No screw-based H3
capacity is assigned here.

### Vertical post to header: SSP single-plate detail

The catalog allows the stud/plate family at either top or bottom plates.
Its SSP single-sill detail uses four 0.148 × 1½-inch stud nails and one such
plate nail; DF/SP uplift is 395 lbf at the listed 1.6 duration factor. At
the adopted duration factor 1.0, the corresponding reference is **1,098 N**.

Rotate that entire detail 180° to put the stud below the single header.
This preserves the timber grain relationships and separation load direction
relative to the connector. Place it on the free rear face. Nominal SSP width
34.925 mm fits a 38.1 mm post, and its 169.8625 mm overall length fits the
238.9 mm post height. Exact lower-flange seating, holes, timber end distances,
nearby runner/bolt interference and driver access remain to be checked.
The cited SSP rating establishes an uplift comparison only.

### Required connection idealization

Neither a thin tie nor a pair is automatically a physical hinge. A sound local
model must retain plate flexibility, screw slip and compression-only timber
contact, and recover each tie's force at a declared physical application line.
Separated ties and contact may resolve joint moments as force couples. The
remaining moment within each individual tie still needs to be reconciled with
its catalog installation or assessed mechanically. Replacing a rigid ML24Z
with another rigid six-degree-of-freedom connector and checking only its
force table would reproduce the original gap.

Thus the useful first local study is **SSP at a rear post/header interface**,
where actual single-plate and grain conditions match a published detail.
The H3 rim option additionally requires restored overhang and verified factory
hole geometry. No physically valid single/end ML24Z reorientation on the
existing rim/header contact faces was established.

## Reproduce the demand inventory

```sh
python3 - <<'PY'
import json
from math import sqrt
from pathlib import Path

path = Path('fea/generated/floor-flush-first/a12-left/block-01/report.json')
report = json.loads(path.read_text())
rows = []
for name, row in report['physical_connection_forces'].items():
    if not name.startswith('clip_'):
        continue
    force, axis = row['force_on_first_xyz_n'], row['axis']
    axial = sum(f*a for f, a in zip(force, axis, strict=True))
    shear = sqrt(max(0, sum(f*f for f in force)-axial*axial))
    rows.append((max(0, -axial), shear, name))
assert len(rows) == 144
print('withdrawal, concurrent shear, screw:', max(rows))
print('withdrawal, maximum shear, screw:', max(rows, key=lambda r: r[1]))
PY
```
