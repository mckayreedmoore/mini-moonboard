# PB-02/PB-03 kerf-right architecture duty map

Status: topology and cost-architecture inventory only. No joint, bolt group,
member change, rating, or drilling is approved. The 24 ML24Z stations below
are the original structural angle duties, not 24 proven interchangeable cleats.
Each has six old structural SDS axes (144 total) to replace with a new load path.

Current status at `74fba89`: PB02 replaces the two right-center base/header
stations. The PB03 lower-service core replaces the two center and two outer
lower-service stations with four 300 mm solid timber blocks and 16 unselected
through-bolt stacks. Exactly **18 legacy angle stations and 108 SDS axes
remain**. The outer upright stacks use a 228.6 mm illustrative wood grip.
Exact retail hardware and outer-pair resistance remain unresolved. This is a
partial development assembly, not a drilling, fabrication, or structural
release.

Sources: `mini_moonboard/compact_floor_flush_frame.py` `stations()` and
`connections()`; `docs/bolted-candidate-interfaces.json` under
`classified_by_width.kerf-right`; and the kerf-right `connection-axes.csv`,
`panel-attachment-axes.csv`, and `stock-profiles.json`. Coordinates are mm in
the current frame, rounded to 0.001. Station XYZ is the old angle origin,
not a proposed bolt center. Left/right are not assumed geometrically identical.

## Member key and distinction key

- `H` = `base_header`; `T` = `base_rail_top`.
- `CL/CR` = `base_principal_center_left/right`.
- `SL/SR` = `base_side_left/right`.
- `PL/PR` = `base_post_center_left/right`.
- `OL/OR` = `base_post_outer_left/right`.
- `BL/BR` = `base_rail_bottom_left/right`.
- `LL/LR` = `base_rail_service_lower_left/right`.
- `UL/UR` = `base_rail_service_upper_left/right`.
- `same family` means only a possible template for study; the exact pose,
  neighbors, screws, cut lengths, and access still require a local CAD screen.
- Historical PB01 is `clip_horizontal_lower_right_1` (`CR`–`LR`), a 2x6 butt
  end at X = 89.05. PB03 now replaces this station, its independently built
  left counterpart, and both lower-service outer stations geometrically. No
  resistance result has been transferred to the outer pair.

## All 24 original ML24Z duties

Each row names the exact old station, timber pair, old origin XYZ, and how it
differs from PB01. The final column is an architecture-screen family, not a
statement that one piece or one bolt pattern works at every row.

| Old station | Pair | XYZ (mm) | Difference / screen family |
| --- | --- | --- | --- |
| `clip_single_top_left_1` | T–SL | -1130.3,1442.993,2184.45 | top, outer end |
| `clip_single_top_right_2` | T–SR | 1130.3,1442.993,2184.45 | top, outer end |
| `clip_split_top_center_left` | CL–T | -89.05,1442.993,2184.45 | top, center |
| `clip_split_top_center_right` | CR–T | 89.05,1442.993,2184.45 | top, center |
| `clip_horizontal_bottom_left_1` | BL–SL | -1130.3,-49.688,405.542 | bottom, outer |
| `clip_horizontal_bottom_left_2` | CL–BL | -89.05,-49.688,405.542 | bottom, center |
| `clip_horizontal_bottom_right_1` | CR–BR | 89.05,-49.688,405.542 | bottom, center |
| `clip_horizontal_bottom_right_2` | BR–SR | 1130.3,-49.688,405.542 | bottom, outer |
| `clip_horizontal_lower_left_1` | LL–SL | -1130.3,616.914,1199.968 | PB03 geometry only |
| `clip_horizontal_lower_left_2` | CL–LL | -89.05,616.914,1199.968 | PB03 geometry only |
| `clip_horizontal_lower_right_1` | CR–LR | 89.05,616.914,1199.968 | PB03 geometry only |
| `clip_horizontal_lower_right_2` | LR–SR | 1130.3,616.914,1199.968 | PB03 geometry only |
| `clip_horizontal_upper_left_1` | UL–SL | -1130.3,733.998,1339.503 | upper, outer |
| `clip_horizontal_upper_left_2` | CL–UL | -89.05,733.998,1339.503 | upper, center |
| `clip_horizontal_upper_right_1` | CR–UR | 89.05,733.998,1339.503 | upper, center |
| `clip_horizontal_upper_right_2` | UR–SR | 1130.3,733.998,1339.503 | upper, outer |
| `clip_timber_header_outer_left` | H–OL | -1181.1,-105.85,238.9 | header/post, outer |
| `clip_timber_header_outer_right` | H–OR | 1181.1,-105.85,238.9 | header/post, outer |
| `clip_split_header_center_left` | H–PL | -89.05,-105.85,238.9 | header/post, center |
| `clip_split_header_center_right` | H–PR | 89.05,-105.85,238.9 | PB02 converted, development only |
| `clip_split_base_center_left` | H–CL | -89.05,-124.9,277 | header/upright, center |
| `clip_split_base_center_right` | H–CR | 89.05,-124.9,277 | PB02 converted, development only |
| `clip_angle_base_left` | H–SL | -1130.3,-105.85,277 | header/upright, outer |
| `clip_angle_base_right` | H–SR | 1130.3,-105.85,277 | header/upright, outer |

