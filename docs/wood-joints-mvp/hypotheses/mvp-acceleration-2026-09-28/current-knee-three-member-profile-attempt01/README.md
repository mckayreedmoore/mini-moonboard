# BG003 finished three-member profile distances

This read-only screen queried the single modeled BG003 stack for
`knee_outer_left_side_1` and `knee_outer_left_side_2` through all three
receivers: `knee_outer_left_spine`, `base_side_left`, and
`knee_outer_left_inner_frame_block`. It used the ordered receiver intervals in
the attempt04 manifest and the source-proposed receiver grain axes. The six
receiver bodies and all inputs were hash-checked before querying. The 72 rays
sample each receiver 0.01 mm inside both modeled bolt-axis interval ends and at
middepth, in both signed `g` and `e = unit(g × a)` directions. No CAD rebuild,
mesh, native mechanics run, or model change was performed.

The interval order is from the modeled underhead datum along +X: spine
1.651–39.751 mm, side member 39.751–128.651 mm, then inner frame block
128.651–217.551 mm. Each interval matched the corresponding finished STEP
vertex projection. This is the modeled interval sequence, not verified
installed head-to-nut order. The three receivers remain one physical-stack
geometry query; they are not treated as independent two-member groups.

## Source grain directions and distances

The source-proposed grains are +Z for the spine and inner frame block, and
`(0, 0.642787610, 0.766044443)` for `base_side_left`. Both modeled bolt axes
point +X. Thus `e` is +Y for the two blocks and
`(0, 0.766044443, −0.642787610)` for the side member. Distances below run from
the bolt centerline to the last material exit in the signed ray direction.

| Bolt | Receiver | Grain ray `g− / g+` (mm) | Cross-grain ray `e− / e+` (mm) |
|---|---|---:|---:|
| `knee_outer_left_side_1` | `knee_outer_left_spine` | 191.6156 / 84.6844 | 75.8219 / 63.8781 |
| `knee_outer_left_side_1` | `base_side_left` | 70.9039 / 2453.5038 | 55.2000 / 84.5000 |
| `knee_outer_left_side_1` | `knee_outer_left_inner_frame_block` | 54.3156 / 84.6844 | 69.4719 / 63.8781 |
| `knee_outer_left_side_2` | `knee_outer_left_spine` | 226.0876 / 50.2124 | 104.7474 / 34.9526 |
| `knee_outer_left_side_2` | `base_side_left` | 115.9039 / 2408.5038 | 55.2000 / 84.5000 |
| `knee_outer_left_side_2` | `knee_outer_left_inner_frame_block` | 88.7876 / 50.2124 | 98.3974 / 34.9526 |

Each reported terminal distance repeats at all three sampled thickness
stations. This is a ray-to-profile geometry result, not a load assignment,
NDS check, or resistance. In particular, a distance to an oblique terminal
plane is measured along the declared `g` or `e` ray; it is not the perpendicular
distance to that plane.

## Square, oblique and corner profiles

The spine and inner-frame-block terminal faces are square to their queried
`g/e` directions at all sampled stations: each terminal is one finite `PLANE`
face with `|n·ray| = 1.0`.

The side member has an oblique grain-end profile. Both bolts' `g−` rays
terminate at BRep face 35, the finished plane at global `z = 277.0 mm`, with
normal `(0, 0, −1)`. Relative to proposed grain, `|n·g| = 0.766044` (40° from
the ray normal). The centerline distances to that oblique plane are 70.9039 mm
for side bolt 1 and 115.9039 mm for side bolt 2. The corresponding `g+` rays
terminate on face 16, square to proposed grain (`|n·g| = 1.0`).

For side bolt 1, each `e+` ray reaches the corner where face 35 meets side
face 18. The query returns both finite faces at the same terminal point:
face 18 is square to `e+` (`|n·e| = 1.0`), while face 35 is oblique to it
(`|n·e| = 0.642788`). The distance to the corner is 84.5000 mm. This is why
69 rays have one terminal face candidate and these three side-bolt-1 `e+`
stations have two. Side bolt 2's `e+` ray reaches face 18 away from that corner
and has one square terminal face. The opposite side-member `e−` rays terminate
on face 15, square to `e−`.

All 72 terminal candidates are `PLANE` faces. The raw output records the exact
coordinates, face IDs, normals, and finite intersections. The square/oblique
classification here applies to these queried directions and stations; the
discrete sampling does not optimize a continuous minimum through receiver
thickness.

## Internal bores

Every ray begins with its modeled 7.5 mm bolt bore as a 0–3.75 mm void. Other
internal gaps are preserved separately from terminal outside faces:

- In `base_side_left`, side bolt 1 `g+` and side bolt 2 `g−` cross the other
  BG003 bolt's cylindrical bore at 41.25–48.75 mm at all three stations.
- In the inner frame block, only the middepth `e` rays cross the two additional
  cylindrical bores. Side bolt 1 has gaps 40.1281–47.6281 mm in `e+` and
  45.7219–53.2219 mm in `e−`. Side bolt 2 has gaps 11.2026–18.7026 mm in `e+`
  and 74.6474–82.1474 mm in `e−`. These are the two internal bores along +Z,
  centered at global `x = −1085.85 mm`, `y = −62.35 mm` and `−155.70 mm`
  (STEP faces 10 and 9), not terminal profile limits.
- The spine rays have no additional internal void intervals beyond each bolt's
  own bore.

The complete material intervals and all exact face hits are in
[`query.json`](query.json). The model does not establish actual lumber grain,
delivered parts, cuts, holes, loads, capacity, physical inspection, or joint
acceptance.

## Reproduction

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 taskset -c 15 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-knee-three-member-profile-attempt01/query.py
```

[`execution.json`](execution.json) records the completed run and hashes.
[`source-pins.json`](source-pins.json) records the pinned acceleration and
attempt04 sources, proposed grain inputs, helper, and finished STEP bodies.
The producer rejects input/hash changes, non-single-solid STEP bodies, grain
disagreements, missing/changed stack intervals, or STEP vertex projections
that disagree with the recorded receiver limits.
