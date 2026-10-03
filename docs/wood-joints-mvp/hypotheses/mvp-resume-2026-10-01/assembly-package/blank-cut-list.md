# Conditional timber blank cut list

This completed export identifies **44 unique timber blanks: 20 frame members and 24
connector blocks**. Six plywood bodies are listed separately. It joins the frozen
[assembly reconciliation](README.md) to the existing stock records and four saved top
geometry overrides; it does not regenerate geometry or nesting.

Use it with the [shop guide](shop-guide.md) and [current-joint addendum](current-joint-addendum.md).
This is a conditional stock-length list, not a complete machining schedule or physical
work authorization. Panel attachment retains its reference HOLD. Actual and Disposition
cells stay blank until observed.

## Read the lengths and sections

The source-stock class identifies the stock before any section reduction: **18 2×6,
10 4×6 and 16 4×4 blanks**. Dimensions are millimetres. Source sections retain their
recorded dimension order. Finished envelopes use **grain × q × r**, except the two
top outer cleats use **grain × X × T**. Grain references below identify saved conditional
material directions; they are not saw settings or observations of delivered grain.

Blank length and finished grain span are separate columns. The longer principal, side
and leg blanks must not be shortened to their finished-envelope lengths. Values below
are rounded to 0.001 mm for reading, with full recorded precision in the JSON/CSV exports.
That display precision assigns no machining tolerance, cleanup or receiving allowance.

The two top outer cleats use 4×6 source stock, 88.9 × 139.7 mm section and 119.7 mm grain
length. Their historical 4×4 stock records are not reused. The four reduced-section
blocks remain in the 4×6 stock class: two center-principal cleats at 83.9 × 139.7 mm and
two inner knee blocks at 88.9 × 133.35 mm. The existing nesting convention takes
full-section blanks before those later rips and preserves the original stock class of
remnants. Rip face/setup and post-rip grade are not supplied or observed.

In the Prepared column, **—** means no separate section reduction; any unchanged prepared
section recorded by the source remains in the machine export. Missing bevel/miter angles,
profile cuts, rip setup, pilot/bore instructions, service machining and machining tolerances
are explicitly **null** in each row's `operation_facts`. This packet does not infer them
from a finished envelope or historical CAD bore.

## Forty-four timber blanks

