# Right five-body boundary source and method trace

**Checked:** 2026-10-01. This traces the complete source interface boundary for
`base_header`, `base_post_outer_right`, `base_side_right`,
`knee_outer_right_spine`, and `knee_outer_right_inner_frame_block` in the
three frozen source cases. It is a method/source map, not a new mechanics
acceptance.

## Frozen source records

The source is the local ignored all-body freeze at
`docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/freeze.json`,
SHA-256 `d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73`.
The tracked [upper-frame review](../upper-frame-joint-review-2026-09-30/README.md)
provides its context. The freeze pins each case's model JSON, input deck,
native DAT, response JSON, all-body audit, and terminal record.

| Case | Model SHA-256 | Response SHA-256 | All-body audit SHA-256 | All-model selected / inactive source tangent rows |
| --- | --- | --- | --- | --- |
| A1 rear | `72d043e1a70702d8d464c21a039e897036e17c95e368ec776063584dac74f5fd` | `257b5b743369fcc2242537b7ccfe81f2efba0a195ef044624d7b67da6a09678c` | `247845921630a092c3f7a79d9ac11c92d732f021d2cb1dc5214e54b1a344deca` | 92 / 108 |
| A12 rear | `8a90452d8afa1f1722b3253b18d5aeec72c432033a22d5d0828082022cc1cda8` | `892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274` | `3da26086016c01f830e055bfa72c8a55370c9adc138b28d73127596924c410d5` | 50 / 150 |
| K12 rear | `8f1d9bce9b62b18b3694f81816ef5c4c7cbe5e94b4c459a640fce7a98db68dbd` | `42ffb135d47bd3bd28874e886682b4f07175ee060fb383b6e3c128e5102073c6` | `66c2b9aa397b16cd4c0b2420c5cf4588e15d12bfd3fbfd75b7df8f2b0d1d4bee` | 46 / 154 |

