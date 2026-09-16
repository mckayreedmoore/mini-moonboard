# Flush floor-beam fabrication budget review

**Development review only. The recorded independent drilling-error envelope
does not preserve the front bolt-pair spacing screen. The shop acceptance rules
below define the FR-3 inspection limits; they do not constitute a fabrication
release.**

Candidate: `compact-floor-flush-development`. The
[build package](floor-flush-build-package.md) controls status. This review closes
the question of whether nominal receiver fit alone demonstrates the proposed
dimensional envelope: it does not. It leaves the supported fabrication-allowance
work in the [MVP master plan](floor-runner-mvp-master-plan.md) ready for exact
closure. The finished acceptance limits are stated below rather than left as a
generic tolerance.

## Reproduce the dimensional comparison

```sh
python3 scripts/floor_flush_fabrication_review.py
```

The standard-library script reads the saved current geometry, A12-left assessment,
and construction connection axes. It reports source hashes, pair-spacing budgets,
the tightest saved directional boundary margin, and catalog stack comparisons.
It does not regenerate CAD, rerun a frame case, or represent measured stock.
Catalog bounds reproduce the local hardware assessments listed below; no new
supplier availability or delivered-lot verification is claimed.

## Bolt placement

The saved geometry records a **1 mm drilling-position radius** and **2 mm inward
cut-normal allowance**. Its boundary-ray calculation in
`scripts/thick_leg_geometry.py:edge_rays` shrinks the timber outline inward by
3 mm. This combines two allowances at timber boundaries; it does not account
for two holes independently moving toward each other.

For the adopted 4D pair-spacing screen, independent error disks of radius `r`
can reduce nominal centre spacing by `2r`. Both mirrored joints give the same
results:

| Pair | Nominal spacing, mm | Adopted 4D, mm | Nominal margin, mm | Margin with two independent 1 mm errors, mm |
| --- | ---: | ---: | ---: | ---: |
| Upper rim/leg | 56.000 | 50.800 | 5.200 | 3.200 |
| Front runner/post | 39.500 | 38.100 | 1.400 | **−0.600** |
| Rear runner/leg | 44.365 | 38.100 | 6.265 | 4.265 |

The front pair can be only 37.5 mm apart within the recorded independent error
envelope. A **0.7 mm independent radius is the mathematical ceiling for this
spacing comparison alone**, with zero remaining spacing margin. It is not a
recommended shop tolerance: boundary distances, drilling angularity, actual
hole diameter, mating-member registration, retained sections and hardware seats
must all be checked together. Common movement of a fixture preserves its pitch,
but independent pitch error does not disappear merely because a jig is proposed.

For the finished front paired holes, use one registered fixture on each mirrored
joint and measure the hole centres after drilling. Accept only a centre-to-centre
pitch of **39.0–40.0 mm**, a pair midpoint no more than **0.5 mm** from the
member datum, and each hole no more than **0.5 mm** perpendicular to the
specified pair line. Reject and reassess any pair outside those limits. Never
elongate a hole or pull a misregistered joint together with the bolt.

The tightest saved A12 directional boundary margin is **0.497 mm**, at
`rail_front_bolt_left_2` in `base_floor_left`, `depth_negative`, after the existing
boundary allowance. This is residual analytical margin, not another allowable
cut or drilling error. The result retains the saved A12 force-directed loaded
edge interpretation; it does not establish margins for the five missing current
cases or reverse loading. Nominal geometry is not newly declared defective by
this dimensional review; the proposed independent drilling envelope is deficient.

## Hardware and stock-grip budgets

Use the existing [half-inch assessment](compact-half-inch-hardware.md),
[three-eighths catalog bounds](clear-space-hardware.md), and
[corrected rear-stack assessment](floor-runner-recess-hardware.md). With nominal
wood grip and maximum head-washer thickness, the adopted nominal-diameter route
requires full body through at least
`wood grip + head washer − nut-side timber bearing length / 4`.

| Joint | Nominal grip, mm | Required full body to first transition, mm | Extra threads/runout budget at shortest bolt and minimum catalog thread length, mm | Tip beyond nut at shortest bolt, thickest washers and tallest nut, mm |
| --- | ---: | ---: | ---: | ---: |
| Upper | 177.800 | 158.928 | 1.600 | 2.743 |
| Front | 76.200 | 69.317 | 5.359 | 10.033 |
| Rear | 88.900 | 78.842 | 7.518 | 9.017 |

