# HL53 solid-center X-face trial — rejected

This is a nominal installed-geometry diagnostic, not a connector selection,
purchase instruction, wood/steel resistance check, or drilling release.
Regenerate the companion JSON with `uv run python -m
scripts.hardware_first_center_hl53 --output
docs/bolted-candidate-prototypes/hardware_first_center_hl53.json`.

The [Simpson C-C-2026 HL page](https://dhcsupplies.s3.us-east-2.amazonaws.com/Documents/simpson-strong-tie/hl-angles.pdf)
shows HL53 as a 7-gauge double-row angle: 2.5-in bend length, 5.75-in leg
reach, four total 1/2-in bolts, D1 = 1.25 in along the bend, D3 = 2 in
from the bend, and D4 = 2.5 in between the two holes *across each flange*.
This transverse pattern is distinct from HL35's two holes along its longer
bend. The catalog's 3.5-in wood-thickness minimum for the “3” and “5”
series and requirement to center on a sufficiently wide member remain
conditional on the actual installed orientation and delivered stock.

The trial grows the header upward from Z = 238.9–277 mm to
Z = 238.9–327.8 mm (3.5-in solid depth), trims only the center-principal
toes to meet it, and models 5.5-in-wide solid center principals and posts
in X. Original post tops and all 66 kerf-right panel/kicker screw axes
are unchanged. Paired angles are placed on both X faces of each center
principal and post. The upper 63.5-mm-long angle is at the front of the
139.7-mm member Y face (Y = −67.75 mm); the lower is at the rear
(Y = −143.95 mm), their maximum independent Y separation of 76.2 mm.
The nominal 9/16-in wood clearance bores are through-cylinders, not bit
instructions. Both holes on each vertical flange lie at Z = 378.6 and
442.1 mm (upper) or 188.1 and 124.6 mm (lower).

In this one pose all sixteen modeled bore records intersect their timber
without missing wood, and none intersects the modeled 66 protected screw
shafts. That is only a nominal cylinder screen: it does not establish NDS
end/edge distances at the principal's oblique toe, adequate ligament,
washer bearing, delivered hole tolerance, connected-joint strength, or
bolt-stack access. Opposing face angles use coincident vertical through-
bores; their force sharing and complete bolt grip are not established.

The decisive failure is physical installation and full kicker-edge support.
The kerf-right kicker panels meet at X = −1.5875 mm. If the left and right
center posts separately support their respective *entire* inner edges,
the left post's inner X face must reach at least that seam and the right
post's inner face must reach no farther right than that seam. Their maximum
nonoverlapping gap is **0 mm**. The centered 5.5-in post trial leaves
0.3 mm between posts and already overhangs the right kicker inner edge by
1.7375 mm. Two bare 7-gauge inner HL53 plates alone would need about
9.1 mm of gap; bolt ends, washers, nuts, and tool sweep need more.
Shifting or widening the posts to fully support both inner edges only
reduces the available gap. A 3.5-in-wide 4x receiver would create more
gap but lose inner-edge support by roughly 25–29 mm. Thus there is no
width/shift range for *these two separate posts* that supplies both full
inner-edge support and the required opposing inner X-face angles.

Reject this paired X-face installed concept. Separate kicker blocking with
the posts moved outward, Y-face angles, or a common central receiver would
be different concepts requiring their own support, bolt, access, and
joint-family checks. No structural acceptance, fabrication, or drilling
follows from the favorable nominal bore screen.
