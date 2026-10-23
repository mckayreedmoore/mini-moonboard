# Current metric member and receiver review

Applies to `eoere-retained-frame-trimmed-three-quarter-v3`: 20 sawn members and four independent plywood leaves.

Use the [assembly review](../builder-plan.md) and [engineering disposition](../README.md). Retained exceedances do not authorize their affected operation. Actual/Disposition cells remain blank.

US lumber sections remain unchanged. All coordinates and cuts below are millimetres. Decimal precision preserves nominal geometry; it is not a cutting tolerance. L follows grain, U/V follow each member's listed basis. The header uses U across depth and V across thickness.

The [stock allocation](stock-nesting.csv) uses13 sticks/150 nominal board feet, including6mm trim at each end and3.175mm kerf per cut. Check actual usable stock before cutting. The four609.6×203.2mm cleat blanks fit side by side across one4×4 sheet with their609.6mm directions parallel to its marked strength axis; do not arrange two609.6mm blanks end to end across1219.2mm.

[Hardware totals](hardware-totals.csv) · [92 proposed stacks](hardware-planning.csv) · [112 receiver occurrences](layout-receivers.csv) · [92 drill setups](drilling-review.csv). Wood bit diameters are10.31875mm (13/32in) and13.49375mm (17/32in); nominal10mm factory angle holes remain separate. The six long cleat stacks use three12.7mm factory spacers each.

## base_floor_left

Blank L × depth × thickness: **1815.646483 × 139.7 × 38.1 mm**. [Dimension sheet](drawings/base_floor_left.svg).

World datum XYZ: `(-1257.3, -175.7, 139.7)`. Positive L/U/V: `(0, 1, 0)`; `(1, 0, 0)`; `(0, 0, -1)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `rail_front_bolt_left_1` | `(80, 38.1, 89.7)` | `(80, 0, 89.7)` |
| `rail_front_bolt_left_2` | `(80, 38.1, 39.7)` | `(80, 0, 39.7)` |
| `rail_rear_bolt_left_1` | `(1732.525893, 38.1, 69.265089)` | `(1732.525893, 0, 69.265089)` |

## base_floor_right

Blank L × depth × thickness: **1815.646483 × 139.7 × 38.1 mm**. [Dimension sheet](drawings/base_floor_right.svg).

World datum XYZ: `(1216.025, -175.7, 139.7)`. Positive L/U/V: `(0, 1, 0)`; `(1, 0, 0)`; `(0, 0, -1)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `rail_front_bolt_right_1` | `(80, 0, 89.7)` | `(80, 38.1, 89.7)` |
| `rail_front_bolt_right_2` | `(80, 0, 39.7)` | `(80, 38.1, 39.7)` |
| `rail_rear_bolt_right_1` | `(1732.525893, 0, 69.265089)` | `(1732.525893, 38.1, 69.265089)` |

## base_header

Blank L × depth × thickness: **2435.225 × 139.7 × 38.1 mm**. [Dimension sheet](drawings/base_header.svg).

World datum XYZ: `(-1219.2, -175.7, 238.9)`. Positive L/U/V: `(1, 0, 0)`; `(0, 1, 0)`; `(0, 0, 1)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_065` | `(1065.0625, 44.45, 38.1)` | `(1065.0625, 44.45, 0)` |
| `eoere_bolt_066` | `(1065.0625, 95.25, 38.1)` | `(1065.0625, 95.25, 0)` |
| `eoere_bolt_079` | `(1334.1375, 95.25, 38.1)` | `(1334.1375, 95.25, 0)` |
| `eoere_bolt_080` | `(1334.1375, 44.45, 38.1)` | `(1334.1375, 44.45, 0)` |
| `eoere_bolt_081` | `(153.9875, 90.4875, 38.1)` | `(153.9875, 90.4875, 0)` |
| `eoere_bolt_082` | `(153.9875, 39.6875, 38.1)` | `(153.9875, 39.6875, 0)` |
| `eoere_bolt_083` | `(2281.2375, 39.6875, 38.1)` | `(2281.2375, 39.6875, 0)` |
| `eoere_bolt_084` | `(2281.2375, 90.4875, 38.1)` | `(2281.2375, 90.4875, 0)` |

