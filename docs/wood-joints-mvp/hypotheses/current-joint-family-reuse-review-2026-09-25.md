# Independent review: current joint-family reuse map

Reviewed the frozen [current-joint-family-reuse.md](../current-joint-family-reuse.md), SHA-256 `961f2365efc3d7d5b81a09a5ac2b7eae015f969b82189ed01276bdba20ddff58`, against its pinned current graph, snapshot, grip screen, ordinary-patch geometry/material inventories, duty registry, and block design count. The review found no blocking factual discrepancy in the counts, modeled head-to-nut orders, centerline spacing definitions, contact areas, or reuse boundary.

## Pins and publication links

The map's embedded hashes match the inspected files: current scene `74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf`; current review report `148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695`; geometry snapshot `0b92357af648604ee8ce42d2f8906e0a4e5498e9e4b835a07938b81dc151d187`; complete graph `7806242ac48b198becf5db97b16b6a5605021b8d86b964f0f02adb6806aeec26`; grip screen `9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a`; duty registry `fde510bd5b5002ce6ab10a9e05593ad7e8f2244d998cef6b450c27cede6d56d8`; source inventory `07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`; ordinary geometry inventory `70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3`; ordinary material map `9e1cbc8945d33683de3cb71ba716581919f508466d8a27b181865da4cc675fd4`; and ordinary-load datums `c3a561b84eb56472264e92eacabae7c2e06fe33633ebba96f1de9ee974924022`.

All 13 local Markdown link targets in the map resolve and are Git-tracked. I used only read-only `git ls-files` metadata for that check. No workspace-only labels are needed; none of the links points to raw CAD or native-solver output.

## Duty and axis reconciliation

The registry has 24 unique former-duty IDs. The map tables have 16 distinct horizontal rows, four distinct center-node rows, and four distinct outer-node rows, also 24 unique IDs. The geometry snapshot contains 92 unique candidate bolt-axis keys, and the grip screen has 92 unique axis rows. The map reconciles these as 64 horizontal axes (16 stations × four), 16 center axes (four stations × four), and 12 unique outer-chain axes.

Each side's two outer former-duty rows intentionally repeat the same six current axis IDs. They describe many-to-one coverage, not twelve new axes per side: two post axes, two three-member side-chain axes, and two inner-header axes give six unique axes on each side. Deduplicating those repeated rows yields 12 outer axes and 92 total. This agrees with the snapshot and the grip screen.

The seven block-design groups account for the current 24 blocks as 15 common horizontal cleats, one shortened G7 cleat, two center-post cleats, two distinct center-principal cleats, two inner-frame blocks, and two exterior spines. The design-count method explicitly includes finished holes/cuts, permits proper rotations, and excludes reflection. The two center-principal singletons are not declared congruent merely because their blank size/volume matches.

## Modeled receiver order and spacing

The table arrows agree with the grip screen's ordered receiver IDs for all 92 axes. The ordinary reference's four axes run cleat→rail/principal, each with a 152.4 mm modeled shaft, 127.0 mm projected wood grip, and 33.00 mm within-pair pitch. Horizontal outer side pairs run side→cleat with 203.2 mm modeled shafts and 177.8 mm projected grip. Top-center rail axes run rail→cleat; bottom-center rail axes run cleat→rail. Center-post axes run cleat→post, while the header pair runs header→cleat. Center-principal pairs run cleat→principal/header. The outer side-axis sequence is spine→side→inner-frame block. The two inner-header axes oppose one another: header→block and block→header. These describe modeled current geometry, not observed or installed hardware.

The outer inner-header pair's center coordinates differ by approximately `(0, 93.35, 22.098) mm`; both axes are parallel to Z (with opposite signs). Removing the component along the axis leaves a 93.35 mm perpendicular centerline spacing. The 95.9299 mm value is the three-dimensional distance between those two selected axis-center points; it includes the 22.098 mm along-axis stagger and is not their perpendicular spacing. The map states the perpendicular value and separately records the global-Z stagger. Other listed pitches also reproduce as perpendicular spacing between parallel axes: outer post 42.05 mm, outer side 45.00 mm, center post 50.00 mm, center-post header 35.00 mm, center-principal 53.00 mm, and center-principal header 65.00 mm.

## Contact areas and reuse boundary

The ordinary-patch inventory has three finished timber bodies—the bottom-center-right cleat, bottom rail, and center principal—four modeled bolts, and three finite face interfaces. Its cleat/rail and cleat/principal areas are each 10,552.973 mm²; its direct rail/principal seat is 5,322.570 mm². The inventory is geometry/material-input only: it assigns no contact law or force, records no native solve, and makes no acceptance or capacity claim.

The current graph gives all 16 horizontal receiver pairs a finite 5,322.570 mm² direct host-to-host face. The 15 common cleats match by proper rigid transforms, but this block-level equivalence does not make the whole patch equivalent: receiver sections/positions, head-to-nut orientation, bolts, direct seats, other connected members, and signed demands differ. Three left center-rail-to-cleat faces are 10,385.138 mm² rather than the common 10,552.973 mm². The unique upper-right G7 cleat is 88.9×88.9×86.9 mm versus the common 88.9×88.9×119.7 mm, and its two cleat contacts are each 7,637.053 mm². Thus the exact whole-patch match is the ordinary reference station itself; other common-group matches support cleat geometry reuse only.

The center-post cleat has 11,375.502 mm² contact with its post and 7,819.502 mm² with the header, with a separate 5,322.570 mm² direct post/header seat. Center-principal cleat contacts are 16,208.820/15,068.728 mm² at the left/right principals and 11,637.122 mm² at each header. The direct header/principal seat is 5,113.122 mm². In the outer chain, spine/post contact is 13,139.963 mm², spine/side and side/inner-block contacts are each 15,653.565 mm², and header/inner-block contact is 11,766.458 mm². The spine and inner block have no direct seat; their cached AABBs are separated by 88.9 mm, with the side host between them. These are finite CAD face areas, not active bearing patches, capacities, or load shares.

The map's unresolved-mechanics section correctly notes that the hold-datum file provides only A12, K12, and A1 point/frame references and labels itself `not_a_load_or_mechanics_result`. It does not supply former-duty signed demands, per-axis actions, contact pressure, or bolt/direct-seat force split. Geometry family reuse therefore cannot establish mechanics reuse or accepted replacement duties.

One non-blocking wording suggestion was sent to the map author: “installed head-to-nut order” in the reuse finding could be changed to “modeled head-to-nut receiver order” to avoid implying physical installation. The map's subsequent scope and limitations already keep this result in the geometry/model domain.

No CAD composition, native solve, or mechanical acceptance review was performed.
