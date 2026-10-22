# Current timber end and receiver coordinates

Applies to **`eoere-paired-frame-retained-2x6-A574-v2`** with **`eoere-paired-frame-retained-2x6-A574-v2`**, extra grid off.
Use with the [builder plan](builder-plan.md); conditional nominal planning only.

Generated from the checked post-revision binding and the preserved shop tables
with two stock, eight stack, sixteen receiver-row and eight enclosed-passage profile overrides.
Shop-result SHA-256: `98fb3d6437d629201e9e60cf6a3068a070f2e1f0574a7364c256c0e8a904f379`.
The producer authenticates profiles, members, selected hardware, drilling paths
and receiver rows, then checks both local endpoints against each world shaft axis.

## Coordinate convention

All dimensions are millimetres. Coordinates preserve the source L/U/V frame.
L follows grain. U and V are member-specific section axes: most timbers use
U across thickness and V across depth; **base_header uses U across its 139.7-mm
depth and V across its 38.1-mm thickness**. Its U=0 reference retains the original datum,
and its bolt receivers run along V. Negative V values elsewhere are intentional.
The per-member world datum and positive unit vectors identify
each face and orientation; left/right members must retain their own labels.
U=0 is the labeled reference face, not necessarily the installed bolt-entry face.
An L=0 profile corner is not a square-end fence across the whole member.

Raw minimum-U face marks below retain source indices; their listing is not a polygon
or saw path. End-plane marks identify vertices on each raw cut face. Use the
issued projections and finished recess/passage details beside these numbers.
Raw blank lengths can exceed the final L extent after angled cuts.

Receiver entry/exit means increasing saved shaft-axis parameter, not a prescribed
drill approach. Recessed entries remain on their recorded finished face. Join paired
receivers in one supported setup; do not independently drill opposite marks.
Bit choices are 13/32 in for 3/8-in bolts and 17/32 in for 1/2-in bolts.
The selected underhead lengths supersede old modeled-length columns. Spacers
go between nut washer and nut. Each cleat/post stack uses two 12.7-mm
factory spacers (25.4 mm total); shared-header stacks retain one 12.7-mm spacer.
No Actual/Disposition values are supplied. Changed installation remains unqualified.

Six decimal places preserve nominal source detail; they are not machining tolerances.
Panel and screw datums remain in the current shop tables linked by the builder plan.

## base_floor_left

Raw blank L × depth × thickness: **1815.646483 × 139.7 × 38.1**.
World datum XYZ: `(-1257.3, -175.7, 139.7)`.
Positive L/U/V unit vectors: `(0, 1, 0)`; `(1, 0, 0)`; `(0, 0, -1)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 139.7)`; 1: `(0, 0)`; 2: `(1781.238528, 0)`; 3: `(1815.646483, 139.7)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_floor_left.svg).
Raw end plane 1, U=0 marks: 1: `(0, 0)`; 0: `(0, 139.7)`.
Raw end plane 2, U=0 marks: 3: `(1815.646483, 139.7)`; 2: `(1781.238528, 0)`.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `rail_front_bolt_left_1` | `(80, 38.1, 89.7)` | `(80, 0, 89.7)` | 13/32 | 9.525 × 152.4 | 0 |
| `rail_front_bolt_left_2` | `(80, 38.1, 39.7)` | `(80, 0, 39.7)` | 13/32 | 9.525 × 152.4 | 0 |
| `rail_rear_bolt_left_1` | `(1732.525893, 38.1, 69.265089)` | `(1732.525893, 0, 69.265089)` | 13/32 | 9.525 × 114.3 | 0 |

## base_floor_right

Raw blank L × depth × thickness: **1815.646483 × 139.7 × 38.1**.
World datum XYZ: `(1216.025, -175.7, 139.7)`.
Positive L/U/V unit vectors: `(0, 1, 0)`; `(1, 0, 0)`; `(0, 0, -1)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 139.7)`; 1: `(0, 0)`; 2: `(1781.238528, 0)`; 3: `(1815.646483, 139.7)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_floor_right.svg).
Raw end plane 1, U=0 marks: 1: `(0, 0)`; 0: `(0, 139.7)`.
Raw end plane 2, U=0 marks: 3: `(1815.646483, 139.7)`; 2: `(1781.238528, 0)`.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `rail_front_bolt_right_1` | `(80, 0, 89.7)` | `(80, 38.1, 89.7)` | 13/32 | 9.525 × 152.4 | 0 |
| `rail_front_bolt_right_2` | `(80, 0, 39.7)` | `(80, 38.1, 39.7)` | 13/32 | 9.525 × 152.4 | 0 |
| `rail_rear_bolt_right_1` | `(1732.525893, 0, 69.265089)` | `(1732.525893, 38.1, 69.265089)` | 13/32 | 9.525 × 114.3 | 0 |

## base_header

