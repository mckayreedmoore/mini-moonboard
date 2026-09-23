# Barrel-nut candidate acceptance criteria

This ledger defines the acceptance contract for the
`compact-floor-flush-bolted-development` integrated kerf-right barrel-nut
candidate described by the [validation plan](barrel-nut-validation-plan.md).
It does not select that candidate, replace the current angle-frame shop
packet, authorize fabrication, or transfer any result from
`compact-floor-flush-development`.

The intended candidate has 20 framing timbers, six fixed plywood panels, 24
former-angle joint duties served by 46 bolt/barrel pairs, twelve retained
frame bolts, and 66 unchanged panel/kicker screw axes. The six required load
cases are A12 left, A12 rear, A12 forward, K12 right, K12 rear, and A1 rear
under the recorded no-slip floor assumption.

## Result rules

Each identifier below must produce one of four results:

- `PASS`: the stated evidence exists and meets the predeclared rule.
- `FAIL`: the evidence exists and violates the rule.
- `UNRESOLVED`: required evidence, method, input, or result is absent.
- `NOT_APPLICABLE`: the frozen candidate does not contain the stated feature
  or the ledger's explicit conditional applicability rule is false.

A missing value is `UNRESOLVED`, not zero demand or a pass. A ratio passes only
at or below 1.0. A margin passes only at or above zero. A required Boolean
passes only when true. Demand and resistance must use compatible bases and the
same signed load case. Characteristic, ultimate, allowable, and test values
must not be mixed without a documented derivation.

Candidate identity, source hashes, complete inventories, equilibrium,
residuals, convergence, and physical load paths are prerequisites to strength
assessment. A numerically stable result created by restraining a real
mechanism fails the applicable load-path criterion.

Before any unresolved calculation, numerical, qualification, or observation
row can become `PASS`, its frozen record must name the method and version,
applicability conditions, input sources, adjustment and safety factors,
numerical limit or Boolean requirement, and failure disposition. Terms such as
"adequate," "valid," "adopted," or "unacceptable" below define the required
subject; they are not permission to choose a threshold after seeing results.
Serviceability, convergence, residual, sensitivity, test, and reassembly limits
must be numeric where the method permits and must be frozen before the related
solve or test. A machine-readable expected set must reject missing and
unexpected criterion identifiers.

## Candidate, load, and input criteria

