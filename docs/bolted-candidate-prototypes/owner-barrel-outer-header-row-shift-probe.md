# Recessed outer-header forward-row sensitivity

The [detached CAD probe](../../scripts/owner_barrel_outer_header_row_shift_probe.py)
compares the current recessed outer-header/post barrel layout with three
forward-row offsets. It reads the kerf-right owner barrel viewer assembly but
does not edit its producer, scene, wood, panels, 66 panel/kicker screw axes,
12 retained frame-bolt axes, or any other joint. The rear row stays at
Y = −135 mm on both sides. Each option translates the **actual viewer**
forward-row barrel, pilot, cross-bore, 25.4 mm counterbore, shaft, washer,
head, and straight tool envelopes together; it cuts copies of only the
header and two outer posts.

| Forward row Y | Nearest removed-wood to fixed screw | Same-side counterbore gap |
| ---: | ---: | ---: |
| −75 mm (viewer) | 2.706 mm | 34.600 mm |
| −80 mm | 7.706 mm | 29.600 mm |
| −85 mm | 12.706 mm | 24.600 mm |
| −90 mm | 17.706 mm | 19.600 mm |

The limiting axis in each pose is `round_kicker_left_rim_2` at the left
forward post machine bore; the mirrored right-side screw has the same nominal
gap. This is distance to the *removed wood*, not a center-to-center
distance or a manufacturing tolerance. The row shift improves that local
nominal margin monotonically, while reducing separation between the two
counterbores. It does not itself prove the joint suitable.

For each option, the probe reports all 12 intended bore-to-host coverage
fractions, Boolean removed volumes, cut validity and connected-solid counts
for the three intended hosts, protected-solid intersections, unrelated-wood
intersections, and new-row versus every other current viewer physical and
path envelope. The protected inventory includes T-nuts, hold holes plus a
provisional rear-bolt projection, lights, wires, all 66 fixed screw axes, and
all 12 frame-bolt axes. It also reports same-side row-to-row intersections
and nominal head/washer/counterbore and barrel/cross-bore fit. A reported
zero means no volume above the 1 mm³ screen threshold, not tolerance or
installation clearance approval.

All 12 intended bores have nominal host coverage 1.000 in all four poses.
The three cut hosts remain single valid solids. The nominal intersections
with protected fixed solids, unrelated wood, other viewer hardware/paths,
and each other are all zero above the screen threshold. The head and washer
envelopes fit within each counterbore; installed hardware does not intersect
the side rim. These favorable nominal results do not establish strength or
serviceability.

In every pose the **installed side rim still blocks the 20 mm straight
outer-header driver envelope**. Removing the rim first is only a conditional,
unverified service idea; the probe does not validate that removal sequence,
real tools, hardware tolerances, structural capacity, or repeated demounting.
One connected Boolean wood solid is not an adequate strength verdict. All
source release flags and this probe's layout, drilling, fabrication, and
structural approvals remain false. These numbers are not cut or drill
instructions.

Focused validation:
`pytest -q tests/test_owner_barrel_outer_header_row_shift_probe.py`.