## base_post_center_left

Blank L × depth × thickness: **238.9 × 139.7 × 38.1 mm**. [Dimension sheet](drawings/base_post_center_left.svg).

World datum XYZ: `(-89.05, -175.7, 0)`. Positive L/U/V: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_075` | `(173.8125, 0, 95.25)` | `(173.8125, 38.1, 95.25)` |
| `eoere_bolt_077` | `(173.8125, 0, 44.45)` | `(173.8125, 38.1, 44.45)` |

## base_post_center_right

Blank L × depth × thickness: **238.9 × 139.7 × 38.1 mm**. [Dimension sheet](drawings/base_post_center_right.svg).

World datum XYZ: `(11.75, -175.7, 0)`. Positive L/U/V: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_076` | `(173.8125, 38.1, 95.25)` | `(173.8125, 0, 95.25)` |
| `eoere_bolt_078` | `(173.8125, 38.1, 44.45)` | `(173.8125, 0, 44.45)` |

## base_post_outer_left

Blank L × depth × thickness: **238.9 × 139.7 × 88.9 mm**. [Dimension sheet](drawings/base_post_outer_left.svg).

World datum XYZ: `(-1219.2, -175.7, 0)`. Positive L/U/V: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `cleat_post_bolt_left_1` | `(173.8125, 88.9, 39.6875)` | `(173.8125, 0, 39.6875)` |
| `cleat_post_bolt_left_2` | `(173.8125, 88.9, 90.4875)` | `(173.8125, 0, 90.4875)` |
| `rail_front_bolt_left_1` | `(50, 88.9, 80)` | `(50, 0, 80)` |
| `rail_front_bolt_left_2` | `(100, 88.9, 80)` | `(100, 0, 80)` |

## base_post_outer_right

Blank L × depth × thickness: **238.9 × 139.7 × 88.9 mm**. [Dimension sheet](drawings/base_post_outer_right.svg).

World datum XYZ: `(1127.125, -175.7, 0)`. Positive L/U/V: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `cleat_post_bolt_right_1` | `(173.8125, 0, 39.6875)` | `(173.8125, 88.9, 39.6875)` |
| `cleat_post_bolt_right_2` | `(173.8125, 0, 90.4875)` | `(173.8125, 88.9, 90.4875)` |
| `rail_front_bolt_right_1` | `(50, 0, 80)` | `(50, 88.9, 80)` |
| `rail_front_bolt_right_2` | `(100, 0, 80)` | `(100, 88.9, 80)` |

## base_principal_center_left

Blank L × depth × thickness: **2532.626012 × 139.7 × 38.1 mm**. [Dimension sheet](drawings/base_principal_center_left.svg).

World datum XYZ: `(-50.95, -182.7, 277)`. Positive L/U/V: `(0, 0.642788, 0.766044)`; `(-1, 0, 0)`; `(0, -0.766044, 0.642788)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_007` | `(2441.079619, 38.1, -12.917519)` | `(2441.079619, 0, -12.917519)` |
| `eoere_bolt_011` | `(2441.079619, 38.1, -63.717519)` | `(2441.079619, 0, -63.717519)` |
| `eoere_bolt_033` | `(330.479619, 38.1, -63.71752)` | `(330.479619, 0, -63.71752)` |
| `eoere_bolt_037` | `(330.479619, 38.1, -12.91752)` | `(330.479619, 0, -12.91752)` |
| `eoere_bolt_044` | `(1155.929619, 38.1, -12.917519)` | `(1155.929619, 0, -12.917519)` |
| `eoere_bolt_048` | `(1155.929619, 38.1, -63.717519)` | `(1155.929619, 0, -63.717519)` |
| `eoere_bolt_052` | `(1468.254619, 38.1, -63.717519)` | `(1468.254619, 0, -63.717519)` |
| `eoere_bolt_056` | `(1468.254619, 38.1, -12.917519)` | `(1468.254619, 0, -12.917519)` |
| `eoere_bolt_072` | `(115.584951, 38.1, -36.490606)` | `(115.584951, 0, -36.490606)` |

## base_principal_center_right

Blank L × depth × thickness: **2532.626012 × 139.7 × 38.1 mm**. [Dimension sheet](drawings/base_principal_center_right.svg).

