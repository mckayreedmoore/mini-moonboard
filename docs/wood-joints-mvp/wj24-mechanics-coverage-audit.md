# WJ24 mechanics coverage audit

Status: evidence crosswalk, 2026-09-24. All 36 migrated criteria and all 11
wood-candidate obligations remain pending. This audit identifies what the
current complete-layout evidence actually covers, the missing candidate
specific demand or method, and the next bounded output needed for each item.
It does not change criteria status or accept geometry, loads, capacity, access,
fabrication, or release.

## Current evidence boundary

The current WJ24 composition is a source-bound, complete *static geometry*
layout: 24 former duties map to 28 connector parts and 104 proposed bolt axes;
all 144 old SDS axes are removed; all 66 fixed Hillman axes and 12 starting
frame-bolt arrangements remain represented. The diagnostic checks exact
inventory and source identities, finished-solid intersections, receiver cuts,
installed CAD role fit, and changed-host/frame-bolt geometry. Its 18
implemented static and source-tracking gates pass. It reports
`capacity_established=false`, `complete_joint_acceptance=false`,
`integrated_clearance_accepted=false`,
`movement_or_installation_access_proven=false`, and all release flags false.
These results are a geometry baseline for further work, not physical load-path
or mechanics acceptance.

The current WJ24 findings that can change geometry or constrain a mechanics
model are specific. The bottom-center left cleat / bottom-rail finite common
face is 10,385.137652 mm² after the E1–E2 service passage; the WJ24 full-contact
slab has a 0.984095945 material fraction at that interface. Rear hold envelope
G1 intersects the bottom-center right cleat by 745.512902 mm³ and G12
intersects the top-center right cleat by 562.789151 mm³. A bounded rearward
withdrawal sweep of LED G7 intersects the lower full-stock cleat by
319.657955 mm³. Those are current geometric constraints, not loads, capacities,
or proof that another tool or staging sequence cannot work.

The source inventory and composition can trace nominal receiver/axis
relationships, but the two center receiver paths do not yet have accepted
backer-to-frame resistance. Four fixed center-kicker axes terminate in two
4×4 backers with 45.24375 mm nominal receiver length; both backer/header
attachments remain unresolved. Twelve frame-bolt records, axes, and CAD
assemblies reconcile, and changed-host cutters clear the finished-host
occupied-axis proxy, but the WJ24 structural recheck is explicitly incomplete.
The 104 candidate axes, 52 ordered wood-interface groups, and 520 CAD roles
do not supply signed actions, stiffness, resistance, or force sharing.

For reference, the crosswalk uses these evidence anchors:

| Anchor | Current evidence and limit |
| --- | --- |
| **I1 — source inventory** | [`source-inventory.json`](source-inventory.json) and [`source-inventory-summary.md`](source-inventory-summary.md) authenticate source identities, 24 duties, 144 former SDS axes, 66 fixed screw axes, 12 frame bolts, six source contacts, and two receiver obligations. This is the migration/source ledger, not a candidate load-path check. |
| **G24 — full-layout geometry** | [`composition.json`](hypotheses/wj24-integrated-static/composition.json), [`diagnostic.json`](hypotheses/wj24-integrated-static/diagnostic.json), and the [run note](hypotheses/wj24-integrated-static/README.md) provide the exact counts, source hashes, 18 implemented gate results, finished-shape screens, receiver-axis checks, contact-face geometry, and listed findings. The [parent audit](hypotheses/wj24-integrated-static/parent-audit.json) independently checks source hashes and fourteen retained raw hosts. All are static/nominal evidence. |
| **C1 — reduced center face** | [`bottom-center-contact-and-hold/README.md`](hypotheses/bottom-center-contact-and-hold/README.md) attributes the 167.835055 mm² loss to the E1–E2 service passage and measures the finite common faces. It establishes nominal area and cause, not pressure or bearing resistance. |
| **B1 — backer geometry witnesses** | [`wj12-backer-unit-statics/README.md`](hypotheses/wj12-backer-unit-statics/README.md) balances 24 synthetic unit-action cases on historical WJ12 geometry; [`wj12-sampled-sections/README.md`](hypotheses/wj12-sampled-sections/README.md) records named cut-plane areas on WJ12. Neither supplies WJ24 demand, a backer attachment check, or resistance. The in-progress [`wj24-backer-loadpath-contract.md`](wj24-backer-loadpath-contract.md) is the next backer-path evidence target. |
| **F1 — retained frame bolts** | G24 `starting_frame_bolt_recheck` reconciles all 12 records/axes, 60 CAD components, and 72 shapes. The in-progress [`wj24-retained-frame-bolt-audit.md`](wj24-retained-frame-bolt-audit.md) covers changed-host geometry and remaining checks. No frame-bolt actions or strength result exist yet. |
| **N1 — local native-preparation history** | [`native-adapter-readiness.md`](native-adapter-readiness.md), the [`WJ16 input report`](hypotheses/wj16-full-stock-mechanics-inputs/README.md), and [`WJ04 patch preparation`](hypotheses/wj04-patch-mesh/README.md) document partial input and mesh preparation on older/representative configurations. The five-body mesh predates WJ24; none is a WJ24 response or a same-configuration case. |
| **A1 — access and transport findings** | [`wj24-led-extraction/README.md`](hypotheses/wj24-led-extraction/README.md) records the bounded G7 sweep. WJ24 G24 also preserves hold, wire, tool, and static component screens. They do not establish full service, assembly, reverse-removal, or transport access. |
| **H1 — provisional hardware inventory** | [`wj24-hardware-inventory/README.md`](hypotheses/wj24-hardware-inventory/README.md) reconciles 104 proposed bolts, 104 nuts, 216 physical washer equivalents, and 28 connector blanks; 16 center-axis catalog lengths are unassigned and prices are null. It is not a selected BOM or fit/resistance result. |

Native mechanics execution is authorized for this candidate lane, but no fresh
WJ24 native case has run. Readiness remains open on the integrated layout,
complete hardware/contact methods, and same-configuration inputs. Historical
WJ04/WJ12/WJ16 actions, convergence or equilibrium witnesses, catalog-unlisted
capacities, and external sign-off do not close rows in this crosswalk. The
explicit no-slip floor assumption stays as recorded; no floor-friction law or
physical inspection is inferred.

## The 36 migrated criteria

“Next output” names an implementable artifact or calculation, not a promise of
pass. It should be source-bound to the frozen WJ24 revision, carry its exact
criterion ID, and remain pending if the applicable method or input is not
available.