Raw blank L × depth × thickness: **2435.225 × 139.7 × 38.1**.
World datum XYZ: `(-1219.2, -175.7, 238.9)`.
Positive L/U/V unit vectors: `(1, 0, 0)`; `(0, 1, 0)`; `(0, 0, 1)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 0)`; 1: `(0, 38.1)`; 4: `(2435.225, 0)`; 5: `(2435.225, 38.1)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_header.svg).
Raw end plane 1, U=0 marks: 0: `(0, 0)`; 1: `(0, 38.1)`.
Raw end plane 2, U=0 marks: 5: `(2435.225, 38.1)`; 4: `(2435.225, 0)`.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_065` | `(1065.0625, 44.45, 38.1)` | `(1065.0625, 44.45, 0)` | 13/32 | 9.525 × 88.9 | 12.7 |
| `eoere_bolt_066` | `(1065.0625, 95.25, 38.1)` | `(1065.0625, 95.25, 0)` | 13/32 | 9.525 × 88.9 | 12.7 |
| `eoere_bolt_079` | `(1334.1375, 95.25, 38.1)` | `(1334.1375, 95.25, 0)` | 13/32 | 9.525 × 88.9 | 12.7 |
| `eoere_bolt_080` | `(1334.1375, 44.45, 38.1)` | `(1334.1375, 44.45, 0)` | 13/32 | 9.525 × 88.9 | 12.7 |
| `eoere_bolt_081` | `(153.9875, 90.4875, 38.1)` | `(153.9875, 90.4875, 0)` | 13/32 | 9.525 × 88.9 | 12.7 |
| `eoere_bolt_082` | `(153.9875, 39.6875, 38.1)` | `(153.9875, 39.6875, 0)` | 13/32 | 9.525 × 88.9 | 12.7 |
| `eoere_bolt_083` | `(2281.2375, 39.6875, 38.1)` | `(2281.2375, 39.6875, 0)` | 13/32 | 9.525 × 88.9 | 12.7 |
| `eoere_bolt_084` | `(2281.2375, 90.4875, 38.1)` | `(2281.2375, 90.4875, 0)` | 13/32 | 9.525 × 88.9 | 12.7 |

## base_post_center_left

Raw blank L × depth × thickness: **238.9 × 139.7 × 38.1**.
World datum XYZ: `(-89.05, -175.7, 0)`.
Positive L/U/V unit vectors: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 0)`; 1: `(238.9, 0)`; 2: `(0, 139.7)`; 3: `(238.9, 139.7)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_post_center_left.svg).
Raw end plane 1, U=0 marks: 0: `(0, 0)`; 2: `(0, 139.7)`.
Raw end plane 2, U=0 marks: 3: `(238.9, 139.7)`; 1: `(238.9, 0)`.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_075` | `(173.8125, 0, 95.25)` | `(173.8125, 38.1, 95.25)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_077` | `(173.8125, 0, 44.45)` | `(173.8125, 38.1, 44.45)` | 13/32 | 9.525 × 63.5 | 0 |

## base_post_center_right

Raw blank L × depth × thickness: **238.9 × 139.7 × 38.1**.
World datum XYZ: `(11.75, -175.7, 0)`.
Positive L/U/V unit vectors: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 0)`; 1: `(238.9, 0)`; 2: `(0, 139.7)`; 3: `(238.9, 139.7)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_post_center_right.svg).
Raw end plane 1, U=0 marks: 0: `(0, 0)`; 2: `(0, 139.7)`.
Raw end plane 2, U=0 marks: 3: `(238.9, 139.7)`; 1: `(238.9, 0)`.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_076` | `(173.8125, 38.1, 95.25)` | `(173.8125, 0, 95.25)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_078` | `(173.8125, 38.1, 44.45)` | `(173.8125, 0, 44.45)` | 13/32 | 9.525 × 63.5 | 0 |

## base_post_outer_left

Raw blank L × depth × thickness: **238.9 × 139.7 × 88.9**.
World datum XYZ: `(-1219.2, -175.7, 0)`.
Positive L/U/V unit vectors: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 0)`; 1: `(238.9, 0)`; 2: `(0, 139.7)`; 3: `(238.9, 139.7)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_post_outer_left.svg).
Raw end plane 1, U=0 marks: 0: `(0, 0)`; 2: `(0, 139.7)`.
Raw end plane 2, U=0 marks: 3: `(238.9, 139.7)`; 1: `(238.9, 0)`.

Finished profile: **9.525 × 9.525 mm, 45° longitudinal corner bevel**
at **U=88.9, V=139.7**, for the full L=0–238.9 mm height.
Raw marks above precede this T-nut clearance cut. Bolt receiver faces at
their own stations retain the full 88.9-mm width; actual cuts remain unverified.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `cleat_post_bolt_left_1` | `(173.8125, 88.9, 39.6875)` | `(173.8125, 0, 39.6875)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `cleat_post_bolt_left_2` | `(173.8125, 88.9, 90.4875)` | `(173.8125, 0, 90.4875)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `rail_front_bolt_left_1` | `(50, 88.9, 80)` | `(50, 0, 80)` | 13/32 | 9.525 × 152.4 | 0 |
| `rail_front_bolt_left_2` | `(100, 88.9, 80)` | `(100, 0, 80)` | 13/32 | 9.525 × 152.4 | 0 |

## base_post_outer_right

Raw blank L × depth × thickness: **238.9 × 139.7 × 88.9**.
World datum XYZ: `(1127.125, -175.7, 0)`.
Positive L/U/V unit vectors: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 0)`; 1: `(238.9, 0)`; 2: `(0, 139.7)`; 3: `(238.9, 139.7)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_post_outer_right.svg).
Raw end plane 1, U=0 marks: 0: `(0, 0)`; 2: `(0, 139.7)`.
Raw end plane 2, U=0 marks: 3: `(238.9, 139.7)`; 1: `(238.9, 0)`.

