# Right outer-knee source trace

**Checked:** 2026-10-01. This note traces source bindings for the right outer
knee assembly only. It does not compute a receiver resultant, capacity, or
joint conclusion.

## Frozen cases and boundary

The source is the local, ignored all-body three-case
`docs/wood-joints-mvp/hypotheses/upper-frame-joint-review-2026-09-30/freeze.json`,
SHA-256 `d4ba1c78eb358d25e32819201e9c59e05d425a06d9e4e5cca3dc09d7139ffd73`.
It pins the model, deck, native DAT, case response, all-body audit, and terminal
record for each case. The tracked [upper-frame review](../upper-frame-joint-review-2026-09-30/README.md)
summarizes that evidence. The shared model identity is candidate
`compact-floor-flush-wood-joints-development`, geometry revision
`led-clearance-2x6-runner-seated-blocks-v1`.

| Case | Response SHA-256 | Native DAT SHA-256 | All-body audit SHA-256 | Response status |
| --- | --- | --- | --- | --- |
| A1 rear | `257b5b743369fcc2242537b7ccfe81f2efba0a195ef044624d7b67da6a09678c` | `b5b9997e299779f76697a84ff739f89d7757c97394144839f541944e98e929e2` | `247845921630a092c3f7a79d9ac11c92d732f021d2cb1dc5214e54b1a344deca` | `PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY` |
| A12 rear | `892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274` | `1f98a6737908286b86771ec4184e8ab08a4b3c1ce95b48a2d42e8284353ffd54` | `3da26086016c01f830e055bfa72c8a55370c9adc138b28d73127596924c410d5` | `PASS_SELECTED_FLOOR_PHYSICAL_RESPONSE_AUDIT_ONLY` |
| K12 rear | `42ffb135d47bd3bd28874e886682b4f07175ee060fb383b6e3c128e5102073c6` | `01dc25ae3636d6c36e1d6daf6c7a648a23938cc3615f9bde45bdc3fc77b05cf6` | `66c2b9aa397b16cd4c0b2420c5cf4588e15d12bfd3fbfd75b7df8f2b0d1d4bee` | `PASS_K12_REAR_SPR489_DIRECT_MASTER_RESPONSE_AUDIT_ONLY` |

Each frozen response record contains seven increments through load factor 1.0 and
records the response-audit gates. These are three conditional case histories;
they do not establish a six-case demand envelope or joint acceptance. The
response records keep `joint_demand_accepted=false` and
`qualified_for_design=false`. K12's SPR489 direct-master recovery remains
case-specific.

## Six axial ties and eight lateral planes

The selected `connection_attachment_rows` are exactly these six named
candidate-bolt axes. Axial-tie first and second endpoint points come from the
corresponding `physical_connection_forces` rows. Coordinates are global XYZ
in mm. Lateral-plane records use a common force point and identify the two
receiver bodies.

| Axis | Outer-seat tie source | First body and point → second body and point | Installation direction |
| --- | --- | --- | --- |
| `knee_outer_right_inner_header_1` | `SPR1775` | `base_header` (1082.675, -62.350, 238.900) → `knee_outer_right_inner_frame_block` (1082.675, -62.350, 416.000) | +Z |
| `knee_outer_right_inner_header_2` | `SPR1776` | `knee_outer_right_inner_frame_block` (1082.675, -155.700, 416.000) → `base_header` (1082.675, -155.700, 238.900) | −Z |
| `knee_outer_right_post_1` | `SPR1777` | `knee_outer_right_spine` (1254.125, -137.600, 171.450) → `base_post_outer_right` (1177.925, -137.600, 171.450) | −X |
| `knee_outer_right_post_2` | `SPR1778` | `knee_outer_right_spine` (1254.125, -137.600, 213.500) → `base_post_outer_right` (1177.925, -137.600, 213.500) | approximately −X |
| `knee_outer_right_side_1` | `SPR1779` | `knee_outer_right_spine` (1254.125, -106.228087, 331.315553) → `knee_outer_right_inner_frame_block` (1038.225, -106.228087, 331.315553) | −X |
| `knee_outer_right_side_2` | `SPR1780` | `knee_outer_right_spine` (1254.125, -77.302644, 365.787553) → `knee_outer_right_inner_frame_block` (1038.225, -77.302644, 365.787553) | approximately −X |

