# PB-02: bolted wood path from shifted right post to right upright

Status: **nominal CAD fit only; structural and hardware access unresolved**. This
is one concrete connection trial in the V4 bolted candidate, not a drilling or
fabrication release. Coordinates are world millimeters. The left post, header,
upright, climbing panels, and all 66 panel/kicker screw axes stay fixed. Only
the right center box post moves +37.8 mm in X, to X=88.75…126.85. The 0.30 mm
projected overlap with the old upright is given **no** structural credit.

## Member path and assembly

Keep the separate 139.7 × 88.9 × 238.9 solid 4×6 kicker backer at
X=−50.95…88.75, Y=−124.9…−36, Z=0…238.9, as in the
[offset probe](simple-center-support-offset.md). Add two separate, plain
rectangular solid-wood cleats, grain vertical. The side cleat's 50.8 mm depth
is a plain rip from solid 2×4 stock, subject to actual stock verification:

| Member | X | Y | Z | Bearing face |
| --- | --- | --- | --- | --- |
| Rear cleat, 38.1 × 38.1 × 460 | 89.05…127.15 | −213.8…−175.7 | 0…460 | Front face on shifted post rear face through Z=238.9. |
| Upright-side cleat, 38.1 × 50.8 × 183 | 89.05…127.15 | −175.7…−124.9 | 277…460 | Left face on original right upright; rear face on rear cleat. |

The load path being proposed is **right post → two Y-axis through bolts → rear
cleat → one Y-axis through bolt → upright-side cleat → one X-axis through bolt
→ original right upright**. The cleats can travel as individual members.
Install the post bolts and their recessed front seats before fitting the right
kicker; join the cleats and upright while their outer bolt ends are exposed.
The existing header is nearby, but this trial does not count mere header face
contact as an additional connector. The backer retains the kicker screws and
is not credited as the post-to-upright transfer member.

| Group | Nominal bore axis | Timber along axis | Diagnostic seat/access |
| --- | --- | ---: | --- |
| Post low/high | X=108, Y=−213.8…−46, Z=110/190, +Y | 167.8 | 25 mm diameter × 10 mm deep front pocket, ending flush at Y=−36; rear end exposed. |
| Upright | X=50.95…127.15, Y=−148.5, Z=344.5, +X | 76.2 | 20 mm diameter illustrative washer footprint on upright left face is entirely on wood in nominal CAD. |
| Cleat link | X=110.5, Y=−213.8…−124.9, Z=370, +Y | 88.9 | Both cleat ends exposed. |

All four are illustrated as nominal 3/8 in bolts in 10.5 mm bores. The bore
diameter is within the 10.31875…11.1125 mm NDS hole interval noted in the
[offset probe](simple-center-support-offset.md); it is not a selected drill.
Retail 3/8 in hex-bolt length leads exist in the
[local retail inventory](simple-joint-retail-inputs.md), including 4 and
8 in classes. Delivered bolt grade, shank/thread position, washers, nut
engagement, exact lengths, and compatible recessed head/washer height have
not been established for these stacks. The 20 and 25 mm washer/seat diameters
are diagnostic geometry, not selected products.

## CAD observations

The two added cleats have zero positive-volume collision with the actual
uncut timber solids, including the original upright, header, bottom rail,
shifted post, and kicker backer. Measured nominal face areas are 9030.42 mm²
at post/rear cleat, 4453.57 mm² at upright/side cleat, and 6972.3 mm² at
the cleat pair. The upright contact is measured on its actual inclined solid.
The side cleat ends at Y=−124.9, 11.806 mm behind the nearest bottom rail
Y bound of −113.094. The rear cleat remains outside the header rear face
at Y=−175.7.

All four 10.5 mm bores pass through their intended wood pair, intersect no
unintended timber, and do not intersect one another. Their bores and the two
cleats and front pockets have zero intersection with the full purchased-length modeled
envelopes of all 48 fixed panel and 18 fixed kicker screws. The 4×6 backer
continues to support both inner kicker edges and receive the right-center
kicker screws; the fixed left-center screws still enter the left post. The
[offset probe](simple-center-support-offset.md) gives the full 63.5 mm
kicker embedment and remaining backer timber.

A straight 20 mm radius × 20 mm tool cylinder outside each bolt end misses
all modeled wood **except** the two post front ends after the right kicker is
present: those cylinders intersect `kicker_right` by 22,941.48 and
22,044.25 mm³ at Z=110 and 190. The front 10 mm pockets end at the kicker
back plane, so nominal seated heads need no projection into the panel, but
actual head/washer height and socket engagement have not been checked.
Removing the kicker restores nominal straight access to those seats.

## Open checks before any strength or installation verdict

- Same-case post, cleat, and upright force **and moment** vectors, including
  tension/prying on the bolts and whether the single upright and link bolts
  can carry the required couple. Serial groups cannot be added as parallel
  capacity; wood bearing, bolt yield, group action, cleat bending/shear,
  splitting, and net section are uncalculated.
- NDS loaded-edge/end classification for every member and force direction.
  The link center is only 16.65 mm from the cleats' right X edge; the post
  bolts are 18.85 mm from the post's right X edge. Either misses a 4D
  (=38.1 mm for 3/8 in) loaded-edge criterion **if that criterion applies**.
  The widened side cleat gives the upright bolt 23.6 mm to its front Y edge
  and 27.2 mm to its rear Y edge; that is only nominal clearance, not an
  adopted loaded-edge classification.
  The upright bolt is only 67.5 mm above the upright's Z=277 lower end;
  nominal 7D is 66.675 mm, leaving 0.825 mm before stock and drilling
  tolerance. Its 20 mm washer fits CAD, but a larger delivered washer may
  overhang the inclined upright. No NDS geometry pass is claimed.
- Delivered bolt and washer dimensions, pocket seat bearing and lost section,
  nut/thread engagement, socket swing and withdrawal, assembly tolerances,
  post-kicker maintenance access, and actual stock dimensions/grade. The
  20 mm radius access probe only tests a short straight approach, not a full
  wrench operation.
- The neighboring center/header and six rail-end duties, altered right-post
  load entry, and any required native response/recheck. None is inherited
  from the selected baseline or solved by this local positive path.

Reproduce with `.venv/bin/python scripts/simple_center_post_transfer_probe.py`
and `.venv/bin/python -m pytest -q
tests/test_simple_center_post_transfer_probe.py`. Inputs are the uncut
`compact_floor_flush_frame` solids and kerf-right `connection-axes.csv` and
`stock-profiles.json`; no source artifact is changed.
