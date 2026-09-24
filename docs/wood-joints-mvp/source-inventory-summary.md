# Wood-joint source inventory summary

This summary renders selected source measurements from
[`source-inventory.json`](source-inventory.json). The machine-readable inventory
is authoritative. Values below describe the reviewed kerf-right source geometry;
they do not establish a candidate joint, drilling instruction, or capacity.

## Inventory counts

| Record | Count |
|---|---:|
| Legacy structural-angle duties | 24 |
| Legacy structural SDS axes | 144 |
| Fixed panel and kicker screw axes | 66 |
| Starting frame-bolt arrangements | 12 |
| Additional receiver obligations | 2 |

## Ordinary workhorse reference

The WJ-04 reference station is `clip_horizontal_lower_right_1`. Its source
hosts are `base_rail_service_lower_right` and
`base_principal_center_right`.

| Source host | Recorded blank dimensions X × N × T |
|---|---:|
| `base_rail_service_lower_right` | 1038.075 × 139.7 × 38.1 mm |
| `base_principal_center_right` | 2532.626012 × 139.7 × 38.1 mm |

| Constraint | Source member | Physical face | Measured width | Rear projection |
|---|---|---|---:|---:|
| Rail rear-face local T | `base_rail_service_lower_right` | `planar_face_02` | 38.1 mm | 139.7 mm local N |
| Principal rear-face local X | `base_principal_center_right` | `planar_face_04` | 38.1 mm | 139.7 mm local N |

These are the two narrowest named constraints in the inventory. The 38.1 mm
faces prevent treating the rear surfaces as 139.7 mm-wide bolt-row faces. WJ-04
must derive its bolt axes and edge distances from the real faces and rail end.