| Identifier | Classification | Acceptance rule | Current status and evidence |
| --- | --- | --- | --- |
| `bn_candidate_identity` | Provenance | One source-built integrated candidate is frozen by commit, source hashes, assembly hash, units, and configuration fingerprint. Detached trials and dirty neighboring worktrees are excluded. | `UNRESOLVED`: [`barrel-nut-candidate.json`](../barrel-nut-candidate.json) records the candidate fingerprint, per-file hashes, HEAD `ca203ae9`, and a dirty-snapshot hash, but the bound work remains dirty and uncommitted. The contract explicitly remains unreleased. |
| `bn_acceptance_contract_complete` | Criteria/provenance | Every adopted identifier has frozen method, applicability, source, factors, limit, and failure-disposition fields, and the expected-set authority rejects missing or unexpected identifiers. | `UNRESOLVED`: the station and resistance registers fail closed on their finite inventories, but method-specific metadata and several numerical acceptance limits remain unresolved. |
| `bn_load_case_identity` | Provenance | All six case names, signed vectors, application points, gravity/equipment, dynamic assumptions, and stand-off values match the maintained producer and are recorded in the frozen candidate contract. | `PASS`: [`barrel-nut-stations.json`](barrel-nut-stations.json) records and authenticates those complete fields for all six prepared cases. This is load-input identity only; no case has been solved or accepted. |
| `bn_connector_inventory` | Inventory | Exactly 24 barrel-joint duties, 46 bolt/barrel pairs, twelve retained frame bolts, and 66 panel/kicker screws are present; no ML24Z or structural SDS connector is active. Every connector has one station and the intended host members. | `PASS`: the source-bound station register enforces the exact counts, hosts, paths, and exclusion of 144 legacy structural SDS axes. This is not a resistance pass. |
| `bn_fixed_surface_policy` | CAD identity | Climbing surface, panel outlines, hold layout, and all 66 panel/kicker screw axes match the fixed policy; kerf-right kicker edge support is explicit. | `PASS`: the station register binds six panels, all 66 fixed axes, and the four center kicker-screw receiver traces. Strength and delivered fit remain separate. |
| `bn_controlled_material_inputs` | Controlled input | The design specification fixes species, grade, moisture/service condition, treatment/incising status, minimum sections, grain directions, and all 2024 NDS values and adjustments for every structural member. | `UNRESOLVED`: a conditional dry, unincised DF-L No. 2 reference exists, but member-specific minimum sections and complete adjustments are not frozen. Delivered conformance remains a separate observation. |
| `bn_controlled_hardware_inputs` | Controlled input | Every bolt-length family, barrel, and washer has a traceable standard or exact product specification covering material minimums, dimensions and tolerances, thread start/runout, usable male and female threads, barrel axis and opening, and relevant resistance inputs. | `UNRESOLVED`: the [selected qualification stack](barrel-nut-selected-hardware.md) fixes STAFAST `JCD14201606NL ZN` barrels, CDE `1456BHT5` / `1472BHT5` / `1480BHT5` / `14104BHT5` fully threaded Grade 5 bolts, and Fastenal `33857` hardened washers. The CDE IFI-199 dimensional table and the bolt/washer standards provide controlled constituent inputs, but the CDE manufacturer certificates and Class 2A confirmations, the Fastenal washer MTR, and delivered dimensions remain absent. STAFAST publishes nominal body geometry only; controlled barrel tolerances, internal thread class and complete female interval, material minimums, resistance, and lot conformity remain absent. |

## Geometry, machining, and service criteria

These criteria can be evaluated before native solves. Nominal CAD results do
not replace controlled tolerances or physical observations.

