# WJ-04 early mechanics screen

Status: **diagnostic only; revise named mechanical gaps.** This screen preserves the old selected-candidate
member-on-bracket actions at the WJ-04 reference station and maps them to group centroids from canonical trial
geometry. It does not qualify the new cleat or replace fresh full-frame actions.

## Inputs and transfer

- Old action candidate: `compact-floor-flush-development`; WJ-04 development candidate: `compact-floor-flush-wood-joints-development`.
- Canonical trial: `narrow_x95p25_ordinary_bolt_candidate`; config SHA-256 `d1c63e1fa5617999e8af68d683cc0f3074fb84f518b048a087ec5ed276206c0e`.
- Group positions, signed axes, and cleat bounds come from hash-bound `WJ04_TRIAL`; the active probe is checked against its config hash.
- Station and cases: `clip_horizontal_lower_right_1`; `a12-left`, `a12-rear`, `a12-forward`, `k12-right`, `k12-rear`, `a1-rear`.
- Source actions are the audited `flange_member_on_bracket_wrenches` for the six former SDS groups.
  Their source ledger is angle-demand-only: it did not replay native solves, check current sources, or recompute resistance.
- The old action on the bracket is held unchanged, translated from the old station origin to each proposed bolt-group centroid,
  and reversed to show the equal-and-opposite connector action on its host. No stiffness redistribution is inferred.
- A two-point rigid fastener-only split is retained as an intermediate comparison. A separate rigid statics witness
  transfers bolt-axis compression to contact and closes each row-axis moment with bolt tension and opposite face compression.
  It assigns no stiffness, pressure distribution, preload, or resistance.

Input hashes:

- `docs/floor-runner-mvp-angle-demands.json`: `5446aeacaccafb70c77358635e5fb84c1b9627eb922209411b748e5e34c9e558`
- `docs/wood-joints-mvp/source-inventory.json`: `07af4c3eb642cf3887595fe4415eb65404cdcf74d66c5c7bb182847ef21c2d78`
- `docs/wood-joints-mvp/wj04-probe.json`: `19dc75908780b16d84eecdac170976eeb94009e4869c9293bf2867d7098af1ac`
- `scripts/wood_joint_wj04_probe.py`: `75d397795e5fa69d1d04f1d14caeb57f93a2da94cacecd4a1edc5bdad3fe4d94`
- `mini_moonboard/wood_joint_wj04_config.py`: `4f94f49ebc0c5f92e6dce339794983607614299f53150fc7264ca54b29e987be`
- `scripts/wood_joint_wj04_early_mechanics.py`: `ef2b23a9802e5110c745911fcbcd3de9cfeeced325b308e986459c3610f14357`

## Source/hash staleness

The old action ledger marks current sources unchecked. This report re-compares declared hashes with the present working tree
to make that provenance gap explicit; a match does not replay or authenticate an old solve.

Old six-case producer snapshot:

- `a12-left`: 207/211 files match; 4 mismatched, 0 missing.
- `a12-rear`: 207/211 files match; 4 mismatched, 0 missing.
- `a12-forward`: 207/211 files match; 4 mismatched, 0 missing.
- `k12-right`: 207/211 files match; 4 mismatched, 0 missing.
- `k12-rear`: 207/211 files match; 4 mismatched, 0 missing.
- `a1-rear`: 207/211 files match; 4 mismatched, 0 missing.

Recorded old hashes that differ from current files:

- `fea/current_response_model.py`: recorded `e724bbb74150923265b13be2513c2634c3cb02b4c3568c43b3aee55626507dce`, current `faae5b14c47c3c485f41d56eb77ec9e9a6c1801e5a143276a91afc3a294a9894`.
- `fea/current_response_run.py`: recorded `1b887692f73561c2d7a0da6f82777dbd887e8223d769c13bdec9b576e8fb5061`, current `2e981f24616afcd441cca911a89942b0f12784f97aa13a59933a4d002ca5f955`.
- `fea/reinforced_frame_demand.py`: recorded `807934918e7f075c4f505df9ed18d024714c2adfe5f5698e430eb4c96be9b552`, current `7c9d9b19155ddb257bdb3479eafa98cdb2fe81788b5f0e62b35d12fae0667655`.
- `mini_moonboard/compact_floor_flush_frame.py`: recorded `4cc03e086b381de2cd04685578bfccccfa72ee6e3545814d8e2469a3196de045`, current `8764bec57564efa79f2636e589aa0e35b229c48975c791eec5c47b20183bf17a`.