| Exact criterion ID | Current evidence | Missing candidate-specific demand or method | Next implementable output |
| --- | --- | --- | --- |
| `actual_angle_lateral_CD_1` | G24 inventories 104 candidate axes and receiver pairs; no per-axis forces. `bolted_timber_checks.py` and `fea/dowel_yield.py` are constituent references only. | WJ24 signed lateral demand at every applicable shear plane; actual wood thickness, grain, gaps, bolt grade and thread section; applicable adjusted yield-mode method. | WJ24 bolt/receiver input table, followed by a mode-by-mode lateral check report for each actual bolt. |
| `additional_group_reduction_sensitivity` | G24 supplies axis coordinates/groups but no force distribution or chosen group factor. | Design-basis group treatment, row geometry/load direction, and fresh group/per-bolt actions for new and retained groups. | Group inventory plus baseline and adopted sensitivity calculation joined to the WJ24 axis IDs. |
| `local_parallel` | G24 has declared geometry/grain metadata; B1 has synthetic WJ12 unit witnesses only. | WJ24 per-member action resolved to local grain and adjusted bearing values; oblique demand cannot be labeled parallel by default. | Signed interface-action table and separate receiving-member bearing checks. |
| `supplemental_EC5_splitting` | No WJ24 splitting result; WJ12 tear-out/section witnesses do not address cross-grain splitting. | Candidate-specific method applicability or a supported equivalent, with group/end/edge geometry, cuts, grain, and signed cross-grain action. | Applicability/method memo with one bounded splitting calculation per affected fastener group or cut shoulder. |
| `sampled_net_member` | G24 binds finished parts and openings; B1 section samples belong to historical WJ12 only. | Complete WJ24 critical-section stations around all bores/cuts, simultaneous member actions, and adjusted section resistance. | Finished-section inventory and demand/resistance records at each bracketed transition and bolt plane. |
| `header_gross_full_length_stability` | G24 retains the header identity/candidate connections; no full-frame response or accepted restraint stiffness. | Full-length header demand, actual restraint spacing, and WJ24 joint translational/rotational stiffness bounds. | Header stability calculation over selected stiffness cases using fresh WJ24 complete-frame actions. |
| `base_bearing_average` | C1 identifies the real reduced left bottom-center face; G24 provides nominal face geometry only. | Fresh signed compression at each reconciled physical bearing face, active face state/area, and chosen contact response. | Contact-adapter face ledger and per-case average-bearing results, including opening where present. |
| `base_bearing_quarter_area_sensitivity` | No WJ24 quarter-area comparison exists; C1 gives nominal face geometry, not pressure. | Same signed reactions plus the adopted quarter-area concentration rule or a justified, explicitly reviewed replacement. | Per-face quarter-area sensitivity report alongside `base_bearing_average`, with the legacy limit retained. |
| `base_end_notch_shear` | G24 preserves the base/end stock source geometry; no candidate section demand at the bevel/notch. | Finished notch/bevel section and any candidate cut, with concurrent shear/torsion actions and method applicability. | Source-bound base-end section extract and signed-case shear check. |
| `group_spacing` | G24 enumerates the 104 axes; current conditional 4D/7D screens are geometry-only. | Selected bolt diameter/design basis, loaded direction, tolerances, and checked minimum spacing for each new and retained group. | Candidate-wide spacing report with axes, required/actual values, separate washer/tool clearance results. |
| `catalog_washer_bounds` | H1 has quantity equivalents; WJ24 washer CAD roles are provisional. | Exact sourced washer SKU dimensions/opening/thickness and every new, retained, receiver, and backer stack. | Source-backed stack schedule and CAD-to-product bound comparison for every washer role. |
| `directional_edges` | G24 shows geometric edges and grain; no fresh signed loads classify loaded edges. | Signed local bolt actions at both host members, actual hole diameter, grain, and finished cut/housing boundaries. | Per-axis two-host loaded-end/edge report with governing distances and applicable limits. |
| `steel_direct` | H1 does not select the 104 bolt products; WJ16's provisional six-inch bolt is an older input case. | WJ24 bolt grade/product, actual thread/shank and shear planes, grip/engagement, signed tension/shear/bending and supported interaction. | Candidate bolt product/property record plus direct and combined demand/capacity report for all cases. |
| `washer_bearing` | G24 includes nominal seat geometry; C1 gives wood contact face areas. Neither supplies seat pressure or axial bolt force. | Product washer annulus/support polygon, seat cuts, signed bolt tension, contact pressure and wood design value. | Per-stack annulus/support extraction and separate washer-seat wood-bearing check. |
| `washer_bending` | H1 has no selected washer properties; nominal CAD thickness is not a sourced plate capacity. | Washer material/thickness, opening, bolt seat, unsupported span, and load distribution. | Sourced washer property table and washer plate bending/stiffness calculation for each distinct stack. |
| `receiver_fit` | G24 `candidate_bore_receivers_present_and_machined`, `candidate_component_*`, and fixed-axis checks establish nominal axis/role fit; four redirected fixed axes reach nominal backers. | Delivered parts/tolerances, selected hardware bounds, screw embedment/resistance, tool access, and receiving capacity. | Final receiver-to-hardware tolerance report; pair with the WJ24 backer path contract for the four redirected screws. |
| `overlap_contact` | G24 records nominal physical-face geometry and selected finite common areas; it does not solve openings, pressure, or transfer. | Full 52-interface contact inventory with finite patches, normals, pair ownership, unilateral opening, and WJ24 force response. | Frozen physical contact graph and adapter report with one record per actual interface and case. |
| `all_machining_represented` | G24 reconstructs 16 shared source hosts and tracks candidate bore/receiver cuts and zero legacy overlays. | A candidate-to-shop cutter/part audit covering every bore, seat, housing, notch, relief, kerf and cut transition. | Machine-readable finished-part cut inventory reconciled against WJ24 solids and shop dimensions. |
| `sampled_member_stability` | G24 has static finished geometry only; B1 samples named WJ12 planes, not all WJ24 frame sections. | All affected frame/connector stations, fresh simultaneous member actions, supports, and material/resistance methods. | Critical-section and member-stability result table over the frozen WJ24 parts and stiffness envelope. |
| `all_bolt_centres_sampled` | G24 axis inventory gives 104 new and 12 retained frame-bolt centers; B1 does not cover this complete layout. | Section/check grid coverage proof for every candidate and retained bolt center, including center backers and close rows. | Axis-to-section coverage artifact; fail closed on any unrepresented axis before strength calculations. |
| `angle_rated_force_components` | G24 replaces all 24 duties and removes the 144 SDS axes, but has zero accepted replacement resistance. | Complete per-duty physical load path, fresh simultaneous six-component actions, and component/joint resistance including internal pieces and group/contact interaction. | Duty-to-interface resistance ledger linking each of the 24 duties to every checked component and governing case/mode. |
| `floor_rail_wood_bearing` | WJ24 retains runner/rail geometry. No fresh support reactions exist; the no-slip floor basis is an unverified assumption. | Candidate rail-floor reactions/contact extent for all cases and wood bearing values under that same conditional support basis. | Per-runner floor-bearing report from fresh WJ24 reactions, with no added friction or anchor credit. |
| `actual_kicker_cutouts` | I1/authority integrity and G24 preserve the kerf-right source and all 66 axes; nominal receiver and edge geometry is present. | Fresh support/resistance for both inner kicker edges and structural validity of each fixed screw receiver, especially the two backers. | Kicker source/cut identity report joined to two edge-support calculations and all 66 receiver dispositions. |
| `taper_native_actual_taper` | G24 retains source/CAD tapered members; no WJ24 native structural representation has run. | Same-fingerprint native model must contain actual recessed members and candidate cuts. | WJ24 native-body manifest proving the exact CAD taper solids/cut identities before solving. |
| `taper_native_matches_cad_taper` | WJ24 has CAD/source identity checks, not native-to-CAD solid comparison. | Paired native/CAD finished solids, surface map, and declared comparison tolerance for every recessed member. | Native-to-CAD geometry authentication report keyed by member and surface. |
| `taper_actual_mesh_volume` | No WJ24 candidate mesh exists; N1's representative WJ04 mesh predates the complete layout. | Frozen candidate mesh and CAD solids with recessed-volume method, mesher settings, and accepted tolerance. | Candidate mesh/CAD volume authentication report before native case runs. |
| `taper_taper_at_least_one_in_ten` | Source taper identity is retained; no WJ24 report reapplies the adopted slope screen to final recessed surfaces. | Actual taper boundary endpoints and modified cut geometry. | Per-member slope-screen record from the WJ24 finished surfaces. |
| `taper_intended_stock_and_runout` | Source/candidate host matching preserves intended members; no receiving or observed stock evidence exists. | Each affected part record must retain 4×6 stock and 1:12 runout identity through cuts; physical stock remains unobserved. | Part-identity schedule linking source member, WJ24 finished part, nominal stock, and runout endpoints. |
| `taper_taper_bounds_sampled` | G24 source and candidate solids are available; no all-transition section grid is reported for WJ24. | Section samples must bracket each taper boundary, new/retained hole, and changed cut. | Taper station coverage map reconciled to the full axis and finished-cut inventories. |
| `taper_actual_net_section_normal_resistance` | No WJ24 taper section demands or net-section resistance; WJ12 named area samples do not transfer. | Actual bored/cut taper sections, concurrent normal demands, grain, and adjusted net resistance. | Per-station WJ24 taper net-section check with governing case and section fingerprint. |
| `taper_sampled_rectangular_shear_torsion` | No WJ24 taper shear/torsion checks; unbored reference scope cannot be carried across bores. | Candidate station forces/moments and a valid bored-section or demonstrably applicable unbored method. | Applicability map plus per-station shear/torsion calculations on actual finished sections. |
| `taper_taper_region_unbored_torsion_applicable` | G24 exposes candidate and retained axes; no section-by-section method map is emitted. | Co-location of every bore/cut with each tapered region and supported method applicability. | Bore/taper overlay report marking unbored method inapplicable at intersecting regions and naming replacement method. |
| `component_layouts` | G24 exact-set checks reconcile 24 duties, 28 pieces, 104 axes, and 52 ordered receiver groups. | Each duty needs an accepted physical owner/path and every connector part, internal joint, washer stack and retained axis needs fit plus a strength disposition. | Duty/part/axis topology ledger with exact 24-duty reconciliation, interface IDs, and open/closed evidence fields. |
| `flush_face_normal_contact` | I1 names six source contacts; G24 describes candidate faces but does not reconcile all six into fresh compression/opening states. | Source-to-candidate face mapping, normals, finite areas, per-case unilateral state, and equal/opposite reactions. | Six-source-contact migration table linked to the full WJ24 physical contact graph and response results. |
| `flush_face_wood_bearing` | C1 and G24 provide face geometry, including the reduced bottom-center patch; no contact pressure or reaction. | Active pressure/area, signed fresh forces, grain/design values and candidate face reconciliation. | Per-face bearing report from the contact adapter with the reduced E1–E2 face preserved. |
| `flush_sampled_taper_top_clearance` | Source monitor identity can be taken from I1/source checks; no fresh deformed WJ24 gaps. | Reconcile all 18 monitor IDs and calculate signed deformed gap in every same-configuration case. | Native monitor mapping and per-case clearance output; require every applicable gap > 0. |