Finished profile: **9.525 × 9.525 mm, 45° longitudinal corner bevel**
at **U=0, V=139.7**, for the full L=0–238.9 mm height.
Raw marks above precede this T-nut clearance cut. Bolt receiver faces at
their own stations retain the full 88.9-mm width; actual cuts remain unverified.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `cleat_post_bolt_right_1` | `(173.8125, 0, 39.6875)` | `(173.8125, 88.9, 39.6875)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `cleat_post_bolt_right_2` | `(173.8125, 0, 90.4875)` | `(173.8125, 88.9, 90.4875)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `rail_front_bolt_right_1` | `(50, 0, 80)` | `(50, 88.9, 80)` | 13/32 | 9.525 × 152.4 | 0 |
| `rail_front_bolt_right_2` | `(100, 0, 80)` | `(100, 88.9, 80)` | 13/32 | 9.525 × 152.4 | 0 |

## base_principal_center_left

Raw blank L × depth × thickness: **2532.626012 × 139.7 × 38.1**.
World datum XYZ: `(-50.95, -182.7, 277)`.
Positive L/U/V unit vectors: `(0, 0.642788, 0.766044)`; `(-1, 0, 0)`; `(0, -0.766044, 0.642788)`.

Raw U=0 face marks (vertex index: L, V): 5: `(0, 0)`; 6: `(37.578947, 31.53248)`; 7: `(90.763326, -108.16752)`; 8: `(2506.167119, 31.532481)`; 9: `(2506.167119, -108.167519)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_principal_center_left.svg).
Raw end plane 1, U=0 marks: 5: `(0, 0)`; 6: `(37.578947, 31.53248)`.
Raw end plane 2, U=0 marks: 5: `(0, 0)`; 7: `(90.763326, -108.16752)`.
Raw end plane 3, U=0 marks: 8: `(2506.167119, 31.532481)`; 9: `(2506.167119, -108.167519)`.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_007` | `(2441.079619, 38.1, -12.917519)` | `(2441.079619, 0, -12.917519)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_011` | `(2441.079619, 38.1, -63.717519)` | `(2441.079619, 0, -63.717519)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_033` | `(330.479619, 38.1, -63.71752)` | `(330.479619, 0, -63.71752)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_037` | `(330.479619, 38.1, -12.91752)` | `(330.479619, 0, -12.91752)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_044` | `(1155.929619, 38.1, -12.917519)` | `(1155.929619, 0, -12.917519)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_048` | `(1155.929619, 38.1, -63.717519)` | `(1155.929619, 0, -63.717519)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_052` | `(1468.254619, 38.1, -63.717519)` | `(1468.254619, 0, -63.717519)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_056` | `(1468.254619, 38.1, -12.917519)` | `(1468.254619, 0, -12.917519)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_072` | `(115.584951, 38.1, -36.490606)` | `(115.584951, 0, -36.490606)` | 13/32 | 9.525 × 63.5 | 0 |

## base_principal_center_right

Raw blank L × depth × thickness: **2532.626012 × 139.7 × 38.1**.
World datum XYZ: `(49.85, -182.7, 277)`.
Positive L/U/V unit vectors: `(0, 0.642788, 0.766044)`; `(-1, 0, 0)`; `(0, -0.766044, 0.642788)`.

Raw U=0 face marks (vertex index: L, V): 5: `(0, 0)`; 6: `(37.578947, 31.53248)`; 7: `(90.763326, -108.16752)`; 8: `(2506.167119, 31.532481)`; 9: `(2506.167119, -108.167519)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_principal_center_right.svg).
Raw end plane 1, U=0 marks: 5: `(0, 0)`; 6: `(37.578947, 31.53248)`.
Raw end plane 2, U=0 marks: 5: `(0, 0)`; 7: `(90.763326, -108.16752)`.
Raw end plane 3, U=0 marks: 8: `(2506.167119, 31.532481)`; 9: `(2506.167119, -108.167519)`.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_008` | `(2441.079619, 0, -12.917519)` | `(2441.079619, 38.1, -12.917519)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_012` | `(2441.079619, 0, -63.717519)` | `(2441.079619, 38.1, -63.717519)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_034` | `(330.479619, 0, -63.71752)` | `(330.479619, 38.1, -63.71752)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_038` | `(330.479619, 0, -12.91752)` | `(330.479619, 38.1, -12.91752)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_045` | `(1155.929619, 0, -12.917519)` | `(1155.929619, 38.1, -12.917519)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_049` | `(1155.929619, 0, -63.717519)` | `(1155.929619, 38.1, -63.717519)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_053` | `(1468.254619, 0, -63.717519)` | `(1468.254619, 38.1, -63.717519)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_057` | `(1468.254619, 0, -12.917519)` | `(1468.254619, 38.1, -12.917519)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_073` | `(115.584951, 0, -36.490606)` | `(115.584951, 38.1, -36.490606)` | 13/32 | 9.525 × 63.5 | 0 |

## base_rail_bottom_left

