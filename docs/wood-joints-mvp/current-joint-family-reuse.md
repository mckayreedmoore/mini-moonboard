# Current WJ24 joint-family reuse map

Status: source-bound geometry and analysis-method crosswalk for the owner-reviewed
revision **led-clearance-2x6-runner-seated-blocks-v1**, checkpoint **b1e8707d**.
It maps the 24 former angle duties onto current block/bolt families and compares
them with the existing bottom-center-right ordinary-joint patch. It is not a
mechanics result, a duty acceptance, or a capacity statement.

The current duty registry still records 24/24 former duties as unresolved or
unaccepted, with no accepted replacement mapping. This map is an evaluation
crosswalk only. The owner scene keeps candidate acceptance, capacity,
installation, fabrication, structural release, and climbing release false.

## Reuse finding

The only exact whole-patch match to the existing ordinary-joint input is its own
current station, **clip_horizontal_bottom_right_1**. That local input contains
the finished bottom-center-right cleat, its bottom rail and center principal,
four candidate bolts (two per receiver pair), and the direct rail-to-principal
seat. It does not include the rest of the frame or assign contact forces.

Fourteen other horizontal stations use a cleat solid and its four-bore pattern
that the current design-count report matches to the ordinary cleat by proper
rigid rotation and translation; reflection is excluded. This permits reuse of
the cleat/hole geometry as a model template. It does not make the surrounding
two receiver bodies, installed head-to-nut order, direct seats, connected
members, or force demand identical. The fifteenth member of that common group
is the ordinary reference station itself. One further horizontal station,
upper-right-center, uses a shortened, unique G7 cleat and is outside the common
solid group.

The eight center and outer-node duties need distinct models. Their cleat
patterns, receiver order, bolt pitches and lengths, direct bearing interfaces,
and connected load paths differ from the four-bolt ordinary patch. The outer
chains also have a third timber receiver in their side-bolt paths. In
particular, each pair of former outer duties on one side maps to a shared
six-axis chain through the spine, side member, inner-frame block, and header;
it is not two independent ordinary patches.

Geometry pattern counts are 15 common horizontal cleats, one unique shortened
G7 cleat, two center-post cleats, two distinct center-principal cleats, two
inner-frame blocks, and two exterior spines: 24 current blocks. Current bolt
coverage reconciles to 64 horizontal axes, 16 center-node axes, and 12
outer-chain axes: 92 total. Axis-center spacings below are perpendicular
distances between parallel centerlines, measured from the frozen snapshot.
The outer inner-header pair also has a 22.098 mm global-Z stagger. These are
geometric quantities only, not code spacing checks.

## Source binding

The listed hashes bind this map to the current revision inputs and the ordinary
patch reference.

| Source | SHA-256 |
| --- | --- |
| [Owner scene](../../site/owner-wood-joints-wj24-scene.json) | 74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf |
| [Owner review report](../../site/owner-wood-joints-review-report.json) | 148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695 |
| [Geometry snapshot, reviewed at b1e8707d](hypotheses/evaluation-resume-2026-09-24/geometry-snapshot.json) | 0b92357af648604ee8ce42d2f8906e0a4e5498e9e4b835a07938b81dc151d187 |
| [Complete contact graph, attempt 02](hypotheses/evaluation-resume-2026-09-24/complete-contact-graph-attempt02.json) | 7806242ac48b198becf5db97b16b6a5605021b8d86b964f0f02adb6806aeec26 |
| [Grip screen, attempt 02](hypotheses/evaluation-resume-2026-09-24/grip-screen-attempt02.json) | 9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a |
| [Current fastener screen](current-fastener-screen.md) | cc4450c2af635ce4b9394aa13042539b7a3c3adac1c2f03be5e747b3732b137e |
| [Seven-pattern block design count](hypotheses/led-clearance-2x6-runner-blocks-2026-09-24/block-designs.json) | f3c7d76ecdd2d3a82d2d96ef8868bc11ddb789ecdaa6b6ff2fdeadeec45d097b |
| [Former-duty registry](duty-registry.json) | fde510bd5b5002ce6ab10a9e05593ad7e8f2244d998cef6b450c27cede6d56d8 |
| [Current material scenarios](current-material-scenarios.md) | dd76354c0fa68a01a336cef22fe1cf854baaaf1ceda22dd11ceb881a274bb3c4 |
| [Source member inventory](source-inventory.json) | 07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78 |
| [Ordinary-patch geometry inventory](hypotheses/evaluation-resume-2026-09-24/ordinary-patch-inputs-attempt01/inventory.json) | 70b396e636175abcad7467dc145029d7126c1ea7dff1d053a61f8c5321e1c1d3 |
| [Ordinary-patch material map](hypotheses/evaluation-resume-2026-09-24/ordinary-patch-materials-attempt01/material-map.json) | 9e1cbc8945d33683de3cb71ba716581919f508466d8a27b181865da4cc675fd4 |
| [Current hold datums](hypotheses/evaluation-resume-2026-09-24/current-load-datums.json) | c3a561b84eb56472264e92eacabae7c2e06fe33633ebba96f1de9ee974924022 |

