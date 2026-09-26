# Wood-joint criteria method map

Status: **planning only; all 36 migrated legacy criteria and 11 candidate
obligations remain pending.** This map assigns a candidate-specific method,
producer, evidence target, and dependency to every row in
[`criteria.json`](criteria.json). It does not change that file, the selected
baseline, any release flag, or any prior result. No angle, barrel-joint,
selected-frame, or diagnostic-case pass transfers to this candidate.

The source questions are the frozen set in
[`floor-runner-mvp-criteria.md`](../floor-runner-mvp-criteria.md), authenticated
by `scripts/floor_flush_checks.py::FROZEN_ADOPTED_CRITERIA`. The candidate
starts from the WJ-01 source inventory, then needs one integrated WJ-06 model,
the WJ-07 layout gate, a frozen WJ-08 mechanics/evidence contract, and fresh
WJ-09 complete-frame cases. A row can close only with source-bound evidence
and either a supported disposition or a documented applicable-method reason.

## Producer and method register

| Ref | Producer / evidence target | What it can establish; current limit |
| --- | --- | --- |
| **S1 — source inventory** | `scripts/wood_joint_inventory.py` → `source-inventory.json`, `source-inventory-summary.md` | Authenticates 24 former duties, 144 former SDS axes, 66 fixed panel/kicker axes, 12 starting frame-bolt arrangements, six source contacts, two center receiver obligations, source faces/grain, and member transforms. Inventory only; no candidate path or resistance. |
| **G1 — finished candidate geometry** | `mini_moonboard/wood_joint_geometry.py`, `mini_moonboard/wood_joint_frame.py`; WJ-03 `scripts/wood_joint_clearance.py`; WJ-04 `scripts/wood_joint_wj04_probe.py`; WJ-05 receiver/transfer producers; integrated WJ-06 producer still required | Geometry primitives cover finished parts, cuts, bores, bolt stacks, washer seats, local extrema, clearance and access. Current WJ-03/04/05 records are local diagnostic configurations; WJ-06 must bind all parts, holes, actual candidate interfaces, installed hardware, retained fasteners, tolerances, and complete counts under one fingerprint. No strength pass. |
| **A1 — early action witness** | `scripts/wood_joint_wj04_early_mechanics.py` → `wj04-early-mechanics.json/.md` | Shifts old angle-ledger actions to proposed WJ-04 faces and closes an idealized statics witness. It is diagnostic only: source cases are not current candidate solves (4 of 211 bound files mismatch per case), and witness assigns no stiffness, pressure, resistance, or load redistribution. Not WJ-09 demand evidence. |
| **R1 — representative resistance methods** | Proposed reusable `mini_moonboard/wood_joint_resistance.py` and `scripts/wood_joint_wj04_resistance.py` (WJ-04 methods task) | Bind one actual WJ-04 host/cleat/bolt/contact topology to explicit loads, material and hardware inputs; emit mode-by-mode component checks and limits. The agreed method boundary is component methods only until a complete joint interaction is demonstrated. No implementation or accepted WJ-04 capacity exists yet. |
| **M1 — joint action/contact model** | Existing accounting primitives in `mini_moonboard/bolted_joint_mechanics.py`; complete candidate consumer required in WJ-08, with fresh actions from WJ-09 | `Wrench`, `shift_wrench`, `to_local`, equilibrium residuals and a compression-only normal projection support accounting. `clearance_response` is a monotonic scalar slip law with caller-supplied stiffness. These primitives do not solve pressure/opening, frictionless contact distribution, bolt-group stiffness, rotation, or coupled complete-joint response. |
| **M2 — timber/bolt reference components** | `mini_moonboard/bolted_timber_checks.py`; `fea/dowel_yield.py` | Existing helpers include DFL dowel-bearing inputs; reference net-tension, parallel row/group tear-out and ideal washer-footprint wood-bearing values; steel/wood single-shear Mode IV; and six single-fastener lateral-yield modes. Each is limited by its docstring to a constituent/reference calculation. Caller still must prove geometry, grain, thread section, gaps, design adjustments, group effects, applicability and combined joint resistance. |
| **C1 — WJ-08 criteria contract** | New fail-closed, fingerprinted criteria producer still required; target output: one criterion record per exact ID and per applicable candidate station/interface/case | Must bind method/version, inputs and source hashes, applicability, coverage, units, result, governing case/mode, limit, status and evidence path. An unimplemented row or missing method stays pending; no empty list, absent connector, or missing demand counts as zero utilization. |
| **F1 — WJ-09 complete-frame cases** | New candidate native model/run and postprocessor still required; target output: authenticated six-case demand/contact/monitor bundle plus linked check results | Must run all six required cases serially against the same frozen WJ-06 geometry and WJ-08 contact/stiffness contract. Export simultaneous signed six-component actions at each physical interface and fastener/group, contact response, member demands and clearance monitors. Re-run affected cases/checks after any revision. |
| **L1 — WJ-07 layout / sequence** | Integrated WJ-06 model plus WJ-07 geometry, tolerance, access and assembly/removal producer still required | Closes physical interface inventory, installed/service clearances, fit, tool strokes, forward/reverse sequence, and individual-part transport under explicit tolerance bounds. Current geometry records are local/nominal and do not close the integrated layout. |
| **H1 — WJ-10 hardware/shop package** | Selected product/source data and WJ-10 BOM, cut, cost and shop producer still required | Binds real stock, fastener/washer/nut/tool properties, whole-frame counts, cut yield and costs to frozen geometry. WJ-03/04/05 hardware is provisional; WJ-05 conditional thread-transition calculations do not select a SKU. |

