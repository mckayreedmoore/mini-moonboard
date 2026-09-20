# PB-02 solid right-center post: bounded CAD probe

Status: **4×4 has a full-section nominal clearance path, but zero-reserve
cleat edges; no connection, floor-bearing, or drilling approval**. This
continues the [adjusted two-cleat trial](simple-center-post-transfer-adjusted.md)
at commit `8f0dffe`. Only its shifted right center post is substituted.
The original left post, inclined right upright, header, kerf-right panels,
all 48 panel and 18 kicker screw axes, separate 4×6 backer, and two plain
solid-wood cleats remain in their prior poses. No glued-up or built-up post
is assumed. The 1/4 in bolt/7.30 mm bore illustration remains conditional.

## Stock poses and nominal geometry

Both poses start at the existing rear-cleat contact plane Y=−175.7 mm,
X=88.75 mm, and Z=0 mm. The rear cleat remains X=89.05…139.85,
Y=−213.8…−175.7, Z=0…460 mm; the side cleat and backer are unchanged.
The post bolt X axes move from 107.8 to **114.45 mm**, keeping Z=110/190 mm.
This moves only these two new bolt axes, never a panel or kicker screw.
It also keeps the proposed serial post → rear cleat → side cleat → original
upright path. The alternative 4×6 is a single bounded ordinary-stock pose,
not a search or a recommended substitution. **No pocket or counterbore is
modeled or accepted** for either post.

| Solid post | X, mm | Y, mm | Base area, mm² | Backer contact Y, mm |
| --- | --- | --- | ---: | ---: |
| 4×4, 88.9² | 88.75…177.65 | −175.7…−86.8 | 7,903.21 | 38.1 |
| 4×6, 88.9 × 139.7 | 88.75…177.65 | −175.7…−36.0 | 12,419.33 | 88.9 |

The original shifted box post occupied X=88.75…126.85 and
Y=−175.7…−36.0 mm, for 5,322.57 mm² at Z=0. The new posts widen the
ground footprint in X, but the 4×4 shortens it 50.8 mm in Y. Their feet
do not intersect the modeled frame timbers, including the floor runners
and lower rail; both have full rectangular Z=0 faces in this uncut CAD.
The ground, any landing pad, fasteners to it, leveling, transport envelope,
and bearing under either footprint are **not modeled**. Both ordinary
nominal stock sections require delivered dimensions, species/grade,
straightness, and cut length (238.9 mm) to be checked before use.

The actual post/rear-cleat contact slice is 12,136.12 mm² in either pose.
The backer remains X=−50.95…88.75, Y=−124.9…−36.0, supporting both inner
kerf-right kicker edges without a positive-volume overlap. The unchanged
left-center and reassigned right-center kicker screw receiving portions
remain wholly in the left post and backer, respectively. All 66 fixed
screw envelopes were screened at their purchased lengths; neither post,
cleat, nor trial bore intersects them. The four illustrative bores each lie
fully in their intended timber pair; they hit no other wood or bore.

## Exact nominal edge/end distances

These are distances from **bore centers** to modeled rectangular timber
boundaries, with no stock or drilling tolerance. The illustrative 4D
reversible loaded-X-edge screen for a 6.35 mm bolt is 25.4 mm; the 7D
full-value parallel-tension end screen is 44.45 mm only where that NDS
classification applies. Force signs and applicability are unresolved.

| Group/member | Center distances, mm | Conditional observation |
| --- | --- | --- |
| Both post bolts, X edges | 25.7 / 63.2 | Near edge exceeds 4D by **0.30 mm**. |
| Rear cleat at post bolts, X edges | 25.4 / 25.4 | Exactly 4D; **zero reserve**. |
| Post low/high, Z ends | 110 / 128.9; 190 / 48.9 | Upper top: 4.45 mm to 7D. |
| Cleat link, both cleats' X edges | 25.4 / 25.4 | Exactly 4D, zero reserve. |
| Cleat link, rear/side Z ends | 370 / 90; 93 / 90 | Above 7D nominally, if applicable. |
| Upright bolt, side-cleat Y edges | 28.4 / 28.4 | Rectangular cleat only. |
| Upright bolt, side-cleat Z ends | 73 / 110 | Inclined upright needs own check. |

For fixed rear-cleat X bounds 89.05…139.85 mm, a reversible 4D screen
requires its post-bolt center to be **both ≥114.45 and ≤114.45 mm**.
This trial uses that sole nominal X location. The widened post allows
114.15…152.25 mm on its own X edges, but the unchanged cleat governs.
Thus replacing the post removes its 6.35 mm shortfall from the adjusted
trial while leaving **no** reversible-edge tolerance at the rear cleat or
link. This is **not a fit verdict** for a reversible joint, a robust
drilling layout, or a strength finding. The
inclined upright's own loaded-edge and oblique-end distances, force
direction, group spacing, bearing, splitting, and net sections remain open.

## Old hardware and access

The historic `clip_split_header_center_right` still intersects the new
4×4/4×6 post by 17,739.26/25,786.04 mm³, respectively. The side cleat
still intersects `clip_split_base_center_right` by 13,986.25 mm³. Modeled
old clip screws also intersect new timber. **Both clip stations and their
fasteners must be removed and their header/base/upright duties replaced**;
this probe does not qualify those duties. Other old connections have not
been promoted to a new capacity model.

At all eight bolt ends, illustrative 20 mm diameter washer disks have
complete nominal wood bearing **on the uncut full-section faces**. For the
4×4, its front face is 50.8 mm behind the installed kicker, and a straight
20 mm radius × 20 mm outward tool cylinder at each front bolt clears every
modeled wood solid with the kicker present. This is a separate no-pocket
check: a short exposed head/washer and straight tool have nominal space;
actual hardware projection and service-tool travel still need measurement.
The buildable access order is to leave the kicker removable during bolt
work, then fit it after the joint is assembled; future service requires
removing it. No precision nut pocket is assumed.

The 4×6 front face is flush with the kicker back plane. Both 20 mm radius
front tool probes intersect the installed right kicker, and any exposed
front hardware would need space there. Removing the kicker for access does
not solve the final installed interference. A recessed pocket/counterbore
would be a different, optional diagnostic with lost-section and fabrication
questions; **the no-pocket 4×6 is not yet viable**. The adjusted trial's
10 mm seat is not inherited as an accepted simple-joint solution. Neither
pose verifies delivered washers, bolt length, shank/thread placement, nut
engagement, socket swing, or withdrawal.

Reproduce with `.venv/bin/python scripts/simple_center_wide_post_probe.py`
and `.venv/bin/python -m pytest -q
tests/test_simple_center_wide_post_probe.py`. Geometry inputs are the
uncut frame solids and unchanged kerf-right axes/profiles; no CAD or
source-packet file is modified.
