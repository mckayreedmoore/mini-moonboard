# Flush-end floor-beam revision

**Selected development geometry: fabrication release is pending.**

Current work is governed by the [floor-runner MVP master
plan](floor-runner-mvp-master-plan.md) and [frozen criteria
ledger](floor-runner-mvp-criteria.md). Fresh no-slip cases remain pending; the
finite-friction A12-left result below is historical comparison evidence.

`compact-floor-flush-development` implements the owner's requested finish of
`compact-floor-taper-development`: floor-runner front ends terminate at the
outer-post plane; rear ends follow the rear legs' inclined back faces. Lower
rim ends terminate at the post/header plane, and leg tops terminate at the
rear faces of the rims. Whole kicker panels and the 1:12 leg recess remain.

The old 7 mm rim-end and 18 mm leg-top reserves are removed. Bolt end distances,
end-cut/bearing resistance, bracket attachment geometry, floor footprint and
actual assembled response must be checked for these new cuts. The preserved
six passing taper cases do not qualify this revision. Existing bracket stations are retained initially. Front and rear runner bolt
pairs are also relocated to preserve end distances within the shortened beams.
The upper bolt pair is relocated downward and slightly rotated within the
joined timber, retaining 56 mm pitch; new forces must confirm the adopted
force-directed edge interpretation and connection resistance.

The complete finite task is tracked in the
[floor-runner MVP master plan](floor-runner-mvp-master-plan.md). Required work includes
source-method applicability, local runner/leg contact, justified fabrication
allowances, a consolidated hardware list and practical assembly instructions.
No drilling or cut tolerances are released by this preview.

## Workshop planning and procurement

The [candidate-specific assembly guide](floor-flush-assembly-guide.md) consolidates
the 20 timber pieces, six panels, 24 angles, 144 angle screws, 66 panel screws
and twelve complete bolt stacks. It records the current cut datums, saw options,
delivered-hardware checks and proposed assembly order. It is a reviewable draft;
the [current construction sheets](floor-flush-construction/), supported
fabrication allowances and remaining resistance decisions must be reviewed
together before release.

## Historical force evidence

The fresh A12-left case converged with 72 explicit timber face contacts and
18 clearance monitors. Its [assessment](floor-flush-a12-left-assessment.json)
meets 37 of 38 implemented criteria, with bolt lateral ratio 0.8792 and sampled
net-member ratio 0.7488. Its historical rim projected-seat scalar is negative
and now retained as a non-adopted sensitivity. The
[cut-method review](flush-cut-method-review.md) and
[taper-method review](taper-method-applicability-review.md) preserve the unresolved
local resistance issues. One converged case does not release this design or
supply the remaining five current cases.

## Initial geometry result

All 24 bolt receivers fit the requested geometry, including complete washer
seats. This does not establish joint resistance. The lower rim ends have
102.805 mm retained normal depth. The historical quarter-depth projected-seat
screen has a **negative 4.970 mm margin** on both rims. It remains recorded as
a non-adopted sensitivity because its mapping to this supported terminal bevel
was not established. Adopted retained-section, bearing, contact and gross/net
checks are frozen in the [criteria ledger](floor-runner-mvp-criteria.md).
With the original upper axes, the upper leg bolt had only 67.102 mm adjusted
distance to the newly flush end. The revised pair addresses that geometric
shortfall; the old force response does not establish its resistance.

The complete bracket envelopes remain within the header footprint; their
existing locations are retained for this initial preview. Screw seating and
resistance remain part of the current connection review.

## Relocated upper bolt layout

Both sides use the same Y/Z positions, mirrored only through the board width.
The pair centre is Y = 1134.25 mm, Z = 1761.5 mm in assembly coordinates. Its
56 mm separation follows the normalized Y/Z direction (18, 53). This is fresh
stock drilling; do not add these holes to timber drilled for an older pattern.
The candidate retains four half-inch upper bolts and twelve bolt stacks total.

Layout screening uses 7D end distances with the existing 3 mm inward-boundary
allowance, 4D on both rear-leg depth edges, and the preceding six cases' rim
load direction (4D loaded, 1.5D unloaded). New joint forces must confirm that
rim load direction. A screen assuming 4D on both rim edges is more restrictive
and is not claimed to pass for this pair.

## Relocated runner bolt layouts

Front pair: centre Y = -91.5625 mm, Z = 84.1375 mm, with 39.5 mm spacing
along the normalized Y/Z direction (1, 1). Rear pair: Y/Z = (1551, 69) and
(1517, 97.5) mm. Both sides mirror these locations through the board width.
Both runner pairs are screened for 7D end distances, 4D on both depth edges
and at least 4D pair spacing, with the existing 3 mm boundary allowance.
Bolt lengths and wood grips are unchanged. These fresh-stock layouts still
require current joint forces, local resistance and full receiver-fit checks.

## Preserved construction basis

Solid 4x6 legs and rims, compact 2x6 header/posts, two full 2x6 outboard runners,
66 panel/kicker screws and twelve complete bolt stacks remain. Upper bolts
retain 56 mm pitch. The main-face datum remains 277 mm above the floor, including
127 mm pad allowance and 150 mm exposed kicker. Two 48 x 72 x 5-inch crash pads
sit side by side with their centre seam running front to back. They remain
separate from the structural assembly and weight.

The [preceding taper hardware requirements](floor-runner-taper-hardware.md)
provide the initial bolt specification: four half-inch x 8-inch upper bolts,
four three-eighths x 4-inch front bolts and four three-eighths x 4.5-inch rear
bolts. Actual shank coverage, nut seating and washers must meet the documented
conditions; those specifications alone do not qualify the shortened ends.

Previous tapered and exterior-brace designs remain available as historical
comparisons. Use the model identifier, not a generic "floor beam" label, to
identify a drawing or analysis.