The scene and report are the current viewer and its source-bound owner review;
the older WJ03, WJ04, WJ05, and WJ06 labels in axis or block IDs are historical
names for parts of this revision, not separate current candidates.

## Ordinary reference patch

The ordinary-patch inventory contains three finished timber bodies:
**bottom_center_right_cleat**, **base_rail_bottom_right**, and
**base_principal_center_right**. Its four exact current axis IDs are
**bottom_center/clip_horizontal_bottom_right_1/rail_1**,
**bottom_center/clip_horizontal_bottom_right_1/rail_2**,
**bottom_center/clip_horizontal_bottom_right_1/principal_1**, and
**bottom_center/clip_horizontal_bottom_right_1/principal_2**. Each pair has
33.00 mm center pitch. All four modeled shafts are 152.4 mm long, have 127.0 mm
of projected wood grip, and run head-to-nut from the cleat into one receiver.
The inventory reports a 10,552.973 mm² finite cleat contact on each receiver
and a 5,322.570 mm² direct rail-to-principal seat in the current contact graph.
The finite areas describe CAD face intersections; they do not establish active
bearing or split the force between the contacts.

For the conditional grain scenario, the ordinary cleat longitudinal axis is
its source-local N, global ±(0, −0.766044, 0.642788); the rail grain is global X
and the principal grain is source-local T, global (0, 0.642788, 0.766044).
Those are scenario/source-frame assignments, not observed boards. The
ordinary-patch inventory is geometry input only: no mesh, contact law, solve,
joint acceptance, or strength result is recorded there.

In this map, **B**, **R**, **P**, and **S** mean the named current block, rail,
principal, and side receiver. An arrow gives the current grip-screen
head-to-nut receiver order. In the axis field, braces expand literally:
**rail_{1,2}** means **rail_1** and **rail_2**; the other grouped suffixes use
the same rule. All listed IDs are in the frozen geometry snapshot and current
scene.

## Sixteen horizontal former duties

The ordinary cleat belongs to the common 15-block group: finished solids,
cuts, and bore geometry were matched by a proper rigid transform to each other
member in that group. Every horizontal receiver pair has a 5,322.570 mm²
finite direct host-to-host seat in the contact graph. A same-sized direct seat
does not establish the same loaded contact or load share.

