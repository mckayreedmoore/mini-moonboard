# WJ-05 fixed screw receiver audit

Status: **blocked center receiver path**. Geometry audit only; every release flag remains false.

## Inventory result

| Item | Result |
|---|---:|
| Fixed axes enumerated | 66 |
| Main panel / kicker axes | 48 / 18 |
| Finished receiver annular checks passed | 66 |
| Axes received directly by structural frame timber | 62 |
| Axes received by separate center backers | 4 |
| Fixed axes moved | 0 |

Every axis has one 45.24375 mm nominal uncut receiver interval. The checked-in JSON records every coordinate, receiver, finished-solid bound, local annular support result, and immediate path. This confirms nominal wood continuity around each modeled axis. It does not establish Hillman resistance or a pilot instruction.

## Center and inner-edge result

The four center kicker axes are `round_kicker_left_center_1`, `round_kicker_left_center_2`, `round_kicker_right_center_1`, and `round_kicker_right_center_2`. They enter the two 88.9 × 88.9 × 238.9 mm diagnostic backers at X=±70 mm and Z=60/192 mm. Both three-point kerf-right inner-edge samples lie inside their assigned backers.

Two provisional vertical bores per backer reach `base_header`, but that path is not accepted. It remains a diagnostic topology.

## Socket outer-envelope path screen

Both producers now use one Ko-ken 3305A-7/16 outside-envelope proxy. It records the seated socket from each hex fastener's far face, preserves the former approach endpoint, and screens the continuous coaxial sweep between them. Top seat datum is the nut bearing face at Z=283.096 mm; bottom seat datum is the bolt underhead face at Z=4.968 mm. The fastener's intended occupancy is recorded separately; it is excluded only from obstacle clashing. The 12-point internal profile and engagement fit are not modeled.
At the repaired right upper station `(25, −76)`, current nominal proxy clearances to `wire_072_F1_G1` are 2.959434 mm for seated body and 1.661248 mm for full approach sweep. The preserved approach endpoint alone measures 1.661248 mm. The prior approach-only model at station `(35, −63)` recorded 140.528820 mm³ wire overlap. These are nominal outside-envelope diagnostics, not tool-fit, tolerance, or access acceptance.

The right pair center spacing is 27.202941 mm (4.283928D), leaving 1.802941 mm beyond 4D. The minimum right backer center-to-edge margin beyond 4D is 1.187500 mm. Tool path, bolt, bore, stack, and backer proxy solids are screened against protected services and unrelated wood. These nominal checks carry no tolerance acceptance.

## Exact blockers

- The center structural duties remain unimplemented: `clip_split_header_center_left`, `clip_split_header_center_right`, `clip_split_base_center_left`, `clip_split_base_center_right`.
- The four provisional backer/header bolt stacks remain unselected and lack complete joint evidence.

Physical observation fields remain blank. No drilling, fabrication, structural, or climbing release is made.