## Frozen 36 legacy criteria

Every status below is **pending**. “Pass” means the existing adopted
acceptance limit from the source criteria (ratio ≤ 1, margin ≥ 0, exact
identity, or positive clearance) applied to the wood-joint candidate with the
named method and fresh evidence.

### Joint fasteners, groups, and bearing

| Exact legacy ID | Wood-joint method and evidence target | Producer / dependency | Status |
| --- | --- | --- | --- |
| `actual_angle_lateral_CD_1` | Recompute nominal-diameter lateral resistance for each applicable new bolt/wood shear interface using actual members, grain angle, bearing lengths, gap, and thread/shank bearing condition. Evaluate all applicable NDS yield modes and adjustments; compare each physical bolt demand. Preserve a root-diameter case when the thread-bearing rule requires it. | R1/M2 → C1, then F1; requires actual bolt, material, bore/grip geometry and signed bolt shear demands. The old angle name retires; its lateral safety question remains. | pending |
| `additional_group_reduction_sensitivity` | Apply the adopted additional group-reduction treatment to every new and retained bolt group where applicable; calculate the baseline group factor and the required sensitivity from actual row geometry and load direction. Do not assume `single_shear`'s supplied reduction terms were selected or justified. | R1/M2 → C1/F1; requires complete group inventory, bolt coordinates, applicable row count/pitch, member grain and per-bolt/group demand. | pending |
| `local_parallel` | Check local wood bearing in every receiving member at every interface using actual signed fastener/contact force projected along that member's grain. Use the applicable design value and adjustments, not a parallel-only label when load is oblique. Keep bolt lateral yield and local wood bearing distinct limit states. | R1/M2 → C1/F1; requires material basis, grain vectors, finished bearing length, actual bolt section and actions. `dfl_dowel_bearing_psi` supplies one reference input only. | pending |
| `supplemental_EC5_splitting` | Retain the splitting safety question. WJ-08 must either demonstrate the adopted supplemental EC5 method applies to each changed bolted solid-wood joint and its load/grain geometry, or record a specific supported replacement method with equivalent scope. Row tear-out references are not a perpendicular-to-grain splitting check. | R1/C1; requires exact group/end/edge geometry, member grain, holes/cuts and signed cross-grain action. No splitting producer exists in the candidate lane. | pending |
| `group_spacing` | Recompute required minimum spacing and pitch for each new/retained bolt group under the selected design basis, actual diameter and load direction; separately retain physical hole/washer/tool clearances. `bolt_pair_spacing`, `linear_bolt_row_report`, and 4D/7D comparisons are geometry screens, not capacity approval. | G1/R1 → C1/L1; requires real bolt dimensions, tolerances, axes, member boundaries and applicable rules. | pending |
| `catalog_washer_bounds` | Inventory every selected washer in every new/retained stack and compare actual catalog or product bounds to its modeled dimensions, thickness, opening and seat. Expand from old 12-bolt inventory to all candidate axes, including receiver/backer and internal connector bolts. | G1/H1 → C1; requires selected products, full candidate stacks and source citations. No washer product is selected. | pending |
| `directional_edges` | In both hosts at each interface, classify the loaded edge/end from the signed local action and grain direction, then check actual end/edge distance to every finished boundary, bore, housing and relief. Report each direction; geometric 4D/7D reserve alone is not the governing rule or a pass. | G1/R1 → C1/F1; requires exact face/grain/cut frames, selected bolt diameter and fresh signed actions. | pending |
| `steel_direct` | Check each selected bolt's direct tension, shear and bending resistance using actual grade/product, shank/thread section, shear planes and simultaneous actions; add a supported interaction check for combined axial/lateral/moment demand. Do not reuse old bolt or ML24Z steel values. | R1/M2 → C1/F1; the helper now reports specified-scenario first-yield component references and a nominal von Mises axial/shear interaction only when a co-located section is identified. That is not a connection design strength. Bending, fracture/thread limits, delivered conformance and the demand model remain open; requires selected bolt basis, section transitions, group force distribution and all-case actions. | pending |
| `washer_bearing` | Check compression transferred through each actual supported washer footprint and corresponding wood bearing area under its signed axial action. Use real washer annulus/contact and wood design basis; the DFL washer-footprint helper assumes ideal full contact and does not establish bolt load, washer stiffness, or support. | R1/M2 → C1/F1; requires actual washer dimensions/material, host cuts, support polygon, contact pressure and axial bolt action. | pending |
| `washer_bending` | Calculate washer plate bending/stiffness for the actual thickness, material, opening, bolt head/nut, unsupported span and seat; compare with a sourced property or an explicit mechanics method. Outside diameter alone is insufficient. | R1/H1 → C1/F1; requires washer product/mechanical properties and actual support/load distribution. No washer-bending producer or accepted capacity is present. | pending |

