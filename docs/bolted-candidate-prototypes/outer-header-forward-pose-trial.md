# Outer-header forward compact-block trial

**Decision: REVISE.** This detached nominal CAD trial does not supply a clear
outer-header replacement. It changes only the two mirrored outer-header blocks
and their four bolt paths per side in the trial; the shared assembly and viewer
are untouched.

The compact solid block is 55.0 mm inward X by 80.0 mm local Y/N by 135.4 mm
vertical Z. Its Y bounds are -120.0 to -40.0 mm, inside the adjacent header's
-175.7 to -36.0 mm 2x6 rear envelope. Its Z bounds are 103.5 to 238.9 mm.
The post bolt axes are Y=-80.0 mm at Z=130.0 and 170.0 mm. The two header
bolt axes are 30.0 mm inward of the post at Y=-93.0 and -67.0 mm. These are
trial coordinates, not drilling dimensions.

The [detached script](../../scripts/outer_header_forward_pose_trial.py) reports:

- Source inventory: 66 fixed panel/kicker screw axes, 12 fixed frame-bolt axes,
  and center posts at X=-180.0/+180.0 mm.
- Both sides: four complete nominal post/header core bores, positive post and
  header contact, no outer-base header stack or 40 mm tool intersection, and no
  intersections with the other composed blocks/stacks/bores screened by the
  owner-corner assembly.
- Left: no finite protected-solid hit from this trial's block, bores, generic
  stacks, or tools.
- Right: the block intersects the provisional `hold_tnut_kicker_10` hold-hole
  and 50.8 mm rear-projection cylinder by **66.429933 mm³**. This is the
  remaining modeled blocker. The projection is provisional, so it must not be
  dismissed as a delivered-hardware clearance or treated as a build pass.

The earlier full-width forward re-pose (139.7 X by 84 Y, Y=-120 to -36 mm)
cleared the outer-base stack but hit a kicker T-nut and hold projection and a
retained frame-bolt envelope on each side. The compact trial removed those
full-width hits except for the right hold projection. No further pose search
is claimed.

This is uncut-wood, generic-stack occupancy only. Same-family bolt spacing,
seating, purchased lengths, tolerances, tool sequence, finished wood,
strength, load path, and drilling are not released. The historical upper
post-bolt loaded-end concern is not resolved by these nominal intersections.
