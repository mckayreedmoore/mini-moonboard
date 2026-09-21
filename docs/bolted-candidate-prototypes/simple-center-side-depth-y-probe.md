# PB-02 ten-bore side-cleat Y screen

The [bounded CAD probe](../../scripts/simple_center_side_depth_y_probe.py) applies
three side-cleat depths and upright Y coordinates to the current ten-bore
`shorter_8in_trial` center. These are finite nominal poses, not an optimized
design. The right post alone stays shifted; the existing principal block,
rear cleat, backer, and both inner kicker edge supports remain. The probe
checks all 66 fixed panel/kicker screw axes (48 panel, 18 kicker), all ten
bores, intended wood reception, modeled washer seats, hardware, socket bodies,
and one modeled insertion approach for each bolt. The changed link insertion
uses its actual trial length plus the helper's illustrative 35 mm allowance.
The long coaxial extension sweep, bought bolt stacks, ratchet motion, and
assembly order are not established by this screen.
No half-lap or custom steel is introduced.

The side cleat remains one solid 88.9 mm wide by 183 mm tall member with its
rear Y face at −175.7 mm against the rear cleat. The front face and upright
axis change together; the link bore and exposed front end follow the new face.
All dimensions below are nominal millimeters.

| Pose | Cleat depth | Upright Y | Least side Y reserve after conditional 4D + project 5 | CAD result |
| --- | ---: | ---: | ---: | --- |
| Minimum depth, centered | 60.8 | −145.3 | 0.0 | Reject: upright-left washer bears on only 0.89818 of modeled principal seat. |
| Moderate depth, upright retained | 71.1 | −135.0 | 0.0 | Reject: side cleat overlaps right bottom rail by 6,512 mm³; principal-right hardware/washer also meets cleat. |
| Deeper, upright retained | 80.0 | −135.0 | +8.9 | Reject: side cleat overlaps right bottom rail by 27,311 mm³; principal-right hardware, washer and socket also meet cleat. |

The 56.8 mm inherited cleat cannot contain two 30.4 mm Y edge distances:
the symmetric minimum is 60.8 mm. The minimum-depth trial removes that
arithmetic deficit but moving the upright toward the rear loses full modeled
washer support on the inclined principal. The deeper two leave the upright
at its current Y; their extra front wood collides with existing structure.
Each trial retains the two inner kicker edge supports, and the changed side
cleat and all bores avoid the 66 fixed screw axes.

The [current placement inventory](simple-center-current-placement-table.md)
provides the source and meaning of the conditional comparators. Even after
the side-Y deficit is removed, every sampled pose retains a −0.55 mm
conditional post-high grain-end reserve and −2.9 mm conditional block/header
parallel-bolt pitch reserve (in each receiving member), after the single
5 mm **project allowance**. These are project comparisons, not code failures
or an NDS determination. The principal's inclined-member and orthogonal-bore
classifications remain unknown, so there is no whole-center clearance claim.

No sampled pose passes complete nominal CAD. This screen supplies no strength,
load path, tolerance, stock-yield, delivered hardware, fabrication, or
drilling qualification. It does not replace the two displaced legacy clips.

Run the focused check:

`.venv/bin/python -m scripts.simple_center_side_depth_y_probe`
