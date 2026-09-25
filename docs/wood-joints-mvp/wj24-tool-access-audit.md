# WJ24 bolt tool and access audit

Status: **coverage audit only; no candidate bolt has a complete WJ24
installation or removal route.** This maps tool and handling evidence against
the 104 bolt axes in the [WJ24 composition](hypotheses/wj24-integrated-static/composition.json)
and [hardware inventory](hypotheses/wj24-hardware-inventory/inventory.json).
It does not select hardware, approve a tool, establish physical fit, or turn a
local clearance result into a full-layout pass.

The composition is `wj24-twenty-four-duty-integrated-static-v1`, trial
`wj24-wj18-plus-top-center-bottom-pairs-v1`. It contains 24 target duties, 28
candidate connector parts, 104 bores, and 520 installed hardware CAD roles.
The inventory schedule binds every candidate axis to its family, station,
receiver pair, modeled grip class, and provisional installed roles. This is
CAD occupancy only. The full-scene diagnostic reports no candidate installed
component conflict, but keeps `movement_or_installation_access_proven` false.
Its 12 retained frame-bolt arrangements are separate from these 104 candidate
axes; their tool and withdrawal proxies remain part of the obstacle scene.

## Axis coverage

The axis patterns below expand to the exact IDs in the inventory's
`candidate_hardware_axis_schedule`; together they cover 104 unique axes. Braces
mean each listed value is combined independently with the other brace groups.

