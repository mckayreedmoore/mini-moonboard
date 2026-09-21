# PB-02: one solid deep-header rear-cleat bolt probe

Status: **rejected nominal geometry**. This is one bounded trial for the
displaced `clip_split_header_center_right` duty. It does not select a joint or
address the separate `clip_split_base_center_right` duty. No drilling release.

## One pose

Use one full-length, solid rectangular header at X=−1219.2…1219.2,
Y=−175.7…−61.4, Z=188.1…277 mm. Its solid section is 114.3 mm in Y by
88.9 mm in Z, so an ordinary 88.9 × 88.9 mm 4×4 cannot supply it. A larger
solid blank, such as a nominal 4×6 ripped to width if stock is available,
would be required; stock and cut yield are unverified. This is geometry only.
Its Z depth is 50.8 mm greater than the original 38.1 mm header. The
front-face recess is the same 25.4 mm as the earlier [recessed-header trial]
(simple-center-header-post-alternate-probe.md). Shorten only the shifted
right post to Z=0…188.1 mm and move its two rear-cleat bolt levels from
Z=110/190 to Z=80/140 mm. Retain the rear cleat, backer, side cleat, fixed
climbing surface, both inner kicker edges, and all 66 panel/kicker screw
axes. No pocket, half-lap, custom steel, or panel fastener change is modeled.

Try one nominal 6.35 mm Y-axis header bolt at X=140, Z=232.55 mm, from
Y=−213.8 to −61.4 mm. Its illustrative 7.30 mm bore crosses 38.1 mm of
rear cleat and 114.3 mm of header. The intended serial path is header →
bolt → rear cleat → relocated post bolts → shifted post. This is a geometry
screen, not a joint or hardware specification.

## Separate results

The deeper header **passes the conditional reversible 4D Z-edge placement
screen** for this bolt: its center is 44.45 mm from either Z edge, versus
4D=25.4 mm. The bore is fully received in the intended cleat/header wood,
misses the modeled 66 fixed screw envelopes and relocated post/link/upright
bores, and has full modeled 20 mm diameter washer bearing at both ends.
The illustrative front 10 mm radius × 5 mm hardware cylinder and 20 mm
radius × 20 mm straight tool cylinder clear modeled wood behind the
installed kicker. Actual nut and wrench access, tolerances, bolt length,
loads, and NDS joint checks are not established.

The front recess independently **removes direct header bearing at both
inner kicker edges**. The header face is Y=−61.4 mm, while the fixed kicker
back is at Y=−36 mm: a 25.4 mm gap across this header-height strip. All ten
fixed `kicker_header_*` screw axes still reach the header, but each has only
19.84375 mm of its modeled 63.5 mm shaft there (fraction 0.3125), down from
45.24375 mm (fraction 0.7125) in the original header. Keeping the axes
therefore does not preserve their receiver depth or the two edge bearings.
The remaining 56 axes are fixed; this rejected trial makes no claim that
their connection capacities have been requalified.

The full-length downward depth increase also places solid header timber
inside unchanged wood. Nominal positive overlap volumes are 450,644.26 mm³
with the backer and 221,225.364 mm³ each with the left center post and two
outer posts. Shortening only the right post does not clear those volumes.
Resolving them would require changes outside this one-pose probe.

The shortened right post itself has no positive-volume overlap with
unintended wood. Both relocated post bores are fully received in the post
and rear cleat, miss other modeled wood and all 66 fixed screw envelopes,
and do not intersect the trial header/link/upright bores. The four fixed
center-kicker screws still have full modeled receiver after the kicker in
their original left post or right backer. These inherited checks do not
repair the ten header screw receivers or the header's solid overlaps.

**Reject this pose.** Increasing Z depth repairs the conditional bolt-edge
distance, but the front recess still removes the required kicker support
and most of the ten original screw receiver depths. The full-length solid
header also intersects retained frame members. No new receiver member,
cutting detail, fastening change, rating, or drilling coordinate follows.

Reproduce with `.venv/bin/python scripts/simple_center_deep_header_probe.py`
and `.venv/bin/python -m pytest -q
tests/test_simple_center_deep_header_probe.py`.