The response/model identity is
`compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. Each response has seven increments
through load factor 1.0. The case responses are conditional physical-response
audits, not design qualification or joint acceptance.

## Complete five-body boundary

For each case model, grouping `raw_source_carrier_law_inventory_rows` by
`name`, assigning that group's `physical_owner` as its owner descriptor, then
selecting rows whose owner `first` or `second` is one of the five bodies
produces 338 distinct interfaces from 392 native carrier components. Every
component grouped under a name has the same owner; the resulting names and
owners match the corresponding subset of `connection_ownership`. The split is
42 internal interfaces (both endpoints in the five bodies) and 296 crossing
interfaces (one endpoint inside). The inventory includes each member's other
physical connections, not just the right knee's six bolts.

| Owner role | Distinct interfaces | Raw carrier components |
| --- | ---: | ---: |
| `timber_or_panel_contact` | 232 | 232 |
| `physical_bolt_outer_seat_tension` | 28 | 28 |
| `candidate_bolt_lateral_plane` | 26 | 52 |
| `panel_screw_lateral_plane` | 20 | 40 |
| `non_qualifying_parametric_screw_withdrawal` | 20 | 20 |
| `retained_bolt_lateral_plane` | 4 | 8 |
| `floor_normal` | 4 | 4 |
| `assumed_no_slip_floor` | 4 | 8 |
| **Total** | **338** | **392** |

Thus the direct `physical_connection_forces` portion is 334 unique interface
actions with 384 source-component references. In each increment, one public
force row maps to each direct `source_connection_name`; lateral rows may list
two source components because the physical interface force already combines
the pair. Treat `source_inventory_rows` as provenance, not as separate forces.
The four floor-tangent interfaces are not taken from that direct map: they are
each reconstructed once from exactly two local DOF 2/3 channels, giving 338
grouped interface rows in total. Do not add raw carrier components or the
retained-bilateral audit records as additional actions.

The direct inventory includes the four separate `floor_normal` connections
`floor_base_post_outer_right_0` through `_3`, each from
`base_post_outer_right` to `floor` with scalar normal +Z. Keep these normal
actions separate from the four friction/tangent connections.

## Selected and released floor tangents

The four tangent owners are
`floor_base_post_outer_right_{0,1,2,3}_friction`, each from
`base_post_outer_right` to `floor`. Their points (mm) are respectively
(1187.45, −140.775, 0), (1206.5, −140.775, 0), (1187.45, −70.925, 0), and
(1206.5, −70.925, 0). The source owner basis is `(+Z, +Y, −X)`; DOF 2 and 3
carry the two tangent directions. Across all seven reported states:

- A1 and A12: tangent names 1 and 3 are selected; names 0 and 2 are released.
- K12: all four tangent names are released.

The response source binds the two active channels in
`exact_floor_tangent_reactions`, with `source_connection_name`,
`source_spring_group`, `source_inventory_row_index`, `source_row_original_index`,
`local_dof`, receiver names/points, `owner_tangent_basis_global_xyz`, and
global endpoint force/radius vectors. Released channels are carried in
`inactive_floor_tangent_zero_actions`; they retain source indices and DOF,
zero force/radius vectors, zero-containing carryover RF intervals, and explicit
`native_reference_or_tangent_equation_present=false` and
`native_tangent_spring_present=false`. These released rows omit the physical
basis, so the generic helper supplies the checked DOF basis from the owner
descriptor. The local source groups for tangent names 0, 1, 2, 3 are
`SPR1288/1289`, `SPR1291/1292`, `SPR1294/1295`, and `SPR1297/1298`, respectively
(DOF 2 then 3; original row indices 176–183 in order).

For a right-boundary map, preserve either the active pair or released pair for
each tangent name at every increment and combine the two channels once. Never
count a potential raw tangent carrier as a force, and never drop a released
name without its explicit zero-action provenance. The branch remains a
diagnostic selected-floor model; it does not qualify floor slip or anchorage.

## Reporting datums, applied loads, and independent audit

For each of the five bodies, the model's
`body_geometry[body].geometry_record.start` and `.end` define the descriptor
midpoint used only as a reporting datum. Their midpoint matches
`all_body_audit.increments[*].body_equilibrium[body].reference_xyz_mm` in all
three cases. These points are not physical cuts, supports, or mass centroids.

| Body | Descriptor-midpoint datum (global XYZ mm) | `physical_body_loads` nodes |
| --- | --- | ---: |
| `base_header` | (−1.5875, −105.85, 257.95) | 212 |
| `base_post_outer_right` | (1196.975, −105.85, 119.45) | 32 |
| `base_side_right` | (1171.575, 665.8107288065, 1228.604230899) | 212 |
| `knee_outer_right_spine` | (1235.075, −112.2, 277.85) | 32 |
| `knee_outer_right_inner_frame_block` | (1082.675, −109.025, 346.5) | 20 |

`member_balance()` uses the corresponding entries in `physical_body_loads`,
looks each source node up in `model.nodes`, scales the nodal force by that
increment's `load_factor`, then adds every incident interface action at its
recorded `first_point` / `second_point` (or common `point`). The grouped right
map therefore needs these five datums, the complete 338-owner interface list,
and no substituted centroids.

The independent pinned all-body audit has status
`PASS_PARENT_ALL_BODY_RESPONSE_SUMS`; its source model and response hashes
match the freeze. Each increment gives each body:
`reference_xyz_mm`, `force_residual_xyz_n`, `moment_residual_xyz_nmm`,
`force_rounding_radius_xyz_n`, `moment_rounding_radius_xyz_nmm`,
`force_interval_distance_from_zero_n`,
`moment_interval_distance_from_zero_nmm`,
`printed_resultants_passed`, and `interval_resultants_passed`. Its tolerance
vector is `[0.1 N, 2.0 N·mm]`. Across these five bodies and seven states per
case, the recorded maxima are:

| Case | Max absolute force residual (N) | Max absolute moment residual (N·mm) | Max force radius (N) | Max moment radius (N·mm) | Max interval distance (force / moment) |
| --- | ---: | ---: | ---: | ---: | --- |
| A1 rear | 0.000117076 | 0.159621 | 0.000623055 | 0.387594 | 0 / 0 |
| A12 rear | 0.000130995 | 0.080699 | 0.000612500 | 0.431418 | 0 / 0 |
| K12 rear | 0.000218000 | 0.295190 | 0.001692500 | 1.562181 | 0 / 0 |

All five-body audit rows have both pass flags true in all 21 case/state sets.
These are the independent values to compare against a reconstructed right
boundary's residuals and rounding intervals; the audit does not establish
joint strength or acceptance.

## Existing helper reuse and limits

The inspected helper is
[current-corner-native-demand-export `produce.py`](../mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt03/produce.py),
SHA-256 `0e6aa1b0ec50e3137d2f431f79365de899d109a5d5c61d37de344c9596681fe8`.
Its `response_interfaces()` and `member_balance()` routines are generic for
the source shape above. Build one right `interface_inventory` row per grouped
source name, with `owner=physical_owner`; then use the case response's
`physical_connection_forces`, special selected/released floor-tangent arrays,
body nodal loads, and a right-side descriptor-midpoint map. Direct actions
already aggregate their component references; tangent actions require the
two-channel combination described above.

The existing script entry point is left-corner-specific: its default contract
(`contract.json`, SHA-256
`f09d341924b2aa4e50ad8ecea43e4fcd1a36d838c99ab4e0fb85712e7dfd6c74`) and
interface map (`interface-map.json`, SHA-256
`c5ce97cbe1fffbb18dfaf1a544fa9a300991b06056b21b37ba3e08b8a1c6aec8`) are
pinned to the left five bodies and 338 left-owner rows. Its preflight requires
`BG001`, `BG003`, and `BG045` with 6 axes, 8 lateral planes, and 6 ties. Do not
use those owner rows or BG labels for this right boundary. Its response
validator also hard-codes 150 inactive tangent rows; the frozen case models
report 108 for A1, 150 for A12, and 154 for K12. Thus the two helper functions
can be reused with a separately source-pinned right contract/map, but the
existing complete producer/preflight cannot be run unchanged on all three
right cases.

No source response, map, or native output was edited, and no solver was run.