## Eleven additional candidate obligations

| Exact obligation ID | Current evidence | Missing candidate-specific demand or method | Next implementable output |
| --- | --- | --- | --- |
| `complete_load_path_coverage` | G24 maps all 24 owners/axes and 28 pieces; receiver arrays are geometry relationships, not proved force paths. | Each source duty must trace through physical contacts, bolts, connector pieces and internal joints to supported frame/floor reactions. | Exact source-duty to interface graph, including shared-fastener ownership and closure of all 144 retired SDS paths. |
| `center_kicker_receiver_paths` | WJ05 geometry has four fixed axes entering two backers at 45.24375 mm nominal length; the receiver audit calls paths blocked. B1 statics are synthetic WJ12 witnesses. | Actual actions and resistance for screw-to-backer, backer-to-header bolts, header receiving sections, and both inner kicker-edge supports. | [`wj24-backer-loadpath-contract.md`](wj24-backer-loadpath-contract.md) plus a candidate-action-linked check record for both backers and both edge supports. |
| `connector_body_behavior` | G24 has 28 connector blank shapes and grain metadata; no combined body or internal-joint capacity. | Finished sections under simultaneous axial/shear/bending/torsion; all piece-to-piece joints and any plywood through-thickness behavior. | Per-connector-body and internal-fastener mechanics sheet keyed to each of the 28 part IDs and selected stock. |
| `housing_and_finished_sections` | No primary-member housing is approved. G24 captures current connector shapes/cuts, not a complete shop cut package. | For every later proposed house/cut: exact setup, shoulder/contact behavior, section loss/splitting, local edges, fit, and combined member effect. | Explicit WJ24 cut/no-cut decision and, for any retained proposed cut, a source-bound cut geometry plus section/load check. |
| `complete_joint_actions` | A1 old-action witness and B1 unit statics do not represent WJ24 demand. N1 says runner `physical_forces()` is point-force output, not full interface wrench. | Fresh simultaneous six-component wrench per physical interface, shifted to a declared datum; bolt tension/lateral distribution, unilateral pressure/opening and equilibrium. | Contact/reaction adapter output with per-case interface wrenches, equal/opposite ownership and equilibrium residuals. |
| `joint_stiffness` | No WJ24 stiffness is accepted. `clearance_response` is scalar/monotonic and B1 equilibrium does not predict sharing. | Evidence-based slip/rotation, free-hole travel, contact law and lower/upper sensitivity consumed consistently by model and resistance checks. | Versioned WJ24 joint-response contract with measured/source-backed inputs or explicitly bounded assumptions and sensitivity records. |
| `installed_clearance` | G24 screens static solids; G1/G12 hold proxies intersect cleats and A1 finds the G7 extraction collision. Gaps are nominal; tolerances are open. | Updated geometry after any relief, real finite installed hardware and service envelopes, tolerance stack, moving/staged configurations. | Full-scene WJ24 clearance report after resolving geometry blockers, with named controlling pairs and min gaps by tolerance case. |
| `assembly_and_removal_access` | WJ24 local tool and LED checks preserve conflicts; no complete forward/reverse operation sequence. | Selected tools, swing/approach/strokes, staging support, wiring/LED motion, sequence-dependent clearance and tolerance. | Integrated stepwise assembly/removal access simulation with operations, tools, poses, and failed pairs retained. |
| `demountable_transport` | I1 lists source transport parts; A1 only checks one LED extraction. No full WJ24 disassembly/transport sequence. | Individual finished parts and repeatable sequence, no routine structural wood-thread removal, and panel screw operations counted separately. | Part-level forward/reverse transport manifest with structural bolt and retained 66 Hillman operation counts. |
| `ordinary_n_envelope` | WJ24 has not reported a complete local-N envelope disposition. Older WJ03 probe records +86.018477 mm permanent and +175.948756 mm temporary workspace excess on its own diagnostic geometry. | All WJ24 permanent connector/hardware extrema from named datums; temporary tools/bolt stroke kept separate. | Full-layout N-extrema report for every duty with dimensioned disposition for any permanent exception. |
| `hardware_source_count_cost` | H1 reconciles provisional 104/104/216 quantities and 28 blanks; 16 center bolt lengths unassigned and prices null. Retained 12 frame bolts and 66 Hillman screws are separate. | Selected sourced products, actual bounds and threads, whole-frame BOM, stock yield, tools, supplier/cost and installation/removal assumptions. | Source-backed WJ10 BOM/cut/cost schedule with unassigned fields explicit until evidence is available. |

## Readiness order implied by the gaps

The omissions most likely to change the layout should resolve before a WJ24
mechanics freeze: disposition G1/G12 hold access and the G7 LED withdrawal
collision; establish the two center backer-to-header paths and both kicker edge
supports; freeze the reduced bottom-center left bearing face as a real contact
patch; and complete the retained-frame-bolt geometry/recheck. Changes to any of
these require regenerating the integrated composition and affected static
checks. Geometry closure still will not provide demand or resistance.

After that freeze, the candidate needs one WJ24 contact/action contract shared
by fresh complete-frame cases and the component resistance checks, followed by
per-axis/member/washer methods and the criteria evidence records. Only then can
the authorized serial six-case native run be ready. Keep WJ08 method coverage,
WJ09 response evidence, and the final dispositions distinct: a converged model
is evidence about response under its recorded assumptions, not a resistance
pass by itself.