| Former duty | Exact current axis family | Receiver/order and modeled length | Reuse distinction |
| --- | --- | --- | --- |
| **clip_single_top_left_1** | **top_outer/clip_single_top_left_1/{rail_{1,2},side_{1,2}}** | Rail R→B, 152.4 mm; side S→B, 203.2 mm | Common cleat. Side receiver is 4×6; the reference principal receiver is 2×6. |
| **clip_single_top_right_2** | **top_outer/clip_single_top_right_2/{rail_{1,2},side_{1,2}}** | Rail R→B, 152.4 mm; side S→B, 203.2 mm | Same distinction as top-left; both axis pairs have 33.00 mm pitch. |
| **clip_split_top_center_left** | **top_center/clip_split_top_center_left/{principal_{1,2},rail_{1,2}}** | Principal B→P, 152.4 mm; rail R→B, 152.4 mm | Common cleat and 2×6 receivers; rail-pair head-to-nut order differs from the reference. |
| **clip_split_top_center_right** | **top_center/clip_split_top_center_right/{principal_{1,2},rail_{1,2}}** | Principal B→P, 152.4 mm; rail R→B, 152.4 mm | Same receiver/contact family as top-left; rail-pair order differs from the reference. |
| **clip_horizontal_bottom_left_1** | **bottom_outer/clip_horizontal_bottom_left_1/{rail_{1,2},side_{1,2}}** | Rail B→R, 152.4 mm; side S→B, 203.2 mm | Common cleat; 4×6 side receiver and longer side axes separate it from the reference. |
| **clip_horizontal_bottom_right_2** | **bottom_outer/clip_horizontal_bottom_right_2/{rail_{1,2},side_{1,2}}** | Rail B→R, 152.4 mm; side S→B, 203.2 mm | Same distinction as bottom-left outer. |
| **clip_horizontal_bottom_left_2** | **bottom_center/clip_horizontal_bottom_left_2/{principal_{1,2},rail_{1,2}}** | Principal B→P, 152.4 mm; rail B→R, 152.4 mm | Common cleat and 2×6 receivers; left rail-cleat contact is 10,385.138 mm², not the reference’s 10,552.973 mm². |
| **clip_horizontal_bottom_right_1** | **bottom_center/clip_horizontal_bottom_right_1/{principal_{1,2},rail_{1,2}}** | Principal B→P, 152.4 mm; rail B→R, 152.4 mm | Exact ordinary-patch reference geometry and axis order. |
| **clip_horizontal_lower_left_1** | **left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_1/{lower_rail_{1,2},lower_side_{1,2}}** | Rail B→R, 152.4 mm; side S→B, 203.2 mm | Common cleat; 4×6 side receiver and longer side axes separate it from the reference. |
| **clip_horizontal_lower_right_2** | **wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/{lower_rail_{1,2},lower_side_{1,2}}** | Rail B→R, 152.4 mm; side S→B, 203.2 mm | Common cleat, but uses the outer 4×6 side receiver. |
| **clip_horizontal_lower_left_2** | **left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_2/{lower_principal_{1,2},lower_rail_{1,2}}** | Principal B→P, 152.4 mm; rail B→R, 152.4 mm | Common cleat and 2×6 receivers; left rail-cleat contact is 10,385.138 mm². |
| **clip_horizontal_lower_right_1** | **wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/{lower_rail_{1,2},lower_principal_{1,2}}** | Rail B→R, 152.4 mm; principal B→P, 152.4 mm | Common full-stock cleat; current label is historical. Contact and receiver groups match the common center family. |
| **clip_horizontal_upper_left_1** | **left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_upper_left_1/{upper_rail_{1,2},upper_side_{1,2}}** | Rail B→R, 152.4 mm; side S→B, 203.2 mm | Common cleat; 4×6 side receiver and longer side axes separate it from the reference. |
| **clip_horizontal_upper_right_2** | **wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/{upper_rail_{1,2},upper_side_{1,2}}** | Rail B→R, 152.4 mm; side S→B, 203.2 mm | Common cleat, but uses the outer 4×6 side receiver. |
| **clip_horizontal_upper_left_2** | **left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_upper_left_2/{upper_principal_{1,2},upper_rail_{1,2}}** | Principal B→P, 152.4 mm; rail B→R, 152.4 mm | Common cleat and 2×6 receivers; left rail-cleat contact is 10,385.138 mm². |
| **clip_horizontal_upper_right_1** | **wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/{upper_rail_{1,2},upper_principal_{1,2}}** | Rail B→R, 152.4 mm; principal B→P, 152.4 mm | Unique shortened G7 cleat; see the measured geometry difference below. |

All fourteen non-reference common-group instances preserve the 33.00 mm
within-pair pitch through their common cleat geometry. The eight outer duties
are not full-patch ordinary transforms: the axis pair into S crosses 88.9 mm
of side-member section plus 88.9 mm of cleat (177.8 mm projected wood grip),
and uses a 203.2 mm modeled shaft; the reference principal pair crosses
38.1 mm of principal plus 88.9 mm of cleat and uses 152.4 mm. The relevant
source-member blanks are 139.7×88.9 mm for the 4×6 side and 139.7×38.1 mm for
the 2×6 rail/principal. The shared block's candidate grain direction is the
same proposed source-local N in this family; source inventory assigns rail
grain X and side/principal grain T. This does not remove the receiver-section,
head-to-nut, or connected-frame differences.