### Finished wood sections and global frame response

| Exact legacy ID | Wood-joint method and evidence target | Producer / dependency | Status |
| --- | --- | --- | --- |
| `sampled_net_member` | Rebuild finished critical-section inventory for all affected frame and connector members with every candidate/retained bore, housing, notch, kerf, relief and cut. Check each section under its simultaneous axial, shear, bending and torsion actions with applicable net-section resistance; cover all bore centers and cut transitions. | G1/M2 → C1/F1; requires final cut solids, candidate axes, material/design values and section demands. Existing `dfl_net_parallel_tension_reference_lbf` covers only one reference tension case. | pending |
| `header_gross_full_length_stability` | Recheck the full header gross-section stability question using changed member geometry, actual unsupported length/restraints and WJ-08 joint translational/rotational stiffness. Do not inherit old angle restraint or old case result. | C1/F1; requires final frame support model, member section/material basis and bounded joint stiffness/contact law. | pending |
| `base_bearing_average` | Reconcile the original base/header bearing location to actual candidate contact faces. For each applicable signed case, calculate average compressive bearing over the real active face area; opening receives no compressive bearing credit. | G1/M1 → C1/F1; requires physical contact graph, face area, normals and fresh signed reactions. | pending |
| `base_bearing_quarter_area_sensitivity` | Retain the adopted quarter-area concentration sensitivity at the mapped physical bearing face(s), using the same signed action and actual candidate areas. Any replacement needs a named contact-pressure method and explicit justification before criteria migration. | G1/M1 → C1/F1; shares `base_bearing_average` input; no quarter-area ratio exists for wood-joint geometry. | pending |
| `base_end_notch_shear` | Recheck shear at the retained base/end bevel or notch in the finished member and any candidate alteration. If no new primary-member house is selected, retain original cut and recompute its applicable shear section; if a cut is proposed, include its shoulder and altered shear path. | G1/M2 → C1/F1; requires authenticated finished taper/end geometry, all cuts and actual member shear/torsion actions. | pending |
| `sampled_member_stability` | Recheck every sampled frame member/section after member and joint changes for applicable stability/failure modes, with supports and stiffness from the frozen candidate. A passed geometry sample or an old-frame Boolean does not establish resistance. | G1/C1/F1; requires all candidate section stations, material values, joint response and six-case member actions. | pending |
| `floor_rail_wood_bearing` | Check actual runner/rail-to-floor wood bearing under the same explicitly conditional no-slip support assumption and fresh candidate reactions. State the support area/load distribution. Do not add floor friction, anchor or verified-floor claims. | G1/M1 → C1/F1; requires retained floor contact geometry, signed support reactions and lumber bearing basis. | pending |
| `taper_actual_net_section_normal_resistance` | Recompute normal resistance of the actual retained tapered member sections, including new/retained holes or cuts and actual normal demands. Use section-wise net geometry, not nominal 4×6 gross dimensions. | G1/M2 → C1/F1; requires taper identity, section samples, machining inventory, material and candidate actions. | pending |
| `taper_sampled_rectangular_shear_torsion` | Recompute retained rectangular-section shear/torsion at all required taper stations and disclose method scope. At bored/cut stations, use a method that includes those openings or an explicitly bounded alternate; do not use the unbored formula there. | G1/M2 → C1/F1; requires final opening map, section properties and simultaneous shear/torsion demands. | pending |