| Identifier | Classification | Acceptance rule | Current status and evidence |
| --- | --- | --- | --- |
| `bn_all_machining_represented` | CAD check | Every shaft bore, insertion bore, head/washer pocket, service opening, retained bolt bore, fixed screw path, recess, and other structural cut appears in the assessed cut solids and member-local records. | `UNRESOLVED`: the prior nominal complete-frame inventory builds valid connected cut solids for all 20 timbers and records 268 host/cutter applications. Separate source-built screens shift all 46 STAFAST bodies and insertion-bore tails 2.0066 mm and extend all twelve outer-rail bores by the corrected 12.4408 mm provisional-reserve amount without a nominal unrelated, protected, peer-path, peer-stack, or maximum-washer collision. The final selected 5 in blind-bore cuts, finished fit, tolerances, and adverse combined-cut solids are not frozen, and the 2 mm rail reserve is not an accepted machining limit. |
| `bn_complete_contact_geometry` | CAD/load-path check | Every intended barrel-joint and retained-bolt bearing face is present after cuts, has a connected surviving face, and has pressure-cell geometry adequate for local resultants. | `PASS` for geometry: all 24 barrel faces use 132 exact trial-cut cells preserving face area and first moments, and the retained interfaces use 72 exact cells. This does not qualify contact stiffness, pressure resistance, opening, or slip. |
| `bn_changed_path_clearance` | CAD check | The two N = 42 mm left-center first rows, the STAFAST 2.0066 mm axis-preserving body shifts, and the final selected 5 in and 6 1/2 in blind-bore corrections have no prohibited cut, hardware, service, fixed-screw, panel, or unrelated-wood intersection and remain inside their receivers with declared tolerances. | `UNRESOLVED`: maintained-source nominal screening removes both service intersections and leaves 6.641 mm nominal gaps. All 46 shifted STAFAST bodies and bore tails clear nominally. The corrected 12.4408 mm provisional-reserve outer-rail probe and selected maximum-washer envelopes clear all twelve intended receivers. The selected 5 in stack retains only 0.1204 mm before machining error. Final machining limits and tolerance-qualified cut sections are not frozen. |
| `bn_barrel_bore_fit` | CAD/tolerance check | Each insertion bore has a declared bit/finished diameter, fit class, position and angular tolerance, and remaining-wood calculation compatible with the controlled barrel envelope. | `UNRESOLVED`: all 46 modeled insertion bores currently have zero nominal diameter allowance and are not shop drill sizes. |
| `bn_stack_engagement_and_tip_clearance` | Stack calculation | Every stack meets minimum usable thread engagement, excludes incomplete threads and chamfers, avoids bottoming, and retains positive worst-case tip clearance over the full tolerance stack. | `UNRESOLVED`: the former 6 in outer-rail comparator is rejected because its adverse physical tip is 1.072 mm and its two-pitch-adjusted complete male-thread endpoint is 3.612 mm short of the modeled barrel axis. The selected CDE 6 1/2 in stack reaches 9.596 mm physically and 7.056 mm after that allowance past the axis, but needs 10.4408 mm added bore depth for zero clearance or 12.4408 mm for the provisional 2 mm reserve. The selected 5 in stack retains only 0.1204 mm before machining error. Controlled STAFAST female-thread endpoints, delivered dimensions, required engagement, and final clearances remain absent. |
| `bn_receiver_fit` | CAD/tolerance check | All bolt, barrel, washer, head, tool, and insertion envelopes remain within their intended receiver and supported seat over the complete tolerance stack. | `UNRESOLVED`: nominal shifted-barrel and outer-rail extension probes clear intended receivers, but final barrel, drill, tool, stock, and machining tolerances are not frozen. The selected Fastenal `33857` washer is 18.4658–19.0246 mm OD against the current 19.05 mm nominal seats, leaving essentially no diametral machining allowance, and the current CAD under-models the maximum head-plus-washer thickness by 0.807 mm. |
| `bn_directional_edges` | CAD/design check | Signed-load edge and end distances pass the adopted method in every affected member, including transverse barrel bores and head pockets. | `UNRESOLVED`: signed candidate demands and a complete barrel-bore breakout method are absent. |
| `bn_group_spacing` | CAD/design check | Bolt/barrel rows and interacting pockets meet the adopted spacing and ligament rules, including unfavorable tolerances. | `UNRESOLVED`: nominal row geometry exists, but no complete barrel-joint spacing basis is adopted. |
| `bn_cut_sections_sampled` | CAD/numerical check | Every bolt axis, barrel bore, pocket, interacting service cut, ligament transition, and governing unbored region is covered by exact or demonstrably conservative section samples. | `UNRESOLVED`: the source-bound governing-joint artifact now replays all cuts on 11 affected members, but its event-directed sample-set stability does not prove continuous/global or tolerance-case coverage, and no sampled section has resistance credit. |
| `bn_tool_access` | Shop geometry check | Each bolt and barrel can be installed, oriented, tightened, inspected, and removed using declared real tool envelopes and the documented assembly order. | `UNRESOLVED`: outer-header driver access requires a rim-first sequence that has only nominal screening. |
| `bn_member_removal` | Shop geometry check | Every transport member can be removed and replaced with panels safely supported, without damage or unintended fastener removal. | `UNRESOLVED`: continuous nominal rim sweeps pass, but tool, tolerance, temporary-support, and physical service checks are absent. |
| `bn_led_passage` | Shop fit check | The packet declares a minimum strand/connector pass-through envelope, and that envelope clears the fixed route, structure, and protected fastener paths with stated installation tolerance. | `UNRESOLVED`: a nominal 25.4 mm route clears CAD hardware, but no minimum strand/connector envelope or tolerance is specified. Delivered conformance remains a separate observation. |
| `bn_panel_stock_yield` | Stock fit check | A source-bound cut layout yields all fixed kerf-right panels from a declared minimum sheet envelope with required orientation, kerf, and trim allowances. | `UNRESOLVED`: the retail listing is smaller than the rectangular main blanks and no acceptable minimum-sheet cut layout is frozen. Owned-sheet conformance remains a separate observation. |

