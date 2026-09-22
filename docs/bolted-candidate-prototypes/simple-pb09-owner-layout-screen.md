# PB09 detached owner-layout screen — lower-service wire-channel trial

PB09 is a source-distinct, ten-station layout study built from authenticated PB07
duties. It does not replace PB07 or the selected construction packet. It does not
authorize cutting, drilling, assembly, or climbing.

The single trial uses 139.7 mm local-N blocks with their front and rear
faces aligned to the adjacent rearward 2×6 N envelope. The four center blocks
use 114.3 mm local X width; the six outer blocks remain 101.6 mm. All ten
use upright rows N = 60 and 92.250 mm and rail rows X = 46 and 74 mm from
the rail butt. The lower/bottom rail rows stay at N = 80.159 mm; upper outer
and upper center rail rows use N = 45 mm. The upper-center move avoids
coincidence with both upright rows and separates the upper-center and lower-
center rail tools. Four lower-service blocks use 76.2 mm local T; the other
six retain 57.15 mm. Bottom-outer rail axes and tools are unchanged. If the
actual E6–E7 cable intersects the uncut left lower-center block, a 5 mm
radius channel is subtracted along its centerline. That provides a nominal
3 mm radial allowance around the 2 mm cable radius. If there is no actual
intersection, the block stays uncut. Channel/bore/stack hits and remaining
rail and upright contact are explicit result fields. Any applied channel
still needs feeding, strength, and owner approval; this is no machining
instruction.

At D = 6.35 mm, the 7D full-value marker is 44.45 mm and conditional 4D
marker is 25.4 mm. The tightest N-end reserve is 0.55 mm at the upper rail
rows; the rear upright row has 3.0 mm rear reserve. For an outer block, the
first rail X row has 1.55 mm to a loaded near-end 7D marker, the second row
has 2.2 mm to a loaded far-edge 4D marker, and row spacing has 2.6 mm over
4D. These are geometric margins, not signed load-case findings.

The first 114.3-mm outer-width trial failed: its outer upright grip was
203.2 mm, leaving the 8-inch bolt 11.5824 mm short of two threads past the
nut. It also had upper/lower center tool-to-installed-stack collisions.
In the revised trial, the nominal 8-inch upright bolt has 190.5 mm wood grip
outer and 152.4 mm center. With the modeled washers and nut, projection
*past the nut* is 3.6576 mm outer / 41.7576 mm center. The outer two-thread
margin is only 1.1176 mm, while the center bolt has a large nominal overhang.
Delivered shank/thread,
washer/nut tolerances, and insertion sequence remain open stock-fit issues.

The previous revised solids cleared modeled block/bore, fixed axes, installed
stack, and cross-station collision checks. The original generic 40 mm access
cylinders still intersected neighboring stack components. The script retains
those diagnostics and separately screens a 25.4 mm
diameter, 40 mm deep cylindrical access envelope. Clearance of that smaller
envelope is only a conditional concept: no actual tool, socket wall, grip,
approach, or one-tool-at-a-time installation sequence has been verified.
The shared protected-volume helper provides 142 T-nut bodies, 142 provisional
50.8 mm rearward hold-hole/bolt envelopes, 132 light bodies, 131 wire solids,
66 panel/kicker screw shafts, and 12 retained frame-bolt shafts. PB09 screens
its blocks, bores, and nominal installed stacks against all of these finite
solids first. If any core intersection exists, the protected 25.4 mm tool pass
is marked **not run**, not clear. Delivered hold-bolt length, actual wiring
bends, panel-screw heads, and retained frame-bolt stacks remain **unverified**;
none receives assumed zero length or clearance.
Native solve, joint mechanics, hardware selection, and fabrication remain out
of scope.

The previous full protected-volume trial returned **REVISE_LAYOUT**. It
found a lower-center block intersecting a modeled light (`light_E7`) and a
conditional outer-upright access envelope intersecting modeled wire
`wire_126_K6_K7`; the latter was deferred behind the core blocker in the
bounded script. That intermediate revision shortened center-block X width
and moved the first upright and upper rail rows. Bottom-outer rail X/N centers,
angles, and the 139.7 mm local-N block depth remain unchanged, so it does not
change the known outer-base-pair overlap with bottom-outer rail tools. The
original 40 mm tool conflicts remain. The one bounded revision CAD test ran
and **failed**: the named `light_E7` intersection is gone, but the
`wire_126_K6_K7` outer-right upright far-access intersection remains at
264.304785 mm³ (up from about 154 mm³ in the previous trial). A new
lower-center block collision with modeled `wire_054_E6_E7` also appeared.
That was **REVISE_LAYOUT**, not a viewer-ready configuration. The separately
reported outer-base overlap of 772.9/682.0 mm³ per side was still open then.