### Geometry identity, physical paths, and clearance

| Exact legacy ID | Wood-joint method and evidence target | Producer / dependency | Status |
| --- | --- | --- | --- |
| `receiver_fit` | Check every structural bolt/washer seat and all 66 fixed Hillman axes against actual finished receiving solids, embedment interval, annular wood and member boundary. Reconcile receiver identity and path through any backer into the frame. `validate_bore_host`, WJ-05 annular checks and washer-seat reports are geometry only. | S1/G1 → L1/C1; requires integrated finished solids, selected fastener envelopes, axes and full receiver attachment graph. | pending |
| `overlap_contact` | Enumerate every real wood/wood, wood/connector and internal connector interface from the candidate solids. Bind physical faces, overlap/contact area, gap/opening behavior and load-path ownership; do not invent contact by numerical gluing or count zero gap as strength. | G1/M1 → C1/F1; requires WJ-06 complete parts/interface graph and contact declaration at every interface. | pending |
| `all_machining_represented` | Compare the integrated finished-part model against every design bore, counterbore, housing, notch, kerf, service relief and corner cut. All geometry used by strength sections, fits and contact faces must be from the same cut model. | G1 → L1/C1; requires one source-bound WJ-06 model and complete cutter/cut inventory. | pending |
| `all_bolt_centres_sampled` | Ensure every selected new bolt center and every retained frame/receiver bolt center is covered by the section sampling/check grid, including closely spaced/multiple rows and housing shoulders. Inventory must reconcile to the final fastener table. | S1/G1 → C1/F1; requires final axis inventory and sampled section records. | pending |
| `actual_kicker_cutouts` | Authenticate the kerf-right surface and actual whole-kicker cutouts against the selected source identity, then confirm both inner edge-support paths and all 66 fixed panel/kicker screw axes/receivers remain represented. Current WJ-05 edge samples/backers are nominal geometry, with receiver-to-frame paths unresolved. | S1, `authority-integrity.json`, G1 and WJ-05 producers → C1; requires integrated candidate/model and unchanged 725-export identity or an explicit source-bound recomputation. | pending |
| `taper_native_actual_taper` | Confirm the candidate structural/native representation contains actual recessed source members, including the correct taper geometry after candidate joints are integrated. | G1 plus native-model identity evidence in F1; requires same frozen CAD/native input fingerprints. | pending |
| `taper_native_matches_cad_taper` | Compare every native finished taper member/surface to its CAD source shape and cut identity; mismatch blocks every affected section/load check. | G1/F1 geometry-authentication step; requires native-to-CAD paired solids and tolerances. | pending |
| `taper_actual_mesh_volume` | Reproduce the existing mesh-versus-CAD recessed-volume authentication on the candidate mesh and source-bound geometry; retain exact tolerance and mesh record. | Candidate CAD/native mesh exporter plus F1 authentication; requires frozen mesh, CAD and mesher settings. | pending |
| `taper_taper_at_least_one_in_ten` | Re-run the adopted specific slope screen on actual recess surfaces, not only nominal member dimensions. | G1 geometry check in C1; requires authenticated start/runout endpoints and any changed cut. | pending |
| `taper_intended_stock_and_runout` | Preserve 4×6 intended member stock and its 1:12 runout identity in each affected part record; reject nominal-2×6 substitution. | S1/G1 source-to-candidate member map plus C1; requires actual section/runout description. | pending |
| `taper_taper_bounds_sampled` | Sample every actual tapered boundary and all adjacent new/retained holes/cuts; section records must bracket each geometry transition and joint-bore location. | G1 → C1/F1; requires final tapered solids, opening map and sample-coverage proof. | pending |
| `taper_taper_region_unbored_torsion_applicable` | Confirm the adopted unbored taper torsion method is used only where the finished taper region has no applicable bore. If any candidate/retained bore crosses it, mark this method inapplicable there and supply a valid bored-section method. | G1/M2 → C1; requires co-located taper, cut and bore geometry plus method applicability evidence. | pending |
| `component_layouts` | Replace the 24-angle component-layout inventory with one owner and physical path per duty, then screen all selected connector parts/bolts/washer stacks/internal pieces and retained axes for local fit, spacing and count. This is not satisfied by duty-owner bookkeeping alone. | S1/G1 → L1/C1; requires complete WJ-06 integrated layout and exact 24-duty/144-old-axis reconciliation. | pending |
| `flush_face_normal_contact` | Reconcile the former six interface identities to the actual physical contact graph. For each real face and each case, establish normal direction, compression-only behavior, opening state and reaction from candidate analysis. An absent former face is not a pass; identify its replacement path. | S1/G1/M1 → C1/F1; requires exact candidate faces, fresh six-case contact results and equilibrium. | pending |
| `flush_face_wood_bearing` | Check bearing at reconciled physical faces from actual active contact areas and signed fresh reactions, with justified pressure distribution and member design values. Keep separate from average/quarter-area legacy base sensitivities. | G1/M1/M2 → C1/F1; requires contact patch/pressure evidence, actual area/material and all-case reactions. | pending |
| `flush_sampled_taper_top_clearance` | Preserve and reconcile the original 18 taper-top monitor identities against the candidate/native monitor set; report every fresh deformed gap and require each applicable gap > 0. If geometry changes, source-bind additions/removals instead of silently dropping a monitor. | S1/G1 → F1; requires exact monitor map, converged six-case candidate displacements and gap sign convention. | pending |
| `angle_rated_force_components` | Replace ML24Z rating arithmetic with a complete resistance envelope for each of the 24 former duties and every real interface/connector/fastener in its replacement path. Check wood bearing/yield, splitting/breakout/net sections, bolt direct and lateral interaction, washer behavior, connector body/internal joints and simultaneous six-component actions in all fresh cases. A zero-angle or missing load path is unresolved, never zero utilization. | R1/M1/M2 → C1/F1; requires final WJ-06 duty/interface graph, selected hardware/material, accepted methods and fresh concurrent actions. No complete candidate joint resistance producer exists yet. | pending |

