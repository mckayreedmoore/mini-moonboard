# Current six-case frame dead-load map

**Scope:** implementation accounting for the reviewed WJ24 geometry
`led-clearance-2x6-runner-seated-blocks-v1`. This documents gravity inputs for a
future complete-frame six-case model. It is not a solved response, a mass
measurement, or a capacity result.

The frozen [six-case contract](hypotheses/evaluation-resume-2026-09-24/current-load-cases.json)
contains the 250 lb × 2 downward climber force and one horizontal force per
case. It contains no body density, self-weight, accessory mass, gravity vector,
or dead-load resultants. Its vertical climber component is 2,224.1108 N. The
contract therefore neither includes nor double-counts board/accessory weight;
the complete-frame model must apply that weight separately in every case. The
climber multiplier applies to the climber force only. Do not multiply gravity
by 2 or combine it with the 20 mm climbing patch.

The separate selected-candidate [design basis](../current-design-basis.md)
states that its native cases include the 25 kg allowance at recorded locations.
That does not supply an application point for this WJ24 contract: this frozen
WJ24 contract is force-only and has a separate revision and provenance.

## Source-bound physical inventory

The owner-reviewed [weight inventory](board-weight-2026-09-24.json) totals
224.4207767 kg of modeled solids and a separate 25.0 kg equipment allowance:
249.4207767 kg / 549.8787 lb. The stated planning sensitivity is 208.5604 to
259.4208 kg / 459.7969 to 571.9249 lb, from 500–600 kg/m³ for wood/plywood and
20–35 kg for equipment. These are estimates, not measured properties.

| Physical mass family and current identities | Inventory amount | Required six-case gravity representation |
| --- | ---: | --- |
| Plywood panels: `main_lower_left`, `main_lower_right`, `main_upper_left`, `main_upper_right`, `kicker_left`, `kicker_right` | 6 solids; 72.071718 kg at 600 kg/m³ | Put density on each current finished panel solid. If a panel is reduced to a shell or resultant, preserve that panel’s own volume and mass centroid from the current source geometry. |
| Frame timber: `base_side_left/right`, `base_rail_top`, `base_header`, `base_post_outer_left/right`, `lumber_leg_left/right`, `base_principal_center_left/right`, `base_post_center_left/right`, `base_rail_bottom_left/right`, `base_rail_service_lower_left/right`, `base_rail_service_upper_left/right`, `base_floor_left/right` | 20 solids; 127.532182 kg at 600 kg/m³ | Put density on every current finished member. The 16 scene `shared_hosts` are not the whole timber list; retain the four named `base_floor_*` and `lumber_leg_*` parts that continue from the surrounding source assembly. |
| Solid block set: `knee_outer_left_spine`, `knee_outer_right_spine`, `wj06_outer_lower_right_cleat`, `wj04_lower_full_stock_cleat`, `wj04_upper_g7_crosscut_full_stock_cleat`, `wj06_outer_upper_right_cleat`, `center_post_cleat_left/right`, `center_principal_cleat_left/right`, `left_service_outer_upper_cleat`, `left_service_inner_upper_cleat`, `left_service_inner_lower_cleat`, `left_service_outer_lower_cleat`, `top_outer_left/right_cleat`, `top_center_left/right_cleat`, `bottom_outer_left/right_cleat`, `bottom_center_left/right_cleat`, `knee_outer_left_inner_frame_block`, `knee_outer_right_inner_frame_block` | 24 solids; 15.558465 kg at 600 kg/m³ | Put density on each current block solid. Use the current candidate part identity and volume; do not substitute a removed angle or historical backer. |
| Candidate block bolts, nuts, and washers: the 92 installed candidate axes, each with `/shaft`, `/head`, `/head_washer`, `/nut_washer`, and `/nut` roles | 460 role solids; 5.381384 kg at 7,850 kg/m³ | Include the physical role volumes once each at their current locations. If the FE representation uses reduced connectors, retain each omitted metal role’s mass once at its source-derived center of mass. |
| Starting frame bolts, nuts, and washers: the 12 retained frame-bolt axes, with five role solids per axis | 60 role solids; 1.904015 kg at 7,850 kg/m³ | Keep all 12 existing stacks in the mass map. Their structural recheck status does not remove their physical mass. Use the installed component geometry once each. |
| Panel/kicker screws: all 66 current screw axes, consisting of 58 fixed and 8 moved axes | 66 screw solids; 0.442914 kg at 7,850 kg/m³ | Include one physical screw body at each current axis. The eight moved screws keep their mass but use their current locations. Do not add their old positions as second masses. |
| Hold T-nuts: `hold_tnut_main_A1` through `hold_tnut_main_K12`, plus `hold_tnut_kicker_1` through `hold_tnut_kicker_10` | 142 T-nuts; 1.530098 kg at 7,850 kg/m³ | Include the 142 current steel T-nut bodies once. This 1.53 kg is already in the modeled subtotal, separate from the 25 kg accessory allowance. |
| Holds, their attachment bolts, and electrical equipment (including the scene’s changed `light_G2`, `wire_073_G1_G2`, and `wire_074_G2_G3` identities) | 25.0 kg unitemized equipment allowance; no per-item mass or center in the weight inventory | Keep the full 25 kg as an additional equipment mass. To prevent duplication, treat it as the non-modeled hold bodies, hold bolts, and electrical equipment; do not add the already modeled T-nuts or the listed frame, block, and panel fasteners to it again. Its location is not established by the geometry inventory. |

