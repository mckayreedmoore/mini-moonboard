# Nominal HL33 hybrid center trial — rejected installed pose

This is one kerf-right geometry screen, not a connector selection or drill plan.
Regenerate the paired JSON with `uv run python -m scripts.hardware_first_center_hl33
--output docs/bolted-candidate-prototypes/hardware_first_center_hl33.json`.
The JSON records every modeled intersection and the six full bore envelopes.

The [official 2026–2027 Simpson catalog](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog)
(HL33 row, PDF page 315) is the current source: 7 gauge, equal 3¼-in (82.55-mm) legs, 2½-in
(63.5-mm) bend length, one hole per leg, D1 = 1¼ in (31.75 mm) along the bend,
D3 = 2 in (50.8 mm) on the vertical leg, and two ½-in bolts total per angle.
The horizontal-leg hole distance from the bend is **not dimensioned** in the
catalog drawing; this trial assumes 50.8 mm. Ideal 4.55-mm plate thickness and
14.2875-mm wood bore diameter are additional **assumptions**, not measured
HL33 dimensions or drilling instructions. Rectangular plates omit bends,
coating, holes, and tolerances. No catalog load is transferred to this pose.

The geometry follows the HL35 hybrid arrangement: one rear-Y HL33 joins a
single solid common post to a raised one-piece shaped header; one outward-X
HL33 joins each one-piece thick principal to that header. The header is
X = −1219.2..1216.025, Y = −258.25..−36, Z = 238.9..327.8 mm. The original
header was 38.1 mm deep; this proposed center region is 88.9 mm deep, and the
rest of the original span remains. This is an authorized hidden-frame change,
so the old header depth is not a rejection reason. The principals are 88.9 mm
wide at their original ±70-mm centerlines. The upper HL33s start at Y = −100
mm; their one nominal vertical hole is at Y = −68.25 mm. The lower HL33 is
behind the header, over the 184.15-mm-wide post. All 66 purchased panel and
kicker axes retain their CSV coordinates. The post and header meet the kicker
rear face at Y = −36 mm and together back the inner seam from Z = 0 to the
277-mm kicker top. The four center kicker screw envelopes each intersect the
post by 438.127 mm³. Positive modeled intersection is not qualified embedment.

CAD fusions describe one-piece timber shapes, **not** glued plies or lap
joints. Minimum sampled blank envelopes, in mm, are 184.15 × 139.7 × 238.9
for the post, 2435.225 × 222.25 × 88.9 for the header, and 88.9 × 139.7 ×
2466.3113 for each principal. Principal Y/Z rotation is sampled at 0.1°;
these are geometric bounds without machining margin. A 4×10×10-ft header,
6×8 post, and 6×6×10-ft principals dimensionally contain those envelopes.
For context, a [retail 4×10 lead](https://www.lowes.com/pd/4-in-x-10-in-x-10-ft-Douglas-Fir-Lumber-Common-3-562-in-x-9-5-in-x-10-ft-Actual/1000028857)
lists an approximately 3.562 × 9.5-in cross section, and a
[retail 6×6×10-ft lead](https://www.homedepot.com/p/202534027) lists 5.5 ×
5.5 × 120 in. These are dimensional leads, not proof of available matching
grade, delivered straight stock, defect-free yield, transport, or machining.
The header needs a 10-ft blank for practical end allowance: a nominal 8-ft
blank exceeds its 2435.225-mm modeled length by only 3.175 mm.

The nominal screen finds no plate-pair, plate-to-intended-wood, plate-to-panel,
or bore-to-panel collisions. All six bores stay inside their intended timber;
independent bore envelopes do not cross. None of the 66 frozen 50.8-mm panel
screw envelopes meets a plate or bore or loses its original modeled receiving
wood. Treating the purchased 63.5-mm **overall** screw length as occupied is
only a conditional sensitivity; it also yields no plate or bore intersection.
None of the 12 existing frame-bolt occupied cylinders meets new wood, plate,
or bore. Their receiving wood, bolt stack, and resistance still need review.

**Reject this installed pose.** Each widened principal intersects its bottom
rail by 133,291 mm³ and both service rails by 135,193 mm³ each. Each upper
vertical plate intersects its bottom rail by 10,576 mm³. Each upper principal
bore also intersects that bottom rail by 3,819 mm³. These are nominal CAD
volumes, not measured delivered-part collisions. Shortening or moving rails
could define a new frame trial, but requires a new rail joint and frame-bolt
check; this trial does not silently assume that redesign.

The single lower HL33 is **not** established as reversible-F1 rated in this
arrangement. Catalog tabulated directions and installation conditions cannot
be converted into a two-way force rating for this unreviewed joint.

Even a collision-free revision would still require delivered connector hole
and bend measurements; head, washer, nut, tool and withdrawal clearance;
wood edge/end distances; delivered screw shaft occupancy and embedment;
one-piece blank verification; and bracket, bolt, timber, and overall load-path
checks. No capacity, cutting, procurement, or drilling approval follows.
