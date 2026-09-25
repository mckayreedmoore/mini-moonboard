# WJ24 fixed panel and kicker screw receiver audit

This audit reconciles the 66 fixed Hillman 42605 panel/kicker screw axes in the
WJ24 development layout with the kerf-right shop coordinates and the
source-bound WJ24 composition and static diagnostic. It covers receiver
identity, nominal receiver material, and recorded purchase-cut placement. It
does not establish a screw capacity, installation result, or complete
receiver-to-frame load path.

The analyzed source is `compact-floor-flush-wood-joints-development`, sourced
from `compact-floor-flush-development`, width option `kerf-right`, source
commit `df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb`. WJ24 is an unaccepted
development hypothesis. Its receiver remapping does not change the selected
baseline shop packet or transfer any acceptance to that candidate.

## Reconciled receiver map

The inventory contains 48 main-panel axes and 18 kicker axes. All 66 retain
their kerf-right global axis coordinates in WJ24. Sixty-two still enter the
same named receiver as the shop packet. Four center-kicker axes keep their
coordinates but redirect from the former center posts to the two WJ24 inner
kicker backers.

| Finished WJ24 receiver | Exact fixed axis IDs | Count |
|---|---|---:|
| `base_side_left` | `round_panel_lower_left_rim_1`, `round_panel_lower_left_rim_2`, `round_panel_lower_left_rim_3`, `round_panel_lower_left_rim_4`, `round_panel_upper_left_rim_1`, `round_panel_upper_left_rim_2`, `round_panel_upper_left_rim_3`, `round_panel_upper_left_rim_4` | 8 |
| `base_principal_center_left` | `round_panel_lower_left_center_1`, `round_panel_lower_left_center_2`, `round_panel_lower_left_center_3`, `round_panel_lower_left_center_4`, `round_panel_upper_left_center_1`, `round_panel_upper_left_center_2`, `round_panel_upper_left_center_3`, `round_panel_upper_left_center_4` | 8 |
| `base_rail_bottom_left` | `round_panel_lower_left_edge_1`, `round_panel_lower_left_edge_2` | 2 |
| `base_rail_service_lower_left` | `round_panel_lower_left_service_1`, `round_panel_lower_left_service_2` | 2 |
| `base_rail_top` | `round_panel_upper_left_edge_1`, `round_panel_upper_left_edge_2`, `round_panel_upper_right_edge_1`, `round_panel_upper_right_edge_2` | 4 |
| `base_rail_service_upper_left` | `round_panel_upper_left_service_1`, `round_panel_upper_left_service_2` | 2 |
| `base_side_right` | `round_panel_lower_right_rim_1`, `round_panel_lower_right_rim_2`, `round_panel_lower_right_rim_3`, `round_panel_lower_right_rim_4`, `round_panel_upper_right_rim_1`, `round_panel_upper_right_rim_2`, `round_panel_upper_right_rim_3`, `round_panel_upper_right_rim_4` | 8 |
| `base_principal_center_right` | `round_panel_lower_right_center_1`, `round_panel_lower_right_center_2`, `round_panel_lower_right_center_3`, `round_panel_lower_right_center_4`, `round_panel_upper_right_center_1`, `round_panel_upper_right_center_2`, `round_panel_upper_right_center_3`, `round_panel_upper_right_center_4` | 8 |
| `base_rail_bottom_right` | `round_panel_lower_right_edge_1`, `round_panel_lower_right_edge_2` | 2 |
| `base_rail_service_lower_right` | `round_panel_lower_right_service_1`, `round_panel_lower_right_service_2` | 2 |
| `base_rail_service_upper_right` | `round_panel_upper_right_service_1`, `round_panel_upper_right_service_2` | 2 |
| `base_post_outer_left` | `round_kicker_left_rim_1`, `round_kicker_left_rim_2` | 2 |
| `inner_kicker_backer_left` | `round_kicker_left_center_1`, `round_kicker_left_center_2` | 2 |
| `base_post_outer_right` | `round_kicker_right_rim_1`, `round_kicker_right_rim_2` | 2 |
| `inner_kicker_backer_right` | `round_kicker_right_center_1`, `round_kicker_right_center_2` | 2 |
| `base_header` | `kicker_header_left_1`, `kicker_header_left_2`, `kicker_header_left_3`, `kicker_header_left_4`, `kicker_header_left_5`, `kicker_header_right_1`, `kicker_header_right_2`, `kicker_header_right_3`, `kicker_header_right_4`, `kicker_header_right_5` | 10 |
| **Total** | **48 main-panel axes + 18 kicker axes** | **66** |

The four receiver overrides are exactly:

| Fixed axis | Source/shop receiver | WJ24 finished receiver | Global axis origin (mm); direction |
|---|---|---|---|
| `round_kicker_left_center_1` | `base_post_center_left` | `inner_kicker_backer_left` | `(-70, -17.74375, 60)`; `(0, -1, 0)` |
| `round_kicker_left_center_2` | `base_post_center_left` | `inner_kicker_backer_left` | `(-70, -17.74375, 192)`; `(0, -1, 0)` |
| `round_kicker_right_center_1` | `base_post_center_right` | `inner_kicker_backer_right` | `(70, -17.74375, 60)`; `(0, -1, 0)` |
| `round_kicker_right_center_2` | `base_post_center_right` | `inner_kicker_backer_right` | `(70, -17.74375, 192)`; `(0, -1, 0)` |

No panel or kicker screw axis is moved by this WJ24 receiver mapping. The
kerf-right shop rows still identify the original baseline receiver for these
four axes; only the WJ24 candidate receiver changes.