Currentness of the other bound producers:

- Old ledger consumer `scripts/clear_space_case_contract.py`: **match**.
- Old ledger consumer `scripts/floor_flush_angle_ledger.py`: **match**.
- Old contact-search producers versus current `fea/current_response_run.py`: **stale_or_mismatched**; current hash `2e981f24616afcd441cca911a89942b0f12784f97aa13a59933a4d002ca5f955`.
- Selected source inventory bindings: 0/7 current hash mismatches.
- WJ-04 probe producer/dependencies: 0/14 current hash mismatches.

## Candidate interfaces

| Interface | Host face normal | Bolt axis | Bolt-row axis | Spacing | Finite-probe area estimate | Old normal action range | Separation cases |
|---|---:|---:|---:|---:|---:|---:|---|
| `rail_to_cleat` | `-0, 0.642788, 0.766044` | `0, 0.642788, 0.766044` | `1, 0, 0` | 25.400 mm | 11401.398713 mm² | [-22.445, -10.385] N | a12-left, a12-rear, a12-forward, k12-right, k12-rear, a1-rear |
| `principal_to_cleat` | `1, 0, -0` | `-1, 0, 0` | `0, -0.766044, 0.642788` | 27.000 mm | 4560.569999 mm² | [13.322, 33.736] N | none |

The signed normal action is reported as **legacy host on bracket**, using the outward normal from each host face toward
the cleat. A negative value indicates a separation tendency in that interface; its equal-and-opposite connector reaction
on the host is positive. Across these old cases the rail interface indicates separation in all six; the principal interface
is compressive in all six. The new bolt axes are parallel to the corresponding face normals, so the provisional topology has
an axial fastener direction for both signs. That alignment establishes no resistance.

### Canonical contact-face edge bands

Coordinate bounds are derived from source-inventory host face planes and canonical cleat dimensions.
The row-axis moment witness uses a finite 10 mm band at the selected face edge, with its resultant 5 mm inside that edge.
Both possible signed edges must fit the full band before the report is generated. The projected bolt-group centroid and each
finite-band resultant must also lie inside the canonical bounds rectangle along both the bolt-row and transverse axes.

| Interface | Band width / inset | Negative edge distance / lever | Positive edge distance / lever | Face band area |
|---|---:|---:|---:|---:|
| `rail_to_cleat` | 10.0 / 5.0 mm | 35.159 / 30.159 mm | 84.541 / 79.541 mm | 952.5 mm² |
| `principal_to_cleat` | 10.0 / 5.0 mm | 19.050 / 14.050 mm | 19.050 / 14.050 mm | 1197.0 mm² |

### Contact-area measurement and coordinate audit

The contact-area estimate is read from the active, trial-bound WJ-04 probe. Its hash-bound producer computes the
cleat/host overlap volume after a 0.1 mm inward translation, divided by that probe depth. The separate canonical
bounds rectangle is the product of the row and transverse coordinate spans used for the edge witness. The signed
difference is probe estimate minus rectangle area; the quantities are reported separately without a tolerance-based
equivalence claim. This is geometry provenance only, not pressure or resistance.

| Interface | Finite-probe estimate | Canonical bounds rectangle | Probe minus rectangle | Ratio | Method |
|---|---:|---:|---:|---:|---|
| `rail_to_cleat` | 11401.398713 mm² | 11401.425000 mm² | -0.026287 mm² | 0.999998000 | `thin_inward_intersection_volume_divided_by_probe_depth` at 0.1 mm |
| `principal_to_cleat` | 4560.569999 mm² | 4560.570000 mm² | -0.000001 mm² | 1.000000000 | `thin_inward_intersection_volume_divided_by_probe_depth` at 0.1 mm |

### Canonical signed material axes