The weight JSON binds each modeled inventory row to mass and volume but does not
provide a general center-of-mass field. For reduced gravity loads, obtain each
listed part or metal-role centroid from its corresponding current geometry
solid, then preserve that individual mass and first moment. This geometry
extraction is separate from the unresolved accessory-mass split above.

For volumetric solids in SI units, apply body force using
`rho * [0, 0, -9.80665]` with density in kg/m³ and coordinates in metres. In the native
N–mm–tonne–second convention used by the current mechanics patches, use
`rho * [0, 0, -9806.65]`, with density in tonne/mm³ and acceleration in
mm/s². Thus 600 kg/m³ is `6.0e-10 tonne/mm³`, and 7,850 kg/m³ is
`7.85e-9 tonne/mm³`; do not pair those native densities with `9.80665`.
In a reduced model, use each source body’s actual mass and source-derived
center of mass, preserving the force and moment of that distributed
self-weight. Do not route hardware to the nearest timber by bounding-box
distance or spread one combined mass over the frame by convenience.

## Accessory placement and model boundary

The 25 kg allowance contributes 245.1663 N of gravity. It has no item split or
center of mass in the board-weight inventory, but that is an analytical
placement choice for the model, not a reason to block all conditional
evaluation pending per-item measurements. The current geometry supplies a
usable placement basis: `panel_grid_v2` defines 132 main-board attachment axes
(A1–K12) and ten kicker axes; the current scene identifies the changed
`light_G2`, `wire_073_G1_G2`, and `wire_074_G2_G3` electrical shapes. These
define candidate regions, not the actual mass distribution. A bounded,
reviewable first implementation can keep a single split parameter
`m_electrical` from 0 to 25 kg, use `25 - m_electrical` at the arithmetic
centroid (equal axis weighting) of the 142 available hold axes as a
hold-and-hold-bolt resultant proxy, and put `m_electrical` at the
combined-volume centroid of the current electrical shapes. Record this as an explicit
resultant scenario, not an inferred installation. Sweep the split endpoints
and selected intermediate values; include hold-axis endpoint
placements at A1, K1, A12, K12, kicker 1, and kicker 10 to show sensitivity to
the unknown hold distribution. Project hold resultants to the current panel face
for the baseline, and declare any outward hold-CG offset as a separate
parameter rather than borrowing the climber’s 100 mm standoff. Do not silently
reuse the historical upper-panel split or assume equal mass at every panel or
T-nut.

The current scene does not supply actual hold locations, accessory sub-masses,
or the center of any equipment outside the listed electrical geometry. The
centroid and endpoint placements above are analytical scenarios tied to
current mounting regions, not evidence of actual installation. If a confirmed
hold layout, equipment split, or external electrical item location is already
available, use those inputs in the same 25 kg budget and retain the scenario
sweep to document sensitivity; do not add the inventory’s T-nuts and fasteners
to the allowance a second time.

The old `fea/current_response_model.prepare` code contains an earlier
`equipment_kg=25` convention: it adds 12.5 kg to each upper main panel at one
point derived from the historical `panel_grid_v2.main_tnut_datums()` table. It
does not enumerate actual hold/bolt/light masses. That is not the current
WJ24 placement map, and its old two-point split must not be imported into the
current six cases without a separate source for the aggregate center of mass.

