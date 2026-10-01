# Current stock-cut scenarios — 2026-10-01

This joins the 20 source-inventory frame-blank proposals and 24 block-blank proposals to the exact current finished STEP bindings in manifest attempt04. All 44 original proposed boxes contain their finished solids; the four reduced sections also fit and lie within their respective original 4×6 boxes. The geometry result is documented in [envelopes.md](envelopes.md). The [nesting method](nesting.md) cuts full-section blanks before the four later section rips, keeping every remnant in its original stock class.

The candidate is `compact-floor-flush-wood-joints-development`, revision `led-clearance-2x6-runner-seated-blocks-v1`. These are proposed stock locations and lengths, not recovered current raw-host solids, delivered lumber, or a shop cut list. Finished grain spans do not replace the recorded source-blank lengths.

## Arithmetic results

The 15 cases combine five stock-length sets with 0, 10 or 20 mm of declared trim at each end. The trim allowance includes its trim-cut loss. Every placed blank reserves a full 3.2 mm separation kerf, including the last blank. Defect, receiving and section-cleanup losses are zero. The counts below are heuristic outputs; none establishes an optimum, availability, price or purchase quantity. All three trim choices give the same counts and placed IDs here; their trim and remainder ledgers differ.

| Nominal stock options | 2×6 sticks | 4×6 sticks | 4×4 sticks | Blanks placed | Sum of blank lengths / sum of stick lengths |
| --- | ---: | ---: | ---: | ---: | ---: |
| 8 ft | 6 | 2 | 1 | 39/44 | 92.863% |
| 10 ft | 8 | 4 | 1 | 44/44 | 83.337% |
| 12 ft | 6 | 4 | 1 | 44/44 | 82.074% |
| 16 ft | 5 | 3 | 1 | 44/44 | 75.235% |
| 8, 10, 12, 16 ft | 9 | 4 | 1 | 44/44 | 88.801% |

The last column adds lengths across different sections. It is an arithmetic length ratio, not a volume, cost or material-yield fraction. Section-specific balances, all cut intervals and remnant intervals are in the local raw result. The mixed-options heuristic chooses the shortest option that fits each new stick; it does not search globally for the cheapest or most efficient combination.

All 8 ft-only cases retain five unplaced IDs: `base_header`, `base_principal_center_left`, `base_principal_center_right`, `base_side_left`, and `base_side_right`. The four principal/side blanks are longer than 2438.4 mm. The header proposal is 2435.225 mm; adding the full 3.2 mm reserve requires 2438.425 mm, 0.025 mm beyond the nominal option even at zero trim. This is incompatibility with that declared conservative arithmetic convention, not a statement that a delivered board cannot be cut. No geometry change is proposed.

## Proposed piece schedule

Lengths below are rounded for reading. The raw result retains their source precision. `Source only` identifies the four retained source-only frame geometries; `Rebuilt` identifies the 16 current rebuilt hosts. Every row uses its current finished STEP, independently of that role. All original sections are actual dimensions: 2×6 = 38.1×139.7 mm, 4×4 = 88.9×88.9 mm and 4×6 = 88.9×139.7 mm.

| Member | Proposed blank length (mm) | Original stock | Later prepared section (mm) | Current role |
| --- | ---: | --- | --- | --- |
| `base_floor_left` | 1815.646 | 2x6 | — | Source only |
| `base_floor_right` | 1815.646 | 2x6 | — | Source only |
| `base_header` | 2435.225 | 2x6 | — | Rebuilt |
| `base_post_center_left` | 238.900 | 2x6 | — | Rebuilt |
| `base_post_center_right` | 238.900 | 2x6 | — | Rebuilt |
| `base_post_outer_left` | 238.900 | 2x6 | — | Rebuilt |
| `base_post_outer_right` | 238.900 | 2x6 | — | Rebuilt |
| `base_principal_center_left` | 2532.626 | 2x6 | — | Rebuilt |
| `base_principal_center_right` | 2532.626 | 2x6 | — | Rebuilt |
| `base_rail_bottom_left` | 1041.250 | 2x6 | — | Rebuilt |
| `base_rail_bottom_right` | 1038.075 | 2x6 | — | Rebuilt |
| `base_rail_service_lower_left` | 1041.250 | 2x6 | — | Rebuilt |
| `base_rail_service_lower_right` | 1038.075 | 2x6 | — | Rebuilt |
| `base_rail_service_upper_left` | 1041.250 | 2x6 | — | Rebuilt |
| `base_rail_service_upper_right` | 1038.075 | 2x6 | — | Rebuilt |
| `base_rail_top` | 2257.425 | 2x6 | — | Rebuilt |
| `base_side_left` | 2570.726 | 4x6 | — | Rebuilt |
| `base_side_right` | 2570.726 | 4x6 | — | Rebuilt |
| `bottom_center_left_cleat` | 119.700 | 4x4 | — | Block proposal |
| `bottom_center_right_cleat` | 119.700 | 4x4 | — | Block proposal |
| `bottom_outer_left_cleat` | 119.700 | 4x4 | — | Block proposal |
| `bottom_outer_right_cleat` | 119.700 | 4x4 | — | Block proposal |
| `center_post_cleat_left` | 128.900 | 4x4 | — | Block proposal |
| `center_post_cleat_right` | 128.900 | 4x4 | — | Block proposal |
| `center_principal_cleat_left` | 134.700 | 4x6 | 83.9×139.7 | Block proposal |
| `center_principal_cleat_right` | 134.700 | 4x6 | 83.9×139.7 | Block proposal |
| `knee_outer_left_inner_frame_block` | 139.000 | 4x6 | 88.9×133.35 | Block proposal |
| `knee_outer_left_spine` | 276.300 | 2x6 | — | Block proposal |
| `knee_outer_right_inner_frame_block` | 139.000 | 4x6 | 88.9×133.35 | Block proposal |
| `knee_outer_right_spine` | 276.300 | 2x6 | — | Block proposal |
| `left_service_inner_lower_cleat` | 119.700 | 4x4 | — | Block proposal |
| `left_service_inner_upper_cleat` | 119.700 | 4x4 | — | Block proposal |
| `left_service_outer_lower_cleat` | 119.700 | 4x4 | — | Block proposal |
| `left_service_outer_upper_cleat` | 119.700 | 4x4 | — | Block proposal |
| `lumber_leg_left` | 2028.463 | 4x6 | — | Source only |
| `lumber_leg_right` | 2028.463 | 4x6 | — | Source only |
| `top_center_left_cleat` | 119.700 | 4x4 | — | Block proposal |
| `top_center_right_cleat` | 119.700 | 4x4 | — | Block proposal |
| `top_outer_left_cleat` | 119.700 | 4x4 | — | Block proposal |
| `top_outer_right_cleat` | 119.700 | 4x4 | — | Block proposal |
| `wj04_lower_full_stock_cleat` | 119.700 | 4x4 | — | Block proposal |
| `wj04_upper_g7_crosscut_full_stock_cleat` | 86.900 | 4x4 | — | Block proposal |
| `wj06_outer_lower_right_cleat` | 119.700 | 4x4 | — | Block proposal |
| `wj06_outer_upper_right_cleat` | 119.700 | 4x4 | — | Block proposal |

