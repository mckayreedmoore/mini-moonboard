# Single-2×8 leg connection review package

This package implements the six-bolt connection in actual frame geometry.
**Assessment failed; do not use these drilling coordinates for construction.**
See the [decision and specific failures](../wider-leg-decision.md). It is
an isolated fresh-stock candidate, not a construction release. Use the final
[assessment](../../fea/results/wider-leg-assessment.json) for numerical decisions;
the earlier 0.818 feasibility ratio describes a different, centered-stock layout.

## What changed

- Replace both support legs and both adjoining outer rims with single nominal
  2×8 members. No doubled vertical stock is used.
- Keep the rims' panel-facing surfaces fixed; the additional depth grows rearward.
- Use six ½-inch bolts per leg, replacing four. The pattern has three stations
  at 66 mm along the leg and two stations at 84 mm along the rim.
- Move the group center 27 mm along the leg and 4 mm along the rim from the old
  four-bolt center. Extend the leg's upper end by 50 mm to maintain end distance.
- Use catalog bearing plates and extra-thick washers. The new leg detail needs
  no custom metal fabrication.

The assembly retains the preceding reinforcement candidate's other components,
including its historical base shoes. This package does not convert the whole
board to a fabrication-free design or qualify those base shoes.

## Lumber and hardware

Require dry, unincised, grade-stamped Douglas Fir–Larch No. 2 or a separately
checked substitute. Nominal section is 38.1 × 184.15 mm; accepted thickness
for the bolt stack is 37.5–38.5 mm. Dimensions and grain direction matter;
an unspecified species or grade is not interchangeable.

| New stock | Quantity | Minimum modeled blank length | Practical stock length |
| --- | ---: | ---: | ---: |
| Single 2×8 outer rim | 2 | 2608.024 mm | 10 ft |
| Single 2×8 support leg | 2 | 1863.960 mm | 8 ft |

Blank lengths are stock envelopes, not instructions to make both ends square.
The STEP model defines bearing-end cuts and the level leg foot. Hardware totals
are 12 Grade 5 ½-13 × 5-inch bolts, 12 matching nuts, 24 Simpson BP1/2 plates,
and 36 Wrought MCX 014943 washers. See the complete
[hardware schedule and acceptance dimensions](../wider-leg-hardware.md).

## Geometry and drilling

- [Complete STEP assembly](assembly.step)
- [24 member-hole drilling records](drilling.csv)
- [Geometry, mass, interference and source-hash report](review.json)
- [Parametric source](../../mini_moonboard/wider_leg_frame.py)

The CSV identifies each member, world Y/Z position, grain station, depth
coordinate and datum. Each bolt passes through two members, hence 24 records
for 12 bolts. Bore diameter is 14.2875 mm (9/16 inch). The coordinates describe
fresh stock; they are not a repair pattern for previously drilled members.
Use the STEP datum geometry when laying out the CSV. Do not substitute the
older preliminary pattern's −20 mm group shift.

Nominal checks find no new interference, all bores fully contained, and all 24
plates fully supported. The narrowest nominal plate-edge reserve is about
2.45 mm. That reserve is the total available allowance for stock-edge,
hole-location and plate-orientation errors together; it is not an additional
per-operation tolerance. Verify full plate support on the actual assembly.
This report does not claim a manufacturing-tolerance sweep.

Complete modeled assembly mass is 194.583 kg before the separately applied
hold/electrical equipment allowance. Existing panel attachment and LED axes
remain in the model. Source hashes bind the nominal geometry evidence to the
files used to generate it.

## Scope of acceptance

The wood, dowel, plate and washer calculations are analytical comparisons with
explicit load/contact/material assumptions. They are not measured breaking
strengths. A passing conditional ratio cannot establish an unverified plate
material property, foot-pressure distribution or lap-joint prying bound.
Owner acceptance of panel construction and exclusion of floor-friction testing
remain the scope basis; no additional panel or floor test is requested here.