| Member | Grain axis | Rail stack axis | Principal stack axis | Stock basis verified |
|---|---:|---:|---:|---|
| `base_rail_service_lower_right` | `1, 0, 0` | `0, 0.642788, 0.766044` | `-1, 0, 0` | False |
| `base_principal_center_right` | `0, 0.642788, 0.766044` | `0, 0.642788, 0.766044` | `-1, 0, 0` | False |
| `wj04_cleat` | `0, -0.766044, 0.642788` | `0, 0.642788, 0.766044` | `-1, 0, 0` | False |

Canonical bolt axes are rail `0, 0.642788, 0.766044` and principal `-1, 0, 0` in global XYZ.
Member grain directions use canonical config axis names and hash-bound source transforms; old probe local labels do not set material directions.
Signed old-action projections and minimum-norm bolt splits are diagnostic. They do not establish current NDS loaded-edge or end categories.

Cleat bolt-axis/grain parallel flags: rail `False`, principal `False`.
Principal cleat minimum T lateral-edge distance is 19.050 mm; conditional 4D reference reserve is -6.350 mm if current lateral force loads that edge.
Principal cleat minimum N grain-end distance is 29.541 mm; 4D/7D reference reserves are 4.141/-14.909 mm, subject to signed NDS end-category applicability.

## Signed actions at proposed group centroids

Each row gives the old host-on-bracket force in canonical local X/T/N and its moment about the current canonical group centroid.
The connector-on-host force and moment are equal and opposite. Moments are N·mm.

| Case | Interface | F X | F T | F N | M X | M T | M N |
|---|---|---:|---:|---:|---:|---:|---:|
| `a12-left` | `rail_to_cleat` | -20.073 | -15.650 | -26.336 | 1078.125 | -3357.832 | 88.370 |
| `a12-left` | `principal_to_cleat` | 20.071 | 15.652 | 26.342 | -1934.320 | 3695.868 | 362.859 |
| `a12-rear` | `rail_to_cleat` | -22.039 | -16.144 | -27.222 | 1763.339 | -3004.231 | 67.179 |
| `a12-rear` | `principal_to_cleat` | 22.039 | 16.143 | 27.217 | -2648.737 | 3299.325 | 474.847 |
| `a12-forward` | `rail_to_cleat` | -17.839 | -14.204 | -27.917 | 1389.951 | -2894.576 | 87.400 |
| `a12-forward` | `principal_to_cleat` | 17.838 | 14.206 | 27.917 | -2395.983 | 3395.218 | 300.530 |
| `k12-right` | `rail_to_cleat` | -32.498 | -21.735 | -29.840 | 85.510 | -5043.086 | 41.033 |
| `k12-right` | `principal_to_cleat` | 32.497 | 21.736 | 29.839 | -888.853 | 5020.812 | 849.947 |
| `k12-rear` | `rail_to_cleat` | -33.735 | -22.445 | -26.944 | -1109.760 | -5650.427 | 39.549 |
| `k12-rear` | `principal_to_cleat` | 33.736 | 22.442 | 26.947 | 501.209 | 5448.286 | 891.054 |
| `a1-rear` | `rail_to_cleat` | -13.322 | -10.385 | -26.750 | 611.667 | -2302.654 | 60.253 |
| `a1-rear` | `principal_to_cleat` | 13.322 | 10.384 | 26.749 | -1709.407 | 2938.764 | 239.524 |

## Bolt tension, face compression, and wrench closure

For each host interface, the statics witness balances the full historical diagnostic wrench with tension-only axial bolt resultants,
transverse point-bolt resultants, and compression-only face-contact resultants. Row-axis moment uses the signed 10 mm face-edge band.
The finite-band couple force exceeds the zero-area edge-resultant force baseline because the resultant sits 5 mm inboard.
This is idealized rigid statics; it does not calculate pressure distribution, opening, stiffness, slip, or resistance.

