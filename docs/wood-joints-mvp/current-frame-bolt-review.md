# Current revised-model frame-bolt review

Status: source-bound geometry screen, 2026-09-24. Current revision:
`led-clearance-2x6-runner-seated-blocks-v1`, reviewed repository commit
`b1e8707d`. This is not a bolt capacity check, a frame pass, or a release.
The owner-authorized evaluation is analysis only; every retained frame bolt
still needs a current-candidate structural recheck.

## Current identity and source binding

The current [geometry snapshot](hypotheses/evaluation-resume-2026-09-24/geometry-snapshot.json)
records 12 retained frame bolts, 12 source occupied axes, 60 installed
components (five per stack), and 72 retained bolt shapes including the 12
occupied-axis proxies. The current scene records the same 12 rows in both
`model_inventory.frame_bolts` and `starting_frame_bolts`; each row says
`candidate_recheck_status: required`.

I compared those 12 rows with the selected candidate's
[kerf-right connection axes](../floor-flush-construction-kerf-right/connection-axes.csv)
and [hardware schedule](../floor-flush-construction-kerf-right/bolt-hardware.csv).
For every row, axis ID, receiver pair, origin, direction, occupied diameter,
occupied length, nominal bolt diameter, length, and grip match the source
packet. Origin, direction, diameter, and length deltas are all zero. The
schedule below therefore identifies the current retained arrangements; it
does not inherit the earlier angle-frame load results.

| Current axis IDs | Receiver pair | Current source origin, left / right (mm) | Direction, left / right | Nominal D × L / wood grip (mm) |
| --- | --- | --- | --- | ---: |
| `lumber_leg_bolt_left_1`, `lumber_leg_bolt_right_1` | `base_side` + `lumber_leg` | (−1127.125, 1125.246, 1734.987) / (1123.950, 1125.246, 1734.987) | −X / +X | 12.7 × 203.2 / 177.8 |
| `lumber_leg_bolt_left_2`, `lumber_leg_bolt_right_2` | `base_side` + `lumber_leg` | (−1127.125, 1143.254, 1788.013) / (1123.950, 1143.254, 1788.013) | −X / +X | 12.7 × 203.2 / 177.8 |
| `rail_front_bolt_left_1`, `rail_front_bolt_right_1` | `base_post_outer` + `base_floor` | (−1179.068, −105.528, 70.172) / (1175.893, −105.528, 70.172) | −X / +X | 9.525 × 101.6 / 76.2 |
| `rail_front_bolt_left_2`, `rail_front_bolt_right_2` | `base_post_outer` + `base_floor` | (−1179.068, −77.597, 98.103) / (1175.893, −77.597, 98.103) | −X / +X | 9.525 × 101.6 / 76.2 |
| `rail_rear_bolt_left_1`, `rail_rear_bolt_right_1` | `base_floor` + `lumber_leg` | (−1217.168, 1551.000, 69.000) / (1213.993, 1551.000, 69.000) | −X / +X | 9.525 × 114.3 / 88.9 |
| `rail_rear_bolt_left_2`, `rail_rear_bolt_right_2` | `base_floor` + `lumber_leg` | (−1217.168, 1517.000, 97.500) / (1213.993, 1517.000, 97.500) | −X / +X | 9.525 × 114.3 / 88.9 |

## Which receiver geometry changed

Across the full current 92-axis block candidate, candidate bores pass through
four receivers that also host retained frame bolts: `base_side_left/right`
have ten candidate axes each, and `base_post_outer_left/right` have two each.
The four `lumber_leg_bolt_*` axes therefore share a changed `base_side`
receiver; the four `rail_front_bolt_*` axes share a changed `base_post_outer`
receiver. Neither `base_floor_left/right` nor `lumber_leg_left/right` has a
current candidate bore axis in the frozen snapshot. The snapshot's raw and
finished bounding extents for `base_side` and the outer posts match; finished
volumes include the current bores. It records no translation or section
enlargement of these members.

This whole-candidate receiver inventory is separate from changes in the final
revision step. The `led-clearance-2x6-runner-seated-blocks-v1` helper changes
the two `knee_outer_*_spine` candidate blocks and eight candidate bolt stacks;
it does not cut or replace a frame receiver or move a retained frame bolt.
The blocks change from 88.9 × 139.7 × 269.95 mm to 38.1 × 139.7 × 276.3 mm
and reach the `base_floor_*` runner tops at z = 139.7 mm. Their eight
candidate-bolt heads move inward 50.8 mm and occupied shafts shorten by
50.8 mm. The 5 mm center-block trims and G2 electrical/panel changes belong
to the predecessor revision. The earlier inner second-bolt stage changes
`base_header`, which is not a receiver for any of these twelve arrangements.

