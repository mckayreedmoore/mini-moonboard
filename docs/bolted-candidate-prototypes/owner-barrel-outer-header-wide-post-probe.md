# Outer-header barrel: wider whole-post trial

The [detached probe][probe] screens ordinary dressed whole-timber replacements
for the two hidden outer posts. It keeps the kerf-right panel outlines, all 66
panel/kicker screw axes, all 12 original frame-bolt axes, the side rims, and
the header unchanged. It does not edit the viewer or cut existing stock. The
bounded set is a rotated 2×6 (139.7 mm X × 38.1 mm Y), 4×6 (88.9 × 139.7),
and 6×6 (139.7 × 139.7), each at 0 and 10 mm inward X shifts on both sides.
Each top-entry pose retains the original two rows at Y = −135 and −75 mm.
The dressed section assumptions are supported by retailer examples: a
[1½ × 5½ in. 2×6 at Lowe's][lowes-2x6], a
[3½ × 5½ in. 4×6 at Home Depot][hd-4x6], and a
[5½ × 5½ in. 6×6 at Home Depot][hd-6x6]. These examples do not establish
local stock, grade equivalence, delivered dimensions, or a selected purchase.

**No tested pose clears all fixed-axis and protected-geometry gates.** The
three sections fail for different reasons:

| Whole post | Decisive nominal geometry |
| --- | --- |
| Rotated 2×6 | The two rows are 60 mm apart. Full 20 mm-diameter access envelopes need at least 80 mm Y depth; the rotated post has 38.1 mm. Centered on the old post, both row centers are outside it by 10.1/11.8 mm, and both named kicker-screw receiver centerlines have zero Y overlap. |
| 4×6 | With the fixed kicker-screw X centerline retained, the post needs at least 89.85 mm X width to fit a 20 mm tool entirely within the post projection and outside the 88.9 mm-wide side rim. A dressed 4×6 supplies 88.9 mm, short by 0.95 mm even at the theoretical limiting shift; both tested shifts have zero tool-center corridor. |
| 6×6 | The 0 mm shift gives a 30.8 mm-wide tool-center corridor, both rows have 40.7/39.0 mm Y edge margins, both fixed kicker screws retain 32.54375 mm receiver-axis overlap, and both original rail-front bolts retain 40.132 mm X-axis overlap. Both modeled bolt shafts and 20 × 40 mm top-access paths clear the side rim. Nevertheless, the full post intersects a protected kicker T-nut by 804.105091 mm³ and its hold/projection envelope by 4926.938504 mm³ on each side. The outer-header rows also fail the protected-inventory screen. The 10 mm inward shift retains those same protected hits. |

For the left side, the rim's inner X edge is −1130.3 mm and the fixed
kicker-screw centerline is X = −1200.15 mm. The 20 mm tool center must be at
least X = −1120.3 mm to clear the rim, while a tool wholly within the post
needs another 10 mm of post beyond it. Thus the post must span at least
−1200.15 to −1110.3 mm: **89.85 mm**. The right side is mirrored. This is a
necessary geometric inequality, not an edge-distance or strength check.

The rotated 2×6 failure is independent of X shift as long as both original
Y rows and 20 mm full access envelopes are required. In its centered pose,
one original rail-front bolt also misses the replacement post in Y.
A Y relocation could trade among row support, original bolt reception, and
kicker-screw embedment, but cannot create the missing 41.9 mm for the two
unchanged access rows. The finite 6×6 protected hits are specific to the
two tested X positions and original Y placement. A further Y/topology change
would need to prove the fixed screw receiver length, both row supports,
header/rim contact, protected holds/electrical, and neighboring barrel paths
again; this probe does not declare every possible whole-timber design
impossible.

The 20 mm access tool, 19.05 mm washer, nominal bolt/barrel dimensions, and
wood envelopes are diagnostic assumptions—not verified purchased-part fits.
No load resistance, complete thread engagement, tolerance stack, assembly
sequence, or final member cost is established. **No drilling, fabrication, or
structural release.**

[probe]: ../../scripts/owner_barrel_outer_header_wide_post_probe.py
[lowes-2x6]: https://www.lowes.com/pd/1000029095
[hd-4x6]: https://www.homedepot.com/p/202094372
[hd-6x6]: https://www.homedepot.com/p/202534027
