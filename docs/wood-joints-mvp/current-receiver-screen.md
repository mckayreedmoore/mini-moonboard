# Current wood-joint receiver and contact screen

This screen audits the current owner-reviewed `led-clearance-2x6-runner-seated-blocks-v1` geometry. It records modeled interfaces and receiver-envelope intersections only. It is not a capacity check, load-sharing result, installation instruction, or release.

The run is [receiver-screen-attempt04.json](hypotheses/evaluation-resume-2026-09-24/receiver-screen-attempt04.json), collected by [`wood_joint_current_receiver_screen.py`](../../scripts/wood_joint_current_receiver_screen.py). The frozen geometry snapshot identifies revision `led-clearance-2x6-runner-seated-blocks-v1` at reviewed repository commit `b1e8707d`; its current report and source hashes are recorded in [geometry-snapshot.json](hypotheses/evaluation-resume-2026-09-24/geometry-snapshot.json). Attempt04 SHA-256: `851495f2ccc80f286a7eae97fc54bcf602a478bb7d4e13eb28e2ae44cfb87991`. Collector SHA-256: `e5e970b41aaa64d1029277f8f6a6122e3623f488f8feed72f43696581c6f0ff0`.

## Current panel screw receivers

The current map contains 66 Hillman panel/kicker screw axes: 58 retain source stations and eight use report-recorded moved stations. `round_panel_lower_left_edge_1` and `round_panel_lower_left_edge_2` now enter `base_rail_bottom_left`; `round_panel_lower_right_edge_1` and `round_panel_lower_right_edge_2` now enter `base_rail_bottom_right`. The four moved kicker-center axes are:

| Axis IDs | Current start `(X, Y, Z)` mm | Direction | Raw receiver |
| --- | --- | --- | --- |
| `round_kicker_left_center_1`, `round_kicker_left_center_2` | `(-161.71, -17.74375, 60)`, `(-161.71, -17.74375, 192)` | `(0, -1, 0)` | `base_post_center_left` |
| `round_kicker_right_center_1`, `round_kicker_right_center_2` | `(160.35, -17.74375, 60)`, `(160.35, -17.74375, 192)` | `(0, -1, 0)` | `base_post_center_right` |

Each center-post receiver has 19.05 mm of X-bounding-box margin on each side of the screw centerline. The lower and upper axes sit 60/178.9 mm and 192/46.9 mm from the post's Z bounding faces, respectively. All four modeled axis envelopes intersect the raw post and clear the finished post. Their exact rotated-BRep intersections start 18.25625 mm from the reported axis origins and extend to the 63.5 mm CAD-envelope ends, for 45.24375 mm full-section-equivalent overlap. That value describes the modeled cylinder only; it is not installed screw embedment.

Across the full set, all 66 current modeled axis envelopes intersect their mapped raw receiver and all 66 clear the corresponding finished receiver. The source-inventory occupied-length field is 50.8 mm, the current axis BRep is 63.5 mm long, and the purchased Hillman 42605 nominal length is 63.5 mm. The 50.8 mm field is the inherited historical SPAX analysis envelope. Keep these provenance fields distinct; none measures the delivered Hillman shaft, threaded length, installed engagement, or resistance.

## Panel support and center kicker seam

The collector measured 22 unique panel-to-finished-receiver pairs. All 22 have finite planar face contact, zero common solid volume, and at most `1.14e-13 mm` computed separation. The four moved-axis pairs are:

| Panel / receiver | Exact finite shared face area |
| --- | ---: |
| `kicker_left` / `base_post_center_left` | 9,075.165 mm² |
| `kicker_right` / `base_post_center_right` | 9,075.165 mm² |
| `main_lower_left` / `base_rail_bottom_left` | 39,594.656 mm² |
| `main_lower_right` / `base_rail_bottom_right` | 39,473.688 mm² |

Each kicker panel also has a measured `base_header` face contact of 46,323.723 mm²; the corresponding outer-post contact is 9,075.165 mm² per side. The kicker panel edges meet at X `-1.5875 mm` within numerical tolerance, with 5,056.957 mm² of finite panel-to-panel face contact. The seam is 141.0725 mm from the left center post's inner X face and 142.8875 mm from the right center post's inner face; the nearest moved kicker screw centerline is 160.1225 mm from the seam midpoint. The current center-post bounding boxes are separated by 283.96 mm in X. Thus the moved screws enter the posts, but the post locations do not provide continuous direct backing under the center seam. The header contact is a separate geometric interface; this screen does not establish panel bending, seam transfer, or required support.

## Frame/block contact graph

Attempt04 checks 52 named current interfaces: 48 unique adjacent receiver pairs declared by the 92 candidate bolt stacks, two exterior block-to-runner seats, and two center-post top seats against the header underside. The 48 bolt interfaces hold 96 adjacent-axis references because four triple-receiver stacks each declare two neighboring pairs. Every row reports finite planar face contact and zero common volume. Face areas range from 5,080.635 to 16,208.820 mm²; computed separation is at most `2.31e-7 mm`.

For each side, the center-post cleat has a declared two-bolt face with the post (11,375.502 mm²) and a separate declared two-bolt face with the header (7,819.502 mm²). A second, non-bolted top-seat contact between that center post and header underside measures 5,322.570 mm² per side. These are parallel geometric routes; no load split or transfer capacity is established. The two exterior spine-block/runner seats each measure 5,080.635 mm². The bolt-interface rows record adjacency from current bolt receiver stacks, not proof that a complete force path can carry demand.

## Open evaluation items

- Check whether the kicker seam and required main-panel edge strips have continuous support over their required spans. The measured face areas are whole-face intersections and do not describe support coverage intervals, panel bending, or bearing adequacy. A bounded exact follow-up is to project the actual panel/receiver common face patches onto those edge strips and report covered intervals and gaps.
- Evaluate force transfer and compatibility through the panel fasteners, center-post/header seats, cleat bolt stacks, inner sandwiches, lower rails, and exterior block/runner contacts. Keep the direct post/header seat and the two-bolt cleat route separate unless an analysis establishes their interaction and load split.
- Resolve actual Hillman screw engagement and the adopted fastener checks from the current purchased-product and installation basis. CAD cylinder overlap does not establish screw thread engagement or resistance.
- Evaluate the runner-to-floor condition under the already stated no-slip floor assumption. The runner-seat face areas do not establish floor anchorage or bearing capacity.

Older receiver and backer studies are history only. In particular, the removed `inner_kicker_backer_left/right` members are absent from this current composition and are not receivers in this screen.