The new runner contact changes the candidate's support/load path even though
it does not cut the rear `base_floor` bolt stations. Its effect on all twelve
frame-bolt demands must come from the revised connected model; forces from an
older candidate are not transferable.

## Bounded geometric priorities

The following are parallel-X centerline spacings from the retained source
stations to the nearest current candidate bore axes in the same changed wood
receiver. They are station screens only; they are not solid-intersection,
edge-distance, or wrench-access results.

| Retained stations | Nearest current candidate axis in shared receiver | Centerline spacing in YZ (mm) | Relevant source-profile screen |
| --- | --- | ---: | --- |
| `lumber_leg_bolt_{left,right}_1` | `top_outer/clip_single_top_left_1/side_1`; `top_outer/clip_single_top_right_2/side_1` | 489.013 | `base_side` nearest cross-grain profile boundary: 43.399 mm |
| `lumber_leg_bolt_{left,right}_2` | `top_outer/clip_single_top_left_1/side_1`; `top_outer/clip_single_top_right_2/side_1` | 435.757 | `lumber_leg` nearest inclined profile end: 94.152 mm |
| `rail_front_bolt_{left,right}_1` | `knee_outer_{left,right}_post_1` | 106.235 | source profile end/edge distances: about 70 mm |
| `rail_front_bolt_{left,right}_2` | same corresponding `knee_outer_..._post_1` | 94.764 | `base_post_outer` / `base_floor` nearest edge: 41.597 mm |
| `rail_rear_bolt_{left,right}_1` | No candidate axis uses either receiver | — | source profile end/edge distances: about 70 mm |
| `rail_rear_bolt_{left,right}_2` | No candidate axis uses either receiver | — | `base_floor` / `lumber_leg` nearest edges: 42.200 / 43.638 mm |

For `rail_front_bolt_{left,right}_2`, the source washer OD is 25.4 mm. Its
center z is 98.103 mm, so the nominal washer's upper Z envelope is 110.803 mm.
The new exterior-block bottom is at z = 139.7 mm, a **28.9 mm vertical
bbox gap**. This is not actual wrench clearance: the full three-dimensional
stack orientation, adjacent solids, tool approach, nut removal, and bolt
withdrawal remain to be checked.

The listed profile distances are centerline-to-profile measurements from the
kerf-right source geometry before subtracting the clearance-hole radius; the
method and member-by-member values are in the prior
[retained frame-bolt audit](wj24-retained-frame-bolt-audit.md). The small
values identify where directional end/edge review is most sensitive:
the upper first, front second, and rear second stations. Confirm each finished
receiver's actual cut, bore diameter and position, grain direction, applicable
load direction, and remaining section there. The source hole ranges are
13.494–14.288 mm for the upper 1/2-inch bolts and 10.319–11.113 mm for the
3/8-inch front/rear bolts; these are finished-hole bounds, not drill-bit
instructions.

Before a current-candidate conclusion, the twelve named stacks need updated
signed actions and resistance checks under the revised block layout, including
the new runner contact/load transfer. Bind actual delivered bolt dimensions,
body-to-thread transitions, grips, washers and nut engagement to the source
stacks; the packet leaves purchased lengths blank. Nominal grips are 177.8,
76.2 and 88.9 mm for upper, front and rear groups respectively. Under the
existing full-body lateral-resistance route, the corresponding under-head
full-body-to-thread-transition measurement minima are 158.9278, 69.3166 and
78.8416 mm; these are delivered-part checks, not capacities. Verify the rear
stations' 50.8 mm remaining leg bearing section. The current model has no
physical inspection or installation proof.

## Frozen source hashes

Current snapshot SHA-256: `0b92357af648604ee8ce42d2f8906e0a4e5498e9e4b835a07938b81dc151d187`.
It binds current scene SHA-256
`74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf`,
review report SHA-256
`148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695`,
and the unchanged selected-candidate construction source. The current scene's
source inventory SHA-256 is
`07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`
(source commit `df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb`). The source packet
hashes used for the identity reconciliation are:

- `connection-axes.csv`: `174033945a2136b094bf99360cb2c6dfa409accef423ab12538ef289b5d36a58`
- `bolt-hardware.csv`: `a3081ca72f92271ae21967684c5b7a459619dc0cf5c00ac53e7d8cecd748afd8`
- `bolt-member-datums.csv`: `1ca8c4c52b88792c583222ff36cac13dad571b43df4045e7cbd96157729be2db`

The snapshot and report describe modeled geometry only. All native mechanics,
tool-access, receiving, material, and complete-joint acceptance questions
remain open for the current revision.