The existing [ordinary-joint preflight](hypotheses/evaluation-resume-2026-09-24/ordinary-native-preflight-attempt04/README.md)
meshed three timber members and local metal bodies. Its [mass audit](hypotheses/evaluation-resume-2026-09-24/ordinary-native-mass-audit-attempt02/audit.json)
checked two timber translations and four bolt/nut translations; it did not
cover the 20 frame timbers, six panels, 24 blocks, or complete installed
hardware inventory. The four local nut-carrier CAD bodies were intentionally
zero density for that engagement diagnostic. If a complete model retains
zero-mass rigid nut carriers, add the real nut mass from the 92/12-stack
inventory once at each source-derived nut center. Do not copy the local
diagnostic omission into frame dead load or also assign mass to a duplicate
nut-display envelope.

The legacy [whole-frame mass helper](../../fea/current_response_model.py)
works on its `no-shoes-development` candidate and routes its modeled hardware
to the nearest raw body. Its geometry and equipment placement do not represent
the current WJ24 block assembly. The current six-case producer remains an
applied-force contract; this table prepares the separate dead-load inputs and
does not claim that the complete-frame model or its mass-application map has
been built or solved.

Using the owner estimate, the modeled-solid subtotal weighs 2,200.8160 N at
9.80665 m/s², the 25 kg accessory allowance weighs 245.1663 N, and the total
planning weight is 2,445.9823 N. The same totals in native units are
`0.2244207767 tonne × 9806.65 mm/s²`, `0.025 tonne × 9806.65 mm/s²`, and
`0.2494207767 tonne × 9806.65 mm/s²`. Apply these as distributed mass/gravity
and explicit accessory-placement scenarios in the complete model, alongside
the six applied climber wrenches. These resultants are arithmetic checks, not
a single support load or a replacement for body-by-body gravity.

## Provenance

The implementation identities above are bound to these current inputs:

| Source | SHA-256 |
| --- | --- |
| [Weight estimate](board-weight-2026-09-24.json) | `7425c8100c9bbf0586d8e1732138eb5ec1e6147f8418b5cf3ea95dc6108e035e` |
| [Weight estimate narrative](board-weight-2026-09-24.md) | `f225a3ab2313135a50d098356689ae1e26da03119bce8530d0d6656c3ed43564` |
| [Reviewed WJ24 scene](../../site/owner-wood-joints-wj24-scene.json) | `74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf` |
| [Current geometry snapshot](hypotheses/evaluation-resume-2026-09-24/geometry-snapshot.json) | `0b92357af648604ee8ce42d2f8906e0a4e5498e9e4b835a07938b81dc151d187` |
| [Current load datums](hypotheses/evaluation-resume-2026-09-24/current-load-datums.json) | `c3a561b84eb56472264e92eacabae7c2e06fe33633ebba96f1de9ee974924022` |
| [Current hold-axis grid source](../../mini_moonboard/panel_grid_v2.py) | `666e0e5c5daa70eb08ad9c49312a5b4478bc20e7d4d58cfb5062ad3c4be96fe8` |
| [Current +52 mm frame transform](../../mini_moonboard/no_shoes_frame.py) | `bba168c8fbf94e4acb165b78797f4919897559fad196023c4051092b8262c470` |
| Current load-datum driver snapshot | `f7d142fa9099abc8f92276a8bb038b5d17d29a71dbf03f0eacee9a78b9fa333f` |
| [Six-case load contract](hypotheses/evaluation-resume-2026-09-24/current-load-cases.json) | `9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a` (file); contract `19fe8aa9b370f2f82758610b8e0231bf0d3972036cf849ef2ffea16e5bf05776` |
| [Separate selected-candidate design basis](../current-design-basis.md) | `c2b18a1cec2546372118aedae1f001a4034239bac9ab3f9ea1aa239195f448fb` |
| Weight inventory producer snapshot | `53eb7e9caf303cc473cb87b9177585a7d14f151a8cb4d7e5ff36271ddafeeef7` |
| Final weight reconciliation producer snapshot | `1b4260a6938dc83a09be3c569b360089647765c71347df0849961aaa3d976b35` |
| [Local zero-load preflight README](hypotheses/evaluation-resume-2026-09-24/ordinary-native-preflight-attempt04/README.md) | `0f4a02e23b3b10e2b1e15ade285b4954b8ce18685e3a1f83c56444cfab2640c8` |
| [Local native mass audit](hypotheses/evaluation-resume-2026-09-24/ordinary-native-mass-audit-attempt02/audit.json) | `c0fbd0bee8a1dece951b180e69dc6272c06223bbce336b0f3196a64d111fdf9a` |
