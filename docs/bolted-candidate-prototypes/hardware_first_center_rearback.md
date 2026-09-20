# Rear-backed common center post / HL35 — incomplete installed trial

This is a bounded kerf-right CAD diagnostic, not a joint selection, load
rating, purchase list, or drilling plan. Regenerate the paired JSON with
`uv run python -m scripts.hardware_first_center_rearback --output
docs/bolted-candidate-prototypes/hardware_first_center_rearback.json`.
It reads all 66 fixed panel/kicker axes and changes none of them.

The [Simpson HL catalog](https://dhcsupplies.s3.us-east-2.amazonaws.com/Documents/simpson-strong-tie/hl-angles.pdf)
gives the HL35 a 127-mm bend length, 82.55-mm nominal leg reach, four total
1/2-in bolts, and a 3.5-in minimum receiving-member thickness for its series.
Its shown 7-gauge steel is screened as an *illustrative* 4.55-mm plate, not a
measured delivered part. A nominal 14.2875-mm wood clearance bore and the
horizontal flange's presumed 50.8-mm hole offset are diagnostic assumptions,
not factory hole or bit instructions. The catalog drawing does not explicitly
dimension that horizontal offset.

The kicker backs are at Y = −36 mm. Merely moving the common post back by the
assumed plate thickness clears its front vertical leg but still puts the
82.55-mm horizontal seat inside both panels. This orientation needs a nominal
minimum 82.55-mm setback; the trial uses 83.55 mm, leaving only 1 mm CAD
panel/seat gap. The hypothetical solid nominal-6×8 post occupies
X = −92.075..92.075, Y = −259.25..−119.55, Z = 0..238.9 mm. The
hypothetical solid receiving header occupies Z = 238.9..327.8 mm and extends
rearward to Y = −341.8 mm so both opposed seats nominally fit.

A separate timber spline covers the seam and both existing center screw axes.
Its lower part is 83.55 mm deep, Y = −119.55..−36, Z = 0..156.35 mm; an
upper notched part is 79.0 mm deep, Y = −115..−36,
Z = 156.35..234.35 mm. The frozen 50.8-mm occupied screw envelopes extend
32.5438 mm into that backing from the panel back, with positive CAD-solid
intersection at all four fixed center kicker axes. This is **not** a Hillman
embedment qualification. The header directly backs the upper edge above
Z = 238.9 mm, but the bracket seat leaves a 4.55-mm unsupported transition
from Z = 234.35 to 238.9 mm. Its support adequacy is not established.

At this idealized pose, the four nominal plate rectangles, post, header, and
notched backing do not volumetrically intersect the protected panels or any
of the 66 frozen screw occupied cylinders. Two modeled post bores and four
header bores lie within their new solids. However, the enlarged header
intersects the current side timbers by 629,301 mm³ each and the two unchanged
principal toes by 283,200 mm³ each. Those hidden members would need a new
simultaneous redesign; simply retaining them fails installed fit. The upper
principal/header connection has not been modeled, so this is not a complete
post–header–principal assembly.

The backing touches the structural post below the front vertical flange but
has no specified or rated block-to-post connection. Contact is not force
transfer. At the front post bolts, the backing begins exactly at the ideal
plate outer face: outward head/washer clearance is zero. A separate relief or
access pocket would be required and would change the backing geometry and
connection. A possible *sequence* is to fit/inspect the angle and bolts,
then fit removable backing and kicker panels; disassembly might require
removing those panels and backing. This has not been proven for actual bolt
heads, nuts, washers, tools, or maintenance. Delivered timber sizes, bracket
tolerances, plate bend, joint capacities, and neighboring frame loads are
also unverified.

**Disposition:** reject this installed trial as incomplete. It shows a
nominal setback/backing envelope, not a feasible joint range or construction
detail. A future trial would have to solve the side/principal clashes,
continuous edge support, front-bolt access, and rated backing-to-post force
path together before any structural calculation could qualify it. Do not
cut, drill, or build from these coordinates.
