# Bounded prior-panel applicability comparison — September 29, 2026

Owner priority is current bolted timber/block joints. This closes the requested scope comparison; it does not start another panel qualification study.

## What carries forward

The [purchased screw record](../../../current-panel-screw-purchase.md) records the owner-accepted panel-construction scope, 66 Hillman 42605 screws, nominal 63.5 mm length and selected pilot/countersink policy. It records absent exact-product resistance data and proxy stiffness in prior analysis. Preserve those limits and the completed panel calculations. Unchanged panel outlines and hardware policy support reuse of construction intent; they do not transfer an earlier frame pass, screw capacity, or receiver force distribution.

Attempt04 retains 58 screw stations and the eight previously owner-directed moves below. All 66 source rows report a raw receiver intersection and a clear finished receiver axis envelope. Those are geometric screen flags, not installation, edge-support, stiffness or strength checks. Four moved kicker axes also change named receiver; the other four change station on the same named bottom rails. No additional receiver-name changes occur in the 66-row source.

| Axis | Previous receiver | Current receiver | Translation from source, mm (X,Y,Z) |
| --- | --- | --- | --- |
| round_kicker_left_center_1 | inner_kicker_backer_left | base_post_center_left | -91.710000, 0.000000, 0.000000 |
| round_kicker_left_center_2 | inner_kicker_backer_left | base_post_center_left | -91.710000, 0.000000, 0.000000 |
| round_kicker_right_center_1 | inner_kicker_backer_right | base_post_center_right | 90.350000, 0.000000, 0.000000 |
| round_kicker_right_center_2 | inner_kicker_backer_right | base_post_center_right | 90.350000, 0.000000, 0.000000 |
| round_panel_lower_left_edge_1 | base_rail_bottom_left | base_rail_bottom_left | 0.000000, 49.430367, 58.908818 |
| round_panel_lower_left_edge_2 | base_rail_bottom_left | base_rail_bottom_left | 0.000000, 49.430367, 58.908818 |
| round_panel_lower_right_edge_1 | base_rail_bottom_right | base_rail_bottom_right | 0.000000, 49.430367, 58.908818 |
| round_panel_lower_right_edge_2 | base_rail_bottom_right | base_rail_bottom_right | 0.000000, 49.430367, 58.908818 |

## Load-transfer consequence

The moved kicker axes now inject their actions into the center posts rather than the prior inner kicker backers. The lower-panel edge axes inject at changed stations on the bottom rails, changing local lever arms and potential edge/support checks. Even retained station names do not preserve frame stiffness: the current bolted block system replaces the earlier structural-angle transfer routes. Prior panel construction scope therefore remains usable, while current receiver-to-frame bolt actions must be calculated for the current connection network.

Exact-product screw resistance, physical receiving/installation and changed-station support checks remain explicit gaps. They do not prevent prescribed-wrench conditional bolt-group calculations. Such calculations must identify their assumed load and may not call it an accepted full-frame demand. No further panel-group expansion or catalog searching is scheduled absent a specific new input or owner request.

## Source pin

- Current manifest: `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json`
- SHA-256: `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11`
- Checks: 66 rows, 58 retained stations, eight owner-moved stations, four receiver-name changes, 66 positive source geometry flags.

No geometry, native-run control, selected-candidate authority or criterion disposition changes.