## Response and numerical criteria

Serviceability limits, stiffness ranges, and numerical tolerances must be
frozen before they are used to select a passing result.

| Identifier | Classification | Acceptance rule | Current status and evidence |
| --- | --- | --- | --- |
| `bn_joint_kinematic_stability` | Load-path check | Every signed case has a physical restraint path for each required relative motion without fictitious springs, clamp friction, or floor anchorage. | `UNRESOLVED`: local and connected rank screens plus opening/reclosure and retry mechanics tests pass their diagnostic rules, but the two isolated single-bolt principal/header joints retain a face-normal twist mode and no accepted signed case proves connected restraint. |
| `bn_case_contact_state` | Load-path/numerical check | Solved unilateral contacts have compatible signs, opening/reclosure behavior, and physical pressure resultants in every case. | `UNRESOLVED`: no signed candidate solve exists. |
| `bn_stiffness_clearance_basis` | Controlled input/qualification | Joint axial, lateral, contact, seating, and clearance behavior is supported by defensible bounds or measurements covering wood, threads, barrel, washer, and hole play. | `UNRESOLVED`: the model now couples a 0.575 mm nominal radial dead zone to each barrel bolt and its mechanics tests pass, but the 1000 N/mm axial, 500 N/mm lateral, and face-contact stiffnesses remain conditional assumptions. Actual fit and response bounds are unsupported. |
| `bn_case_convergence` | Numerical check | Each of the six frozen cases reaches the predeclared active-set and nonlinear convergence limits without changing physical assumptions. | `UNRESOLVED`: six cases prepare but have not been solved. |
| `bn_case_equilibrium_residual` | Numerical check | Global, member, connector, and contact equilibrium and residual tolerances pass for each final case. | `UNRESOLVED`: no solved result exists. |
| `bn_case_inventory_complete` | Numerical/provenance check | Each final case contains every required member, mass/load, all 46 barrel pairs, all twelve retained bolts, all 66 fixed screws, and every floor/member contact in the frozen accepted discretization. Connector counts derive from the frozen station register; contact-cell counts derive from the accepted model rather than this criterion. | `UNRESOLVED`: preparation and fail-closed runner checks enforce 132 barrel-face cells, 72 retained-face cells, 46 axial/radial barrel groups, and all required connections, but no final accepted solved-case inventory exists. |
| `bn_analysis_bevel_geometry_mapping` | Model-geometry check | Each former full-bevel surrogate is eliminated from the response mesh, and the replacement uncut member prism preserves the source-bound volume, centroid, connector locations, and contact-point mapping. | `PASS`: all four former projection members now use source-bound constant-X CAD prisms meshed as C3D20; volume, centroid, bolt points, and contact-point mappings pass. No `analysis_only_full_bevel_members` remain. This pass does not establish affected cut-solid ligament or local-section equivalence; those remain `UNRESOLVED` under `bn_cut_sections_sampled` and the local resistance criteria. |
| `bn_mesh_and_contact_sensitivity` | Numerical check | Predeclared local mesh, face-cell, penalty/stiffness, and clearance sensitivities do not reverse acceptance or hide a mechanism. | `UNRESOLVED`. |
| `bn_signed_action_ledger` | Demand extraction | All 24 interfaces and 46 fasteners have source-bound signed force and moment tuples for all six cases, with common datums and individual row sharing. | `UNRESOLVED`: a fail-closed extractor and schema exist, but they reject missing or unaccepted native reports. No accepted candidate demands exist; preliminary scales and old angle-frame forces do not transfer. |