| WJ24 family | Axes and exact ID pattern | Installed evidence | Existing tool/access evidence and its limit |
|---|---|---|---|
| `wj03_outer` (20) | `knee_outer_{left,right}_{bridge_link,bridge_spine,header,post,side}_{1,2}` | All 20 axes have five provisional stack roles in the WJ24 composition and inventory. | The archived [WJ-03 compact-outer tool report](hypotheses/wj03-compact-outer-tools.md) covers these exact axis IDs in its local trial. It checks socket approach, sampled open-end-wrench strokes, nut and washer handling, bolt withdrawal, and head-washer release. It reports clear bolt-only withdrawal and loose-nut removal for all 20, but the full-turn wrench proxy overlaps all 20; the socket-plus-nut axial exit overlaps four; the nut-washer slide overlaps two. It assumes removable holds and projecting hold bolts are already removed. It does not include the other WJ24 candidate families in the tool-path scene, so none of its clear sub-operations is a WJ24 route pass. |
| `wj05_backer` (4) | `backer_header_{left,right}_{1,2}` | Four provisional CAD stacks each have `bottom_head`, `bottom_washer`, `shaft`, `top_nut`, and `top_washer` roles. A `top_washer` CAD envelope represents three physical washers; the inventory counts four physical washers per bolt. | [Transport operations](transport-operations.md#wj-05-center-backer-states-and-below-access) records the only current access dependency: bottom head pockets are reached from below while the frame is open or lifted, with the nut side above. A modeled deep socket projects about 54.8 mm below the backer before ratchet/extension clearance. This has no selected tool, verified receiver fit, complete counterhold/turn route, support transfer, or reverse route. The stack SKU and delivered thread engagement are also unassigned. |
| `wj04_g7` (8) | `wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/{lower,upper}_{principal,rail}_{1,2}` | All eight bores and five-role stack envelopes are represented in the WJ24 inventory. | No operation-specific access report is bound to these exact WJ24 axes. The [ordinary WJ-04 tool report](wj04-tool-access.md) is a different local trial at `clip_horizontal_lower_right_1`; its FACOM open-wrench candidate and operation screens do not transfer to this WJ04-G7 trial. The separate G7 LED withdrawal finding is a service-motion issue, not bolt-tool evidence. |
| `wj06_outer_pair` (8) | `wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis/{lower,upper}_{rail,side}_{1,2}` | All eight installed stack envelopes are represented. | No operation-specific head/nut tool route or counterhold screen is recorded for these axes. Static installed-stack checks do not answer tool entry, turn/regrip, removal, or retrieval. |
| `wj05_center_x190` (16) | `center_post_header_{left,right}_{1,2}`; `center_post_{left,right}_{1,2}`; `center_principal_header_{left,right}_{1,2}`; `center_principal_{left,right}_{1,2}` | All 16 provisional stacks and receiver pairs are inventoried. Their nominal modeled lengths are unassigned; modeled grips are 100.915644, 127, or 167 mm. | The [WJ-05 center-tools comparison](hypotheses/wj05-center-tools/README.md) screens only `center_principal_header_left_2` and `center_principal_header_right_2` in its earlier local trial, using catalog-sized socket, extension, ratchet, and FACOM wrench envelopes. It finds extension/head, inward counterhold, and ratchet/backer or post/washer overlaps; the alternate ratchet stroke still hits the post washer and timber. Receiver fit and complete turning/counterhold remain open. The other 14 axes have no matching operation screen. The two screened axes share IDs with WJ24, but the older report's scene and local member state differ; it is comparison evidence, not WJ24 access acceptance. |
| `left_service` (16) | `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_1/{lower_rail,lower_side}_{1,2}`; `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_2/{lower_principal,lower_rail}_{1,2}`; `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_upper_left_1/{upper_rail,upper_side}_{1,2}`; `left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_upper_left_2/{upper_principal,upper_rail}_{1,2}` | All 16 installed stack envelopes and receivers are represented. | No exact operation-level head/nut tool, counterhold, regrip, or removal path is recorded for these axes. The family name and installed CAD geometry do not imply mirrored tool access. |
| `top_outer` (8) | `top_outer/clip_single_top_{left_1,right_2}_{rail,side}_{1,2}` | All eight installed stack envelopes are represented. | No exact operation-level access route is recorded. The WJ-03 report is for different axes and its open/clear findings do not cover these top stations. |
| `top_center` (8) | `top_center/clip_split_top_center_{left,right}_{principal,rail}_{1,2}` | All eight installed stacks have a current WJ24 full-scene static check. | WJ24 records generic head/nut approach envelopes for both ends of all eight axes. Head approaches are clear in that proxy. Each of the four principal-bolt nut approaches overlaps the opposite-side matching principal nut envelope (1,064.085706 mm³ per reported pair); both rail-pair nut approaches have no reported peer-envelope hit. Every axis still marks receiver-tool fit and full turning stroke/counterhold unresolved. The proxy is not a catalog tool or a complete operation. |
| `bottom_outer` (8) | `bottom_outer/clip_horizontal_bottom_left_1/{rail,side}_{1,2}`; `bottom_outer/clip_horizontal_bottom_right_2/{rail,side}_{1,2}` | All eight installed stacks have a current WJ24 full-scene static check. | WJ24 records generic 25.4 mm diameter × 50 mm head/nut approach cylinders. The two side-1 head approaches hit fixed service wires (`wire_001_A1_A2`: 182.434194 mm³; mirrored `wire_121_K1_K2`: 205.919258 mm³). Each rail-2 nut approach intersects the archived WJ-03 side-nut tool proxy. The remaining recorded approaches have no reported overlap in that limited screen. These results only screen the bottom-outer approach proxies; they do not validate the WJ-03 tools or complete any bolt operation. |
| `bottom_center` (8) | `bottom_center/clip_horizontal_bottom_left_2/{principal,rail}_{1,2}`; `bottom_center/clip_horizontal_bottom_right_1/{principal,rail}_{1,2}` | All eight installed stacks have a current WJ24 full-scene static check. | WJ24 records generic head/nut approach envelopes. The left principal-1 head envelope intersects `wire_049_E1_E2` (205.919258 mm³); the mirrored right principal-1 head envelope intersects `wire_073_G1_G2` (205.908164 mm³). Each principal nut envelope overlaps the opposite-side matching principal nut envelope (1,064.085706 mm³); right principal nut approaches also hit `wire_071_F2_F1`. Both rail nut approaches per side intersect the neighboring center-principal cleat (9,716.015633 or 4,188.225330 mm³); the right rail-1 nut also intersects `wire_072_F1_G1`. All eight axes mark receiver-tool fit and turning/counterhold/sequential access unresolved. |

Each brace pattern expands independently. No family inherits another
family's access result because its axis is nearby, mirrored, similarly named,
or has a matching nominal grip.

## What the current full-layout screens establish

The WJ24 compositor and diagnostic establish source-bound identity and static
occupancy: 104 candidate bores, 520 installed CAD roles, 28 candidate parts,
24 replaced duties, 144 removed legacy SDS axes, 66 fixed panel/kicker axes,
and 12 starting frame-bolt arrangements. This means the audit can name which
model stack each operation must cover. It does not establish that any real
bolt, nut, washer, wrench, socket, or driver is present or fits.

The current WJ24 access rows cover only the 24 bottom-outer, top-center, and
bottom-center axes above, and are nonreceiver approach-envelope comparisons.
For top-center and bottom-center, the diagnostic itself marks complete
turning/counterhold and sequential access unresolved. For bottom-outer, the
reused 25.4 × 50 mm cylinder is a generic proxy; the report labels tool fit
unestablished. The WJ24 diagnostic's `movement_or_installation_access_proven`
gate is false. None of the archived local results changes that gate.

The [ordinary WJ-04 hardware basis](ordinary-hardware-basis.md) nominates a
FACOM 34 7/16-in open-end wrench as a tool candidate for its separate narrow
WJ-04 trial and says a paired wrench operation still needs screening. Its
published head/handle envelope is not a physical-fit result and does not
qualify the eight WJ04-G7 axes above. The WJ-04 access report's modeled 30°
working strokes, open-end exit proxy, 60° reindex, nut slide, bolt withdrawal,
and head-washer release are a useful operation vocabulary, but the sampled
15°/75° headings and broad boxes remain that report's own diagnostic inputs.

The [WJ-03 report](hypotheses/wj03-compact-outer-tools.md) identifies a
promising sequence to test on its 20 exact axes: hold the nut with the FACOM
open-end candidate, turn the bolt from the head side with the Ko-ken
7/16-in socket and a named ordinary 3/8-drive ratchet, withdraw the bolt
through the nut, then remove the loose nut and washer. Its clear bolt-only
withdrawal does not verify this sequence: the head-side ratchet/socket sweep,
fixed nut counterhold, stack capture, and loose-part handling after withdrawal
were not checked. Treat this as a candidate operation contract for a future
full-layout screen, not an approved procedure.

## Reusable operation record

Every candidate bolt should have a forward and reverse operation record bound
to its exact WJ24 axis ID. At minimum, the record needs:

1. The source layout/trial, station ID, bolt axis and direction, receiver pair,
   modeled stack roles, hardware-selection state, and the support state for
   the joint and nearby members.
2. The actual proposed head-side and nut-side tools, source-bound dimensions,
   engagement or jaw fit, entry side, and continuous approach and withdrawal
   shapes. A cylinder or rectangular envelope may be used for early screening
   only if clearly labeled as a proxy.
3. The work sequence: insert bolt; place and retain washers/nut; counterhold
   one end; turn the other; repeat each bounded stroke and regrip; confirm
   thread disengagement; capture the loose nut and washers; withdraw the bolt;
   release and capture the remaining washer. Record the reverse installation
   path as well.
4. The state of adjacent candidate stacks, all 12 retained frame-bolt
   assemblies, 66 fixed panel/kicker screw axes, nearby wood, panels, holds,
   lights and wires during each motion. Any assumed removal or service state
   must be an explicit prerequisite and also have a recovery path.
5. The support transfer and stable staging state before a bolt is released,
   plus the path for tools and loose parts after removal. For the WJ-05
   backers this includes below access while open/lifted and reverse access
   before the frame closes or is set down.
6. The result for each operation step, exact modeled obstacles, relevant
   dimensional allowances, unmodeled fit/hand/contact questions, and a clear
   statement that CAD clearance does not establish physical fit.

This preserves bolt, washer, and nut operations separately from connector
parts and individual transport members, as required by the [transport
operations contract](transport-operations.md#wj-07-acceptance-record). It
also gives WJ-07 the named support and reverse-path evidence it needs. No
operation may assume that structural wood threads are routinely removed.

## Suggested order of work

1. Bind the contract to the frozen 104-axis inventory and obtain explicit
   ordinary-hardware and tool candidates per modeled grip/orientation class.
   The inventory assigns no catalog bolt length to the 16 WJ05-center-x190
   axes, and no universal SKU to the other WJ24 classes. Do not derive tool
   dimensions or delivered shank from an analysis envelope.
2. Resolve the current WJ24 approach-envelope blockers for bottom-center,
   top-center, and bottom-outer in a named geometry variant, then rerun the
   full scene. In parallel, screen the exact full operation—not just approach
   entry—for these 24 axes.
3. Test the WJ-03 head-turn/nut-counterhold sequence as a separate operation
   hypothesis. First close its unmodeled head-side working sweep and nut-side
   counterhold; then check the 20 axes against the assembled WJ24 scene and
   its support/service states. Do not carry forward local clear counts.
4. Define and screen the WJ-05 backer operation while the frame is open or
   lifted, including the bottom tool/ratchet path, top nut counterhold, tool
   withdrawal, support transfer, and complete reverse route.
5. Apply the same per-axis record to the uncovered WJ04-G7, WJ06 outer-pair,
   remaining WJ05-center-x190, left-service, and top-outer axes. Close WJ-07
   only after all 104 axes are accounted for in forward and reverse states.

The [access-relief probe](../../scripts/wood_joint_wj24_access_relief_probe.py)
addresses the G1/G12 provisional hold-bolt corridors and G7 LED withdrawal.
Those are geometry/service questions: they do not establish wrench or socket
access. Any geometry relief must be brought into the composed WJ24 scene
before its bolt routes are screened again.

This audit is not a fabrication release, physical fit finding, approved
assembly/disassembly procedure, mechanical acceptance, candidate selection,
or climbing release.
