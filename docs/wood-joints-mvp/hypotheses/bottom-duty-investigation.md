# Bottom-duty development sequence

Status: read-only investigation, 2026-09-24. These four duties remain outside
the validated [sixteen-duty static composition](wj16-integrated-static/README.md).
This is a proposed investigation order, not a geometry or mechanics pass.
The [canonical inventory](../source-inventory.json) supplies the stations,
receivers, source faces, grain directions, and old screw datums below.

| Duty | Rail | Other receiver |
| --- | --- | --- |
| `clip_horizontal_bottom_left_1` | `base_rail_bottom_left` | `base_side_left` |
| `clip_horizontal_bottom_right_2` | `base_rail_bottom_right` | `base_side_right` |
| `clip_horizontal_bottom_left_2` | `base_rail_bottom_left` | `base_principal_center_left` |
| `clip_horizontal_bottom_right_1` | `base_rail_bottom_right` | `base_principal_center_right` |

Each duty accounts for six former SDS axes, three into the rail and three
into the upright. The rail grain is X; side and principal grain is T. The
rails are 38.1 mm thick in T and 139.7 mm deep in N. Their left/right lengths
are 1041.25 and 1038.075 mm, respectively. Derive each placement from its own
source faces instead of mirroring a nominal width across the kerf-right frame.

Investigate the two outer duties first with one full-section timber cleat
and four through-bolts per duty. An 88.9 mm cleat layer would produce a
127 mm rail grip and a 177.8 mm side grip. The earlier six- and eight-inch
hardware envelopes are dimensional starting points only; thread transition,
product selection, fit, and resistance require their own evidence.

The critical outer check is the existing WJ03 spine outside each side member.
It occupies global Z 146–416 mm and can intercept the side-bolt tail,
nut, washer, or tool route. The reference eight-inch bolt is 203.2 mm nominal,
with a 198.628 mm lower length bound. Subtracting the 177.8 mm wood grip from
that lower bound leaves 20.828 mm before accounting for washers and nut;
this is not a measured tail projection. Check the exact installed components
and the full removal route. The under-header links and
rear bridges end at Z 238.9 mm, below the bottom rails beginning around
Z 319 mm, but remain part of the collision scene.

The center pair shares the principal members with the existing center
principal cleats. It needs a separate placement and shared-host cut review;
neither ordinary service-rail clearances nor WJ16 acceptance transfers to it.
Preserve every fixed panel axis and reconstruct the source and candidate cuts
before checking new bores, washer support, services, and complete joints.

No new cleat position has yet passed a bottom-duty geometry probe. The old
SDS rows are datum seeds, not accepted bolt rows. No bottom replacement,
machining instruction, capacity, or transport path is established here.
