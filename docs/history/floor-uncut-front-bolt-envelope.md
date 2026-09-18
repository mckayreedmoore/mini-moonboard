# Uncut-candidate front bolt dimensional envelope

Date: September 14, 2026. Candidate: `compact-floor-uncut-development`.
This is a dimensional screen of the separate investigation, not released drilling
or a replacement for the selected flush candidate's evidence.

## Combined spacing and timber boundaries

The two front axes have 40.5 mm pitch along the Y/Z diagonal, centered at
Y = −91.5625 mm and Z = 84.1375 mm. Each coordinate offset is
`40.5 / (2 sqrt(2)) = 14.318912319 mm`. The lower axis is therefore
(Y, Z) = (−105.881412319, 69.818587681) mm, and the upper axis is
(−77.243587681, 98.456412319) mm. Both sides mirror these coordinates.

Apply the existing assumptions together: independent 1 mm drill-position error
radius and 2 mm inward profile-cut error measured normal to each boundary.
These are distinct assumptions, not a general ±3 mm fabrication tolerance.
The adopted placement screen uses 7D at loaded grain ends and 4D at loaded
cross-grain edges, with D = 9.525 mm. Applicability and current load directions
remain separate resistance questions.

| Comparison | Worst dimensional value | Adopted minimum | Margin |
| --- | ---: | ---: | ---: |
| Pair spacing after independent drill errors | 38.500000 mm | 38.100000 mm | 0.400000 mm |
| Lower axis to post foot / runner front end after drill and cut errors | 66.818588 mm | 66.675000 mm | 0.143588 mm |
| Upper axis to post forward edge / runner top after drill and cut errors | 38.243588 mm | 38.100000 mm | 0.143588 mm |

Thus the pitch increase does not fail these simultaneous boundary comparisons,
but it leaves little additional dimensional allowance. Stock undersize, layout
datum error and drilling registration are not additional free allowances.
The post retains Y = −175.7 to −36 mm; the runner top is Z = 139.7 mm.
These dimensions and `front_points()` in the candidate model reproduce the table.

## Washer perimeter

The recorded maximum ⅜-inch washer OD is 1.030 inches, giving radius
13.081 mm. The closest raw-profile boundary is 41.243588 mm from the upper
front axis. Subtracting maximum radius and the same combined 3 mm error
allowance leaves **25.162588 mm** of exterior-boundary clearance. The two
maximum-size washers also remain separated: worst center spacing 38.5 mm
minus two radii leaves **12.338 mm**.

These are perimeter comparisons. They do not establish complete flat seating
around all machining, adequate bore clearance, tool access, or registration
through the assembled 177.8 mm grip. Those checks must use the actual attachment
faces, openings and delivered hardware. Washer size does not cure the tight
wood end/edge margin.

## Front bolt length exposes a separate failure of the catalog-wide envelope

The provisional front stack is ⅜ × 8 inches through 139.7 mm of post and
38.1 mm of runner. Using the existing quarter-thread-bearing route and maximum
head-washer thickness requires full body through
`177.8 + 2.6416 − 38.1/4 = 170.9166 mm` from under the head.

The [recorded catalog limits](clear-space-hardware.md) for the 8-inch bolt are
−0.18 inch length tolerance and at least 1.25 inches of thread. At nominal
length, subtracting minimum thread length leaves 171.45 mm, only 0.5334 mm
above the required body length. At the shortest listed length it leaves
**166.878 mm**, falling **4.0386 mm short**, even before runout or additional
thread length. The stated catalog range therefore cannot support a blanket
nominal-diameter bearing acceptance for this stack.

Minimum thread length is not a guarantee of supplied full-body length. A
particular measured bolt might meet the body requirement, but no supplied lot
has been measured. A different justified hardware/stack or resistance route
is needed before this investigation can close. Nominal tip projection and
nut seating alone do not resolve the shortfall.

## Decision

The revised front pitch passes the stated spacing and raw boundary arithmetic.
The complete fabrication envelope remains open, and the catalog-wide front
full-body envelope does not pass. Keep the investigation unselected and do not
release its drilling or transfer the flush candidate's connection resistance.