Raw blank L × depth × thickness: **1041.25 × 139.7 × 38.1**.
World datum XYZ: `(-1130.3, 46.261686, 381.587123)`.
Positive L/U/V unit vectors: `(1, 0, 0)`; `(0, 0.642788, 0.766044)`; `(0, -0.766044, 0.642788)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 139.7)`; 2: `(0, 0)`; 4: `(1041.25, 139.7)`; 6: `(1041.25, 0)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_rail_bottom_left.svg).
Raw end plane 1, U=0 marks: 2: `(0, 0)`; 0: `(0, 139.7)`.
Raw end plane 2, U=0 marks: 4: `(1041.25, 139.7)`; 6: `(1041.25, 0)`.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_002` | `(65.0875, 38.1, 44.45)` | `(65.0875, 0, 44.45)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_019` | `(976.1625, 38.1, 44.45)` | `(976.1625, 0, 44.45)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_029` | `(65.0875, 38.1, 95.25)` | `(65.0875, 0, 95.25)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_040` | `(976.1625, 38.1, 95.25)` | `(976.1625, 0, 95.25)` | 13/32 | 9.525 × 63.5 | 0 |

## base_rail_bottom_right

Raw blank L × depth × thickness: **1077.275 × 139.7 × 38.1**.
World datum XYZ: `(49.85, 46.261686, 381.587123)`.
Positive L/U/V unit vectors: `(1, 0, 0)`; `(0, 0.642788, 0.766044)`; `(0, -0.766044, 0.642788)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 139.7)`; 2: `(0, 0)`; 4: `(1077.275, 139.7)`; 6: `(1077.275, 0)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_rail_bottom_right.svg).
Raw end plane 1, U=0 marks: 2: `(0, 0)`; 0: `(0, 139.7)`.
Raw end plane 2, U=0 marks: 4: `(1077.275, 139.7)`; 6: `(1077.275, 0)`.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_014` | `(1012.1875, 38.1, 44.45)` | `(1012.1875, 0, 44.45)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_025` | `(65.0875, 38.1, 44.45)` | `(65.0875, 0, 44.45)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_059` | `(65.0875, 38.1, 95.25)` | `(65.0875, 0, 95.25)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_062` | `(1012.1875, 38.1, 95.25)` | `(1012.1875, 0, 95.25)` | 13/32 | 9.525 × 63.5 | 0 |

## base_rail_service_lower_left

Raw blank L × depth × thickness: **1041.25 × 139.7 × 38.1**.
World datum XYZ: `(-1130.3, 685.015803, 1142.824638)`.
Positive L/U/V unit vectors: `(1, 0, 0)`; `(0, 0.642788, 0.766044)`; `(0, -0.766044, 0.642788)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 139.7)`; 2: `(0, 0)`; 4: `(1041.25, 139.7)`; 6: `(1041.25, 0)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_rail_service_lower_left.svg).
Raw end plane 1, U=0 marks: 2: `(0, 0)`; 0: `(0, 139.7)`.
Raw end plane 2, U=0 marks: 4: `(1041.25, 139.7)`; 6: `(1041.25, 0)`.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_003` | `(65.0875, 0, 44.45)` | `(65.0875, 38.1, 44.45)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_020` | `(976.1625, 0, 44.45)` | `(976.1625, 38.1, 44.45)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_030` | `(65.0875, 0, 95.25)` | `(65.0875, 38.1, 95.25)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_041` | `(976.1625, 0, 95.25)` | `(976.1625, 38.1, 95.25)` | 13/32 | 9.525 × 63.5 | 0 |

## base_rail_service_lower_right

Raw blank L × depth × thickness: **1077.275 × 139.7 × 38.1**.
World datum XYZ: `(49.85, 685.015803, 1142.824638)`.
Positive L/U/V unit vectors: `(1, 0, 0)`; `(0, 0.642788, 0.766044)`; `(0, -0.766044, 0.642788)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 139.7)`; 2: `(0, 0)`; 4: `(1077.275, 139.7)`; 6: `(1077.275, 0)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_rail_service_lower_right.svg).
Raw end plane 1, U=0 marks: 2: `(0, 0)`; 0: `(0, 139.7)`.
Raw end plane 2, U=0 marks: 4: `(1077.275, 139.7)`; 6: `(1077.275, 0)`.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_015` | `(1012.1875, 0, 44.45)` | `(1012.1875, 38.1, 44.45)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_026` | `(65.0875, 0, 44.45)` | `(65.0875, 38.1, 44.45)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_060` | `(65.0875, 0, 95.25)` | `(65.0875, 38.1, 95.25)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_063` | `(1012.1875, 0, 95.25)` | `(1012.1875, 38.1, 95.25)` | 13/32 | 9.525 × 63.5 | 0 |

## base_rail_service_upper_left