The two side axes are modeled as continuous axes across three ordered wood
receivers: `knee_outer_right_spine` → `base_side_right` →
`knee_outer_right_inner_frame_block`. Their axial tie joins the first and
last receiver; each interface has its own lateral plane. This is the model's
receiver order, not an independent statement about a delivered bolt.

| Plane | Source components (SPRING2 DOF) | First body → second body | Point (global XYZ mm) | Axis basis row |
| --- | --- | --- | --- | --- |
| 41 | `SPR1403` (2), `SPR1404` (3) | `base_header` → `knee_outer_right_inner_frame_block` | (1082.675, -62.350, 277.000) | +Z |
| 42 | `SPR1405` (2), `SPR1406` (3) | `knee_outer_right_inner_frame_block` → `base_header` | (1082.675, -155.700, 277.000) | −Z |
| 43 | `SPR1407` (2), `SPR1408` (3) | `knee_outer_right_spine` → `base_post_outer_right` | (1216.025, -137.600, 171.450) | −X |
| 44 | `SPR1409` (2), `SPR1410` (3) | `knee_outer_right_spine` → `base_post_outer_right` | (1216.025, -137.600, 213.500) | approximately −X |
| 45 | `SPR1411` (2), `SPR1412` (3) | `knee_outer_right_spine` → `base_side_right` | (1216.025, -106.228087, 331.315553) | −X |
| 46 | `SPR1413` (2), `SPR1414` (3) | `base_side_right` → `knee_outer_right_inner_frame_block` | (1127.125, -106.228087, 331.315553) | −X |
| 47 | `SPR1415` (2), `SPR1416` (3) | `knee_outer_right_spine` → `base_side_right` | (1216.025, -77.302644, 365.787553) | approximately −X |
| 48 | `SPR1417` (2), `SPR1418` (3) | `base_side_right` → `knee_outer_right_inner_frame_block` | (1127.125, -77.302644, 365.787553) | approximately −X |

Each source `force_basis` stores rows `[axis, transverse-2, transverse-3]`.
The recorded signs are: plane 41, `(+Z, +Y, −X)`; plane 42,
`(−Z, −Y, −X)`; planes 43, 45 and 46, `(−X, −Z, −Y)`; planes 44, 47 and
48, approximately `(−X, −Z, −Y)`. The latter rows contain only tiny rotated
components (about `2.61e−16` or `3.65e−16`). The two retained local SPRING2
components occupy transverse rows 2 and 3. Preserve those basis signs when
interpreting local component signs; the global force record already reports
the force on its named first receiver.

The pinned model's `source_carrier_inventory_rows` bind every lateral pair
to law `bilateral`, the named candidate-bolt lateral plane, its two endpoint
nodes, and DOFs 2 and 3. `physical_connection_forces` gives the global
`force_on_first_xyz_n` and `force_on_second_xyz_n` at the plane point, plus
`source_row_ids` and the two source-inventory bindings. The sign is already
on the named first body; the second-body action is its reported
action-reaction counterpart with native RF rounding radii retained. The separate
retained-bilateral audit has one record per SPRING2 source component, keyed
by `source_group` / `source_row_id`, with endpoint RF and rounding intervals,
local first-end force, relative displacement, `bilateral_kdu_N`, RF-minus-Kdu,
and interval-intersection check. It is a source/recovery cross-check, not a
second physical force to add.

For each outer-seat row the source inventory binds exactly one `SPRINGA`
component to law `tension_only` and role `physical_bolt_outer_seat_tension`.
The response exposes `source_row_ids`, receiver names and points,
`scalar_normal`, global equal-and-opposite endpoint actions, and
`axial_along_installation_direction_n`. Preserve the named first-body sign and
this axial scalar; do not substitute an unsigned vector norm for the signed
receiver action.

## Scope protection

The source inventory contains 92 new candidate bolt axes, 12 retained
leg/runner axes and 66 panel-screw axes per case. This trace selects only the
six `knee_outer_right_*` axes above and their planes 41–48 and six outer-seat
ties. The top upper 32 axes are excluded. No BG identifier is assigned here:
none is present in these frozen source bindings. The existing
left-corner complete register (local
`current-corner-complete-resistance-register-attempt01/`, pending its owner's
publication)
and [native-demand export](../mvp-acceleration-2026-09-28/current-corner-native-demand-export-attempt03/README.md)
were inspected only as method context; their axis owners, forces, BG
identifiers and any acceptance do not transfer to this right assembly.
Read-only hash checks confirmed the per-case files against the freeze pins.
This trace uses the response JSON source bindings; it does not parse DAT bytes
or invoke a native solver.
