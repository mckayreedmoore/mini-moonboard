# Full-center thick-header / outer-post nominal trial — rejected

This is one kerf-right CAD occupancy trial, not a connector selection or drilling plan.
Regenerate its JSON with `uv run python -m scripts.hardware_first_center_thick_outer
--output docs/bolted-candidate-prototypes/hardware_first_center_thick_outer.json`.
No other pose was screened here.

The lower connection copies the paired HL35 layout of
[`hardware_first_center_outer_post.py`](../../scripts/hardware_first_center_outer_post.py):
vertical legs on the outside X faces of one 184.15-mm-wide, front-aligned post,
and two inward seats under the header. The lower vertical legs share two
full-width post through-bolt axes. Their joint action is unresolved. The
header is one shaped CAD solid: the original full-span header plus a central
raised region, X = −230..230 mm, Y = −258.25..−36 mm, Z = 238.9..327.8 mm.
The lower and upper bracketed header bores each have 88.9 mm of nominal wood,
meeting the [HL35 catalog](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog)
minimum in this ideal model. The two principal toes are cut above Z = 327.8
mm, and each gets one outward-X short-bend HL33 at Y = −100..−36.5 mm.
This is the already modeled upper pose, with its assumed horizontal hole inset.

The original six inner rail ends intersect the widened principals; the two
bottom rails also intersect the upper plates and bores. This trial makes one
planar inner-end cut at X = ±120 mm on each of those six rails. All ten changed
wood shapes are single CAD solids. After those cuts, the nominal plates,
bores, panels, other wood and twelve existing frame-bolt occupied axes have
no reported intersection. The six header bores and two shared post bores stay
inside their receiver wood. The closest upper/lower header bore X axes are
123.975 mm apart, and no independent bore cylinders intersect. The panel
solids and all 66 protected screw axes retain their coordinates and modeled
receivers. Four center kicker screw cylinders still enter the post by
438.127 mm³ each.

**Reject this installed geometry.** The post top is Z = 234.35 mm and the
header bottom is Z = 238.9 mm. The inward HL35 seats occupy the 4.55-mm band
only outside a 19.05-mm X gap at center. The kerf-right kicker seam is at
X = −1.5875 mm, inside that gap: it lacks continuous rear support across the
4.55-mm height. This is a decisive nominal support gap even though the fixed
screw receiver cylinders still intersect the post.
A one-piece central post tongue within the 19.05-mm seat gap is a separate
possible layout; its geometry, hardware clearance and support are **not**
modeled or proven by this trial. It is not included in the result.

A separate conditional envelope check extends each protected screw cylinder
to the purchased 63.5-mm **overall** screw length. The two upper center kicker
screws then intersect the second shared post bore by 4.629 mm³ each. Delivered
shaft occupancy is unknown, so this does not establish a real screw clash.

Minimum sampled blank envelopes, in mm, are 2435.225 × 222.25 × 88.9 for the
header, 184.15 × 139.7 × 234.35 for the post, 88.9 × 139.7 × 2466.3113 for
each principal, and 1010.3/1007.125 × 38.1 × 139.7 for left/right rails.
The [Lowe's 4×10×12-ft #2 Better Douglas-fir green lead](https://www.lowes.com/pd/4-in-x-10-in-x-12-ft-Douglas-Fir-Lumber-Common-3-562-in-x-9-5-in-x-12-ft-Actual/1000028861)
lists an actual 3.562 × 9.5 in (90.4748 × 241.3 mm) cross section and 12-ft
length; it contains the nominal header envelope dimensionally. The 6×8 post,
6×6×10-ft principals, and 2×6 rail stock examples also contain their nominal
envelopes dimensionally. Local inventory, dry size, defects, cuts and
machining allowances are unknown; the green retail listing is only a
dimensional comparator.

One outward-X HL33 per principal has **no established reversible-F1 coverage**.
The six shortened rails also have **no rail-to-center attachment** or verified
load path. Shared-post-bolt action, delivered bracket dimensions, fastener
stacks, edge/end distances, and strength remain unresolved. The screen uses
ideal 4.55-mm plate rectangles and 14.2875-mm occupied bores; the HL35 header
hole inset and HL33 horizontal hole inset are assumptions. No cutting,
drilling, capacity, or fabrication release follows from this trial.
