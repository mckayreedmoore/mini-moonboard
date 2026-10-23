# Revised front-post and runner coordinates

Applies to `eoere-local-front-bolt-moves-v4`.

The two lower front bolts move from50 to60mm above the floor. Upper bolts stay100mm; all four remain80mm from the common front end. Cleat/post bolts stay at173.8125mm in their factory angle holes. Upper long-support bolts stay1/2in at their existing axes.

These four dimension sheets and the [complete receiver table](receiver-holes.csv) supersede the corresponding v3 coordinates. Other member drawings, dimensions, stock allocation and hardware remain in the [preserved packet](../owner-frame-v3/layout.md). Actual/Disposition cells stay blank. Design-review coordinates are not issued cutting/drilling instructions.

## base_floor_left

Blank L × depth × thickness: **1815.646483 × 139.7 × 38.1 mm**. [Dimension sheet](drawings/base_floor_left.svg).

World datum XYZ: `(-1257.3, -175.7, 139.7)`. Positive L/U/V: `(0, 1, 0)`; `(1, 0, 0)`; `(0, 0, -1)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `rail_front_bolt_left_1` | `(80, 38.1, 79.7)` | `(80, 0, 79.7)` |
| `rail_front_bolt_left_2` | `(80, 38.1, 39.7)` | `(80, 0, 39.7)` |
| `rail_rear_bolt_left_1` | `(1732.525893, 38.1, 69.265089)` | `(1732.525893, 0, 69.265089)` |

## base_floor_right

Blank L × depth × thickness: **1815.646483 × 139.7 × 38.1 mm**. [Dimension sheet](drawings/base_floor_right.svg).

World datum XYZ: `(1216.025, -175.7, 139.7)`. Positive L/U/V: `(0, 1, 0)`; `(1, 0, 0)`; `(0, 0, -1)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `rail_front_bolt_right_1` | `(80, 0, 79.7)` | `(80, 38.1, 79.7)` |
| `rail_front_bolt_right_2` | `(80, 0, 39.7)` | `(80, 38.1, 39.7)` |
| `rail_rear_bolt_right_1` | `(1732.525893, 0, 69.265089)` | `(1732.525893, 38.1, 69.265089)` |

## base_post_outer_left

Blank L × depth × thickness: **238.9 × 139.7 × 88.9 mm**. [Dimension sheet](drawings/base_post_outer_left.svg).

World datum XYZ: `(-1219.2, -175.7, 0)`. Positive L/U/V: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `cleat_post_bolt_left_1` | `(173.8125, 88.9, 39.6875)` | `(173.8125, 0, 39.6875)` |
| `cleat_post_bolt_left_2` | `(173.8125, 88.9, 90.4875)` | `(173.8125, 0, 90.4875)` |
| `rail_front_bolt_left_1` | `(60, 88.9, 80)` | `(60, 0, 80)` |
| `rail_front_bolt_left_2` | `(100, 88.9, 80)` | `(100, 0, 80)` |

## base_post_outer_right

Blank L × depth × thickness: **238.9 × 139.7 × 88.9 mm**. [Dimension sheet](drawings/base_post_outer_right.svg).

World datum XYZ: `(1127.125, -175.7, 0)`. Positive L/U/V: `(0, 0, 1)`; `(1, 0, 0)`; `(0, 1, 0)`.

| Axis | Entry L,U,V (mm) | Exit L,U,V (mm) |
| --- | --- | --- |
| `cleat_post_bolt_right_1` | `(173.8125, 0, 39.6875)` | `(173.8125, 88.9, 39.6875)` |
| `cleat_post_bolt_right_2` | `(173.8125, 0, 90.4875)` | `(173.8125, 88.9, 90.4875)` |
| `rail_front_bolt_right_1` | `(60, 0, 80)` | `(60, 88.9, 80)` |
| `rail_front_bolt_right_2` | `(100, 0, 80)` | `(100, 88.9, 80)` |