| Case | Interface | Edge | Band / inset | Edge distance | Finite lever | Finite couple force | Zero-area edge force | Peak bolt tension | Peak face compression | Force / moment residual |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `a12-left` | `rail_to_cleat` | negative | 10.0 / 5.0 mm | 35.159 mm | 30.159 mm | 35.748 N | 30.664 N | 29.178 N | 35.748 N | 0 N / 1e-06 N·mm |
| `a12-left` | `principal_to_cleat` | negative | 10.0 / 5.0 mm | 19.050 mm | 14.050 mm | 25.826 N | 19.048 N | 139.761 N | 146.920 N | 0 N / 0 N·mm |
| `a12-rear` | `rail_to_cleat` | negative | 10.0 / 5.0 mm | 35.159 mm | 30.159 mm | 58.468 N | 50.153 N | 39.951 N | 58.468 N | 0 N / 1e-06 N·mm |
| `a12-rear` | `principal_to_cleat` | negative | 10.0 / 5.0 mm | 19.050 mm | 14.050 mm | 33.797 N | 24.926 N | 128.076 N | 133.217 N | 0 N / 0 N·mm |
| `a12-forward` | `rail_to_cleat` | negative | 10.0 / 5.0 mm | 35.159 mm | 30.159 mm | 46.087 N | 39.533 N | 33.587 N | 46.087 N | 0 N / 1e-06 N·mm |
| `a12-forward` | `principal_to_cleat` | negative | 10.0 / 5.0 mm | 19.050 mm | 14.050 mm | 21.390 N | 15.776 N | 127.525 N | 134.668 N | 0 N / 0 N·mm |
| `k12-right` | `rail_to_cleat` | negative | 10.0 / 5.0 mm | 35.159 mm | 30.159 mm | 2.835 N | 2.432 N | 13.900 N | 2.835 N | 0 N / 2e-06 N·mm |
| `k12-right` | `principal_to_cleat` | negative | 10.0 / 5.0 mm | 19.050 mm | 14.050 mm | 60.494 N | 44.617 N | 199.955 N | 202.205 N | 0 N / 0 N·mm |
| `k12-rear` | `rail_to_cleat` | positive | 10.0 / 5.0 mm | 84.541 mm | 79.541 mm | 13.952 N | 13.127 N | 19.756 N | 13.952 N | 0 N / 2e-06 N·mm |
| `k12-rear` | `principal_to_cleat` | negative | 10.0 / 5.0 mm | 19.050 mm | 14.050 mm | 63.420 N | 46.775 N | 216.630 N | 218.657 N | 0 N / 0 N·mm |
| `a1-rear` | `rail_to_cleat` | negative | 10.0 / 5.0 mm | 35.159 mm | 30.159 mm | 20.281 N | 17.397 N | 17.705 N | 20.281 N | 0 N / 1e-06 N·mm |
| `a1-rear` | `principal_to_cleat` | negative | 10.0 / 5.0 mm | 19.050 mm | 14.050 mm | 17.048 N | 12.573 N | 110.706 N | 115.504 N | 0 N / 0 N·mm |

## Complete-joint resistance disposition

Disposition: **revise_named_constraint**; full bounded capacity feasible from current inputs: **False**.
Old loads remain stale angle-demand diagnostics. No fresh candidate per-fastener demand or resistance comparison exists.