## Eleven additional candidate obligations

| Exact obligation ID | Wood-joint method and evidence target | Producer / dependency | Status |
| --- | --- | --- | --- |
| `complete_load_path_coverage` | For each exact ID in `source-inventory.json::legacy_duties`, trace load from each original host through actual bearing, bolts, connector parts and internal joints to the frame/floor. Reconcile 24 replacement owners and all 144 removed SDS axes to zero surviving legacy structural paths; distinguish multiple interfaces and shared physical fasteners. | S1 → integrated WJ-06 graph, L1 and C1. WJ-03 currently maps only four duties; WJ-04 one trial; WJ-05 center structural duties remain unresolved. | pending |
| `center_kicker_receiver_paths` | For left and right center receiver obligations, trace all four fixed center-kicker axes through finished backers (or integrated receivers) into the frame, and both inner kicker edges into supported frame paths. Check screw engagement/resistance, backer/header joint, edge bearing/splitting and complete case forces. | `scripts/wood_joint_wj05_receiver_audit.py` and `scripts/wood_joints_wj05_center_backer_transfer_probe.py` provide nominal receiver geometry only; WJ-08 methods + WJ-09 fresh actions required. | pending |
| `connector_body_behavior` | For each solid or multi-piece connector, check finished connector sections under combined axial, shear, bending and torsion; check every internal fastener/contact path and piece-to-piece failure mode. If plywood is proposed, prove layup directions, layer shear/peel, through-thickness bolt/washer behavior and transfer without assumed glue action. | G1/R1/C1 → F1; requires final stock/layup and grain or panel axes, internal interface graph, actions, material properties and methods. | pending |
| `housing_and_finished_sections` | No primary-member house is default. For any explicitly proposed housing/notch, bind exact cut/tool setup; check shoulder bearing, shear/block/net section, loaded cross-grain splitting, local edge/end distances, connector fit and combined effect on full member sections. Missing applicable method keeps that cut out of the accepted layout. | G1/R1/M2 → L1/C1/F1; requires cut solids, sections, grain, exact reactions and removal/fit evidence. | pending |
| `complete_joint_actions` | At each physical interface, shift a signed full 3D wrench to a declared joint datum; preserve all three force and moment components simultaneously. Resolve tension-only bolts, unilateral finite-face compression, lateral bolt actions, group distribution, opening and equilibrium across the whole connector—not independent scalar components. | A1 is old-action diagnostic only. M1 plus new WJ-08 complete-joint formulation and F1 fresh cases required; needs same contact/stiffness inputs as frame model. | pending |
| `joint_stiffness` | Specify evidence-backed translational slip and rotational stiffness for every interface/direction, free-hole travel, opening/contact law and load history sufficient for full-frame redistribution. Select bounded lower/upper sensitivities before WJ-09; report response changes and governing check. `clearance_response` accepts an assumed scalar stiffness and excludes reversal/history; it is not a joint stiffness model. | M1/C1 → F1; requires connector/member/hardware compliance basis, gaps/tolerances, contact law and sensitivity envelope. No stiffness values are accepted. | pending |
| `installed_clearance` | Recheck all finished wood and finite installed head/washer/nut/bolt bodies with holds/T-nuts, LEDs, wire, panels, runners, floor/pads and stated tolerances in the integrated candidate. Record controlling pair, axis/datum and minimum gap; include changes from receiver/backer paths. | Existing WJ-03/04/05 clearance scripts are local nominal screens; G1 + L1 required for integrated tolerance result. | pending |
| `assembly_and_removal_access` | Verify real tool bodies, swing/approach, insertion and complete withdrawal strokes, support states, serial operation order, service disconnect/reinstall and continuous moving-part clearance. Check lower-panel → kicker → node access where used, then reverse assembly. | `wj03-sequence-diagnostic.json`, WJ-04 probe and WJ-05 tool screens are incomplete local diagnostics; L1 must use selected products/tools and integrated tolerance geometry. | pending |
| `demountable_transport` | Bind each finished member/connector to its individually transportable part and provide forward/reverse sequence with zero routine removal of structural wood-engaging threads. Count retained 66 panel screw operations separately from structural bolt operations. | S1 `transport_decomposition`, G1 and L1; requires frozen member sizes, actual joint disassembly, operation and screw counts. | pending |
| `ordinary_n_envelope` | Report each connector and installed hardware's local-N extrema from a named datum against 139.7 mm. Keep permanent body/hardware depth separate from temporary tool and bolt-stroke workspace; any permanent exception must be dimensioned and named. | WJ-03 geometry currently shows body/installed envelope to 225.718477 mm (86.018477 mm excess) and temporary bolt stroke to 315.648756 mm (workspace excess 175.948756 mm); L1 must disposition the permanent outer-node excess and verify temporary workspace. Other stations remain unintegrated. | pending |
| `hardware_source_count_cost` | Bind exact candidate bolt, washer, nut, connector stock, pilot/clearance geometry, tools, supplier/specification, whole-frame quantity, delivered-length/thread limits, stock yield, installation/removal labor assumptions and cost. Keep 66 purchased Hillman panel/kicker screws separately accounted; no old SDS capacity/product policy transfers. | H1/WJ-10; requires frozen WJ-06 geometry and selected real products. WJ-03/04/05 quantities/products remain provisional or unselected. | pending |