Small verification cases must also demonstrate action/reaction and moment
balance, tension-only engagement, face opening and reclosure, direction
reversal, asymmetric row sharing, and an intentionally free mechanism. These
checks support the numerical criteria; they do not replace full cases.

## Complete-joint resistance criteria

Each distinct family and geometry-critical variant must cover every applicable
mode below. Published evidence may be used only where its topology, material,
action, and adjustment basis apply. Ordinary NDS lateral-bolt equations may be
used as a constituent submodel; they do not rate axial barrel anchorage.

| Identifier | Classification | Acceptance rule | Current status and evidence |
| --- | --- | --- | --- |
| `bn_bolt_steel_interaction` | Design calculation | Bolt tension, shear, bending, and their applicable interaction pass using the actual body/root portions and controlled material minimums. | `UNRESOLVED`: the selected Grade 5 basis provides constituent proof, yield, and tensile minima, but lot conformity, actual threaded geometry, signed demands, bending/shear interaction, and complete-joint load distribution remain open. |
| `bn_male_thread_stripping` | Design calculation | Usable male engagement and thread shear resistance pass for the controlling same-case action. | `UNRESOLVED`. |
| `bn_female_thread_stripping` | Design calculation | Usable barrel-thread engagement and female thread resistance pass for the controlling same-case action. | `UNRESOLVED`. |
| `bn_barrel_wall_and_flexure` | Design calculation/qualification | Barrel wall, net section, local thread loading, bending, and opening pass. | `UNRESOLVED`: selected STAFAST `JCD14201606NL ZN` has no published controlled material minimum, barrel resistance, or complete applicable method. |
| `bn_head_washer_bending` | Design calculation | The controlled head/washer assembly passes bending and seating over its actual support. | `UNRESOLVED`: Fastenal `33857` is selected with ASTM F436/F436M material and dimensional bounds, but lot MTR, delivered dimensions, supported-seat geometry, eccentricity, signed demand, and bending calculation remain open. |
| `bn_head_washer_wood_bearing` | Design calculation | Timber compression, pull-through, breakout, and seat integrity pass at every head/washer pocket. | `UNRESOLVED`: ideal full-contact washer values are only constituent scales. |
| `bn_bolt_lateral_submodel` | Design calculation | Each qualifying shear-plane subcase passes the applicable 2024 NDS lateral-yield and embedment checks with actual shank/thread geometry and grain angle. Nonqualifying rows are `NOT_APPLICABLE`, not passes. | `UNRESOLVED`. |
| `bn_barrel_wood_bearing` | Design calculation/qualification | Barrel-body bearing in the actual grain direction and local bore geometry passes using an applicable mechanics or qualification basis. | `UNRESOLVED`. |
| `bn_wood_splitting_breakout` | Design calculation/qualification | Splitting, edge/end breakout, shear-out, and pocket/ligament fracture pass for both load directions and interacting cuts. | `UNRESOLVED`; 2.092 mm principal/header head-pocket edge stock and 6.35 mm outer-header pocket side stock require closure. |
| `bn_local_net_section_interaction` | Design calculation | Exact cut sections pass combined axial, flexural, shear, and torsional actions with applicable wood adjustments. | `UNRESOLVED`. |
| `bn_group_eccentricity_and_sharing` | Design calculation/qualification | Multirow groups pass with justified unequal stiffness, eccentricity, clearance, opening, and reversed-action distribution; no automatic multiple of one-fastener capacity is used. | `UNRESOLVED`. |
| `bn_contact_pressure_and_opening` | Design calculation | Cut-face pressure, narrow strips, resultants, local bearing, and loss of contact pass under each signed case. | `UNRESOLVED`. |
| `bn_joint_slip_serviceability` | Design calculation/qualification | Slip, rotation, opening, and residual set remain within limits frozen before assessment. | `UNRESOLVED`: no adopted limits or supported stiffness exist. |
| `bn_reassembly_durability` | Qualification | The stated disassembly/reassembly scope does not cause unacceptable fit loss, damage, engagement loss, or permanent set. No broader cycle-life claim is made. | `UNRESOLVED`: no physical evidence or defensible bound exists. |
| `bn_kicker_backing_transfer` | Design calculation/qualification | The four fixed center kicker screws, two posts, post/header barrel joints, and connected framing provide a complete passing path for signed kicker actions without importing SPAX properties. | `UNRESOLVED`: geometric receiver traces exist; screw and post/header strength do not. |
| `bn_retained_frame_bolts` | Design calculation | All twelve retained frame-bolt arrangements pass applicable bolt, washer, wood, group, contact, and member checks under new candidate demands. | `UNRESOLVED`: physical axes are retained, but old demands and passes do not transfer. |
| `bn_complete_joint_evidence_route` | Qualification/evidence check | Every applicable mode at every geometry-critical variant is assigned to supported published evidence, geometry-specific mechanics with controlled inputs, or predeclared relevant complete-joint tests. | `UNRESOLVED`: the machine resistance ledger inventories 3,216 station/fastener/case results and the qualification plan defines the remaining route, but every resistance result remains unresolved pending controlled inputs, methods, stiffness, and signed demands. |
| `bn_complete_joint_test_acceptance` | Conditional qualification | Where calculation or published evidence cannot close a governing mode, a predeclared complete-joint test program supplies an adjusted design basis that exceeds same-case demand and meets strength, slip, damage, conditioning, sampling, and statistical limits. | `UNRESOLVED` where required; exploratory coupons cannot pass this row. |
| `bn_complete_joint_utilization` | Design calculation | Every station × case × applicable failure-mode demand/resistance ratio is at most 1.0, with provenance and the governing reserve recorded. | `UNRESOLVED`. |
| `bn_floor_support_and_global_stability` | Design/load-path check | All six cases pass floor bearing, uplift, and global equilibrium while tangential floor degrees of freedom are constrained by the explicit no-slip analytical assumption. Required horizontal reactions are reported without claiming sliding resistance, measured friction, or an anchor. | `UNRESOLVED`: the assumption is recorded; no candidate response exists. |