The extra-thread figures are conditional dimensional budgets, **not guaranteed
delivered shank lengths**: catalog thread lengths are minimums. Measure actual
full body to the first transition, and count runout as threaded bearing. Verify
usable threads start before the nut's bearing face and that complete threads
extend beyond its outer face. With minimum washers and nominal thread starts,
the available nut-seat distances past those starts are 17.069 mm upper and
3.251 mm front/rear. These values do not qualify an actual runout profile.

Actual stock grip affects both checks. Increased grip consumes tip projection
millimetre for millimetre, and its distribution between the two timbers changes
the required shank threshold. The upper stack's 2.743 mm projected-tip budget
must also cover the actual bolt-tip chamfer and formed-thread engagement; it is
not a 2.743 mm allowable timber oversize. No generic torque or preload is added.

On delivery, inspect every bolt against the existing budgets: measure full
smooth body to the first thread transition, thread/runout length, actual wood
grip, washer thickness and outside dimensions, nut height, and threads beyond
the nut. The minimum required full-body lengths to the first transition are
**158.928 mm upper, 69.317 mm front and 78.842 mm rear**; the recorded extra
thread/runout budgets are **1.600, 5.359 and 7.518 mm**, respectively; and the
shortest-stack tip budgets beyond the nut are **2.743, 10.033 and 9.017 mm**.
Reject incompatible delivered hardware rather than substituting spacers,
reversing the stack, or cutting threads.

## Washer seating and machined clearances

The catalog upper washer thickness range is 2.1844–3.3528 mm; the smaller range
is 1.6256–2.6416 mm. Catalog maximum outside radii exceed the modeled radii by
**0.0635 mm upper** and **0.381 mm front/rear**. Existing all-24-receiver fit uses
nominal CAD washer envelopes. A full-seat tolerance check must include those
maximum envelopes, actual bore/washer concentricity, cut variation and nearby
openings; a zero unsupported volume at nominal geometry does not provide that
budget. Existing catalog-minimum washer resistance checks answer a different
question and do not certify the maximum-size fit.
Accept only full, flat seating of the maximum washer envelope on sound timber;
any unsupported edge, rocking washer or partial bearing is a reject and requires
reassessment.

The 2 mm runner/recess clearance remains nominal CAD geometry. Taper depth,
runner height, foot cuts, stock variation and relative displacement can consume
it. It is not permission to deepen the recess or a released gap tolerance.
The historical negative projected-seat scalar is retained as a non-adopted
sensitivity. It does not grant extra inward cut allowance; adopted retained
section, bearing, contact and gross/net checks control.

Inspect the 1:12 recess and all receiver stock before drilling: timber must be
sound and check-free through the transition, with a smooth continuous slope,
no overcut, and no split, tear-out or damaged bearing surface. Reject or
reassess any such defect; do not repair it by deepening the recess.

## Concrete remaining release constraints

1. Apply the frozen retained-section, bearing, contact and gross/net checks and
   retain the taper local-fracture method limitation and inspection controls.
2. Define a practical paired-hole drilling/inspection method whose actual pitch,
   registration and angular errors fit the entire connection budget. Check both
   mirrored pairs; the present independent 1 mm radius does not work at the front.
3. Establish accepted actual stock sections, cut limits, bore dimensions and
   washer-seat envelopes, then assess their combined adverse configurations.
4. Recalculate shank, nut seating and engagement against actual delivered stock
   and hardware. Reject incompatible hardware; do not improvise spacers or holes.
5. Give measurable rejection/rework rules for overcuts, misplaced holes, split
   receiver wood, insufficient full-body coverage and incomplete seating.

For the 66 purchased Hillman 42605 screws, verify every axis remains contained
in its supporting receiver and no screw tip protrudes. Use them only for the
accepted panel/kicker scope; do not transfer SPAX capacity, spacing or stiffness
claims. Place the two **48 × 72 × 5 inch** pads side by side with their seam
front-to-back; they remain loose viewer/support-layout items, not structural
supports.

The existing material, accepted panel/T-nut and floor scope remains unchanged.
Future current response cases use the owner's explicit conditional no-slip
support assumption, with normal contact allowed to open. The recorded A12-left
response used the historical monotonic per-cell Coulomb scenario and remains
evidence only under that assumption. This review adds no floor test, panel
campaign or external signoff gate.
