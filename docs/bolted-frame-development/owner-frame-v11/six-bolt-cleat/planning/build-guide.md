# Build guide: fixed 102-bolt frame

The owner is proceeding with the retained `v11-six-bolt-cleat-v1` design as-is. This guide organizes its existing construction information; it does not change the design or assert structural acceptance. The [evaluation record](../README.md#current-acceptance-work) retains the numerical exceedance, material and installation assumptions, unverified no-slip floor condition and other limits.

Use the [printable build packet](build-packet.html) and [30 dimensioned part-reference sheets](part-reference-sheets.html) alongside this guide. The current [102-axis hardware crosswalk](hardware-axis-crosswalk.csv), [136 receiver records](receiver-planning.csv) and [hole mask](omitted-post-hole-mask.csv) govern the bolt layout. Older 112-bolt/A574/spacer shopping lists do not govern this frame.

## Materials and cut-piece inventory

Use dry DF-L No. 2 timber on the recorded basis. Nominal 2×6 means 38.1 × 139.7 mm; nominal 4×6 means 88.9 × 139.7 mm. The existing [13-board assignment](../../shorter-bolts/build-package/geometry-packet/stock-allocation.csv) includes 25.4 mm per-end trim and 3.175 mm per-member kerf planning allowances; its finished envelopes are not square-blank saw settings.

| Stock | Boards | Assigned pieces |
| --- | ---: | --- |
| 2×6 × 8 ft | 5 | Two floor runners and two center front posts; left/right bottom, lower-service and upper-service rails |
| 2×6 × 10 ft | 3 | Header and two center principal supports |
| 4×6 × 8 ft | 3 | Two rear legs, two outer front posts and top rail |
| 4×6 × 10 ft | 2 | Left and right side rims |

This yields **20 sawn pieces**. Keep each source ID on its piece: `base_floor_left/right`, `base_header`, `base_post_center_left/right`, `base_post_outer_left/right`, `base_principal_center_left/right`, `base_rail_bottom_left/right`, `base_rail_service_lower_left/right`, `base_rail_service_upper_left/right`, `base_rail_top`, `base_side_left/right` and `lumber_leg_left/right`.

| Sheet cut pieces | Quantity | Material and IDs |
| --- | ---: | --- |
| Main climbing panels | 4 | Recorded Roseburg AC fir 23/32 CAT face-panel basis: `main_lower_left/right`, `main_upper_left/right` |
| Whole kickers | 2 | Same face-panel basis: `kicker_left/right`; retain their complete outlines |
| Cleat leaves | 4 | Nominal ¾-inch generic birch: `eoere_cleat_left`, `eoere_cleat_left_outer`, `eoere_cleat_right`, `eoere_cleat_right_outer` |

The four leaves make two glued cleats, each with two nominal 19.05 mm leaves. These are **cut-piece counts**, not a new plywood-sheet purchasing layout. Finished piece envelopes are **1217.6125 × 1219.2 mm** for each main panel, **1217.6125 × 277 mm** for each kicker and **361.186083 × 139.7 × 19.05 mm** for each trapezoidal cleat leaf. Use the current outlines and the [existing member/cut records](../../shorter-bolts/build-package/geometry-packet/member-cut-planning.csv). Retain the [recorded face-panel selection](../../owner-material-purchase-decisions.json); the birch purchase applies to the cleats.

## Hardware shopping and sorting

The [grouped schedule](grouped-hardware.csv) requires **102 bolts, 102 nuts, 204 washers, 24 angles and 66 panel/kicker screws; no spacers or packers**. Quantities below are individual pieces. Existing product links are references, not a current price, stock or delivered-inventory check.

| Quantity | Bolt, all Grade 5 hex head and retained partial-thread profile | Recorded SKU/type |
| ---: | --- | --- |
| 48 | 3/8–16 × 2½ in | Bolt Depot 363 |
| 8 | 3/8–16 × 3 in | Bolt Depot 365 |
| 2 | 3/8–16 × 4½ in | Bolt Depot 368 |
| 24 | 3/8–16 × 4¾ in | Zoro G0341148 |
| 12 | 3/8–16 × 6½ in | Conditional Style 1 HCS type; supplier SKU unselected |
| 4 | 3/8–16 × 6 in | Conditional Style 1 HCS type; supplier SKU unselected |
| 4 | 1/2–13 × 8½ in | Zoro G0340956 |

| Quantity | Remaining hardware |
| ---: | --- |
| 82 | 3/8–16 SAE J995 Grade 5 nuts, Bolt Depot 2571 |
| 16 | 3/8–16 SAE J995 Grade 8 nuts, 2584, for the sixteen conditional long bolts |
| 4 | 1/2–13 SAE J995 Grade 5 nuts, 2573 |
| 196 | 3/8-inch USS washers, 15023 dimensional family; sort into the thickness groups below |
| 8 | 1/2-inch USS washers, 15025 dimensional family |
| 24 | Retained Eoere ZX128-B-T4 factory angles; owner reports owning this bracket model |
| 66 | Purchased Hillman 42605, #10 × 2½ in, #2 Phillips: 48 main-panel screws and nine per kicker |

Put one specified washer under every bolt head and one under every nut. All washers require the existing **minimum Fy of 200 MPa**, retained ID/OD and bearing-face geometry. The nominal SKU or “Grade 5” wording alone does not establish that material requirement; the [receiving specification](../washer-material-specification.json) identifies the existing documentation basis.

| Washer group | Quantity | Retained delivered-thickness range |
| --- | ---: | --- |
| Ordinary 3/8-inch ends | 184 | 2.35–2.6416 mm |
| Front/rear floor-joint 3/8-inch ends | 12 | 1.6256–2.032 mm |
| All 1/2-inch ends | 8 | 2.85–3.175 mm |

The twelve thinner foot washers are both ends of `rail_front_bolt_left_1/2`, `rail_front_bolt_right_1/2`, `rail_rear_bolt_left_1` and `rail_rear_bolt_right_1`. Keep these separately labeled. The current minima are recorded in the [evaluation’s working-assumption table](../README.md#current-working-assumptions); the earlier 2.30 mm addendum is historical.

### Sixteen special long bolts

Use the [current active-profile binding](profile-contract-binding-v1.json) and its [compact source profile intake](../../external-hex-heads/build-package/hardware-profile-intake.json). Both lengths specify ASME B18.2.1-2012 full-size-body, partially threaded hex cap screws with default Style 1 continuous-radius fillet and separately specified SAE J429 Grade 5 material. A generic length/grade listing, full-thread bolt or seven-inch substitute does not describe this contract.

| Profile requirement | Twelve 6½-inch bolts | Four 6-inch front bolts |
| --- | ---: | ---: |
| Underhead length | 160.528–165.1 mm | 149.86–152.4 mm |
| Minimum full-body length from underhead | 125.476 mm | 119.126 mm |
| Maximum grip-gaging input, LG | 133.35 mm | 127.0 mm |
| Minimum full-form thread length | 31.75 mm | 25.4 mm |
| Full-body diameter | 9.3726–9.525 mm | 9.3726–9.525 mm |

Keep the contract’s conditional UNRC-2A/no-undercut core requirements and 7.31774 mm analysis root floor. LG is a gaging limit, not an observed thread start or proof that the nut seats freely. The twelve 6½-inch axes are the four `cleat_post_bolt_*` axes, `eoere_bolt_067/070/071/074` and four `v11_cleat_*_side_*` axes. The four six-inch axes are `rail_front_bolt_*`. Their recorded hex across flats is 9/16 inch.

## Tools, datums and marking

Have the cutting tools needed for the drawn profiles, a drill and suitable guide, clamps, exit backers, awl/transfer marker, tape/rule, square and calipers. Have matching hex wrenches/sockets, a #2 Phillips driver, the selected Kobalt #10 pilot/countersink insert, sanding/dust-removal supplies, mixing containers and either volume measures or a suitable weighing scale for T-88. Printed jigs are marking aids.

All part-sheet dimensions are millimetres. Label each piece with its exact ID, left/right hand, reference face and local zero before cutting or marking. L follows the saved grain/reference axis; U and V follow that part’s shown basis. Header U/V and runner U/V are different: do not reorder dimensions by assuming U is always thickness. Preserve the actual bevels, continuous rear-leg recess and whole kicker profiles shown on the part sheets.

The assembly is not a simple mirror about world X = 0. Left/right rail lengths and the right-side kerf offset differ. Use each part’s own sheet and datum; do not flip a left template to make a right part. Receiver CSV endpoints mean increasing axis parameter, **not a selected drilling side**. Historical BRep face numbers and viewer image scale are not physical measuring datums.

The [horizontal marking jig](../../shorter-bolts/build-package/bracket-jig/README.md) applies only to the twelve listed loose-rail FAR pairs, before adjacent timber blocks its end stop. The [handed V3 rear-foot templates](../../shorter-bolts/build-package/runner-leg-jigs/README-v3.md) print in millimetres at 100%, flat skin down and ribs up; use their scale check. Their 2 mm apertures take an awl, not a drill. Neither template supplies post-flange height registration or every frame hole.

## Cleat glue-up

Use the recorded **System Three T-88 structural-cleat process**; ordinary wood glue remains the general preference elsewhere. Match the two leaves for each hand and preserve the shown grain orientation. Prepare clean unfinished faces, remove sanding dust and avoid sanding through a thin face veneer. Apply adhesive across the mating faces, bring them into maintained contact and keep the pair registered without squeezing the adhesive out.

Mix **1:1 resin/hardener by volume OR 100:83 by weight**; do not interchange the ratios. The retained manufacturer process gives about **45 minutes working time, 6–8 hours hardening and 24 hours functional strength at 70°F**. Allow the temperature-dependent cure before subsequent machining/loading; colder conditions take longer. Follow the current product instructions for handling and cure. The effective 0.2 mm analysis zone is not a shop gap, shim, spread-thickness target or clamp-pressure instruction. [Recorded structural-cleat basis and sources](../README.md#structural-glue-exception) · [Manufacturer product instructions](https://www.systemthree.com/products/t-88-structural-epoxy-adhesive)

## Coordinated assembly sequence

1. Sort stock and hardware into labeled piece/axis groups. Lay out the twenty timber profiles and ten sheet pieces from their own sheets. Preserve the finished datums while making the cuts; keep the leg recess and sloping foot surfaces together with their handed marks. Prepare and cure the paired cleat leaves, then finish their registered outlines and bores.
2. Support the incomplete frame while dry-fitting the two side/leg/runner assemblies, header, top, center supports and horizontal rails. Fit the factory angles and cleats in their recorded orientations. Keep **two bolts at each rail–leg joint, one at each leg–floor joint and six at each cleat**. Identify head and nut access before closing adjacent assemblies or fitting panels.
3. Mark and cut the [32 existing timber service bores](service-passage-layout.csv) on their eight named hosts using the separate passage marks on the part sheets. The printed coordinates already include the recorded F1–G1 40 mm routing shift; do not add it again. Do not copy the older ten T-nut recesses or add other timber wiring cutouts. These Ø38.1 mm openings are separate from frame-bolt holes. Mark only the active axes in the current crosswalk. Use actual bracket factory holes as transfer-marking references where applicable; do not populate every steel hole. The four `v11_cleat_left_post_1/2` and `v11_cleat_right_post_1/2` near-post positions are masked and receive **no wood mark or drill**. The outer-top connections retain their active FAR pairs only. Keep the [current mask](omitted-post-hole-mask.csv) at the bench.
4. Label the matching faces, clamp the matching wood receivers in their dry-fit registration and temporarily disassemble as needed for drill-guide access. Transfer marks before removing a fitting, then remove marking templates and steel fittings from the wood-clearance-bit path. Keep the steel factory holes unchanged. Use a guide and exit backer, preserving the matched centerline through the wood receivers. Do not elongate a hole or use a driven bolt to pull misregistered parts together.
5. Use the existing finished **wood bolt-clearance** rule: nominal D + 1/32 to D + 1/16 inch. That is **10.31875–11.1125 mm for 3/8-inch bolts**, and **13.49375–14.2875 mm for 1/2-inch bolts**. Select a bit/process that produces the required finished opening and check the opening itself. The receiver’s occupied CAD bore, a factory steel hole and a screw pilot are different things; the CSV does not itself select a bit, bushing, approach or drilling depth.
6. Reassemble complete bolt/washer/nut stacks in the current per-axis orientation, with the correct long-bolt profiles and washer groups. Maintain flat washer seats and the intended timber/angle backing contact. Fit all parts before final snug seating. The existing analysis credits **no tightening preload or interface friction and supplies no installation torque value**. Preserve tool access: the four short-post nut positions have recorded long-tool obstructions; the compact approach screened in the source is 25.4 mm diameter × 25.4 mm long, not a measured tool fit.
7. Fit the four main panels and two kickers, keeping the existing outlines, seams, backing and [66 current screw stations](../../shorter-bolts/build-package/geometry-packet/panel-screw-axis-planning.csv). Do not transpose an earlier candidate’s screw heights. Preserve access to the bolt stacks before covering them.
8. For Hillman 42605, use the owner-selected **Kobalt #10 insert: 1/8-inch pilot and 3/8-inch face countersink**, then drive with #2 Phillips so the flat head is flush without breaking through the face veneer. Carry out the recorded same-plywood/scrap-DF-L offcut check before the production holes. Do not turn this lead hole into a plywood clearance hole. The old 50.8 mm screw length and 4.1402 mm occupied diameter in analysis CSVs are not the purchased 63.5 mm screw or its pilot. [Purchase/tool record](../../../../current-panel-screw-purchase.md)
9. Use the [current 142 T-nut / 132 LED opening table](panel-opening-layout.csv) for panel marks: view the climbing face, measure from its left edge and the stated TOP/DOWN or BOTTOM/UP datum. The table already includes the existing G2 LED +5 mm outward move; do not add it again. Right-hand offsets already include the present kerf placement. These openings are separate from the 66 attachment screws. Follow the existing [hold/T-nut instructions](../../../../moonboard-hold-hardware.md) and [LED layout instructions](../../../../led-wiring-reference.md) for those separate panel openings. Reconcile the finished part and fastener counts, backing, complete stacks and accessible nuts against this packet. Record observations only when made; the floor condition remains the assumption stated in the evaluation record.

## Printable completion record

Leave entries blank until observed. Keep this record with the printed sheets; do not pre-fill or rewrite the frozen CSV Actual/Disposition cells.

| Check | Date / initials | Actual / notes |
| --- | --- | --- |
| Thirteen stock boards identified; twenty timber IDs and handed datums marked | | |
| Four main panels, two kickers and four cleat leaves identified | | |
| T-88 mix basis, glue-up temperature and cure interval recorded | | |
| 102 bolt types/lengths, 102 nuts and sixteen long-bolt profiles matched | | |
| 184 ordinary, twelve foot and eight larger washers sorted to current requirements | | |
| Dry-fit and tool access checked before transfer marking | | |
| Current active axes marked; four masked near-post positions left unused | | |
| Matching wood holes aligned; finished openings and washer seats checked | | |
| 32 source-listed timber service bores and existing routing shift checked | | |
| 102 complete two-washer stacks fitted; zero spacers/packers | | |
| Hillman offcut pilot/countersink/flush-head result recorded | | |
| 48 main-panel and eighteen kicker screws installed at their recorded stations | | |
| 142 T-nut and 132 LED openings matched; existing G2 shift retained | | |
| Final part/count/backing/access observations recorded | | |