Raw blank L × depth × thickness: **1041.25 × 139.7 × 38.1**.
World datum XYZ: `(-1130.3, 670.592949, 1342.970769)`.
Positive L/U/V unit vectors: `(1, 0, 0)`; `(0, 0.642788, 0.766044)`; `(0, -0.766044, 0.642788)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 0)`; 2: `(0, -139.7)`; 4: `(1041.25, 0)`; 6: `(1041.25, -139.7)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_rail_service_upper_left.svg).
Raw end plane 1, U=0 marks: 2: `(0, -139.7)`; 0: `(0, 0)`.
Raw end plane 2, U=0 marks: 4: `(1041.25, 0)`; 6: `(1041.25, -139.7)`.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_004` | `(65.0875, 38.1, -95.25)` | `(65.0875, 0, -95.25)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_021` | `(976.1625, 38.1, -95.25)` | `(976.1625, 0, -95.25)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_031` | `(65.0875, 38.1, -44.45)` | `(65.0875, 0, -44.45)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_042` | `(976.1625, 38.1, -44.45)` | `(976.1625, 0, -44.45)` | 13/32 | 9.525 × 63.5 | 0 |

## base_rail_service_upper_right

Raw blank L × depth × thickness: **1077.275 × 139.7 × 38.1**.
World datum XYZ: `(49.85, 670.592949, 1342.970769)`.
Positive L/U/V unit vectors: `(1, 0, 0)`; `(0, 0.642788, 0.766044)`; `(0, -0.766044, 0.642788)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 0)`; 2: `(0, -139.7)`; 4: `(1077.275, 0)`; 6: `(1077.275, -139.7)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_rail_service_upper_right.svg).
Raw end plane 1, U=0 marks: 2: `(0, -139.7)`; 0: `(0, 0)`.
Raw end plane 2, U=0 marks: 4: `(1077.275, 0)`; 6: `(1077.275, -139.7)`.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_016` | `(1012.1875, 38.1, -95.25)` | `(1012.1875, 0, -95.25)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_027` | `(65.0875, 38.1, -95.25)` | `(65.0875, 0, -95.25)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_061` | `(65.0875, 38.1, -44.45)` | `(65.0875, 0, -44.45)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_064` | `(1012.1875, 38.1, -44.45)` | `(1012.1875, 0, -44.45)` | 13/32 | 9.525 × 63.5 | 0 |

## base_rail_top

Raw blank L × depth × thickness: **2765.425 × 139.7 × 38.1**.
World datum XYZ: `(-1130.3, 1511.0943, 2127.306654)`.
Positive L/U/V unit vectors: `(1, 0, 0)`; `(0, 0.642788, 0.766044)`; `(0, -0.766044, 0.642788)`.

Raw U=0 face marks (vertex index: L, V): 0: `(-254, 139.7)`; 2: `(-254, 0)`; 4: `(2511.425, 139.7)`; 6: `(2511.425, 0)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_rail_top.svg).

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_001` | `(65.0875, 0, 95.25)` | `(65.0875, 38.1, 95.25)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_005` | `(65.0875, 0, 44.45)` | `(65.0875, 38.1, 44.45)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_017` | `(2192.3375, 0, 44.45)` | `(2192.3375, 38.1, 44.45)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_018` | `(2192.3375, 0, 95.25)` | `(2192.3375, 38.1, 95.25)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_022` | `(976.1625, 0, 44.45)` | `(976.1625, 38.1, 44.45)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_023` | `(976.1625, 0, 95.25)` | `(976.1625, 38.1, 95.25)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_024` | `(1245.2375, 0, 95.25)` | `(1245.2375, 38.1, 95.25)` | 13/32 | 9.525 × 63.5 | 0 |
| `eoere_bolt_028` | `(1245.2375, 0, 44.45)` | `(1245.2375, 38.1, 44.45)` | 13/32 | 9.525 × 63.5 | 0 |
| `outboard_angle_left_eoere_bolt_001` | `(-150.8125, 0, 95.25)` | `(-150.8125, 38.1, 95.25)` | 13/32 | 9.525 × 76.2 | 12.7 |
| `outboard_angle_left_eoere_bolt_005` | `(-150.8125, 0, 44.45)` | `(-150.8125, 38.1, 44.45)` | 13/32 | 9.525 × 76.2 | 12.7 |
| `outboard_angle_right_eoere_bolt_017` | `(2408.2375, 0, 44.45)` | `(2408.2375, 38.1, 44.45)` | 13/32 | 9.525 × 76.2 | 12.7 |
| `outboard_angle_right_eoere_bolt_018` | `(2408.2375, 0, 95.25)` | `(2408.2375, 38.1, 95.25)` | 13/32 | 9.525 × 76.2 | 12.7 |

## base_side_left

Raw blank L × depth × thickness: **2570.726012 × 139.7 × 88.9**.
World datum XYZ: `(-1130.3, -175.7, 277)`.
Positive L/U/V unit vectors: `(0, 0.642788, 0.766044)`; `(-1, 0, 0)`; `(0, -0.766044, 0.642788)`.