World datum XYZ: `(49.85, -182.7, 277)`. Positive L/U/V: `(0, 0.642788, 0.766044)`; `(-1, 0, 0)`; `(0, -0.766044, 0.642788)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_008` | `(2441.079619, 0, -12.917519)` | `(2441.079619, 38.1, -12.917519)` |
| `eoere_bolt_012` | `(2441.079619, 0, -63.717519)` | `(2441.079619, 38.1, -63.717519)` |
| `eoere_bolt_034` | `(330.479619, 0, -63.71752)` | `(330.479619, 38.1, -63.71752)` |
| `eoere_bolt_038` | `(330.479619, 0, -12.91752)` | `(330.479619, 38.1, -12.91752)` |
| `eoere_bolt_045` | `(1155.929619, 0, -12.917519)` | `(1155.929619, 38.1, -12.917519)` |
| `eoere_bolt_049` | `(1155.929619, 0, -63.717519)` | `(1155.929619, 38.1, -63.717519)` |
| `eoere_bolt_053` | `(1468.254619, 0, -63.717519)` | `(1468.254619, 38.1, -63.717519)` |
| `eoere_bolt_057` | `(1468.254619, 0, -12.917519)` | `(1468.254619, 38.1, -12.917519)` |
| `eoere_bolt_073` | `(115.584951, 0, -36.490606)` | `(115.584951, 38.1, -36.490606)` |

## base_rail_bottom_left

Blank L × depth × thickness: **1041.25 × 139.7 × 38.1 mm**. [Dimension sheet](drawings/base_rail_bottom_left.svg).

World datum XYZ: `(-1130.3, 46.261686, 381.587123)`. Positive L/U/V: `(1, 0, 0)`; `(0, 0.642788, 0.766044)`; `(0, -0.766044, 0.642788)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_002` | `(65.0875, 38.1, 44.45)` | `(65.0875, 0, 44.45)` |
| `eoere_bolt_019` | `(976.1625, 38.1, 44.45)` | `(976.1625, 0, 44.45)` |
| `eoere_bolt_029` | `(65.0875, 38.1, 95.25)` | `(65.0875, 0, 95.25)` |
| `eoere_bolt_040` | `(976.1625, 38.1, 95.25)` | `(976.1625, 0, 95.25)` |

## base_rail_bottom_right

Blank L × depth × thickness: **1077.275 × 139.7 × 38.1 mm**. [Dimension sheet](drawings/base_rail_bottom_right.svg).

World datum XYZ: `(49.85, 46.261686, 381.587123)`. Positive L/U/V: `(1, 0, 0)`; `(0, 0.642788, 0.766044)`; `(0, -0.766044, 0.642788)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_014` | `(1012.1875, 38.1, 44.45)` | `(1012.1875, 0, 44.45)` |
| `eoere_bolt_025` | `(65.0875, 38.1, 44.45)` | `(65.0875, 0, 44.45)` |
| `eoere_bolt_059` | `(65.0875, 38.1, 95.25)` | `(65.0875, 0, 95.25)` |
| `eoere_bolt_062` | `(1012.1875, 38.1, 95.25)` | `(1012.1875, 0, 95.25)` |

## base_rail_service_lower_left

Blank L × depth × thickness: **1041.25 × 139.7 × 38.1 mm**. [Dimension sheet](drawings/base_rail_service_lower_left.svg).

World datum XYZ: `(-1130.3, 685.015803, 1142.824638)`. Positive L/U/V: `(1, 0, 0)`; `(0, 0.642788, 0.766044)`; `(0, -0.766044, 0.642788)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_003` | `(65.0875, 0, 44.45)` | `(65.0875, 38.1, 44.45)` |
| `eoere_bolt_020` | `(976.1625, 0, 44.45)` | `(976.1625, 38.1, 44.45)` |
| `eoere_bolt_030` | `(65.0875, 0, 95.25)` | `(65.0875, 38.1, 95.25)` |
| `eoere_bolt_041` | `(976.1625, 0, 95.25)` | `(976.1625, 38.1, 95.25)` |

## base_rail_service_lower_right

Blank L × depth × thickness: **1077.275 × 139.7 × 38.1 mm**. [Dimension sheet](drawings/base_rail_service_lower_right.svg).

