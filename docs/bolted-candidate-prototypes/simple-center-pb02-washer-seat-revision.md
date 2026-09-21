# PB-02 center side-cleat and upright washer-seat revision

This is a bounded nominal CAD result against the working PB-02 ten-bore center.
The [reproducible probe](../../scripts/simple_center_pb02_washer_seat_revision.py)
uses the current `simple_center_side_depth_y_probe` and its maintained ten-bore
checker. It changes only the right upright side cleat, the upright bore Y/Z,
the cleat-link bore length to its new front face, and the adjacent
header-side cleat top Z (with the checker following its changed top face).
The left center post/support, panel and kicker axes, kerf-right outlines,
inner kicker supports, and all existing source geometry remain untouched.
No ledger or existing source is revised.

All coordinates are millimeters. The side cleat remains a single square-ended
88.9 mm wide solid with rear Y −175.7 and top Z 460. The working 61.6-mm
trial uses front Y −114.1, bottom Z 277, upright Y −144.5 and Z 356.
The adjacent header-side cleat top is Z 344 instead of 348. This creates a
nominal 2 mm gap from the upright-left 10 mm radius washer envelope to its
top. The washer is modeled as fully bearing on the inclined principal.

| Trial | Side depth | Upright Y/Z | Header-side top Z | Side bottom Z | Ten-bore nominal CAD |
| --- | ---: | ---: | ---: | ---: | --- |
| Minimum depth, lowered header cleat | 60.8 | −145.3 / 355 | 343 | 277 | Clear, but zero side-Y target reserve |
| Working 61.6-mm trial | 61.6 | −144.5 / 356 | 344 | 277 | Clear; rear side-Y reserve +0.8, front 0.0 |
| Deeper, square-shortened from below | 65.0 | −141.1 / 358 | 344 | 305 | Rejected: 517.239 mm³ side-cleat/right lower-rail overlap |

The working 61.6-mm trial checks all ten intended bores with 100% modeled reception,
all 20 modeled washer seats with 100% bearing, all 66 fixed screw axes
(48 panel, 18 kicker), both inner kicker edge supports, neighbor solids,
modeled socket and hardware bodies, and one straight insertion end for each
bolt. The link rear insertion end clears; its front approach intersects the
right lower rail by 2,480.808 mm³. These are nominal model envelopes, not an
assembly-sequence or tool-sweep proof. The working side-cleat Y distances are
31.2 mm rear and 30.4 mm front, meeting the conditional 4D+5 project target
at the front exactly, leaving **0 mm reserve beyond the project 5 mm allowance**.
Its side-cleat Z grain-end distances are 79 and 104 mm
at the upright, and 93 and 90 mm at the link. The least reserve over the
conditional 7D+5 target (49.45 mm) is +29.55 mm.

The shortened header-side cleat still touches the header at Z 277 over
9,273.165 mm² of nominal common face. The header-cleat bore retains positive
reception in both the header and cleat, with 100% total modeled reception.
The probe also confirms all 66 fixed axis names, bounds and modeled volumes
match the unchanged source geometry.

Raising the deeper cleat bottom through Z 305 does not remove its rail
collision: the actual CAD intersection is around Z 407–412. Raising the
bottom above that collision would put it above the upright bore and violate
the 7D+5 bottom-end target. This square-shortening alternative is rejected.

The current placement inventory still reports a −0.55 mm conditional
post-high grain-end reserve and −2.9 mm conditional parallel-bolt pitch
reserves in the header and its post-side cleat, after the single 5 mm project
allowance. Inclined-principal and orthogonal-bore placement classifications
are unresolved. The working pose has only a 2 mm nominal washer-to-cleat
gap and zero front side-Y allowance beyond the project target. Bought stacks,
manufacturing tolerances, complete insertion/assembly access, joint strength,
load path, and the two displaced clip duties remain unqualified.

**Conditional geometry only. No drilling, fabrication, or strength release.**

Run `.venv/bin/python -m scripts.simple_center_pb02_washer_seat_revision`
or `.venv/bin/python -m pytest -q tests/test_simple_center_pb02_washer_seat_revision.py`.
