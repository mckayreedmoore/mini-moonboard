# PB-02 principal corner block: Y-separated two-bolt groups

**Bounded result: no complete fit in four named rectangular-stock trials.**
This tests a bolted solid-wood corner block and continues the prior
`simple-center-header-principal-two-bolt-probe.md`
without widening the block into the left center principal. It uses the
passing PB-02 tolerance pose, retains both inner kicker supports, and leaves
the panel/kicker outlines and all 66 fixed screw axes unchanged. Each trial
changes both header bolt centers and both block-to-right-principal bolt
centers. Global coordinates are millimeters. Block grain runs along Y;
all four blocks are ordinary solid rectangular rips and crosscuts.

| Trial | Block X, Y, Z bounds | Header bolt Y | Principal bolt Y | Result |
| --- | --- | --- | --- | --- |
| Compact Y | −20…50.95, −200…−45, 277…348 | −145, −80 | −155, −95 | Bottom header hardware hits backer; first principal right hardware hits side cleat |
| Rear reach | −20…50.95, −235…−45, 277…348 | −150, −90 | −170, −100 | Same header conflict; first principal right hardware hits rear and side cleats |
| Forward reach | −20…50.95, −205…5, 277…348 | −155, −95 | −130, −50 | Block hits both lower members; header/backer and principal/side hardware conflicts |
| Rightward stock | −15…50.95, −205…0, 277…348 | −150, −95 | −125, −55 | Block hits both lower members; header/backer and principal/side hardware conflicts |

The Y pairs meet the illustrative 4D = 25.4 mm pitch comparator for a
6.35 mm bolt, but none provides a complete occupied-volume fit. The
first two keep the block's front face at Y −45; the latter two extend it
forward. In every trial the block and principal bores avoid the left center
principal, and all ten bores have their intended wood reception. That alone
does not make an accessible bolt group.

The compact and rear blocks have no measured solid-wood overlap; none of
the four trials has a bore/bore intersection. The forward block occupies
15,523.74 mm³ of the left lower member and 43,115.73 mm³ of the right;
the rightward block occupies 10,274.08 and 35,880.40 mm³ respectively.
Those are modeled volumes, not cut allowances.

The fixed backer creates a conditional header-axis incompatibility for
this X range and a Y-only bolt pair. The header rear edge is Y −175.7;
the 4D centerline marker puts a center at or forward of Y −150.3.
The backer begins at Y −124.9 beneath the header. A 10 mm-radius bottom
washer/hardware envelope must stay at or rearward of Y −134.9 to clear it.
The resulting usable rear Y interval is **−150.3…−134.9 mm, only 15.4 mm**,
less than the 25.4 mm pair comparator. A center ahead of the backer is
outside the header's front edge at Y −36. These are conditional geometric
limits for this unchanged backer, header, and X placement, not an NDS
connection verdict or a proof against every conceivable new layout.

For the first two blocks, the cross-bolt right end has a second conditional
restriction. The upright side cleat ends at Y −118.9; a 10 mm-radius right
washer needs its center at or ahead of Y −108.9 to avoid that neighboring
wood. A 7D = 44.45 mm block-front grain-end marker with front Y −45 puts
the center at or behind Y −89.45. This **19.45 mm front corridor** is again
shorter than a 4D pair pitch. A rear approach past the side cleat cannot
receive the right principal, whose rear starts at Y −182.7. Moving the
block front forward widens this corridor but the screened forward blocks
occupy neighboring lower members. The inclined principal's grain/end
classification remains unresolved; box-coordinate markers do not replace
a directional check.

The script builds each full proposed assembly and checks the six unchanged
plus four changed bores, all twenty exposed ends, intended wood, every
other wood member, all 66 fixed screw envelopes, bore/bore intersections,
washer bearing and interference, exposed hardware, sockets, and an
illustrative full-length insertion path plus 25 mm from both ends. It also
rechecks the existing center kicker and header screw receivers and both
inner kicker supports. Insertion from the block's left face is obstructed
by the unchanged left principal even when the occupied bore itself clears
it; an unobstructed route would have to be demonstrated from another end.
For the first principal bolt in all four trials, both modeled insertion
ends are blocked by neighboring wood, so it cannot be installed through
either screened straight path. Other inherited paths are likewise
reported individually rather than silently presumed clear.
The 7.30 mm bore, 10 mm washer/hardware radius, and 7.8486 mm by
24.511 mm socket body are modeled envelopes, not selected drill bits or
proof of full wrench swing.

No native solve, load or strength assessment, purchased bolt stack,
tolerance qualification, drilling coordinates, or fabrication release is
claimed. Reproduce with `.venv/bin/python
scripts/simple_center_principal_alternate_group_probe.py`; run the focused
test with `.venv/bin/python -m pytest -q
tests/test_simple_center_principal_alternate_group_probe.py`.