## Missing limit-state methods and shared inputs

### Actual missing methods

Existing code provides useful geometry, wrench-accounting, and constituent
reference functions, but these do not produce adjusted wood-joint capacities.
The WJ-08/WJ-09 contract needs explicit, source-cited methods for:

- Complete multi-member bolt lateral resistance: applicable yield modes,
  actual DFL bearing inputs, thread/root versus nominal shank basis, member
  thicknesses/gaps, NDS adjustments, group action and adopted extra group
  sensitivity.
- Direct bolt tension/shear/bending and the combined action envelope at all
  shear planes, including the selected product's grade and thread section.
- Loaded edge/end breakout and group tear-out for signed grain directions,
  plus the separate cross-grain splitting/local fracture question for groups,
  bores and any cut shoulders.
- Unilateral finite-area bearing pressure and opening coupled to bolt tension,
  lateral load, prying and simultaneous moments; a statics witness alone does
  not give pressure, load share, or resistance.
- Actual washer bending and supported wood-bearing behavior using washer
  stiffness/thickness, contact footprint and unsupported span.
- Solid connector body bending/shear/torsion and splitting; every internal
  multi-piece interface; and, only if selected, structural-plywood layer and
  through-thickness behavior.
- Full-frame joint translation/rotation/slip stiffness and bounded sensitivity
  that consistently drives both the frame solution and resistance check.