| Limit state | Status | Main unresolved inputs |
|---|---|---|
| `fresh_same_case_interface_actions` | **UNRESOLVED_DEMAND** | current candidate demands; old selected-candidate angle wrenches are provenance-preserved diagnostics only; stiffness/contact model to resolve per-fastener lateral and axial actions without assumed equal sharing |
| `wood_bearing_end_edge_group_net_section_splitting` | **UNRESOLVED_GEOMETRY_MATERIAL_DEMAND** | signed current per-fastener lateral vectors on each member and applicable NDS loaded-edge/end category; delivered bore diameters, exact bore/cut geometry, neighboring holes, and finished member section boundaries; cross-grain splitting method and applicability basis separate from Appendix E; verified delivered species/grade/moisture and NDS design-value adjustment inputs |
| `bolt_lateral_yield_and_bending` | **UNRESOLVED_MATERIAL_DEMAND** | current per-fastener lateral demand and zero-gap/contact applicability for both wood/wood single-shear interfaces; delivered full-body and thread-root diameters plus thread-bearing lengths in each wood layer; delivered-bolt Fyb supported by applicable ASTM F1575/F606 evidence; grade label alone does not set Fyb; applicable NDS adjustment factors and complete group/spacing checks |
| `bolt_steel_tension_shear_interaction` | **UNRESOLVED_MATERIAL_DEMAND_METHOD** | certified minimum bolt yield strength and controlling tensile area; actual shank/thread shear-plane area for each installed stack; same-bolt signed axial and lateral demand; adopted tension/shear interaction rule applicable to this joint |
| `washer_bearing_and_plate_spread` | **UNRESOLVED_MATERIAL_GEOMETRY_DEMAND** | verified washer seat fit on actual finished wood around each delivered bore; washer plate bending/spread capacity and local wood crushing/pull-through method; washer/nut/bolt delivered dimensions, material properties, and actual axial demand |
| `unilateral_contact_pressure_opening` | **GEOMETRY_WITNESS_ONLY** | pressure distribution and contact stiffness on both wood sides; opening extent, fit/gap, local Fc-perp design resistance, and coupled bolt tension |
| `cleat_internal_transfer_and_section` | **UNRESOLVED_GEOMETRY_DEMAND_MATERIAL** | complete cut/hole/defect geometry and finished-section checks at every critical cleat cut; same-case coupled force and all moment components at cleat datum; verified cleat grade/species and adjusted material design values; cross-grain splitting/block-shear method and applicability |
| `complete_joint_capacity_envelope` | **UNRESOLVED** | all component dispositions above on one fresh, source-bound candidate demand set |

Wood checks require actual signed member-side fastener actions, finished holes/cuts, material and adjustment inputs; Appendix E covers parallel-grain net/tear-out modes only.
Bolt checks require measured thread engagement in both bearing layers, product-applicable Fyb and steel areas; tension/shear interaction remains unadopted.
Washer steel spread, unilateral contact pressure/opening, and cleat internal transfer remain unresolved. The finite 10 mm contact band is equilibrium geometry only.

## Coupled cleat free-body source closure

Both host-on-bracket interface wrenches are translated to one shared datum and summed. This audits the historical source ledger
balance only; it does not evaluate cleat bending, splitting, fastener interaction, or revised-frame demand.

| Case | Force residual | Moment residual |
|---|---:|---:|
| `a12-left` | 0.00679 N | 0.323 N·mm |
| `a12-rear` | 0.00463 N | 0.174 N·mm |
| `a12-forward` | 0.00162 N | 0.134 N·mm |
| `k12-right` | 0.00116 N | 0.112 N·mm |
| `k12-rear` | 0.00393 N | 0.214 N·mm |
| `a1-rear` | 0.000661 N | 0.0198 N·mm |

## What this supports

- Signed legacy interface force and all three moment components can be reconstructed at each proposed group centroid.
- The rail side requires a tie path under every old case; compression contact alone cannot supply its normal action.
- Each interface has a finite-band row-axis contact-couple witness with signed edge choice, in-face lever, and full wrench closure.
  The 5 mm inset increases couple force over the optimistic zero-area edge resultant. Geometry, hardware, NDS resistance,
  joint interaction, and fresh candidate demands remain open.
- Both historical interface actions are summed at one shared datum to expose old-ledger closure residuals before geometry reuse.
- The principal face has a compression-normal component in all six old cases. This does not prove that contact remains closed
  after coupled moments, tolerances, or changed full-frame stiffness.

## Checks this cannot support

- No resistance or pass for bolt tension, shear, interaction, withdrawal, washer bearing, wood bearing, splitting, or connector bending.
- No contact-pressure distribution, opening extent, slip, rotational stiffness, bolt preload, group stiffness, or load sharing between faces.
- No cleat internal stress, complete wood/bolt/contact capacity, or fresh six-case demand for the revised frame and cleat.
- No reuse of the old angle rating, selected-candidate case pass, or any legacy screw capacity.
- No drilling, stock selection, fabrication, or structural release.

The reported local results are sufficient to carry WJ-04 into an explicit mechanics-method step. They do not clear the
tool, tolerance, stock, length, end/edge, or service-obstruction blockers in the geometric probe.
