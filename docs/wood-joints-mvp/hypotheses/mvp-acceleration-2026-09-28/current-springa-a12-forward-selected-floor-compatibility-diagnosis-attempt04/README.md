# A12-forward M5 selected-floor compatibility diagnosis

This read-only report applies the unchanged pinned zero-U 711 strict signed
normal interval classifier to the frozen M5 DAT. It checks all 100 floor
normal laws at all seven printed load factors and compares the result with the
source-bound M1–M5 input masks and prior output records. The classifier uses
native spring/RF data internally, but this packet exports no force or reaction
values and produces no corner demands.

## M5 compatibility result

The parent response gate rejected the completed M5 run because inactive
normal `SPR1026` was not strictly separated with zero endpoint RF. The pinned
interval classification confirms that its source cell,
`floor_base_floor_left_1`, is strictly positive at every printed state. Two
other inactive cells are also strictly positive. Five selected cells are
strictly separated. There are no ambiguous intervals:

| Input status | Cell | Source group | Classification at all seven states | q interval at 0.1 | q interval at 1.0 |
| --- | --- | --- | --- | ---: | ---: |
| Inactive | `floor_base_floor_left_1` | SPR1026 | Strictly positive | `[5.2887325e-6, 5.2887335e-6] mm` | `[5.2887325e-5, 5.2887335e-5] mm` |
| Inactive | `floor_base_floor_right_7` | SPR1158 | Strictly positive | `[1.4130785e-6, 1.4130795e-6] mm` | `[1.4130785e-5, 1.4130795e-5] mm` |
| Inactive | `floor_base_post_outer_left_1` | SPR1278 | Strictly positive | `[3.6410655e-5, 3.6410665e-5] mm` | `[3.6410655e-4, 3.6410665e-4] mm` |
| Selected | `floor_base_floor_right_0` | SPR1137 | Strictly separated, zero endpoint RF | `[-1.4975575e-5, -1.4975565e-5] mm` | `[-1.4975575e-4, -1.4975565e-4] mm` |
| Selected | `floor_base_floor_right_2` | SPR1143 | Strictly separated, zero endpoint RF | `[-2.2930925e-5, -2.2930915e-5] mm` | `[-2.2930925e-4, -2.2930915e-4] mm` |
| Selected | `floor_base_floor_right_4` | SPR1149 | Strictly separated, zero endpoint RF | `[-1.6283485e-5, -1.6283475e-5] mm` | `[-1.6283485e-4, -1.6283475e-4] mm` |
| Selected | `floor_base_floor_right_6` | SPR1155 | Strictly separated, zero endpoint RF | `[-4.5913675e-6, -4.5913665e-6] mm` | `[-4.5913675e-5, -4.5913665e-5] mm` |
| Selected | `floor_lumber_leg_left_2` | SPR1305 | Strictly separated, zero endpoint RF | `[-0.0012805365, -0.0012805355] mm` | `[-0.012805365, -0.012805355] mm` |

Across all seven states M5 has 32 strictly positive, 68 strictly separated,
and 0 ambiguous normals. Its 34-cell proposed input and 32-cell positive
output differ in eight cells: the three inactive positive cells above and the
five selected separated cells above. The strict response gate therefore
rejects this proposal. This is a branch compatibility result for this frozen
response, not an inferred physical failure.

## M1–M5 mask sequence

The recorded input-to-output counts are M1 `35→31`, M2 `31→37`, M3 `37→37`,
M4 `37→34`, and M5 `34→32`. The equal M3 counts are different sets. The
observed outputs for M1 through M4 exactly match the next recorded input,
which is the documented proposal handoff. None of those outputs equals its
own or an earlier input. M5's 32-cell output matches none of the M1–M5 inputs
or prior outputs; it is the M2 31-cell input plus
`floor_base_post_center_right_0`. Thus this five-proposal record contains no
verified return/fixed-point mask. It does not establish whether any compatible
mask exists outside the tested inputs.

`diagnosis.json` stores every normal's signed q and geometric elongation
interval at each state, the complete seven positive masks, exact M1–M5
input/output set comparisons, and all eight selected/inactive mismatches.
`source-pins.json` records the report and producer hashes and revalidates the
frozen M5 source closure plus prior lineage. Reproduce from the unchanged
frozen run with:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/\
current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt04/produce.py
```

The producer is write-once. It launches no solver, changes no geometry/law/
tolerance, exports no force/reaction, and emits no next-mask proposal.