World datum XYZ: `(49.85, 685.015803, 1142.824638)`. Positive L/U/V: `(1, 0, 0)`; `(0, 0.642788, 0.766044)`; `(0, -0.766044, 0.642788)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_015` | `(1012.1875, 0, 44.45)` | `(1012.1875, 38.1, 44.45)` |
| `eoere_bolt_026` | `(65.0875, 0, 44.45)` | `(65.0875, 38.1, 44.45)` |
| `eoere_bolt_060` | `(65.0875, 0, 95.25)` | `(65.0875, 38.1, 95.25)` |
| `eoere_bolt_063` | `(1012.1875, 0, 95.25)` | `(1012.1875, 38.1, 95.25)` |

## base_rail_service_upper_left

Blank L × depth × thickness: **1041.25 × 139.7 × 38.1 mm**. [Dimension sheet](drawings/base_rail_service_upper_left.svg).

World datum XYZ: `(-1130.3, 670.592949, 1342.970769)`. Positive L/U/V: `(1, 0, 0)`; `(0, 0.642788, 0.766044)`; `(0, -0.766044, 0.642788)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_004` | `(65.0875, 38.1, -95.25)` | `(65.0875, 0, -95.25)` |
| `eoere_bolt_021` | `(976.1625, 38.1, -95.25)` | `(976.1625, 0, -95.25)` |
| `eoere_bolt_031` | `(65.0875, 38.1, -44.45)` | `(65.0875, 0, -44.45)` |
| `eoere_bolt_042` | `(976.1625, 38.1, -44.45)` | `(976.1625, 0, -44.45)` |

## base_rail_service_upper_right

Blank L × depth × thickness: **1077.275 × 139.7 × 38.1 mm**. [Dimension sheet](drawings/base_rail_service_upper_right.svg).

World datum XYZ: `(49.85, 670.592949, 1342.970769)`. Positive L/U/V: `(1, 0, 0)`; `(0, 0.642788, 0.766044)`; `(0, -0.766044, 0.642788)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_016` | `(1012.1875, 38.1, -95.25)` | `(1012.1875, 0, -95.25)` |
| `eoere_bolt_027` | `(65.0875, 38.1, -95.25)` | `(65.0875, 0, -95.25)` |
| `eoere_bolt_061` | `(65.0875, 38.1, -44.45)` | `(65.0875, 0, -44.45)` |
| `eoere_bolt_064` | `(1012.1875, 38.1, -44.45)` | `(1012.1875, 0, -44.45)` |

## base_rail_top

Blank L × depth × thickness: **2257.425 × 139.7 × 38.1 mm**. [Dimension sheet](drawings/base_rail_top.svg).

World datum XYZ: `(-1130.3, 1511.0943, 2127.306654)`. Positive L/U/V: `(1, 0, 0)`; `(0, 0.642788, 0.766044)`; `(0, -0.766044, 0.642788)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_001` | `(65.0875, 0, 95.25)` | `(65.0875, 38.1, 95.25)` |
| `eoere_bolt_005` | `(65.0875, 0, 44.45)` | `(65.0875, 38.1, 44.45)` |
| `eoere_bolt_017` | `(2192.3375, 0, 44.45)` | `(2192.3375, 38.1, 44.45)` |
| `eoere_bolt_018` | `(2192.3375, 0, 95.25)` | `(2192.3375, 38.1, 95.25)` |
| `eoere_bolt_022` | `(976.1625, 0, 44.45)` | `(976.1625, 38.1, 44.45)` |
| `eoere_bolt_023` | `(976.1625, 0, 95.25)` | `(976.1625, 38.1, 95.25)` |
| `eoere_bolt_024` | `(1245.2375, 0, 95.25)` | `(1245.2375, 38.1, 95.25)` |
| `eoere_bolt_028` | `(1245.2375, 0, 44.45)` | `(1245.2375, 38.1, 44.45)` |

## base_side_left

Blank L × depth × thickness: **2501.667606 × 139.700001 × 88.9 mm**. [Dimension sheet](drawings/base_side_left.svg).