| Member | Duty | Source stock / section, mm | Blank length, mm | Prepared section, mm | Finished envelope, mm | Grain | Actual | Disposition |
| --- | --- | --- | ---: | --- | --- | --- | --- | --- |
| `base_floor_left` | Frame | 2x6 / 38.100 × 139.700 | 1815.646 | — | 1815.646 × 139.700 × 38.100 | GY | | |
| `base_floor_right` | Frame | 2x6 / 38.100 × 139.700 | 1815.646 | — | 1815.646 × 139.700 × 38.100 | GY | | |
| `base_header` | Frame | 2x6 / 38.100 × 139.700 | 2435.225 | — | 2435.225 × 38.100 × 139.700 | GX | | |
| `base_post_center_left` | Frame | 2x6 / 38.100 × 139.700 | 238.900 | — | 238.900 × 139.700 × 38.100 | GZ | | |
| `base_post_center_right` | Frame | 2x6 / 38.100 × 139.700 | 238.900 | — | 238.900 × 139.700 × 38.100 | GZ | | |
| `base_post_outer_left` | Frame | 2x6 / 38.100 × 139.700 | 238.900 | — | 238.900 × 139.700 × 38.100 | GZ | | |
| `base_post_outer_right` | Frame | 2x6 / 38.100 × 139.700 | 238.900 | — | 238.900 × 139.700 × 38.100 | GZ | | |
| `base_principal_center_left` | Frame | 2x6 / 38.100 × 139.700 | 2532.626 | — | 2506.167 × 139.700 × 38.100 | GS | | |
| `base_principal_center_right` | Frame | 2x6 / 38.100 × 139.700 | 2532.626 | — | 2506.167 × 139.700 × 38.100 | GS | | |
| `base_rail_bottom_left` | Frame | 2x6 / 38.100 × 139.700 | 1041.250 | — | 1041.250 × 38.100 × 139.700 | GX | | |
| `base_rail_bottom_right` | Frame | 2x6 / 38.100 × 139.700 | 1038.075 | — | 1038.075 × 38.100 × 139.700 | GX | | |
| `base_rail_service_lower_left` | Frame | 2x6 / 38.100 × 139.700 | 1041.250 | — | 1041.250 × 38.100 × 139.700 | GX | | |
| `base_rail_service_lower_right` | Frame | 2x6 / 38.100 × 139.700 | 1038.075 | — | 1038.075 × 38.100 × 139.700 | GX | | |
| `base_rail_service_upper_left` | Frame | 2x6 / 38.100 × 139.700 | 1041.250 | — | 1041.250 × 38.100 × 139.700 | GX | | |
| `base_rail_service_upper_right` | Frame | 2x6 / 38.100 × 139.700 | 1038.075 | — | 1038.075 × 38.100 × 139.700 | GX | | |
| `base_rail_top` | Frame | 2x6 / 38.100 × 139.700 | 2257.425 | — | 2257.425 × 38.100 × 139.700 | GX | | |
| `base_side_left` | Frame | 4x6 / 88.900 × 139.700 | 2570.726 | — | 2539.768 × 139.700 × 88.900 | GS | | |
| `base_side_right` | Frame | 4x6 / 88.900 × 139.700 | 2570.726 | — | 2539.768 × 139.700 × 88.900 | GS | | |
| `bottom_center_left_cleat` | Block | 4x4 / 88.900 × 88.900 | 119.700 | — | 119.700 × 88.900 × 88.900 | GN+ | | |
| `bottom_center_right_cleat` | Block | 4x4 / 88.900 × 88.900 | 119.700 | — | 119.700 × 88.900 × 88.900 | GN+ | | |
| `bottom_outer_left_cleat` | Block | 4x4 / 88.900 × 88.900 | 119.700 | — | 119.700 × 88.900 × 88.900 | GN+ | | |
| `bottom_outer_right_cleat` | Block | 4x4 / 88.900 × 88.900 | 119.700 | — | 119.700 × 88.900 × 88.900 | GN+ | | |
| `center_post_cleat_left` | Block | 4x4 / 88.900 × 88.900 | 128.900 | — | 128.900 × 88.900 × 88.900 | GZ | | |
| `center_post_cleat_right` | Block | 4x4 / 88.900 × 88.900 | 128.900 | — | 128.900 × 88.900 × 88.900 | GZ | | |
| `center_principal_cleat_left` | Block | 4x6 / 88.900 × 139.700 | 134.700 | 83.900 × 139.700 | 134.700 × 139.700 × 83.900 | GZ | | |
| `center_principal_cleat_right` | Block | 4x6 / 88.900 × 139.700 | 134.700 | 83.900 × 139.700 | 134.700 × 139.700 × 83.900 | GZ | | |
| `knee_outer_left_inner_frame_block` | Block | 4x6 / 88.900 × 139.700 | 139.000 | 88.900 × 133.350 | 139.000 × 133.350 × 88.900 | GZ | | |
| `knee_outer_left_spine` | Block | 2x6 / 38.100 × 139.700 | 276.300 | — | 276.300 × 139.700 × 38.100 | GZ | | |
| `knee_outer_right_inner_frame_block` | Block | 4x6 / 88.900 × 139.700 | 139.000 | 88.900 × 133.350 | 139.000 × 133.350 × 88.900 | GZ | | |
| `knee_outer_right_spine` | Block | 2x6 / 38.100 × 139.700 | 276.300 | — | 276.300 × 139.700 × 38.100 | GZ | | |
| `left_service_inner_lower_cleat` | Block | 4x4 / 88.900 × 88.900 | 119.700 | — | 119.700 × 88.900 × 88.900 | GN+ | | |
| `left_service_inner_upper_cleat` | Block | 4x4 / 88.900 × 88.900 | 119.700 | — | 119.700 × 88.900 × 88.900 | GN- | | |
| `left_service_outer_lower_cleat` | Block | 4x4 / 88.900 × 88.900 | 119.700 | — | 119.700 × 88.900 × 88.900 | GN- | | |
| `left_service_outer_upper_cleat` | Block | 4x4 / 88.900 × 88.900 | 119.700 | — | 119.700 × 88.900 × 88.900 | GN+ | | |
| `lumber_leg_left` | Frame | 4x6 / 88.900 × 139.700 | 2028.463 | — | 1989.026 × 139.700 × 88.900 | GL | | |
| `lumber_leg_right` | Frame | 4x6 / 88.900 × 139.700 | 2028.463 | — | 1989.026 × 139.700 × 88.900 | GL | | |
| `top_center_left_cleat` | Block | 4x4 / 88.900 × 88.900 | 119.700 | — | 119.700 × 88.900 × 88.900 | GN+ | | |
| `top_center_right_cleat` | Block | 4x4 / 88.900 × 88.900 | 119.700 | — | 119.700 × 88.900 × 88.900 | GN- | | |
| `top_outer_left_cleat` | Block | 4x6 / 88.900 × 139.700 | 119.700 | — | 119.700 × 88.900 × 139.700 | GN+ | | |
| `top_outer_right_cleat` | Block | 4x6 / 88.900 × 139.700 | 119.700 | — | 119.700 × 88.900 × 139.700 | GN- | | |
| `wj04_lower_full_stock_cleat` | Block | 4x4 / 88.900 × 88.900 | 119.700 | — | 119.700 × 88.900 × 88.900 | GN- | | |
| `wj04_upper_g7_crosscut_full_stock_cleat` | Block | 4x4 / 88.900 × 88.900 | 86.900 | — | 86.900 × 88.900 × 88.900 | GN+ | | |
| `wj06_outer_lower_right_cleat` | Block | 4x4 / 88.900 × 88.900 | 119.700 | — | 119.700 × 88.900 × 88.900 | GN- | | |
| `wj06_outer_upper_right_cleat` | Block | 4x4 / 88.900 × 88.900 | 119.700 | — | 119.700 × 88.900 × 88.900 | GN- | | |

