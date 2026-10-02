# Upper screw shop overlay

This 66-axis schedule supplements the [conditional shop and assembly guide](../assembly-package/shop-guide.md). It records the owner-authorized October 2, 2026 upper-row move as a coordinate overlay. It does not adopt or replace that guide, change source authority or existing STEP holes, authorize physical cutting, or claim that any cut was made.

## Axis changes

Generate the full front-datum and direction schedule with `python3 shop_axes.py`:

- `rawlocal/shop-axes/axes.csv` — all 66 axes.
- `rawlocal/shop-axes/receipt.json` — frozen input and geometry pins, reconciliation, and CSV hash.

The export checks all 172 saved geometry source pins and verifies 62 axes retain their saved front datum, direction, panel, and receiver. Four upper axes move `+65.95 mm` along panel coordinate `T`, with translation `(0, 42.391842858827275, 50.5206310236966) mm`. Their screw directions stay unchanged.

Frozen CSV SHA-256: `46406c559d1f427ad4422edf033759831a83d0ddcef4bbb871579da132853eca`.
Receipt SHA-256: `535bcdaeb85ed683e66040c8042dd6c3bdea7d835ca7a9d7c510de99d6cf773d`.

| Axis | Panel | Receiver before → after | Front datum after, global mm |
| --- | --- | --- | --- |
| `round_panel_upper_left_rim_4` | `main_upper_left` | `base_side_left` → `base_side_left` | `(-1200.15, 1537.324502383678, 2130.164909134918)` |
| `round_panel_upper_right_rim_4` | `main_upper_right` | `base_side_right` → `base_side_right` | `(1196.975, 1537.324502383678, 2130.164909134918)` |
| `round_panel_upper_left_center_4` | `main_upper_left` | `base_principal_center_left` → `base_rail_top` | `(-70, 1537.324502383678, 2130.164909134918)` |
| `round_panel_upper_right_center_4` | `main_upper_right` | `base_principal_center_right` → `base_rail_top` | `(70, 1537.324502383678, 2130.164909134918)` |

The two center receivers are now `base_rail_top`; rim receivers remain on their same-side members. Old moved-axis bores remain part of saved source geometry; they are not additional drilling instructions. Existing source STEP holes and their authority remain unchanged.

## Shop references retained

No body, timber, structural bolt, nut, or washer counts change. The guide BOM still records 20 frame timber bodies, 24 blocks, 44 timber blanks, six plywood bodies, 104 structural stacks (92 candidate plus 12 retained), 104 nuts, 208 washers, and 66 separate panel/kicker screws. Use its existing fit and operation sections for handling; this overlay adds screw coordinates only.

The 66 screws remain purchased Hillman 42605, #10 × 2-1/2 in (63.5 mm), #2 Phillips. Retain owner-selected Kobalt 80277 / Lowe’s 1208451 #10 insert policy: 1/8 in (3.175 mm) lead pilot through plywood into its receiver, plus 3/8 in (9.525 mm) countersink at the plywood face. The `4.1402 mm` nominal CAD occupied diameter is an analysis envelope, not a drill-bit size. These facts follow the [purchase record](../../../../current-panel-screw-purchase.md) and [shop guide](../assembly-package/shop-guide.md); no Hillman resistance or installation observation is added.

This addendum does not direct new holes at either old or moved stations. Keep the existing shop checklist’s Actual and Disposition fields blank until observed. Saved geometry checks support this coordinate overlay only; they do not claim guide adoption, physical fit, cuts, or mechanical acceptance.
