# PB-02 right-center X-edge reserve: one nominal geometry pose

Status: **positive nominal post-bolt X-edge reserve in the post and rear
cleat; diagnostic only**. This follows the
[solid-post probe](simple-center-wide-post-probe.md). It is not structural
acceptance, a bolt selection, or drilling authority. The two old right-center
clip stations and their header/base/upright duties remain unresolved.

## Exact pose

The already shifted solid 4×4 right post stays at X=88.75…177.65,
Y=−175.7…−86.8, Z=0…238.9 mm. Its two illustrative post-bolt axes move
from X=114.45 to **140.00 mm**, at Z=110 and 190 mm. A **single solid
nominal 2×4 rear cleat**, wide face along X, occupies X=89.05…177.95,
Y=−213.8…−175.7, Z=0…460 mm. It is 88.9 × 38.1 mm in section, with no
lamination, half-lap, pocket, or custom metal. The separate cleat-link bolt
stays at X=114.45, Z=370 mm. Its side cleat, the 4×6 kicker backer, left
support, both kicker outlines, and all panel/kicker screw axes stay fixed.

| Member at both post bolts | Left/right X center distances, mm | Minimum beyond 4D=25.4 mm |
| --- | ---: | ---: |
| 4×4 post | 51.25 / 37.65 | **+12.25** |
| Rear cleat | 50.95 / 37.95 | +12.55 |

The retained cleat-link bolt has rear-cleat X distances 25.4/63.5 mm: its
left edge is still exactly 4D, with **zero nominal reserve**. Its side-cleat
edge and all load-direction, bolt-group, splitting, net-section, and
inclined-upright checks remain open. Post-bolt Z center distances are
110/128.9 and 190/48.9 mm; the upper top has only 4.45 mm beyond a
conditional 7D=44.45 mm end screen if that classification applies.

The fixed backer ends at X=88.75 and the post starts there, with zero X gap
and **9,102.09 mm² nominal X-face contact** over Y=−124.9…−86.8 and
Z=0…238.9 mm. The post/rear-cleat Y-face contact is 21,166.54 mm².
These are face contacts, not proven fastened load paths. The backer still
supports both inner kicker edges, and all four center kicker screw receiving
portions remain in their intended left post/backer.

The CAD screen counted all 48 panel and 18 kicker screw axes at modeled
diameter and purchased length. It found no positive-volume fixed-screw hit
with new wood or bores, no unintended wood overlap, and no unintended bore
receiver or bore-pair intersection. All four illustrative bores are fully
received by their intended wood pairs. The actual mixed layout was checked:
post bores at X=140, Z=110/190 run Y=−213.8…−86.8; the link bore at
X=114.45, Z=370 runs Y=−213.8…−118.9; the upright bore remains at
Y=−147.3, Z=350. All use a 3.65 mm radius. Their exact CAD pair
intersections are empty. The separate trials in the script supply post-bolt
fields from X=140 and link-bolt fields from X=114.45; invariant wood and
upright fields are shared, and the mixed bore-pair field is rebuilt from
those actual axes.

The post front is 50.8 mm behind the installed kicker back. Illustrative
20 mm radius × 20 mm outward tool cylinders at all eight bolt ends clear
modeled wood, and all 20 mm diameter washer disks have full nominal bearing
on uncut faces. No pocket is modeled. Actual washer, nut, bolt grip and
thread/shank arrangement, tool travel, assembly sequence, and service access
still require checks. The post foot has an uncut rectangular modeled face;
floor bearing and pad details are not established.

Two nearby exact placements were rejected while bounding this probe. A rear
cleat starting at X=76.35 overlapped the inclined right upright by
4,731.88 mm³. Moving the post start to X=101.45 created a 12.70 mm gap
from the fixed backer, breaking their contact. The reported pose uses
neither change.

All dimensions above are **nominal CAD dimensions**, not delivered stock
or drilling tolerances. The supplied 4×4 retail lead lists a possible
minimum width near 87.3 mm despite its 88.9 mm nominal actual width;
measure the delivered post and cleat before relying on any margin. The
illustrative 1/4 in bolt and 7.30 mm bore are not selected hardware. Old
`clip_split_base_center_right` and `clip_split_header_center_right` and
their screws still collide with new wood; their functions need separate
replacement and verification. No strength, floor, or build approval follows.

Reproduce with `.venv/bin/python scripts/simple_center_edge_reserve_probe.py`
and `.venv/bin/python -m pytest -q
tests/test_simple_center_edge_reserve_probe.py`.