Raw U=0 face marks (vertex index: L, V): 5: `(0, 0)`; 6: `(43.9695, 36.894791)`; 7: `(86.263813, -102.805209)`; 8: `(2501.667606, 36.894792)`; 9: `(2501.667606, -102.805208)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_side_left.svg).

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_006` | `(2436.580106, 0, -7.555208)` | `(2436.580106, 88.9, -7.555208)` | 13/32 | 9.525 × 120.65 | 0 |
| `eoere_bolt_010` | `(2436.580106, 0, -58.355208)` | `(2436.580106, 88.9, -58.355208)` | 13/32 | 9.525 × 120.65 | 0 |
| `eoere_bolt_032` | `(325.980106, 0, -58.355209)` | `(325.980106, 88.9, -58.355209)` | 13/32 | 9.525 × 120.65 | 0 |
| `eoere_bolt_036` | `(325.980106, 0, -7.555209)` | `(325.980106, 88.9, -7.555209)` | 13/32 | 9.525 × 120.65 | 0 |
| `eoere_bolt_043` | `(1151.430106, 0, -7.555208)` | `(1151.430106, 88.9, -7.555208)` | 13/32 | 9.525 × 120.65 | 0 |
| `eoere_bolt_047` | `(1151.430106, 0, -58.355208)` | `(1151.430106, 88.9, -58.355208)` | 13/32 | 9.525 × 120.65 | 0 |
| `eoere_bolt_051` | `(1463.755106, 0, -58.355208)` | `(1463.755106, 88.9, -58.355208)` | 13/32 | 9.525 × 120.65 | 0 |
| `eoere_bolt_055` | `(1463.755106, 0, -7.555208)` | `(1463.755106, 88.9, -7.555208)` | 13/32 | 9.525 × 120.65 | 0 |
| `eoere_bolt_071` | `(108.024162, 0, -27.480008)` | `(108.024162, 88.9, -27.480008)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `lumber_leg_bolt_left_1` | `(1964.60552, 0, -49.764222)` | `(1964.60552, 88.9, -49.764222)` | 17/32 | 12.7 × 215.9 | 0 |

## base_side_right

Raw blank L × depth × thickness: **2570.726012 × 139.7 × 88.9**.
World datum XYZ: `(1216.025, -175.7, 277)`.
Positive L/U/V unit vectors: `(0, 0.642788, 0.766044)`; `(-1, 0, 0)`; `(0, -0.766044, 0.642788)`.

Raw U=0 face marks (vertex index: L, V): 5: `(0, 0)`; 6: `(43.9695, 36.894791)`; 7: `(86.263813, -102.805209)`; 8: `(2501.667606, 36.894792)`; 9: `(2501.667606, -102.805208)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/base_side_right.svg).

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_009` | `(2436.580106, 88.9, -7.555208)` | `(2436.580106, 0, -7.555208)` | 13/32 | 9.525 × 120.65 | 0 |
| `eoere_bolt_013` | `(2436.580106, 88.9, -58.355208)` | `(2436.580106, 0, -58.355208)` | 13/32 | 9.525 × 120.65 | 0 |
| `eoere_bolt_035` | `(325.980106, 88.9, -58.355209)` | `(325.980106, 0, -58.355209)` | 13/32 | 9.525 × 120.65 | 0 |
| `eoere_bolt_039` | `(325.980106, 88.9, -7.555209)` | `(325.980106, 0, -7.555209)` | 13/32 | 9.525 × 120.65 | 0 |
| `eoere_bolt_046` | `(1151.430106, 88.9, -7.555208)` | `(1151.430106, 0, -7.555208)` | 13/32 | 9.525 × 120.65 | 0 |
| `eoere_bolt_050` | `(1151.430106, 88.9, -58.355208)` | `(1151.430106, 0, -58.355208)` | 13/32 | 9.525 × 120.65 | 0 |
| `eoere_bolt_054` | `(1463.755106, 88.9, -58.355208)` | `(1463.755106, 0, -58.355208)` | 13/32 | 9.525 × 120.65 | 0 |
| `eoere_bolt_058` | `(1463.755106, 88.9, -7.555208)` | `(1463.755106, 0, -7.555208)` | 13/32 | 9.525 × 120.65 | 0 |
| `eoere_bolt_074` | `(108.024162, 88.9, -27.480008)` | `(108.024162, 0, -27.480008)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `lumber_leg_bolt_right_1` | `(1964.60552, 88.9, -49.764222)` | `(1964.60552, 0, -49.764222)` | 17/32 | 12.7 × 215.9 | 0 |

## eoere_cleat_left

Raw blank L × depth × thickness: **609.6 × 203.2 × 28.575**.
World datum XYZ: `(-1247.775, -213.8, 139.7)`.
Positive L/U/V unit vectors: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 0)`; 1: `(0, 203.2)`; 4: `(609.6, 0)`; 5: `(609.6, 203.2)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/eoere_cleat_left.svg).

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_071` | `(202.3875, 28.575, 128.5875)` | `(202.3875, 0, 128.5875)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `cleat_post_bolt_left_1` | `(34.1125, 28.575, 77.7875)` | `(34.1125, 0, 77.7875)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `cleat_post_bolt_left_2` | `(34.1125, 28.575, 128.5875)` | `(34.1125, 0, 128.5875)` | 13/32 | 9.525 × 203.2 | 25.4 |

## eoere_cleat_left_outer

Raw blank L × depth × thickness: **609.6 × 203.2 × 28.575**.
World datum XYZ: `(-1276.35, -213.8, 139.7)`.
Positive L/U/V unit vectors: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 0)`; 1: `(0, 203.2)`; 4: `(609.6, 0)`; 5: `(609.6, 203.2)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/eoere_cleat_left_outer.svg).

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_071` | `(202.3875, 28.575, 128.5875)` | `(202.3875, 0, 128.5875)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `cleat_post_bolt_left_1` | `(34.1125, 28.575, 77.7875)` | `(34.1125, 0, 77.7875)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `cleat_post_bolt_left_2` | `(34.1125, 28.575, 128.5875)` | `(34.1125, 0, 128.5875)` | 13/32 | 9.525 × 203.2 | 25.4 |