## Applicable selected-baseline criteria

No selected-baseline result transfers. Every row below must be rerun on the
frozen barrel candidate. These exact candidate identifiers make the required
set countable; each points back to the named baseline method without importing
its saved value.

| Candidate identifier | Baseline method retained | Classification | Acceptance rule | Current status |
| --- | --- | --- | --- | --- |
| `bn_sampled_net_member` | `sampled_net_member` | Design calculation | Every sampled exact gross/net member section passes under candidate demands. | `UNRESOLVED` |
| `bn_header_gross_full_length_stability` | `header_gross_full_length_stability` | Design calculation | Full-length header gross-section stability ratio is at most 1.0. | `UNRESOLVED` |
| `bn_base_bearing_average` | `base_bearing_average` | Design calculation | Average header/base bearing ratio is at most 1.0. | `UNRESOLVED` |
| `bn_base_bearing_quarter_area_sensitivity` | `base_bearing_quarter_area_sensitivity` | Design calculation | Existing quarter-area bearing comparison is at most 1.0. | `UNRESOLVED` |
| `bn_base_end_notch_shear` | `base_end_notch_shear` | Design calculation | Retained-end shear ratio is at most 1.0. | `UNRESOLVED` |
| `bn_sampled_member_stability` | `sampled_member_stability` | Design calculation | Every required member-section stability check passes. | `UNRESOLVED` |
| `bn_floor_rail_wood_bearing` | `floor_rail_wood_bearing` | Design calculation | Explicit floor-cell timber-bearing ratio is at most 1.0. | `UNRESOLVED` |
| `bn_actual_kicker_cutouts` | `actual_kicker_cutouts` | CAD/native identity | Exact whole-kicker inventory matches the frozen candidate. | `UNRESOLVED` pending frozen source |
| `bn_taper_native_actual_taper` | `taper_native_actual_taper` | CAD/native identity | Native model contains the actual recess. | `UNRESOLVED` pending frozen source |
| `bn_taper_native_matches_cad_taper` | `taper_native_matches_cad_taper` | CAD/native identity | Native recess equals frozen candidate CAD. | `UNRESOLVED` pending frozen source |
| `bn_taper_actual_mesh_volume` | `taper_actual_mesh_volume` | Numerical/CAD check | Meshed recess volume matches frozen candidate geometry within the adopted tolerance. | `UNRESOLVED` |
| `bn_taper_taper_at_least_one_in_ten` | `taper_taper_at_least_one_in_ten` | Geometry check | Existing slope comparison returns true. | `UNRESOLVED` pending frozen source |
| `bn_taper_intended_stock_and_runout` | `taper_intended_stock_and_runout` | Geometry check | Intended stock and 1:12 runout identity return true. | `UNRESOLVED` pending frozen source |
| `bn_taper_taper_bounds_sampled` | `taper_taper_bounds_sampled` | Numerical check | Recess-region section coverage is complete. | `UNRESOLVED` |
| `bn_taper_actual_net_section_normal_resistance` | `taper_actual_net_section_normal_resistance` | Design calculation | Actual retained net-section normal-resistance ratio is at most 1.0. | `UNRESOLVED` |
| `bn_taper_sampled_rectangular_shear_torsion` | `taper_sampled_rectangular_shear_torsion` | Design calculation | Sampled retained shear/torsion ratio is at most 1.0. | `UNRESOLVED` |
| `bn_taper_taper_region_unbored_torsion_applicable` | `taper_taper_region_unbored_torsion_applicable` | Design/CAD check | Torsion method is used only in its supported unbored region. | `UNRESOLVED` |
| `bn_flush_face_normal_contact` | `flush_face_normal_contact` | Load-path check | All six retained interfaces exist and have valid compression-only response. | `UNRESOLVED` |
| `bn_flush_face_wood_bearing` | `flush_face_wood_bearing` | Design calculation | Maximum retained-interface wood-bearing ratio is at most 1.0. | `UNRESOLVED` |
| `bn_flush_sampled_taper_top_clearance` | `flush_sampled_taper_top_clearance` | Numerical/CAD check | Every required deformed taper-top monitor gap remains positive. | `UNRESOLVED` |
| `bn_retained_actual_angle_lateral_CD_1` | `actual_angle_lateral_CD_1` | Design calculation | Retained-bolt nominal-diameter lateral ratio is at most 1.0 under candidate force angle. | `UNRESOLVED` |
| `bn_retained_additional_group_reduction_sensitivity` | `additional_group_reduction_sensitivity` | Design calculation | Adopted retained-bolt group-reduction comparison is at most 1.0. | `UNRESOLVED` |
| `bn_retained_local_parallel` | `local_parallel` | Design calculation | Retained-bolt local parallel-bearing ratio is at most 1.0. | `UNRESOLVED` |
| `bn_retained_supplemental_EC5_splitting` | `supplemental_EC5_splitting` | Design calculation | Retained-bolt supplemental splitting ratio is at most 1.0 where applicable. | `UNRESOLVED` |
| `bn_retained_group_spacing` | `group_spacing` | CAD/design check | Retained-bolt group spacing margin is at least zero. | `UNRESOLVED` |
| `bn_retained_catalog_washer_bounds` | `catalog_washer_bounds` | CAD/design check | All twelve retained stacks have supported washer inventory and seating envelopes. | `UNRESOLVED` |
| `bn_retained_directional_edges` | `directional_edges` | CAD/design check | Retained-bolt signed edge/end margins are at least zero. | `UNRESOLVED` |
| `bn_retained_steel_direct` | `steel_direct` | Design calculation | Retained-bolt direct steel ratio is at most 1.0. | `UNRESOLVED` |
| `bn_retained_washer_bearing` | `washer_bearing` | Design calculation | Retained-stack timber washer-bearing ratio is at most 1.0. | `UNRESOLVED` |
| `bn_retained_washer_bending` | `washer_bending` | Design calculation | Retained-stack washer-bending ratio is at most 1.0. | `UNRESOLVED` |
| `bn_retained_receiver_fit` | `receiver_fit` | CAD check | Every retained receiver, bore, and washer seat passes candidate geometry. | `UNRESOLVED` pending frozen source |
| `bn_retained_overlap_contact` | `overlap_contact` | Design/load-path check | Every applicable retained member-overlap contact is present and valid. | `UNRESOLVED` |
| `bn_retained_all_bolt_centres_sampled` | `all_bolt_centres_sampled` | Design check | Every retained bolt bore is covered by required member-section samples. | `UNRESOLVED` |
| `bn_retained_component_layouts` | `component_layouts` | CAD/design check | Every retained local component layout passes its adopted screen. | `UNRESOLVED` |