The bottom rail, lower service rail, and upper service rail sit at different
slope stations; lower and upper service rails are close neighbors. Top-rail
connections meet a continuous transverse top member rather than a service
rail end. Header/post joints are vertical butt contacts below the header;
header/upright joints are above it. The center header-post and header-upright
stations share a local assembly region, so access and bore paths must be
checked together. Outer duties also neighbor floor, rim, and side framing.
These are mechanically distinct topology/access questions even where old
ML24Z count and nominal lumber sections match.

## Twelve old frame-bolt axes: separate starting references

These are **not** among the 24 ML24Z duties or 144 SDS axes. Retain/reassess
each only after the new frame topology is drawn; do not credit old capacity
or assume its hole remains clear. All run along global X in the source CSV.

| Old axis | Timber pair | Y,Z (mm) | Duty |
| --- | --- | --- | --- |
| `lumber_leg_bolt_left_1` | SL–`lumber_leg_left` | 1125.246,1734.987 | side/leg |
| `lumber_leg_bolt_left_2` | SL–`lumber_leg_left` | 1143.254,1788.013 | side/leg |
| `lumber_leg_bolt_right_1` | SR–`lumber_leg_right` | 1125.246,1734.987 | side/leg |
| `lumber_leg_bolt_right_2` | SR–`lumber_leg_right` | 1143.254,1788.013 | side/leg |
| `rail_front_bolt_left_1` | OL–`base_floor_left` | -105.528,70.172 | front floor |
| `rail_front_bolt_left_2` | OL–`base_floor_left` | -77.597,98.103 | front floor |
| `rail_front_bolt_right_1` | OR–`base_floor_right` | -105.528,70.172 | front floor |
| `rail_front_bolt_right_2` | OR–`base_floor_right` | -77.597,98.103 | front floor |
| `rail_rear_bolt_left_1` | `base_floor_left`–`lumber_leg_left` | 1551,69 | rear floor |
| `rail_rear_bolt_left_2` | `base_floor_left`–`lumber_leg_left` | 1517,97.5 | rear floor |
| `rail_rear_bolt_right_1` | `base_floor_right`–`lumber_leg_right` | 1551,69 | rear floor |
| `rail_rear_bolt_right_2` | `base_floor_right`–`lumber_leg_right` | 1517,97.5 | rear floor |

## Fixed panel/kicker receivers

All 66 purchased Hillman panel/kicker screw axes and six panel outlines are
fixed. An architecture must retain a positively supported receiving member
with actual embedment at **every** axis; preserving only the screw coordinates
is insufficient. Counts below are from `panel-attachment-axes.csv`.

| Receiver | Fixed axes | Group |
| --- | ---: | --- |
| SL, SR | 8 each | main-panel rim |
| CL, CR | 8 each | main-panel center |
| BL, BR | 2 each | lower-panel bottom |
| LL, LR | 2 each | lower-panel service |
| UL, UR | 2 each | upper-panel service |
| T | 4 | upper-panel top |
| OL, OR | 2 each | kicker outer |
| PL, PR | 2 each | kicker center |
| H | 10 | kicker header |

Thus each main panel has 12 axes (four panels, 48 total); each kicker has
nine axes (two kickers, 18 total). The kerf-right kicker panel seam is at
X = -1.5875 mm; center-post inner faces are X = -50.95 and +50.95 mm.
Any center-post relocation must re-prove the four fixed kicker-center
receivers and panel-edge support, not just clear an angle or bolt.

## Minimum distinct CAD screens before architecture selection

One representative per **topologically different local condition** is the
minimum screening set below. A passed representative only licenses further
screens of the other named stations, not extrapolated approval. Each screen
must show both members, actual panel receivers, neighbor timber, complete
bolt bores, head/washer/nut/tool volumes, assembly order, and separation.

1. The four `clip_horizontal_lower_*` stations: the PB03 lower-service core
   checks actual kerf-right center and outer conditions independently with four
   300 mm blocks, 16 complete generic stacks, nearby timber, finished panels,
   all 66 fixed axes, bore intersections, and tool paths. The outer pair uses
   the actual side members and coincident rail butt faces. Its upright stacks
   have a 228.6 mm illustrative grip. Exact retail hardware, resistance,
   tolerances, and release remain open.
2. `clip_horizontal_upper_right_1` and `_2`: center and outer upper-service
   ends. Their lower-neighbor gap and fixed upper-panel receivers differ.
3. `clip_horizontal_bottom_right_1` and `_2`: center and outer bottom-rail
   ends. The header, kicker, and lower-panel bottom screws bound this region.
4. `clip_split_top_center_right` and `clip_single_top_right_2`: center and
   outer top-rail conditions, including its four fixed upper-panel screws.
5. `clip_split_header_center_right` and `clip_timber_header_outer_right`:
   header-to-center/outer posts, with kicker screws and front floor joint.
6. `clip_split_base_center_right` and `clip_angle_base_right`: header-to-
   center/outer inclined uprights, checked with the post joints above.
7. The three existing bolt-pair families: side/leg, front post/floor, and
   rear floor/leg, in the changed center/base load path and trim geometry.

These are representative original ML24Z station families plus three old-bolt-
pair families. The four-station PB03 lower-service core is a geometry-only
conversion. Audit the remaining 18 stations against actual kerf-right stock,
panel receivers, and neighbor volumes before finalizing a single or mixed
architecture. A family may split further when contact, load angle, grain,
edge/end distance, access, cost, or screw backing differs. Cost comparison
must count distinct cleat stock/cuts, bolt lengths, washers/nuts, and added
backers across all original 24 stations and 12 old frame-bolt axes. No strength,
stiffness, or six-case verdict follows from this inventory.
