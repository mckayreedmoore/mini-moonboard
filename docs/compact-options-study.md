# Compact-frame options 1, 2, 3, 4 and 8

This bounded study implements the owner's requested assumption audit, bolt-layout
screen, larger-bolt and stronger-steel comparisons, and leg-position/angle trial.
It retains the 4×6 structural-member direction and compact 2×6 kicker base.
The published preferred geometry remains unchanged until a replacement is supported.

## Load and resistance assumptions

The existing target is one 250 lb climber. The current demanding case applies
2224.11 N downward (twice bodyweight), 300 N rearward, a 100 mm hold standoff,
actual modeled assembly weight and 25 kg equipment. Twice bodyweight and the
simultaneous horizontal action remain screening scenarios, not a validated
climbing-impact spectrum. The adopted duration factor remains 1.0.

The prescribed angle-dependent reduction term was previously bounded by its
maximum Ktheta=1.25. Recomputing all yield modes with each bolt's actual maximum
force-to-grain angle changes the original two-bolt ratio from 2.208 to 1.960.
This corrects a conservative assessment assumption without changing the geometry
or native forces. A hypothetical additional duration factor of 1.6 gives 1.225;
its applicability has not been established and it is not adopted.

| Accepted A12 case | Downward force | Rearward force | Original reference ratio | Actual-angle reference ratio |
| --- | ---: | ---: | ---: | ---: |
| Original doubled-load case | 2224.11 N | 300 N | 2.208 | 1.960 |
| New static comparison | 1112.06 N | 300 N | 0.738 | 0.659 |

The static case's maximum timber displacement is 14.04 mm. Its conservative
force-directed edge-distance screen has a −33.84 mm minimum margin: a lateral
strength ratio below one is not an overall connection pass. Changed force
sharing and contact states mean the doubled-load result cannot simply be divided
by two. The matching reports and checks are under
[compact-options-study](../fea/results/compact-options-study/).