`bn_all_machining_represented` above expands the baseline method of the same
name to all candidate cuts. Barrel-specific forms of the applicable bolt,
washer, wood, spacing, contact, and group concepts are covered by the
complete-joint criteria rather than being hidden inside retained-bolt results.

`angle_rated_force_components` is obsolete for this candidate and is replaced
by the complete-joint resistance set. `finite_floor_friction_law` remains
inapplicable because these cases use the stated no-slip support assumption.
`ml24z_unlisted_actions` is not a candidate criterion.

## Documentation and review criteria

| Identifier | Classification | Acceptance rule | Current status and evidence |
| --- | --- | --- | --- |
| `bn_diy_packet_traceability` | Documentation gate | BOM, stock/cut list, machining sheets, tolerances, jigs, assembly/service sequence, checklists, viewer, schedules, evidence links, costs, limitations, and substitution rules all describe the same accepted frozen candidate. | `UNRESOLVED`: candidate packet does not exist. |
| `bn_independent_mechanics_review` | Review gate | An independent reviewer checks the governing joint, signed action mapping, contact assumptions, hardware/thread evidence, and cut-section methods. Every supported finding is corrected and affected checks are rerun; rejected findings retain a written technical basis. | `UNRESOLVED`. |
| `bn_independent_shop_review` | Review gate | An independent reviewer traces a representative joint and every exceptional family from BOM through drilling, assembly, inspection, and removal. Every supported finding is corrected and affected shop checks are rerun; rejected findings retain a written technical basis. | `UNRESOLVED`. |

## Physical observations kept outside design-pass counts

The following fields are installation conditions. Their Actual and
Disposition cells stay blank until observed. Publishing conditional DIY
documentation must not relabel them as design passes.

| Identifier | Required observation | Actual | Disposition |
| --- | --- | --- | --- |
| `bn_delivered_stack_observation` | Bolt markings, length, body/thread transition, runout, usable threads, barrel dimensions/thread opening, washers, engagement, seating, and tip reserve |  |  |
| `bn_delivered_lumber_panel_observation` | Species/grade stamps, moisture, dimensions, grain, defects, actual plywood dimensions, and stock yield |  |  |
| `bn_finished_machining_observation` | Finished bore/pocket locations and sizes, remaining wood, fit, splits, tear-out, overcut, and datum registration |  |  |
| `bn_installed_joint_observation` | Barrel orientation/retention, tool access, tightening basis, contact, damage, LED fit, panel support, assembly, removal, and reassembly |  |  |

Any observed deviation outside the accepted input envelope triggers stop and
reassessment. It does not become a field adjustment, elongated hole, hardware
substitution, or undocumented capacity reduction.
