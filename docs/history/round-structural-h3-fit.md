# H3 supplemental tie: current mounting rejected

**An H3 cannot be added in its standard vertical-uplift mounting to the
unchanged `round-structural-development` base using the inspected nominal
manufacturer geometry.** The rear mounting cannot reach the rim; the front
mounting is occupied by the kicker panels. No part, screw axis, or drilling
instruction has been changed.

## Primary geometry and scope

The **US [C-C-2026 catalog](https://ssttoolbox.widen.net/content/orplhjaqw1/pdf/C-C-2026.pdf),
page 299**, has a dimensioned H3 graphic. Visually inspecting that graphic
confirms **1 9/16 inch (39.6875 mm) for each perpendicular wing**, 1 1/2 inch
(38.1 mm) lower-wing height and 4 5/8 inch (117.475 mm) overall height. These
labels are embedded in the graphic and were absent from extracted PDF text.
The US graphic is the controlling nominal geometry for this result.

The regional [installation guide](https://strongtie.co.nz/sites/default/files/installation_guides/H3%20Installation%20Guides.pdf)
places the upper flange against the rafter side and the lower flange against
the perpendicular vertical plate face, with four fasteners into each member.
This mounting also matches the US catalog's H3 installation on page 301.

The linked installation DXF was also inspected. It contains projected
isometric artwork, including spline representations of the holes. Its drawing
coordinates were **not** treated as manufactured hole coordinates. The
[source reference](h3-geometry-reference.json) records inspected hashes and
dimensions. The earlier regional illustration labels 115 × 40 × 40 mm;
**no regional-to-US dimensional equivalence is assumed**. Its dimensions are
not used in the corrected calculation. Neither illustration supplies exact
manufacturing tolerances or product hole centers.

Precise hole centers are unnecessary to reject the rear placement: even the
entire favorable wing envelope misses the receiver. A detailed H3 solid is
also unnecessary to reject putting its receiver-contact flange into an
already occupied panel volume. These are necessary geometric checks; this
report does not claim a completed hole-pattern, screw-clearance or driver-access
audit.

## Current coordinates and rejection

The [reproducible screen](../fea/round_structural_h3_fit.py) reads the current
raw CAD solids and records the
[corrected result](../fea/results/round-structural-h3-fit-v2.json). Both sides give the
same result:

| Standard mounting | Current geometry | Decisive obstruction |
| --- | --- | --- |
| Lower flange on rear header face | Header rear Y = −270.95 mm; closest rim Y = −223.862730 mm | The 47.087270 mm gap exceeds the complete US 39.6875 mm wing reach by **7.399770 mm**. |
| Lower flange on front header face | Header front Y = −36 mm; header Z = 186.9–225 mm | Kicker plywood occupies **100%** of a 0.1 mm exterior layer over this entire receiver face. |

The rear bound uses the smallest Y anywhere on the rim, at its horizontal
bearing cut. The rim moves farther forward as it rises at 50° above horizontal.
Consequently the upper fasteners' actual raised positions cannot improve the
reach result. Moving the upper flange to either inner or outer rim side, or
changing the left/right handed part, does not change the Y gap.

For the front check, the layer volume is 9290.304 mm³; its intersections with
the two nonoverlapping kicker panels total the same volume. Any lower-flange
material contacting this header face therefore occupies existing plywood.
Installing the tie outside the plywood would introduce an 18.25625 mm spacer
and a different fastener/connection detail. It is not the assessed mounting.

For a vertical bend with the upper flange on either vertical rim side, the
perpendicular lower flange must lie on a front or rear vertical header face.
The header end faces are parallel to the rim side faces. Rotating the H3 so its
bend becomes horizontal changes the manufacturer's uplift load direction;
that is not an escape from this standard-mounting rejection.

## Consequence for the base decision

Withdraw H3 as a direct add-on for the unchanged candidate. Making space would
require a specific revised panel/receiver or connection detail, followed by
actual hole, fastener, access and load-path checks. The previously identified
conditional uplift value is not assigned to this frame. No alternative tie is
selected merely to continue a hardware search.

Validation: twelve lightweight tests cover the rejection logic, partial-coverage
and sufficient-reach counterexamples, invalid/double-counted geometry, input
changes during assessment and preservation of existing output files. Source
hashes are captured before CAD evaluation and checked afterward. Outputs are
created exclusively; an existing report is never overwritten. The CAD run
independently measures the current obstruction. It does not assess connection
resistance or close the overall base release gate.

The preserved `round-structural-h3-fit-v1.json` used the regional 40 mm envelope
without establishing US dimensional equivalence, and recorded source hashes
only after the run. **That report is superseded by v2 and must not be used as
the US H3 fit conclusion.**