### Grain reference directions

These global XYZ reference vectors are rounded here; the exact per-member vectors
and their source-record identity remain in the machine export. Opposite signed
references preserve the source convention for the same unoriented grain line.

| Reference | Conditional global grain vector (X, Y, Z) |
| --- | --- |
| GX | (1.000000, 0.000000, 0.000000) |
| GY | (0.000000, 1.000000, 0.000000) |
| GZ | (0.000000, 0.000000, 1.000000) |
| GS | (0.000000, 0.642788, 0.766044) |
| GL | (0.000000, -0.239152, 0.970982) |
| GN+ | (0.000000, -0.766044, 0.642788) |
| GN- | (0.000000, 0.766044, -0.642788) |

## Six plywood bodies, separate from timber

Keep four main panels and two whole kickers. Source blank dimensions below retain
their source order; the local X/T/N envelope is an independent saved geometry record.
The kicker's rotated local extents are not its sheet-cut depth or a bevel instruction.
Six bodies are not six purchased sheets. Sheet nesting and the purchased Roseburg AC
fir strength-axis binding retain their scope in the [assembly package](README.md#stock-panel-quantities-and-cost-scope)
and [panel-material note](../upper-corner-screw-layout/panel-material-fidelity.md).

| Body | Identity | Source blank dimensions, mm | Recorded local X × T × N envelope, mm | Actual | Disposition |
| --- | --- | --- | --- | --- | --- |
| `kicker_left` | whole kicker | 1217.612 × 277.000 × 18.256 | 1217.612 × 223.858 × 192.037 | | |
| `kicker_right` | whole kicker | 1217.612 × 277.000 × 18.256 | 1217.612 × 223.858 × 192.037 | | |
| `main_lower_left` | main panel | 1217.612 × 1219.200 × 18.256 | 1217.612 × 1219.200 × 18.256 | | |
| `main_lower_right` | main panel | 1217.612 × 1219.200 × 18.256 | 1217.612 × 1219.200 × 18.256 | | |
| `main_upper_left` | main panel | 1217.612 × 1219.200 × 18.256 | 1217.612 × 1219.200 × 18.256 | | |
| `main_upper_right` | main panel | 1217.612 × 1219.200 × 18.256 | 1217.612 × 1219.200 × 18.256 | | |

The unchanged fastening policy remains 66 purchased Hillman 42605 panel/kicker
screws, 104 frame bolt stacks/nuts and 208 exterior washers. Use the [shop guide](shop-guide.md#forward-assembly)
for the purchased screw and owner-selected pilot/countersink policy. This list adds
no screw stations, insert pilots, old-bore drilling instructions or fastening products.

## Existing stock-scenario index

All fifteen replacement-aware scenarios are copied from frozen `stock-scenarios.json`
without running its nesting helper. Each reserves 3.2 mm separation kerf per blank and
the recorded 0, 10 or 20 mm trim at each stick end. These are first-fit scenarios,
with no new optimization, stock selection, price or purchasing quantity.

| Existing scenario ID | 2×6 sticks | 4×6 sticks | 4×4 sticks | Blanks placed |
| --- | ---: | ---: | ---: | ---: |
| `stock-8ft-trim-0mm` | 6 | 3 | 1 | 39/44 |
| `stock-8ft-trim-10mm` | 6 | 3 | 1 | 39/44 |
| `stock-8ft-trim-20mm` | 6 | 3 | 1 | 39/44 |
| `stock-10ft-trim-0mm` | 8 | 4 | 1 | 44/44 |
| `stock-10ft-trim-10mm` | 8 | 4 | 1 | 44/44 |
| `stock-10ft-trim-20mm` | 8 | 4 | 1 | 44/44 |
| `stock-12ft-trim-0mm` | 6 | 4 | 1 | 44/44 |
| `stock-12ft-trim-10mm` | 6 | 4 | 1 | 44/44 |
| `stock-12ft-trim-20mm` | 6 | 4 | 1 | 44/44 |
| `stock-16ft-trim-0mm` | 5 | 3 | 1 | 44/44 |
| `stock-16ft-trim-10mm` | 5 | 3 | 1 | 44/44 |
| `stock-16ft-trim-20mm` | 5 | 3 | 1 | 44/44 |
| `stock-8-10-12-16ft-trim-0mm` | 9 | 4 | 1 | 44/44 |
| `stock-8-10-12-16ft-trim-10mm` | 9 | 4 | 1 | 44/44 |
| `stock-8-10-12-16ft-trim-20mm` | 9 | 4 | 1 | 44/44 |

The three 8-ft scenarios leave `base_header`, both center principals and both sides
unplaced. Larger and mixed scenarios place all 44 under their saved conventions.
The current index includes the top 4×6 replacements; the earlier stock packet's
4×4-top-cleat placements remain history. Existing nesting files are unchanged.

## Engineering source bindings and export

[blank_cut_list.py](blank_cut_list.py) uses only the standard library. Seven frozen
input packets and the four top replacement STEP byte hashes are checked before
and after export. The other geometry hashes and exact grain axes are inherited
from those frozen records; no geometry is imported or mechanically evaluated.

| Consumed packet | SHA-256 |
| --- | --- |
| `rawlocal/reconciled-assembly.json` | `2bb4e95fbd2a7ec158d24bc12860e0961000fdb9f9af7ffd8504ef966b2aee87` |
| `rawlocal/bodies.csv` | `9e54e5da262074e98e84e2c846e37d81e905791d7f619b3253142f4dd37f14bc` |
| `rawlocal/stock-classes.csv` | `c792f7c8d8e58a498d1ebed246b88aa0df3d916b6977a1b317d494637554a3f7` |
| `rawlocal/stock-scenarios.json` | `f10b683f0e23cf303ea9163468fa929f9a5850f649a54cf28752b1ebacf26cf8` |
| `docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/cut-scenarios.json` | `9a450e0b6bca73cf62b95f5759bfcacffd9d682b3c465df3fbc27327723d6978` |
| `docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/envelopes.json` | `0f13d1c697d8c7b3dcb1a5db5a7ab215e05bc9bee4e729fc35763ff449436e01` |
| `docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/top-corner-correction/proposal.json` | `5932768c7a7d91535f69a90787b32222eb4d165ac6353d3e2ed4daf9e248e2b2` |

Producer SHA-256: `548c20babe0516c8fe5e0f161eb6ebb85158d002f43a4146e20f1d8791f93869`.

Ignored output child: `rawlocal/blank-cut-list/attempt01/`.
`blank-cut-list.json` retains all row fields and eleven source pins; the two CSVs
retain blank Actual/Disposition cells. `stock-scenario-index.json` retains all fifteen
saved scenario objects verbatim. The child also contains this worksheet, the producer
snapshot and a receipt binding their exact bytes. Raw outputs are local provenance,
not newly published geometry evidence.

| Export | SHA-256 |
| --- | --- |
| `blank-cut-list.json` | `780b2b140578777f04164e6919b4a02070512fb67d81056884ab8a1e70dc1699` |
| `timber-blanks.csv` | `f51cad031cd3523c16e97317a463d82c4de802af3c8caa21c04b3e019dafc655` |
| `plywood-bodies.csv` | `a7534ef7bfb694153d1d191697811aa4ecda6f731e430210b902dbc6895e7d89` |
| `stock-scenario-index.json` | `2646c08250817f07735cfbbf1634131781d87ff378f320d6cdda2c590a4601d0` |

From the repository root:

```sh
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/blank_cut_list.py --write
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/assembly-package/blank_cut_list.py --verify
```

Write refuses to replace different raw bytes; verify reads the same frozen records
and compares the export byte-for-byte. It runs no CAD, native/frame calculation,
stock optimization, supplier research, software tests or review loop. The list assigns
no delivered wood grade, physical fit, inspected cuts, joint capacity or climber rating.
