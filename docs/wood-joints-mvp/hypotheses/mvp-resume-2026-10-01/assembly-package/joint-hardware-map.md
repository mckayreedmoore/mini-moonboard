# Joint hardware map

Conditional planning schedule for the 24 named block joints. Axis expressions expand to exact `axis_id` values: `stem_[1,2]` means `stem_1` and `stem_2`; `{a,b}_[1,2]` expands both stems for both numbers. In one cell, a following `/stem_[1,2]` reuses the preceding axis directory. Each axis takes one bolt, one matched nut and two separate washers. Length is current nominal planning length.

## Current fastener routes

| Code | Working-order family; need | Thread × nominal; bolt supplier/item; matched nut; two washers |
| --- | --- | --- |
| O | Ordinary candidate; 44 | 1/4-20 × 6 in; K.L. Jack `25C600HCS5Z`; K.L. Jack nut `25CNFH5Z`; K.L. Jack washers `25NWUS` |
| CP | Center post; 4 | 1/4-20 × 6 in; K.L. Jack `25C600HCS5Z`; K.L. Jack nut `25CNFH5Z`; K.L. Jack washers `25NWUS` |
| SD | Side; 12 | 1/4-20 × 8 in; Lawson `FA21103`; K.L. Jack nut `25CNFH5Z`; K.L. Jack washers `25NWUS` |
| TR | Top rail; 4 | 1/4-20 × 8 in; Lawson `FA21103`; Bolt Depot nut `2569`; Hillman `885522` / Lowe's `755754` washers |
| KH | Inner knee/header; 4 | 1/4-20 × 8 in; Lawson `FA21103`; K.L. Jack nut `25CNFH5Z`; K.L. Jack washers `25NWUS` |
| CH | Center principal/header; 4 | 1/4-20 × 8 in; Lawson `FA21103`; K.L. Jack nut `25CNFH5Z`; K.L. Jack washers `25NWUS` |
| TS | Top side; 4 | 5/16-18 × 8 in; Bolt Depot `28650`; Bolt Depot nut `2583`; Bolt Depot washers `2995` |
| OP | Outer post; 4 | 1/4-20 × 4 in; K.L. Jack `25C400HCS5Z`; K.L. Jack nut `25CNFH5Z`; K.L. Jack washers `25NWUS` |
| CPr | Center principal; 4 | 1/4-20 × 5.5 in; K.L. Jack `25C550HCS5Z`; K.L. Jack nut `25CNFH5Z`; K.L. Jack washers `25NWUS` |
| PH | Center post/header; 4 | 1/4-20 × 7.5 in; HiStrength `104-049`; K.L. Jack nut `25CNFH5Z`; K.L. Jack washers `25NWUS` |
| KS | Continuous knee side; 4 | 1/4-20 × 9.5 in; Ro-Brand `HC5127`; K.L. Jack nut `25CNFH5Z`; K.L. Jack washers `25NWUS` |
| RF | Retained front; 4 | 3/8-16 × 4 in; Bolt Depot `367`; Bolt Depot nut `2571`; Bolt Depot washers `15023` |
| RR | Retained rear; 4 | 3/8-16 × 4.5 in; Bolt Depot `368`; Bolt Depot nut `2571`; Bolt Depot washers `15023` |
| RL | Retained upper leg; 4 | 1/2-13 × 8 in; Bolt Depot `407`; Bolt Depot nut `2573`; Bolt Depot washers `15025` |

## Candidate block schedule

Codes with `×n` give axes and physical stacks for that block. `†` marks a continuous knee axis shared by the spine and inner-frame block rows; count each such axis once.

