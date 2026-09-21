# PB-02 combined center cleats: nominal assembly geometry

**Combined nominal geometry is rejected.** This probe places the committed
[header/principal reserve cleat](simple-center-principal-cleat-reserve-probe.md)
and [header/post side cleat](simple-center-header-post-side-cleat-probe.md)
**simultaneously** in the right-only shifted-post/link-edge frame. It is one
nominal center/base assembly screen, not two independent acceptance claims.
The original header, shifted right post, backer, rear cleat, upright-side
cleat, link-edge bores, panel and kicker shapes, and fixed screw policy are
inherited. Coordinates below are global millimeters.

| New solid | Bounds X; Y; Z | Grain | Serial contact and bolts |
| --- | --- | --- | --- |
| Header/principal cleat | −20…50.95; −190…−45; 277…380 | Y | Header top → cleat bottom via Z bolt at X=15.475, Y=−145.3; cleat right → principal left via X bolt at Y=−95, Z=330 |
| Header/post cleat | 177.65…266.55; −175.7…−86.8; 110…238.9 | Z | Shifted post right → cleat left via X bolt at Y=−150, Z=160; cleat top → header bottom via Z bolt at X=222.1, Y=−130 |

Each of the four new bolts has two modeled exposed ends. At all eight ends,
the probe checks a 10-mm-radius by 0.01-mm inward washer bearing disk, a
matching outward face occupancy disk, a
10-mm-radius by 5-mm outward hardware cylinder, and a 20-mm-radius by
20-mm outward straight tool cylinder. It also rechecks the eight inherited
post, upright, and link bolt ends against both new cleats, including their
washer bearing and face occupancy disks, bores, hardware, and tool envelopes.
The outward disk checks surface occupancy only, not purchased washer
thickness. These cylinders are
nominal occupancy screens; no purchased stack or wrench swing is established.

The script checks the two new solids against every neighboring modeled wood
member and against each other. All four complete new bore envelopes are
checked against their named two-member receivers, unintended wood, each
other, four inherited bores, and all 66 fixed screw envelopes. It checks the
new solids and all new hardware/tool envelopes against those same fixed
screws. The ten `kicker_header_*` modeled shafts retain a 0.7125 receiver
fraction in the unchanged header; four center-kicker screws retain 1.0 in
their inherited receivers. Both inner kicker edges remain supported. The
inherited frame screen reports 48 panel plus 18 kicker axes and no inherited
solid, bore, screw, or straight-tool collisions.

The simultaneous pose fails at the **inherited upright-left end**. Its
washer face occupancy, 10-mm-radius by 5-mm hardware envelope, and
20-mm-radius by 20-mm straight tool envelope occupy the new
header/principal cleat at the principal's left X face. The hardware/cleat
intersection is 1,570.79633 mm³; the tool/cleat intersection is
25,132.74123 mm³. The inward washer bearing disk still has full principal
bearing, which does not make the exposed seat accessible. All four new
bores have full intended receiver fractions, no unintended wood or
inherited/new bore intersection; new cleats, hardware and tools miss the 66
fixed screw envelopes. This local collision is enough to reject the exact
combined pose.

The intended serial wood/bolt routes are:

1. `shifted_right_post` → X through-bolt → `header_post_side_cleat` → Z
   through-bolt → `base_header`, with post/cleat side-face and cleat/header
   end-face contact.
2. `base_principal_center_right` → X through-bolt → `header_side_cleat` → Z
   through-bolt → `base_header`, with principal/cleat side-face and
   cleat/header face contact.

The inherited shifted-post pose displaces the old
`clip_split_base_center_right` and `clip_split_header_center_right` ML24Z
stations. Those old clips and their twelve SDS structural screw axes are not
new load paths; the separate 66 fixed panel/kicker axes are retained.

This is a nominal geometry result only. In particular, the earlier
header/principal cleat's underside tool has just 0.4 mm nominal backer gap,
and the header rear edge has exactly 5 mm beyond a conditional 4D marker.
The header/post cleat's post-bolt rear Y edge has only 0.3 mm beyond that
marker; its Z bolt enters cleat end grain. These small margins have no
tolerance allowance. The earlier illustrative header/post 7-in and 8-in
vertical-bolt stack issue is still open; this combined probe does not select
or screen delivered bolts or threads. Nor does it determine signed combined
joint actions, moment transfer, contact retention, splitting, wood bearing,
bolt yield, washer pressure, installation sequence, strength, or all-six-case
response. It is no cut, drilling, fabrication, or rating release.

Reproduce with `.venv/bin/python scripts/simple_center_combined_cleats_probe.py`
and `.venv/bin/python -m pytest -q
tests/test_simple_center_combined_cleats_probe.py`.