## eoere_cleat_right

Raw blank L × depth × thickness: **609.6 × 203.2 × 28.575**.
World datum XYZ: `(1216.025, -213.8, 139.7)`.
Positive L/U/V unit vectors: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 0)`; 1: `(0, 203.2)`; 4: `(609.6, 0)`; 5: `(609.6, 203.2)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/eoere_cleat_right.svg).

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_074` | `(202.3875, 0, 128.5875)` | `(202.3875, 28.575, 128.5875)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `cleat_post_bolt_right_1` | `(34.1125, 0, 77.7875)` | `(34.1125, 28.575, 77.7875)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `cleat_post_bolt_right_2` | `(34.1125, 0, 128.5875)` | `(34.1125, 28.575, 128.5875)` | 13/32 | 9.525 × 203.2 | 25.4 |

## eoere_cleat_right_outer

Raw blank L × depth × thickness: **609.6 × 203.2 × 28.575**.
World datum XYZ: `(1244.6, -213.8, 139.7)`.
Positive L/U/V unit vectors: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

Raw U=0 face marks (vertex index: L, V): 0: `(0, 0)`; 1: `(0, 203.2)`; 4: `(609.6, 0)`; 5: `(609.6, 203.2)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/eoere_cleat_right_outer.svg).

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `eoere_bolt_074` | `(202.3875, 0, 128.5875)` | `(202.3875, 28.575, 128.5875)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `cleat_post_bolt_right_1` | `(34.1125, 0, 77.7875)` | `(34.1125, 28.575, 77.7875)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `cleat_post_bolt_right_2` | `(34.1125, 0, 128.5875)` | `(34.1125, 28.575, 128.5875)` | 13/32 | 9.525 × 203.2 | 25.4 |

## lumber_leg_left

Raw blank L × depth × thickness: **2028.462988 × 139.7 × 88.9**.
World datum XYZ: `(-1308.1, 1639.946483, 0)`.
Positive L/U/V unit vectors: `(0, -0.239152, 0.970982)`; `(1, 0, 0)`; `(0, 0.970982, 0.239152)`.

Raw U=0 face marks (vertex index: L, V): 0: `(1886.917692, -139.7)`; 1: `(1989.026085, 0)`; 2: `(34.407955, -139.7)`; 3: `(0, 0)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/lumber_leg_left.svg).
Raw end plane 1, U=0 marks: 1: `(1989.026085, 0)`; 0: `(1886.917692, -139.7)`.
Raw end plane 2, U=0 marks: 2: `(34.407955, -139.7)`; 3: `(0, 0)`.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `lumber_leg_bolt_left_1` | `(1822.298142, 88.9, -81.252626)` | `(1822.298142, 0, -81.252626)` | 17/32 | 12.7 × 215.9 | 0 |
| `rail_rear_bolt_left_1` | `(88.269485, 50.8, -63.863974)` | `(88.269485, 0, -63.863974)` | 13/32 | 9.525 × 114.3 | 0 |
| `outboard_leg_lap_left_-1` | `(977.715031, 76.2, -69.85)` | `(977.715031, 0, -69.85)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `outboard_leg_lap_left_1` | `(1028.515031, 76.2, -69.85)` | `(1028.515031, 0, -69.85)` | 13/32 | 9.525 × 203.2 | 25.4 |

## lumber_leg_right

Raw blank L × depth × thickness: **2028.462988 × 139.7 × 88.9**.
World datum XYZ: `(1216.025, 1639.946483, 0)`.
Positive L/U/V unit vectors: `(0, -0.239152, 0.970982)`; `(1, 0, 0)`; `(0, 0.970982, 0.239152)`.

Raw U=0 face marks (vertex index: L, V): 0: `(1886.917692, -139.7)`; 1: `(1989.026085, 0)`; 2: `(34.407955, -139.7)`; 3: `(0, 0)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/lumber_leg_right.svg).
Raw end plane 1, U=0 marks: 1: `(1989.026085, 0)`; 0: `(1886.917692, -139.7)`.
Raw end plane 2, U=0 marks: 2: `(34.407955, -139.7)`; 3: `(0, 0)`.

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `lumber_leg_bolt_right_1` | `(1822.298142, 0, -81.252626)` | `(1822.298142, 88.9, -81.252626)` | 17/32 | 12.7 × 215.9 | 0 |
| `rail_rear_bolt_right_1` | `(88.269485, 38.1, -63.863974)` | `(88.269485, 88.9, -63.863974)` | 13/32 | 9.525 × 114.3 | 0 |
| `outboard_leg_lap_right_-1` | `(977.715031, 12.7, -69.85)` | `(977.715031, 88.9, -69.85)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `outboard_leg_lap_right_1` | `(1028.515031, 12.7, -69.85)` | `(1028.515031, 88.9, -69.85)` | 13/32 | 9.525 × 203.2 | 25.4 |

## outboard_knee_left