The official [EN 12572-2:2017 preview](https://preview.sist.si/sist-preview/39968/eb82f102549541eba9b79bad025432c2/SIST-EN-12572-2-2017.pdf)
separates structural-integrity calculation from panel-deflection testing. Its
panel-deflection load must not be substituted for the complete frame design
load: the preview does not include the complete normative load/calculation
annexes. No EN compliance or reduced climber target is inferred here.

## Reference basis

- [AWC 2024 NDS corrected reduction table](https://web-media.awc.org/wp-content/uploads/2025/03/31134949/2024-NDS-Errata-and-Addenda-03.28.25.pdf).
- [AWC NDS connection adjustments](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Chapter11.pdf): duration-factor eligibility, group action and other applicable adjustments remain separate.
- [AWC NDS dowel fasteners](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20210928_AWCWebsite_Chapter12.pdf): bending-yield evidence and the relevant connection equations.

## Bolt layouts, diameters and steel

The bounded screen evaluates 18 families: two, three or four bolts per leg,
with diameters ⅜, ½, ⅝, ¾, ⅞ and 1 inch. It uses actual two-bolt A12 joint
resultants, actual force-dependent grain-angle reductions, a 3 mm geometric
reserve and the retained conservative edge/end rules. This is a fixed-resultant
screen, not an assembled prediction of each proposed connection.

No tested family passes at adopted Cd=1.0, or at the separately labeled
hypothetical Cd=1.6. The best eligible family remains two ¾-inch bolts at
77 mm spacing: nominal ratio 1.970, hypothetical duration-adjusted ratio 1.231.
The small difference from actual recovered-force ratio 1.960 reflects elastic
redistribution assumptions in this planar screen. Neither ⅞-inch nor 1-inch
families contain eligible layouts within the stated bounds.

Increasing hypothetical bolt bending yield from 45 to 90 ksi at the same best
layout does not improve the governing ratio: Mode II contains no bolt bending
yield parameter. It helps some smaller-bolt bending-controlled comparisons,
but their saved best layouts still exceed the reference. This is not a verified
Grade 8 product substitution or a reoptimization at the higher bending strength.
NDS 12.3.6.2 permits the stated bending-test or tensile-test-derived evidence;
a grade label alone has not established the delivered fastener assumptions.

Reproduce the bounded layout and steel comparison:

```sh
uv run python -m scripts.compact_layout_options
```

## Physical leg-position trial

Five raw-stock options retain both ¾-inch bolts and the compact base. All pass
raw hole containment and washer seating. These fit checks do not rank strength.

| Option | Joint shift along slope | Rearward foot shift | Leg angle from vertical |
| --- | ---: | ---: | ---: |
| control | 0 mm | 0 mm | 15.08° |
| foot150 | 0 mm | 150 mm | 19.95° |
| foot300 | 0 mm | 300 mm | 24.54° |
| lower150 | -150 mm | 150 mm | 24.51° |
| upper150 | 150 mm | 150 mm | 15.78° |

The `upper150` option is selected for one actual assembled trial because the
higher support attachment reduces the unsupported upper rim length while the
rearward foot shift retains a similar leg angle. This is a geometric rationale,
not a proven optimum. The four alternative fits do not receive inferred native
forces or a passing claim.

The selected option also passes the complete machined-receiver audit. Its new
leg prisms have level floor-contact faces, preserve the original group-to-stock
depth offset and top allowance, and use fresh rim/leg drilling. Panel axes,
commercial connections and the kicker base are retained.

```sh
uv run python -m scripts.compact_option_study --leg upper150 --output fea/generated/compact-leg-upper150-a12
```

The `upper150` A12 doubled-load solve converged after 12 contact iterations.
Its left-joint moment falls from 701.70 to 293.72 N·m. The worst bolt force falls
from 10.601 to 5.234 kN. With actual force-to-grain angle and adopted Cd=1.0,
the lateral ratio falls from 1.960 to **0.979**. Maximum timber displacement
falls from 58.33 to 21.06 mm. The original maximum-angle comparison remains
1.096, and the original full-thread-root sensitivity remains 1.520.

This is a promising first-case lateral result, not an overall pass. Only about
2% nominal lateral margin remains. The first right-hand bolt has 138.59 N total
lateral force, of which 132.74 N acts across the rim grain; its adjusted distance
to the loaded rim edge is about 42.36 mm versus the retained 76.20 mm (4D)
reference, producing a −33.84 mm margin. This is not merely a tiny cross-grain
component in an otherwise parallel load. The force magnitude is small, but
that does not by itself establish an exception to the placement criterion.
Directional placement, actual hardware/thread coverage, remaining local wood
checks and the revised load envelope still prevent construction release.

[Archived upper150 evidence](../fea/results/compact-options-study/upper150-rear/manifest.json)
contains the native report, authenticated source snapshot, actual CAD receiver
geometry and checks. Its assumption comparison is in the adjacent
`assumptions.json`. No earlier candidate is overwritten or qualified by these
results. The current viewer retains its preceding preferred configuration.

407 default tests passed with 15 historical tests deselected after the new
assumption, geometry and initial layout work. The final layout extension receives
its own focused checks. An independent read-only review found no confirmed
physical-geometry/native-axis mismatch in the leg-position implementation.

## Layout screen using the moved-leg forces

The follow-up screen uses the accepted upper150 forces and its actual revised
leg grain. No ¾-inch or larger layout meets the retained edge/end reserve in
this same-case screen. Thus the actual two-bolt lateral ratio of 0.979 does not
supply a placement-compliant solution by itself.

The best eligible nominal-45-ksi layout is two ⅝-inch bolts at ratio 1.422.
Independently optimizing layouts at hypothetical Fyb=90 ksi gives a best result
of **1.172**, using three ½-inch bolts per leg, with 3.10 mm minimum edge/end
reserve. It remains above one at adopted Cd=1.0. Its hypothetical Cd=1.6 result
is 0.733, but neither the higher bending-yield product evidence nor duration
adjustment is adopted, and no new three-bolt assembled solve has been performed.
This identifies a possible combination for further development, not released
hardware or drilling. The bounded results do not prove that every possible
leg position or bolt pattern fails.

The source script and [updated screen](../fea/results/compact-options-study/upper150-layouts.json)
retain exact axes and search limits. Original fixed-layout results remain
preserved separately. No additional native trials were run for bolt grade alone.

The approved follow-up is recorded in the [two higher-leg trials](compact-higher-leg-study.md), including verified catalog hardware, both actual assembled results and the remaining placement shortfalls.