The left bottom-center, lower-center, and upper-center rail contacts are the
three 10,385.138 mm² outliers within the common pattern; their principal
contacts remain 10,552.973 mm². The upper-right-center G7 body is
88.9×88.9×86.9 mm rather than the common 88.9×88.9×119.7 mm. Its two finite
cleat contacts are each 7,637.053 mm². Its rail/principal pair pitch and
receiver topology remain the two-pair horizontal layout, but its shortened
body is not the ordinary solid and loses 27.6% of each common cleat-face
intersection area in this geometric comparison. Neither area is a bearing
capacity.

All horizontal block grain directions above are the current proposed
conditional scenario ±(0, −0.766044, 0.642788), including G7. The current
material report does not identify the delivered stock or its R/T ring
orientation. Axis order is included because a transform of a wood solid does
not itself place the head and nut on the same receiver side.

## Four center-node former duties

Each center duty uses a separate current four-axis station. The two left and
right center-post cleats are one proper-rotation shape group; the two
center-principal cleats are separate singleton patterns. All plumb-block grain
directions are proposed +Z scenarios, distinct from the ordinary block's
proposed source-local N.

| Former duty | Exact current axes | Current local geometry and load-path distinctions |
| --- | --- | --- |
| **clip_split_header_center_left** | **center_post_left_1**, **center_post_left_2**, **center_post_header_left_1**, **center_post_header_left_2** | Two axes through **center_post_cleat_left** and **base_post_center_left**, then two other axes through the same cleat and **base_header**. Pitches are 50.00 mm at the post and 35.00 mm at the header; modeled shaft lengths are 139.2174 and 179.2174 mm. Head-to-nut order is cleat→post and header→cleat. The graph also has a 5,322.570 mm² direct post/header seat; cleat contacts are 11,375.502 mm² at the post and 7,819.502 mm² at the header. Geometry differs from the ordinary rail/principal patch. |
| **clip_split_header_center_right** | **center_post_right_1**, **center_post_right_2**, **center_post_header_right_1**, **center_post_header_right_2** | Proper-rotation counterpart of the left center-post cleat. It has the same 50.00/35.00 mm pitches, 139.2174/179.2174 mm modeled shaft lengths, receiver order split, 5,322.570 mm² post/header seat, and per-side cleat contact areas. |
| **clip_split_base_center_left** | **center_principal_left_1**, **center_principal_left_2**, **center_principal_header_left_1**, **center_principal_header_left_2** | Two axes connect **center_principal_cleat_left** to **base_principal_center_left** and two connect it to **base_header**. Pitches are 53.00 mm at the principal and 65.00 mm at the header; modeled lengths are 139.2174 and 190.0174 mm. Both pairs run cleat→receiver. The header/principal direct seat is 5,113.122 mm²; cleat contacts are 16,208.820 mm² at the principal and 11,637.122 mm² at the header. A separate 5,322.570 mm² bottom-rail/principal seat also meets this principal node. The trimmed block is 83.9×139.7×134.7 mm. |
| **clip_split_base_center_right** | **center_principal_right_1**, **center_principal_right_2**, **center_principal_header_right_1**, **center_principal_header_right_2** | Separate right singleton cleat pattern with the same 53.00/65.00 mm pitches and 139.2174/190.0174 mm modeled lengths. The direct header/principal seat is 5,113.122 mm²; principal and header cleat contacts are 15,068.728 and 11,637.122 mm². The additional bottom-rail/principal seat is 5,322.570 mm². Equal blank dimensions and volume do not establish a rigid transform to the left singleton. |

These plumb nodes therefore cannot use the ordinary 33.00/33.00 mm bore grid
or its 152.4 mm shaft envelope as their exact geometry. Their two bolt pairs
attach different host sections and share bearing with separate direct seats.
The principal blocks were trimmed 5 mm at outer faces and tops in this
revision; their direct contacts and axes were rechecked in the current graph
and grip screen.

## Four outer-node former duties

The former header-to-outer-post duty and the former header-to-side duty on each
side are now mapped to one connected chain. Each historical duty row below
therefore names the same six current axes for that side; this records
many-to-one geometry coverage, not a separate accepted replacement for either
duty.