## Cut and edge geometry

The WJ24 composition records all 66 fixed axes and assigns the 62 unchanged
receiver purchase cuts to rebuilt source hosts. The four redirected receiver
cuts are assigned to the candidate backer parts. Its diagnostic reports all
66 raw receivers present, all 66 purchase cuts on the composed receivers, and
zero overlap between each finished receiver and its frozen axis envelope.
Those are geometric bookkeeping checks using the source occupied-axis
envelope (50.8 mm long by 4.1402 mm diameter in the source inventory). The
shop packet separately specifies purchased 63.5 mm Hillman 42605 screws and
the owner-selected Kobalt #10 insert: a 1/8-inch lead-hole pilot plus a
3/8-inch face countersink, with an offcut trial before the production holes.
The modeled envelope is not the Hillman body, pilot, countersink, tolerance,
penetration, or thread engagement.

The two candidate finished backers retain these nominal bounds, also used by
the prior inner-edge screen:

| Part | Finished bounds X, Y, Z (mm) |
|---|---|
| `inner_kicker_backer_left` | `[-90.4875, -1.5875] × [-124.9, -36.0] × [0, 238.9]` |
| `inner_kicker_backer_right` | `[-1.5875, 87.3125] × [-124.9, -36.0] × [0, 238.9]` |

For each backer, the WJ05 inner-kicker-edge screen sampled three points at the
bottom, middle, and top of the edge. All six points also fall inside the
current WJ24 finished backer bounds. Each point is within 0.5 mm of the
backer's inner X edge and 0.1 mm of its Y edge. This confirms only the sampled
nominal geometry. It gives no tolerance margin, continuous edge-contact area,
physical fit, or support capacity.

At the kerf-right outer K edge, the right kicker replacement ends at global
X = 1216.025 mm and its two outboard-rim axes are at X = 1196.975 mm. The
modeled axis-to-edge distance is therefore 19.05 mm. The 4×4 source packet has
the corresponding axis at 1200.15 mm; the kerf-right coordinate shifts that
axis 3.175 mm toward the center along with the right edge, preserving the
19.05 mm edge distance. The left outboard-rim axes remain 19.05 mm from the
left kicker edge in the kerf-right shop coordinates. This reconciles the
width/cut coordinate effect; it is not an edge-distance capacity check.

## What the static pass leaves open

The WJ24 fixed-receiver subcheck is positive for axis identity, candidate
receiver presence, raw material, purchase-cut presence, and a clear finished
axis envelope for all 66 rows. The contract script
[`wood_joint_wj24_fixed_receiver_contract.py`](../../scripts/wood_joint_wj24_fixed_receiver_contract.py)
rejoins the inventory, both kerf-right screw coordinate files, the WJ24
composition and diagnostic, and the three-point inner-edge screen. It emits
the per-axis coordinates, receiver, cut owner, and status as JSON without
rebuilding CAD or running a solver.

The passing checks do not measure required support or embedment: the WJ24
diagnostic records that check as not evaluated for all 66 axes. The source
inventory marks `receiver_to_frame_path_complete` false for all 66. For the
62 direct axes its path note says the replacement interfaces remain
unqualified; for the four redirected axes the backer-to-frame attachment is
unresolved. In particular, showing that a fixed kicker screw enters a backer
does not show how the backer transfers that force into the frame.

The backer/header bolt arrangement is a separate, provisional WJ05/WJ24
connection: two proposed through-bolts per backer connect each backer to
`base_header`. The load path then depends on separate header-to-center-post and
header-to-principal-cleat interfaces. These are not accepted transfer joints;
the current evidence does not reconcile complete actions and compatibility
through those interfaces. The nominal bore, edge, and clearance screens are
not a transfer calculation. The 66 Hillman axes have no adopted resistance or
stiffness basis in this audit. Do not transfer SPAX envelope values or
resistance to Hillman 42605, and do not treat the purchase-length field as a
delivered embedment length. Physical wood, cuts, holes, screws, and edge
support have not been inspected.

Accordingly this audit accepts no screw, backer attachment, complete load
path, capacity, installation sequence, fabrication, structure, or climbing
release. It records a source-bound receiver map with nominal static geometry
checks only.

## Source records

- [`source-inventory.json`](source-inventory.json): 66 fixed axes, original and WJ24 receiver names, global coordinates, and receiver-to-frame path status. Its recorded SHA-256 is `07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`.
- [Kerf-right shop packet](../floor-flush-construction-kerf-right/README.md), especially [`panel-attachment-axes.csv`](../floor-flush-construction-kerf-right/panel-attachment-axes.csv) and [`connection-axes.csv`](../floor-flush-construction-kerf-right/connection-axes.csv): purchased Hillman length and shop coordinates. Modeled occupied length/diameter are analysis envelopes, not shop instructions.
- [`current-panel-screw-purchase.md`](../current-panel-screw-purchase.md) and the [shop checklist](../floor-flush-shop-checklist.md): Hillman 42605 purchase identity, owner-selected pilot/countersink, and the required offcut trial. These shop instructions do not supply a Hillman structural resistance basis.
- [`wj24-integrated-static/composition.json`](hypotheses/wj24-integrated-static/composition.json) and [`diagnostic.json`](hypotheses/wj24-integrated-static/diagnostic.json): current recorded WJ24 receiver-cut map and static receiver findings.
- [`wj05-receiver-audit.json`](wj05-receiver-audit.json): prior three-point center kicker edge screen and provisional backer/header attachment geometry.