The shared `_build()` supplies the same block solid to PB09 screen,
outer-base comparison, and owner-corner assembly. It now computes the exact
uncut block/`wire_054_E6_E7` overlap with `protected._volume` before deciding
whether a channel is needed. A zero pre-cut overlap leaves the block solid
and records zero removed wood; a positive overlap applies the channel and
records pre/post wire intersections and removed wood. The assembly gate checks
that evidence instead of demanding a cut in every pose.

The first refactor test
correctly failed: the cable sweep was started in local coordinates and removed
**0 mm³**. After correcting the sweep plane to world coordinates, the focused
diagnostic passed **2/2 in 99.31 s**. The actual channel removes
**3,582.400322 mm³**; it intersects **no** modeled bore or generic stack.
The relieved block retains rail/upright contact of **14,913.358546 /
10,645.14 mm²**. Its intersection with the intended `wire_054_E6_E7` is
**0 mm³**. Named earlier `light_E7` and `wire_126_K6_K7` targeted hits are
also zero in this pose. This does not make the layout clear: the actual
decision is **REVISE_LAYOUT**.

Remaining protected intersections from the bounded diagnostic, in mm³:

| Candidate | Protected solid(s): intersection |
| --- | --- |
| Lower-center left block | `wire_055_E7_E8`: 81.893695 |
| Lower-center right block | `light_G7`: 1520.122437 |
| Lower-center right block | `wire_078_G6_G7`: 732.748491 |
| Lower-center right block | `wire_079_G7_G8`: 646.244504 |
| Upper-outer left block | `hold_tnut_main_A7`: 68.779167 |
| Bottom-outer left block | `hold_tnut_main_A1`: 68.779167 |
| Upper-center left block | `wire_055_E7_E8`: 818.578063 |
| Upper-center left upright-1 bore / shaft | `wire_055_E7_E8`: 92.710270 / 77.011287 |
| Upper-center right block | `hold_tnut_main_G7`: 804.105091 |
| Upper-center right block | provisional hold projection: 4926.938504 |
| Upper-center right block | `wire_079_G7_G8`: 285.545926 |
| Upper-center right upright-1 bore / shaft | `wire_079_G7_G8`: 45.871482 / 77.010506 |
| Upper-center right upright-1 washer / nut | `wire_079_G7_G8`: 96.758326 / 143.163581 |

The protected 25.4 mm access-tool pass was **not run due to core hits**;
an empty protected-tool result is therefore not clearance. Local 25.4 mm far
rail access cylinders additionally hit the opposite upper-service rail timber:
lower-center left rail rows 1/2: **6090.595271 / 5773.235654 mm³**;
lower-center right: **6090.595271 / 6207.166619 mm³**;
lower-outer left: **6090.595271 / 6207.166619 mm³**;
lower-outer right: **6207.166619 / 6207.166619 mm³**.
Each upper-center and upper-outer near rail tool also intersects its matching
lower block by **12880.529880 mm³ per row**, two rows per station, eight
cross-station hits total. These are not waived by a one-tool-at-a-time sequence.

The generic 5-in rail trial has only **+1.1176 mm nominal two-thread margin**
for a 76.2-mm-T block with the model's listed washer/nut dimensions; no
retail rail bolt has been selected, and actual tolerances may consume it.
The service channel still needs owner approval, feeding proof, and structural
assessment. The configuration may be displayed only as an explicitly
unresolved development concept; it is not a drilling or build release.

The **2/2 PASS** and exact 3,582.400322 mm³ removal above belong to the
completed pre-adaptive shared-cut diagnostic. The follow-up adaptive-evidence
test was stopped on owner request after its fast test passed (1/2 in 79.07 s);
the second CAD test and exact pre-cut wire overlap were **not completed**.
Thus the current adaptive branch is statically checked but its numerical
branch outcome is not claimed. Overall layout disposition remains
**REVISE_LAYOUT** due the recorded protected and access conflicts, regardless
of whether the E6–E7 channel proves necessary in this T pose.

Static X bounds explain why another center-width-only trim is not enough at
the retained rail X rows. The left center block begins at
X = −89.05 − width; the E6–E7 vertical wire route reaches approximately
X = −189.2 mm with a 2 mm cable radius. Clearing it solely on the block's
left side requires width < 98.15 mm. The retained second rail row at X = 74
needs width > 99.4 mm for a positive conditional far-edge 4D margin. Those
intervals do not overlap. A new row/pose/tool concept would be necessary;
this note does not authorize one.

The owner-approved ±180 mm center-post placement belongs to subsequent
candidate integration. This PB07-derived screen retains its original frame
member positions and does not certify the post shift, separate fixed-kicker-
screw backing, or their interactions.