| Former duty | Shared exact current axes for this side | Geometric chain and distinctions |
| --- | --- | --- |
| **clip_timber_header_outer_left** | **knee_outer_left_post_1**, **knee_outer_left_post_2**, **knee_outer_left_side_1**, **knee_outer_left_side_2**, **knee_outer_left_inner_header_1**, **knee_outer_left_inner_header_2** | The post pair crosses **knee_outer_left_spine** and **base_post_outer_left** (42.05 mm perpendicular spacing, 101.6 mm shafts). Under the proposed +Z grain scenario, its spine lower/upper end distances are 31.75/244.55 mm at post 1 and 73.80/202.50 mm at post 2; the distinct outer-post receiver has 171.45/67.45 mm and 213.50/25.40 mm. The side pair traverses spine, **base_side_left**, and **knee_outer_left_inner_frame_block** in one axis (45.00 mm separation, with ΔY=28.9254 mm and ΔZ=34.4720 mm, 241.3 mm shafts). The two inner-header axes join **base_header** to that inner-frame block (202.5 mm shafts, 93.35 mm perpendicular spacing with a 22.098 mm global-Z stagger); their head-to-nut orders oppose one another. This is a multi-member chain, not a cleat two-pair patch. |
| **clip_angle_base_left** | Same six left-side axes listed above | Shares that same chain and the same direct faces: spine/post 13,139.963 mm²; spine/side and side/inner-frame each 15,653.565 mm²; header/inner-frame 11,766.458 mm². Spine and inner-frame endpoints are separated, with the side member intervening; no direct spine-to-inner-frame seat is present. |
| **clip_timber_header_outer_right** | **knee_outer_right_post_1**, **knee_outer_right_post_2**, **knee_outer_right_side_1**, **knee_outer_right_side_2**, **knee_outer_right_inner_header_1**, **knee_outer_right_inner_header_2** | Right counterpart: same receiver sequence and distances by member: spine ends 31.75/244.55 mm and 73.80/202.50 mm; distinct outer-post ends 171.45/67.45 mm and 213.50/25.40 mm; side-pair ΔY=28.9254 mm and ΔZ=34.4720 mm; inner-header perpendicular spacing 93.35 mm with 22.098 mm global-Z stagger. Modeled shafts are 101.6/241.3/202.5 mm, with opposed head-to-nut order in the inner-header pair and the same four contact areas as the left. |
| **clip_angle_base_right** | Same six right-side axes listed above | Shares that same right-side chain. It cannot reuse the ordinary two-receiver geometry because the side bolt axes cross three members and the header connection enters through a distinct inner-frame block. |

The exterior spine proposal is a 38.1×139.7×276.3 mm single 2×6 blank with
long grain +Z. The end/edge values above are kept separately for the two wood
receivers in each post-bolt axis. They are signed-branch geometry inputs; no
current post-axis action selects which end is loaded or unloaded. The
inner-frame block scenario is +Z but is explicitly less
directly supported by the stock review; its proposed blank is
88.9×133.35×139.0 mm. The side host's source-frame grain is T and the outer
post grain is +Z; the header grain is X. These conditional/source-frame
assignments differ from the ordinary patch's one cleat, rail, and principal
grain layout. As in the other sections, no stock orientation is observed.

## What is still missing for mechanics reuse

The current hold-datum file contains only A12, K12, and A1 point/frame
references and explicitly marks itself **not_a_load_or_mechanics_result**. It
does not provide signed force or moment demands for the former duties, per-axis
actions, contact pressure state, force split between direct seats and bolts,
or local member resultants. Therefore this geometry map cannot establish
whether a rotated ordinary case produces the loaded or unloaded side of any
current pair, whether a bolt row reverses tension, or whether a local response
transfers through another connected joint.

The contact graph records current member-pair geometry only. It does not
assign contact law, active bearing, load share, stiffness, fastener resistance,
wood resistance, or complete-joint capacity. The modeled bolt envelope also
does not establish a selected delivered product or thread engagement. A later
mechanics comparison must use the exact per-station bodies and their
signed demand vector and keep the several shared host and retained-frame
connections in scope. Same block pattern is evidence for reusing that block
geometry only.