World datum XYZ: `(-1130.3, -175.7, 277)`. Positive L/U/V: `(0, 0.642788, 0.766044)`; `(-1, 0, 0)`; `(0, -0.766044, 0.642788)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_006` | `(2436.580106, 0, -7.555208)` | `(2436.580106, 88.9, -7.555208)` |
| `eoere_bolt_010` | `(2436.580106, 0, -58.355208)` | `(2436.580106, 88.9, -58.355208)` |
| `eoere_bolt_032` | `(325.980106, 0, -58.355209)` | `(325.980106, 88.9, -58.355209)` |
| `eoere_bolt_036` | `(325.980106, 0, -7.555209)` | `(325.980106, 88.9, -7.555209)` |
| `eoere_bolt_043` | `(1151.430106, 0, -7.555208)` | `(1151.430106, 88.9, -7.555208)` |
| `eoere_bolt_047` | `(1151.430106, 0, -58.355208)` | `(1151.430106, 88.9, -58.355208)` |
| `eoere_bolt_051` | `(1463.755106, 0, -58.355208)` | `(1463.755106, 88.9, -58.355208)` |
| `eoere_bolt_055` | `(1463.755106, 0, -7.555208)` | `(1463.755106, 88.9, -7.555208)` |
| `eoere_bolt_071` | `(108.024162, 0, -27.480008)` | `(108.024162, 88.9, -27.480008)` |
| `lumber_leg_bolt_left_1` | `(1964.60552, 0, -49.764222)` | `(1964.60552, 88.9, -49.764222)` |

## base_side_right

Blank L × depth × thickness: **2501.667606 × 139.700001 × 88.9 mm**. [Dimension sheet](drawings/base_side_right.svg).

World datum XYZ: `(1216.025, -175.7, 277)`. Positive L/U/V: `(0, 0.642788, 0.766044)`; `(-1, 0, 0)`; `(0, -0.766044, 0.642788)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_009` | `(2436.580106, 88.9, -7.555208)` | `(2436.580106, 0, -7.555208)` |
| `eoere_bolt_013` | `(2436.580106, 88.9, -58.355208)` | `(2436.580106, 0, -58.355208)` |
| `eoere_bolt_035` | `(325.980106, 88.9, -58.355209)` | `(325.980106, 0, -58.355209)` |
| `eoere_bolt_039` | `(325.980106, 88.9, -7.555209)` | `(325.980106, 0, -7.555209)` |
| `eoere_bolt_046` | `(1151.430106, 88.9, -7.555208)` | `(1151.430106, 0, -7.555208)` |
| `eoere_bolt_050` | `(1151.430106, 88.9, -58.355208)` | `(1151.430106, 0, -58.355208)` |
| `eoere_bolt_054` | `(1463.755106, 88.9, -58.355208)` | `(1463.755106, 0, -58.355208)` |
| `eoere_bolt_058` | `(1463.755106, 88.9, -7.555208)` | `(1463.755106, 0, -7.555208)` |
| `eoere_bolt_074` | `(108.024162, 88.9, -27.480008)` | `(108.024162, 0, -27.480008)` |
| `lumber_leg_bolt_right_1` | `(1964.60552, 88.9, -49.764222)` | `(1964.60552, 0, -49.764222)` |

## eoere_cleat_left

Blank L × depth × thickness: **609.6 × 203.2 × 19.05 mm**. [Dimension sheet](drawings/eoere_cleat_left.svg).

World datum XYZ: `(-1238.25, -213.8, 139.7)`. Positive L/U/V: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