| Block ID | Other receivers | Exact axis pattern → route/count |
| --- | --- | --- |
| `bottom_center_left_cleat` | `base_principal_center_left`, `base_rail_bottom_left` | `bottom_center/clip_horizontal_bottom_left_2/{principal,rail}_[1,2]` → O×4 |
| `bottom_center_right_cleat` | `base_principal_center_right`, `base_rail_bottom_right` | `bottom_center/clip_horizontal_bottom_right_1/{principal,rail}_[1,2]` → O×4 |
| `bottom_outer_left_cleat` | `base_rail_bottom_left`, `base_side_left` | `bottom_outer/clip_horizontal_bottom_left_1/rail_[1,2]` → O×2; `/side_[1,2]` → SD×2 |
| `bottom_outer_right_cleat` | `base_rail_bottom_right`, `base_side_right` | `bottom_outer/clip_horizontal_bottom_right_2/rail_[1,2]` → O×2; `/side_[1,2]` → SD×2 |
| `center_post_cleat_left` | `base_header`, `base_post_center_left` | `center_post_header_left_[1,2]` → PH×2; `center_post_left_[1,2]` → CP×2 |
| `center_post_cleat_right` | `base_header`, `base_post_center_right` | `center_post_header_right_[1,2]` → PH×2; `center_post_right_[1,2]` → CP×2 |
| `center_principal_cleat_left` | `base_header`, `base_principal_center_left` | `center_principal_header_left_[1,2]` → CH×2; `center_principal_left_[1,2]` → CPr×2 |
| `center_principal_cleat_right` | `base_header`, `base_principal_center_right` | `center_principal_header_right_[1,2]` → CH×2; `center_principal_right_[1,2]` → CPr×2 |
| `knee_outer_left_inner_frame_block` | `base_header`, `base_side_left` | `knee_outer_left_inner_header_[1,2]` → KH×2; `knee_outer_left_side_[1,2]`† → KS×2 |
| `knee_outer_left_spine` | `base_post_outer_left`, `base_side_left` | `knee_outer_left_post_[1,2]` → OP×2; `knee_outer_left_side_[1,2]`† → KS×2 |
| `knee_outer_right_inner_frame_block` | `base_header`, `base_side_right` | `knee_outer_right_inner_header_[1,2]` → KH×2; `knee_outer_right_side_[1,2]`† → KS×2 |
| `knee_outer_right_spine` | `base_post_outer_right`, `base_side_right` | `knee_outer_right_post_[1,2]` → OP×2; `knee_outer_right_side_[1,2]`† → KS×2 |
| `left_service_inner_lower_cleat` | `base_principal_center_left`, `base_rail_service_lower_left` | `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_2/{lower_principal,lower_rail}_[1,2]` → O×4 |
| `left_service_inner_upper_cleat` | `base_principal_center_left`, `base_rail_service_upper_left` | `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_upper_left_2/{upper_principal,upper_rail}_[1,2]` → O×4 |
| `left_service_outer_lower_cleat` | `base_rail_service_lower_left`, `base_side_left` | `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_1/lower_rail_[1,2]` → O×2; `/lower_side_[1,2]` → SD×2 |
| `left_service_outer_upper_cleat` | `base_rail_service_upper_left`, `base_side_left` | `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_upper_left_1/upper_rail_[1,2]` → O×2; `/upper_side_[1,2]` → SD×2 |
| `top_center_left_cleat` | `base_principal_center_left`, `base_rail_top` | `top_center/clip_split_top_center_left/{principal,rail}_[1,2]` → O×4 |
| `top_center_right_cleat` | `base_principal_center_right`, `base_rail_top` | `top_center/clip_split_top_center_right/{principal,rail}_[1,2]` → O×4 |
| `top_outer_left_cleat` | `base_rail_top`, `base_side_left` | `top_outer/clip_single_top_left_1/rail_[1,2]` → TR×2; `/side_[1,2]` → TS×2 |
| `top_outer_right_cleat` | `base_rail_top`, `base_side_right` | `top_outer/clip_single_top_right_2/rail_[1,2]` → TR×2; `/side_[1,2]` → TS×2 |
| `wj04_lower_full_stock_cleat` | `base_principal_center_right`, `base_rail_service_lower_right` | `wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/{lower_principal,lower_rail}_[1,2]` → O×4 |
| `wj04_upper_g7_crosscut_full_stock_cleat` | `base_principal_center_right`, `base_rail_service_upper_right` | `wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/{upper_principal,upper_rail}_[1,2]` → O×4 |
| `wj06_outer_lower_right_cleat` | `base_rail_service_lower_right`, `base_side_right` | `wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/lower_rail_[1,2]` → O×2; `/lower_side_[1,2]` → SD×2 |
| `wj06_outer_upper_right_cleat` | `base_rail_service_upper_right`, `base_side_right` | `wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/upper_rail_[1,2]` → O×2; `/upper_side_[1,2]` → SD×2 |

## Retained frame-bolt schedule

These 12 axes are outside the 24 block rows: four per retained family.

| Exact retained axis pattern | Route/count |
| --- | --- |
| `rail_front_bolt_{left,right}_[1,2]` | RF×4 |
| `rail_rear_bolt_{left,right}_[1,2]` | RR×4 |
| `lumber_leg_bolt_{left,right}_[1,2]` | RL×4 |

Block rows show 96 axis incidences; the four shared continuous-knee shafts account for four duplicate incidences, leaving 92 unique candidate stacks. Add 12 retained stacks: 104 bolts, 104 nuts and 208 washers. The 66 purchased Hillman `42605` panel/kicker screws remain separate.

Use [current fourteen-family hardware routes](working-hardware.md) and the [per-axis working profiles](hardware-engagement.md#working-order-export) for profile fields and limits. The [shop guide's captured-nut paths](shop-guide.md#removal-and-member-transport) give the four bottom-block operations and their conditional reverse for insertion. This map is conditional planning; listed routes and nominal lengths do not establish delivered fit or conformity.