Raw blank L × depth × thickness: **1468.033399 × 139.7 × 38.1**.
World datum XYZ: `(-1365.25, 1377.562948, 1589.695766)`.
Positive L/U/V unit vectors: `(0, 0.071507, 0.99744)`; `(-1, 0, 0)`; `(0, -0.99744, 0.071507)`.

Raw U=-19.05 face marks (vertex index: L, V): 0: `(-734.016699, 69.85)`; 1: `(-734.016699, -69.85)`; 4: `(559.885456, -69.85)`; 5: `(661.009441, 69.85)`; 6: `(-663.724176, -8.219778)`; 7: `(-615.393276, 7.425161)`; 8: `(513.581003, -20.972503)`; 9: `(543.368342, 20.177886)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/outboard_knee_left.svg).

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `outboard_angle_left_eoere_bolt_010` | `(519.12303, -19.05, -20.575194)` | `(519.12303, 19.05, -20.575194)` | 13/32 | 9.525 × 76.2 | 12.7 |
| `outboard_leg_lap_left_-1` | `(-658.182149, -19.05, -7.82247)` | `(-658.182149, 19.05, -7.82247)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `outboard_leg_lap_left_1` | `(-609.85125, -19.05, 7.82247)` | `(-609.85125, 19.05, 7.82247)` | 13/32 | 9.525 × 203.2 | 25.4 |

## outboard_knee_right

Raw blank L × depth × thickness: **1468.033399 × 139.7 × 38.1**.
World datum XYZ: `(1362.075, 1377.562948, 1589.695766)`.
Positive L/U/V unit vectors: `(0, 0.071507, 0.99744)`; `(1, 0, 0)`; `(0, 0.99744, -0.071507)`.

Raw U=-19.05 face marks (vertex index: L, V): 0: `(-734.016699, 69.85)`; 1: `(-734.016699, -69.85)`; 4: `(661.009441, -69.85)`; 5: `(559.885456, 69.85)`; 6: `(-604.309223, -8.219778)`; 7: `(-652.640123, 7.425161)`; 8: `(554.452396, -20.972503)`; 9: `(524.665057, 20.177886)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/outboard_knee_right.svg).

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `outboard_angle_right_eoere_bolt_013` | `(519.12303, -19.05, 20.575194)` | `(519.12303, 19.05, 20.575194)` | 13/32 | 9.525 × 76.2 | 12.7 |
| `outboard_leg_lap_right_-1` | `(-658.182149, -19.05, 7.82247)` | `(-658.182149, 19.05, 7.82247)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `outboard_leg_lap_right_1` | `(-609.85125, -19.05, -7.82247)` | `(-609.85125, 19.05, -7.82247)` | 13/32 | 9.525 × 203.2 | 25.4 |

## outboard_leg_packer_left

Raw blank L × depth × thickness: **200 × 139.7 × 38.1**.
World datum XYZ: `(-1327.15, 1332.22658, 957.302068)`.
Positive L/U/V unit vectors: `(0, -0.239152, 0.970982)`; `(-1, 0, 0)`; `(0, -0.970982, -0.239152)`.

Raw U=-19.05 face marks (vertex index: L, V): 0: `(-100, 69.85)`; 1: `(-100, -69.85)`; 4: `(100, -69.85)`; 5: `(100, 69.85)`; 6: `(-30.79502, 1.328787)`; 7: `(20.00498, 1.328787)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/outboard_leg_packer_left.svg).

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `outboard_leg_lap_left_-1` | `(-25.4, -19.05, 0)` | `(-25.4, 19.05, 0)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `outboard_leg_lap_left_1` | `(25.4, -19.05, 0)` | `(25.4, 19.05, 0)` | 13/32 | 9.525 × 203.2 | 25.4 |

## outboard_leg_packer_right

Raw blank L × depth × thickness: **200 × 139.7 × 38.1**.
World datum XYZ: `(1323.975, 1332.22658, 957.302068)`.
Positive L/U/V unit vectors: `(0, -0.239152, 0.970982)`; `(1, 0, 0)`; `(0, 0.970982, 0.239152)`.

Raw U=-19.05 face marks (vertex index: L, V): 0: `(-100, 69.85)`; 1: `(-100, -69.85)`; 4: `(100, -69.85)`; 5: `(100, 69.85)`; 6: `(-20.00498, 1.328787)`; 7: `(30.79502, 1.328787)`.

[Dimensioned raw-end and drill sheet](paired-frame-v2/drawings/outboard_leg_packer_right.svg).

| Axis | Entry (L, U, V) | Exit (L, U, V) | Bit (in) | Selected bolt Ø × underhead (mm) | Nut-side spacer (mm) |
| --- | --- | --- | --- | --- | --- |
| `outboard_leg_lap_right_-1` | `(-25.4, -19.05, 0)` | `(-25.4, 19.05, 0)` | 13/32 | 9.525 × 203.2 | 25.4 |
| `outboard_leg_lap_right_1` | `(25.4, -19.05, 0)` | `(25.4, 19.05, 0)` | 13/32 | 9.525 × 203.2 | 25.4 |

## Reproduction

```sh
uv run python -m scripts.eoere_builder_layout --check
uv run pytest -q tests/test_eoere_builder_layout.py
```

Use `--write` after reviewing changed source revisions. This presentation
adds no cuts, holes, hardware, capacity, observed fit or release.
