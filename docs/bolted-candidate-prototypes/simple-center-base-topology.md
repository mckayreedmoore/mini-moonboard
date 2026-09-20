# PB-02 preliminary center/base topology (kerf-right)

Status: inventory only. No joint geometry, resistance, transport sequence, or
drilling is approved. Coordinates are world millimeters. This is the separate
bolted-development lane; the selected baseline and its six-case evidence are
unchanged.

## Minimum connected region and duties

The local region has 11 timber members: `base_header`,
`base_principal_center_left/right`, `base_post_center_left/right`, and
`base_rail_bottom_left/right`, `base_rail_service_lower_left/right`, and
`base_rail_service_upper_left/right`. Both sides must remain connected through
the header, not merely have individually plausible joints.

| Duty | Existing stations | Current meeting faces or extents |
| --- | --- | --- |
| Header/principals | `clip_split_base_center_left/right` | Meet at Z=277. |
| Header/posts | `clip_split_header_center_left/right` | Meet at Z=238.9. |
| Bottom rails/principals | `clip_horizontal_bottom_left_2`, `_right_1` | X=±89.05. |
| Lower rails/principals | `clip_horizontal_lower_left_2`, `_right_1` | X=±89.05. |
| Upper rails/principals | `clip_horizontal_upper_left_2`, `_right_1` | X=±89.05. |

The header spans X=-1219.2..1216.025, Y=-175.7..-36, Z=238.9..277.
The left/right center posts span X=-89.05..-50.95 and 50.95..89.05,
Y=-175.7..-36, Z=0..238.9. The principal X intervals are the same;
their inclined profiles run from Z=277 to approximately Z=2217.104.
The six rails meet the principal faces at X=-89.05 or +89.05 without
an existing X overlap. Their inner-to-outer X intervals are
-1130.3..-89.05 (left) and 89.05..1127.125 (right).

## Boundary connections that cannot be dropped

`clip_split_top_center_left/right` connect the principals to `base_rail_top`.
Each bottom, lower-service, and upper-service rail has an opposite outer-end
clip (`clip_horizontal_bottom/lower/upper_left_1` or `_right_2`) to the
corresponding side member. The header also meets the outer posts and side
members at `clip_timber_header_outer_left/right` and
`clip_angle_base_left/right`. PB-02 may redraw these joints, but must account
for each load-transfer duty and preserve the panel receivers at its boundary.

## Fixed kicker axes and inner-edge support

The two physical kicker panels meet at X=-1.5875. Their front-to-back screw
axes start at Y=-17.74375, point along (0,-1,0), and have a historical
50.8-mm occupied length; the purchased Hillman screws are 63.5 mm long.
These are fixed panel axes, not proposed structural-bolt holes.

| Fixed axes | X positions | Z positions | Current receiver |
| --- | --- | --- | --- |
| `round_kicker_left_rim_1/2` | -1200.15 | 60, 192 | `base_post_outer_left` |
| `round_kicker_right_rim_1/2` | 1196.975 | 60, 192 | `base_post_outer_right` |
| `round_kicker_left_center_1/2` | -70 | 60, 192 | `base_post_center_left` |
| `round_kicker_right_center_1/2` | 70 | 60, 192 | `base_post_center_right` |
| `kicker_header_left_1..5` | -200,-400,-600,-800,-1000 | 257.95 | `base_header` |
| `kicker_header_right_1..5` | 200,400,600,800,1000 | 257.95 | `base_header` |

The existing center posts' inner faces are X=-50.95 and +50.95. Relative to
the seam, the left and right inner kicker edges nominally overhang those
faces by 49.3625 and 52.5375 mm. Screw-axis intersection with a post does
not prove adequate edge support. Any changed center backing must demonstrate
both inner-edge support and actual receiving timber for all 18 kicker axes;
it must also preserve the other 48 fixed main-panel screw axes.

## Twelve existing frame-bolt arrangements: starting references only

All listed axes run in the X direction. Each side has two leg bolts, two
front runner bolts, and two rear runner bolts. Their modeled lengths are
analysis envelopes, not purchased-length or drill instructions.

| Axis pair per side | Start X left/right | Shared Y,Z centers | Modeled length |
| --- | --- | --- | --- |
| `lumber_leg_bolt_left/right_1/2` | -1127.125 / 1123.95 | See below. | 203.2 |
| `rail_front_bolt_left/right_1/2` | -1179.068 / 1175.893 | See below. | 101.6 |
| `rail_rear_bolt_left/right_1/2` | -1217.168 / 1213.993 | (1551,69); (1517,97.5) | 114.3 |

Leg bolt Y,Z centers: (1125.246,1734.987) and (1143.254,1788.013).
Front runner bolt centers: (-105.528,70.172) and (-77.597,98.103).

The four leg axes connect each `base_side_*` to its `lumber_leg_*`.
The four front axes connect each `base_post_outer_*` to `base_floor_*`;
the four rear axes connect `base_floor_*` to `lumber_leg_*`. Their positions
and force checks must be revisited if the hidden frame or receiving stack
changes. No earlier bolt result transfers automatically.

## Geometry PB-02 must prove before an architecture decision

- Every proposed full-section overlap has two uncut member sections, a real
  centerline offset, complete bolt paths, and retained panel-screw receivers.
- Every rectangular cleat has separate rail-to-cleat and upright/post-to-cleat
  bolt groups, nonintersecting bores, and a continuous load path through the
  cleat and header. It cannot count two serial groups as parallel capacity.
- Heads, washers, nuts, and tools fit on both ends of each ordinary through
  bolt, including at the header/post face and the crowded center rail ends.
- All six inner rail ends, top/outer boundary duties, and any changed frame
  bolts remain connected; no hidden SDS path is assumed after replacement.
- Both kicker inner edges and all 66 fixed panel/kicker screw axes retain
  suitable receivers without moving the climbing surface or panel outlines.

Source records:
[`stock-profiles.json`](../floor-flush-construction-kerf-right/stock-profiles.json),
[`connection-axes.csv`](../floor-flush-construction-kerf-right/connection-axes.csv),
and [`compact_floor_flush_frame.py`](../../mini_moonboard/compact_floor_flush_frame.py).
These coordinates are a preliminary topology screen, not a fit or strength
verdict, joint selection, native solve, or fabrication release.
