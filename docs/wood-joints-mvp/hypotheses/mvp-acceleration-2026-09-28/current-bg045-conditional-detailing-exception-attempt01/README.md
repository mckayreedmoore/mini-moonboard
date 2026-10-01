# BG045 conditional 4D exception and geometry-only band screen

This packet records the current A1-rear BG045 axis-2 block-edge comparison and
one unapproved, geometry-only both-Y-face band sensitivity. It preserves the
reviewed 92 candidate bolt axes. It changes no production axis or geometry,
does not query or rebuild CAD, and runs no native solver.

## Current exception

For the named conditional 1/4-in bolt scenario, `D = 6.35 mm`, so the Table
12.5.1C perpendicular-to-grain loaded-edge comparator is `4D = 25.4 mm`.
A1-rear `knee_outer_left_inner_header_2` has a modeled source-envelope
center-to-`−Y` distance of `20.0 mm`. The explicit conditional difference is
therefore `25.4 − 20.0 = 5.4 mm`.

That arithmetic does not depend on inspecting delivered stock. It remains a
conditional source-envelope detailing exception, not an adopted joint failure
or a move instruction. The block's proposed grain is `+Z`; the A1 axis-2
lateral action on it is `(50.096, −71.224, 0) N`, perpendicular to that grain.
The source ray screen and the two-axis resultant both identify `−Y` as the
first face for this A1 case. A ray is geometric context; NDS does not supply a
universal ray-intersection algorithm for every oblique in-plane action.
Separate signed-component face checks are a conservative sensitivity, not an
independent universal NDS rule. The A1 header's full lateral action is oblique
to its proposed `+X` grain, so its isolated cross-grain component does not
settle the header's detailing applicability.

The reviewed scope is NDS-2024 Chapter 12: §12.5.1.3 refers dowels with
`D ≥ 1/4 in` to Tables 12.5.1C/12.5.1D; Table 12.5.1C provides 4D loaded and
1.5D unloaded perpendicular-to-grain edge distances. Section 12.5.2.2's
end-grain lateral factor does not waive the detailing provisions. Applicability
to the completed end-grain block detail, and any group-versus-individual
direction convention, remain unresolved. The source dependency records the
official Chapter 12 source digest and reviewed clauses.

## Optional both-face band arithmetic

Requiring both block Y faces to be at least 4D would give a geometric center
band `−150.3 ≤ y ≤ −67.75 mm` in the current `[-175.7, −42.35] mm` source
envelope. This is only a conservative two-face envelope sensitivity. It is
not an NDS loaded/unloaded-edge interpretation, is not approved, and does not
specify an axis change.

| BG045 axis | Current Y (mm) | Current −Y/+Y block distances (mm) | Band Y (mm) | Shift (mm) |
|---|---:|---:|---:|---:|
| `knee_outer_left_inner_header_1` | −62.35 | 113.35 / 20.00 | −67.75 | −5.40 |
| `knee_outer_left_inner_header_2` | −155.70 | 20.00 / 113.35 | −150.30 | +5.40 |

The current A1 action on axis 1 points toward `−Y`, where its edge distance is
113.35 mm. Its 20 mm `+Y` side is the unloaded side on that named reading and
exceeds conditional `1.5D = 9.525 mm`; moving axis 1 inward is not required by
that loaded-edge comparison. Applying 4D on both faces moves each axis anyway,
reducing their Y pitch from 93.35 to 82.55 mm. No row-spacing conclusion is
implied.

The required geometry consequence is near the existing BG003 orthogonal X
bores. The pinned finished-profile section has two BG003 center lines at
`(Y,Z) = (−106.2281, 331.3156)` and `(−77.3026, 365.7876) mm`; the modeled
BG003 and BG045 bore diameters are each 7.5 mm. Since the cross-bores traverse
the same section in the existing profile query, the screen's minimum
centerline distances reduce to the Y separations below. The nominal web is
centerline separation minus the sum of the two radii (7.5 mm total).

| BG045 axis / BG003 bore | Current centerline distance (mm) | Band sensitivity (mm) | Current nominal web (mm) | Band nominal web (mm) |
|---|---:|---:|---:|---:|
| Axis 1 / BG003 bore 1 | 43.878 | 38.478 | 36.378 | 30.978 |
| Axis 1 / BG003 bore 2 | 14.953 | **9.553** | 7.453 | **2.053** |
| Axis 2 / BG003 bore 1 | 49.472 | 44.072 | 41.972 | 36.572 |
| Axis 2 / BG003 bore 2 | 78.397 | 72.997 | 70.897 | 65.497 |

The `2.053 mm` value is a nominal geometry-only web between modeled bore
envelopes, not a strength margin or splitting criterion. Axis 1's inward move
is what brings it closer to BG003 bore 2. This is a required review item before
any axis change, along with recomputing the complete bore union and the
continuous finished profile at the proposed coordinates. The reused BG003
profile query samples 72 rays; it does not optimize a continuous minimum
through receiver thickness, and it covers the current axes rather than the
proposed band.

The header source-envelope Y distances under the band would be 31.75/107.95 mm
(`+Y/−Y`) for axis 1 and 114.30/25.40 mm for axis 2. The simple rectangular
envelope shows no new header edge proximity in this arithmetic, but the header
force remains oblique and its actual finished receiver is not qualified.
Existing washer-seat records preserve the seat centers but mark the washer
unselected and omit the exact finished support polygon and opening radius;
they cannot establish washer fit, bearing support, or clearance after a move.
Among the ten unchanged Hillman screw axes entering `base_header`, the nearest
XY projection is `kicker_header_left_5`: 85.850 mm from axis 1 and 118.551 mm
from axis 2. This is only a lower-bound source-coordinate screen using legacy
occupied envelopes, not a physical Hillman dimension or receiver-capacity
check; no claim is made about the other screw receivers.

## Stop boundary

This packet describes conditional coordinates only; it authorizes no model
change. Before implementing a relocation or altering reviewed geometry,
resolve the loaded-edge applicability for the completed block detail; check
actual finished edge/profile and tolerances; recompute the affected BG003/BG045
bore union, web, spacing and receiver geometry; validate washer support/access
and the affected corner screw receivers/load transfer; and apply the relevant
complete-joint bearing, net-section/group interaction, and supported splitting
methods. The identified screw dependency here is the ten `base_header` Hillman
axes; preserve the 66-screw inventory and expand receiver checks only for
another identified geometric consequence. Preserve the reviewed 92-axis
geometry until required changes are reported and reviewed.

The current method gap is specific: the screened EN 1995-1-1:2004 §8.1.4 /
Figure 8.1 arrangement is not mapped to BG045's end-grain-axis block/header
topology, while NDS §§3.8.2 and 11.1.3 do not supply a general equation for
this new bolt-group arrangement. The existing profile screen is for current
geometry and does not certify the described band. No universal
oblique-ray/component rule or complete splitting criterion is established
here.

The read-only arithmetic is reproducible with [`produce.py`](produce.py). Its
source SHA-256 pins and the machine-readable calculations are in
[`detail-screen.json`](detail-screen.json). Key reused records are the
[BG045 applicability dependency](../current-bg045-edge-applicability-dependency-attempt01/README.md),
[BG045 two-case direction screen](../current-corner-bg045-two-case-wood-mode-screen-attempt01/README.md),
[local section screen](../current-corner-local-wood-screen-attempt01/README.md),
and [BG003 finished-profile query](../current-knee-three-member-profile-attempt01/README.md).