There are 18 proposed 4×4 blanks totalling 2140.200 mm, eight 4×6 blanks totalling 9745.778 mm, and 18 2×6 blanks totalling 21135.370 mm. The four later section rips remain in the 4×6 source group. Their species/grade and post-rip grade are unassigned. The schedule supplies neither drilling instructions nor resistance acceptance.

## Frozen evidence and replay

The raw `cut-scenarios.json`, `envelopes.json` and `source-pins.json` stay local and ignored. The consumer checks exact frozen input/producer bytes, reconciles all 44 identities and source dimensions, requires both applicable containment details, checks prepared boxes lie inside original boxes, and rechecks all 44 current STEP hashes. Replay the envelope first so its complete input and producer pin set is also checked.

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/envelopes.py --verify
.venv/bin/python docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/cut_scenarios.py --verify
.venv/bin/python -m pytest -q docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01
.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01
.venv/bin/ruff format --check docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01
```

`--write` creates each local result once and refuses to overwrite an existing frozen result. `--verify` compares exact canonical bytes. The packing feasibility comparisons use Decimal values without a fit tolerance; the helper allows at most 1e-9 absolute output-unit difference when validating floats after serialization. The tests include a blank one float step beyond a stock boundary.

| Produced or maintained artifact | SHA-256 |
| --- | --- |
| `cut_scenarios.py` | `7591868860c9a6fa652f4430b574ae1ec936358bace191341fb3b4d866356098` |
| `test_cut_scenarios.py` | `ec92e69ce38732535cdceafdc3f8b1e340f2bc5d4cf6198a16718f35a3c03b88` |
| `nesting.py` | `c601d895319934cc42641e843470a413d70ece804141ba8b7ef3dd55936550b6` |
| `test_nesting.py` | `ed30b7219868b741e2f06f6555d3745d015df4fcf9c01d24410aafc445825c4a` |
| `cut-scenarios.json` | `9a450e0b6bca73cf62b95f5759bfcacffd9d682b3c465df3fbc27327723d6978` |

| Consumer input | SHA-256 |
| --- | --- |
| `docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/envelopes.json` | `0f13d1c697d8c7b3dcb1a5db5a7ab215e05bc9bee4e729fc35763ff449436e01` |
| `docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/envelopes.py` | `a4aa9e6d8d22178bdae28cab4c829d1f45fb5633575dd7119fe57cf03b374b0d` |
| `docs/wood-joints-mvp/hypotheses/current-stock-envelope-reconciliation-2026-10-01/nesting.py` | `c601d895319934cc42641e843470a413d70ece804141ba8b7ef3dd55936550b6` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json` | `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11` |
| `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-timber-source-yield-attempt01/current-timber-source-yield.json` | `2c710708d5e775d742375e28fadd323ecfe7f8e81c186c6028704c903a65266c` |
| `docs/wood-joints-mvp/source-inventory.json` | `07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78` |

The envelope note publishes the remaining geometry-source and STEP hashes. These outputs support subsequent material and build-package reconciliation; they do not assign stock grades, measured weights, prices, machining feasibility, joint capacities, actual observations, fabrication approval or a climbing release.
