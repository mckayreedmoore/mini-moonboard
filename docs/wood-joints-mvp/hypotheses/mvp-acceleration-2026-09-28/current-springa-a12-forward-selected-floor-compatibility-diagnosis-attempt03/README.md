# A12-forward M4 normal-mask diagnosis

This read-only report classifies the frozen M4 DAT with the unchanged zero-U
711 signed normal interval method. It compares only same-case input masks M1
through M4 and the seven printed load factors. It exports no spring force,
support reaction, or corner demand.

## Result

M4 returned zero and completed the full step in 40.69 s, but the unchanged
response gate rejected it because selected normal `SPR1068` was not strictly
positive after rounding. Its source cell is `floor_base_floor_left_15`. The
pinned interval method classifies it as strictly separated with zero endpoint
RF at all seven states; its q interval runs from `[-0.0014633195,
-0.0014633185] mm` at load factor 0.1 to `[-0.014633195,
-0.014633185] mm` at load factor 1.0.

The full strict classification is stable but incompatible with M4's selected
set: each of the seven states has 34 strictly positive, 66 strictly separated,
and 0 ambiguous or noncomplementary normals. The three M4-selected cells that
are not positive at any state are:

| Cell | Source group | Classification at all seven states | q interval at load factor 1.0 (mm) |
| --- | --- | --- | --- |
| `floor_base_floor_left_15` | `SPR1068` | Strictly separated, zero endpoint RF | `[-0.014633195, -0.014633185]` |
| `floor_base_floor_left_17` | `SPR1074` | Strictly separated, zero endpoint RF | `[-0.011069735, -0.011069725]` |
| `floor_base_post_outer_left_1` | `SPR1278` | Strictly separated, zero endpoint RF | `[-0.00067066475, -0.00067066465]` |

No strictly positive cell falls outside the M4 input. The q and geometric
elongation intervals for all 700 normal-state records are in `diagnosis.json`;
the rules and arithmetic bounds are exactly those in the pinned method source.

## Mask comparison and recurrence

The M4 positive output is a 34-cell set and exactly matches none of M1–M4:

| Input mask | Input cells | Output comparison |
| --- | ---: | --- |
| M1 / attempt01 | 35 | Output is the input minus `floor_base_post_outer_left_1`. |
| M2 / attempt02 | 31 | Output adds right_0, right_2, right_4, right_6, post_center_right_0, and lumber_leg_left_2; left_1, right_7, and post_outer_left_1 are not positive. |
| M3 / attempt03 | 37 | Output removes left_9, left_11, and left_13. |
| M4 / attempt04 | 37 | Output removes left_15, left_17, and post_outer_left_1. |

The preceding M3 run's stable positive set was M4, which is why M4 became the
next explicit input hypothesis. M4's stable output is a distinct 34-cell set,
not M3 or M4. Thus no exact M3↔M4 two-mask recurrence is observed, and no
M1–M4 input repeats as the M4 output. The classification is stable only across
this run's seven load factors; it does not establish a unique or accepted
floor-support solution.

The parent terminal record says this is a response incompatibility, not an
inferred physical failure. No tolerance, law, geometry, or load was changed.
No next mask is emitted by this diagnostic; the separate M5 proposal packet
uses the exact 34-cell classification only as an explicitly diagnostic input
hypothesis.

Reproduce with:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/\
current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt03/produce.py
```