Finished perimeter, ordered (L,V) points inmm: (194.698106, 38.1); (0, 38.1); (0, 177.8); (137.3, 177.8); (137.3, 172.302669); (174.122005, 203.2); (391.456624, 203.2). Keep its concave corner and marked strength direction. The larger blank is not the finished outline.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_071` | `(202.3875, 19.05, 128.5875)` | `(202.3875, 0, 128.5875)` |
| `cleat_post_bolt_left_1` | `(34.1125, 19.05, 77.7875)` | `(34.1125, 0, 77.7875)` |
| `cleat_post_bolt_left_2` | `(34.1125, 19.05, 128.5875)` | `(34.1125, 0, 128.5875)` |

## eoere_cleat_left_outer

Blank L × depth × thickness: **609.6 × 203.2 × 19.05 mm**. [Dimension sheet](drawings/eoere_cleat_left_outer.svg).

World datum XYZ: `(-1257.3, -213.8, 139.7)`. Positive L/U/V: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

Finished perimeter, ordered (L,V) points inmm: (194.698106, 38.1); (0, 38.1); (0, 177.8); (137.3, 177.8); (137.3, 172.302669); (174.122005, 203.2); (391.456624, 203.2). Keep its concave corner and marked strength direction. The larger blank is not the finished outline.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_071` | `(202.3875, 19.05, 128.5875)` | `(202.3875, 0, 128.5875)` |
| `cleat_post_bolt_left_1` | `(34.1125, 19.05, 77.7875)` | `(34.1125, 0, 77.7875)` |
| `cleat_post_bolt_left_2` | `(34.1125, 19.05, 128.5875)` | `(34.1125, 0, 128.5875)` |

## eoere_cleat_right

Blank L × depth × thickness: **609.6 × 203.2 × 19.05 mm**. [Dimension sheet](drawings/eoere_cleat_right.svg).

World datum XYZ: `(1216.025, -213.8, 139.7)`. Positive L/U/V: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

Finished perimeter, ordered (L,V) points inmm: (194.698106, 38.1); (0, 38.1); (0, 177.8); (137.3, 177.8); (137.3, 172.302669); (174.122005, 203.2); (391.456624, 203.2). Keep its concave corner and marked strength direction. The larger blank is not the finished outline.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_074` | `(202.3875, 0, 128.5875)` | `(202.3875, 19.05, 128.5875)` |
| `cleat_post_bolt_right_1` | `(34.1125, 0, 77.7875)` | `(34.1125, 19.05, 77.7875)` |
| `cleat_post_bolt_right_2` | `(34.1125, 0, 128.5875)` | `(34.1125, 19.05, 128.5875)` |

## eoere_cleat_right_outer

Blank L × depth × thickness: **609.6 × 203.2 × 19.05 mm**. [Dimension sheet](drawings/eoere_cleat_right_outer.svg).

World datum XYZ: `(1235.075, -213.8, 139.7)`. Positive L/U/V: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

Finished perimeter, ordered (L,V) points inmm: (194.698106, 38.1); (0, 38.1); (0, 177.8); (137.3, 177.8); (137.3, 172.302669); (174.122005, 203.2); (391.456624, 203.2). Keep its concave corner and marked strength direction. The larger blank is not the finished outline.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `eoere_bolt_074` | `(202.3875, 0, 128.5875)` | `(202.3875, 19.05, 128.5875)` |
| `cleat_post_bolt_right_1` | `(34.1125, 0, 77.7875)` | `(34.1125, 19.05, 77.7875)` |
| `cleat_post_bolt_right_2` | `(34.1125, 0, 128.5875)` | `(34.1125, 19.05, 128.5875)` |

## lumber_leg_left

Blank L × depth × thickness: **2028.462988 × 139.7 × 88.9 mm**. [Dimension sheet](drawings/lumber_leg_left.svg).

World datum XYZ: `(-1308.1, 1639.946483, 0)`. Positive L/U/V: `(0, -0.239152, 0.970982)`; `(1, 0, 0)`; `(0, 0.970982, 0.239152)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `lumber_leg_bolt_left_1` | `(1822.298142, 88.9, -81.252626)` | `(1822.298142, 0, -81.252626)` |
| `rail_rear_bolt_left_1` | `(88.269485, 50.8, -63.863974)` | `(88.269485, 0, -63.863974)` |

## lumber_leg_right

Blank L × depth × thickness: **2028.462988 × 139.7 × 88.9 mm**. [Dimension sheet](drawings/lumber_leg_right.svg).

World datum XYZ: `(1216.025, 1639.946483, 0)`. Positive L/U/V: `(0, -0.239152, 0.970982)`; `(1, 0, 0)`; `(0, 0.970982, 0.239152)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `lumber_leg_bolt_right_1` | `(1822.298142, 0, -81.252626)` | `(1822.298142, 88.9, -81.252626)` |
| `rail_rear_bolt_right_1` | `(88.269485, 38.1, -63.863974)` | `(88.269485, 88.9, -63.863974)` |