- Bored/tapered member section and stability checks wherever an adopted
  unbored or gross-section method no longer applies.

Reference functions in `mini_moonboard/bolted_timber_checks.py` and
`fea/dowel_yield.py` may be reused only within their documented scope. In
particular, a parallel row/group tear-out reference does not close splitting;
the six single-bolt yield values are not group/joint resistance; and ideal
washer-annulus bearing is not washer strength or pressure distribution.

### Shared inputs every evidence bundle must bind

1. **Candidate and geometry identity:** candidate ID; source and candidate
   fingerprints; complete finished-part/cut/receiver/bolt inventory; 24-duty
   ownership; all physical contact faces and datums; exact axis mapping; 66
   fixed screw axes; 12 retained frame bolts; taper/kicker/monitor identity.
2. **Six-case actions:** fresh same-configuration frame run IDs and source
   hashes; signed simultaneous force and moment vectors shifted to declared
   interface and bolt-group datums; per-fastener distribution; member forces;
   contact state/pressure; deformed clearances; equilibrium and convergence.
   The WJ-04 early-mechanics file uses old diagnostic actions and cannot fill
   this input.
3. **Wood basis:** member species/grade assumption, section/layup, grain
   vectors, applicable design values and adjustment factors, service
   conditions, bearing direction, and each finished cut/opening. Keep physical
   receiving/inspection observations blank until WJ-11.
4. **Hardware basis:** selected bolt/washer/nut/connector products and
   quantities; bolt grade, nominal and root diameter, thread transition,
   bearing lengths, shear planes, grip, washer dimensions/thickness/support,
   material properties, tolerance and applicable product/source records.
5. **Joint response basis:** contact graph and face normals; unilateral law;
   gaps/free travel; bolt tension/lateral actions; connection stiffness and
   rotation; force/moment sharing; and bounded sensitivity inputs consumed by
   both F1 and resistance checks.
6. **Geometry/operations basis:** machine cuts and their section effects;
   all real services/holds/panels/pads/floor obstacles; tolerance stack; named
   N datums; real tool envelopes and motion sequence; transport parts; hardware
   and stock counts/cost. Preserve the explicit no-slip floor assumption.

Each eventual evidence record should carry exact criterion ID, method ID and
revision, candidate/geometry/hardware fingerprints, producer command/source
hash, applicable stations/interfaces/cases, input units, formula/source and
scope, result and limit, governing case/mode, status, and known limits. Allowed
evidence states remain those in the candidate plan (`unverified`, `failed`,
`passed_under_recorded_assumptions`, `not_applicable_with_reason`). Until that
evidence exists, every mapping in this document remains pending; this map is
not an engineering disposition or release.
