# Floor-runner MVP criteria ledger

This ledger freezes the acceptance rules for the six fresh
`compact-floor-flush-development` cases required by the
[master plan](floor-runner-mvp-master-plan.md). It does not transfer any result
from the historical finite-friction A12-left case or from another candidate.

## Case prerequisites

Each case must use the exact selected geometry and source-authenticated no-slip
producer, converge its compression-only contact active set, meet the native
equilibrium and residual limits, and retain every required physical connection,
floor cell and member-contact record. Failure of identity, provenance,
convergence or inventory stops assessment rather than producing a component
pass.

## Adopted assessment criteria

`scripts.floor_flush_checks.FROZEN_ADOPTED_CRITERIA` is the machine-readable
authority. Every fresh case must contain and pass that exact required set:

- bolt and joint-group lateral resistance, local parallel bearing, supplemental
  splitting, spacing, directional edge/end distance, receiver fit, washer and
  steel checks;
- sampled gross/net member resistance and stability, represented machining,
  bolt-section sampling, header stability, base bearing and end-notch shear;
- floor-runner bearing, all six runner/post/leg contact interfaces, compression-
  only contact behavior and sampled taper-top clearance;
- native/CAD taper identity, mesh volume, slope/runout, retained net section,
  shear/torsion and unbored-region applicability checks; and
- all 24 ML24Z listed force-component interactions and complete component
  layouts.

The finite-Coulomb-law criterion is conditional and applies only to historical
or sensitivity runs that include that law. It is absent from the selected
no-slip cases. Full-root bolt results remain non-adopted hardware sensitivities;
the specified partial-thread/body condition and delivered-hardware inspection
remain mandatory.

## Complete criterion inventory

No supplied value may disappear silently. `floor_flush_checks` rejects a case
when any required identifier below is absent or when an unexpected identifier
appears. Every required Boolean must be true; every ratio criterion uses its
existing limit of 1.0 and every margin criterion uses its existing zero lower
bound.

| Identifier | Classification | Check or evidence | Acceptance/disposition | Stage |
| --- | --- | --- | --- | --- |
| `actual_angle_lateral_CD_1` | Design calculation | Nominal-diameter bolt lateral comparison | Ratio ≤ 1.0 | Fresh case |
| `additional_group_reduction_sensitivity` | Design calculation | Existing additional bolt-group reduction comparison | Ratio ≤ 1.0; remains adopted despite its historical name | Fresh case |
| `local_parallel` | Design calculation | Local wood parallel-bearing comparison | Ratio ≤ 1.0 | Fresh case |
| `supplemental_EC5_splitting` | Design calculation | Existing supplemental splitting comparison | Ratio ≤ 1.0 | Fresh case |
| `sampled_net_member` | Design calculation | Sampled conservative net-section envelope | Ratio ≤ 1.0 | Fresh case |
| `header_gross_full_length_stability` | Design calculation | Full-length header gross-section stability | Ratio ≤ 1.0 | Fresh case |
| `base_bearing_average` | Design calculation | Average header/base bearing | Ratio ≤ 1.0 | Fresh case |
| `base_bearing_quarter_area_sensitivity` | Design calculation | Existing quarter-area corner bearing comparison | Ratio ≤ 1.0; remains adopted despite its historical name | Fresh case |
| `base_end_notch_shear` | Design calculation | Conservative retained-end shear comparison | Ratio ≤ 1.0 | Fresh case |
| `group_spacing` | CAD/design check | Minimum component spacing margin | Margin ≥ 0 | FR-3 and fresh case |
| `catalog_washer_bounds` | CAD/design check | Complete catalog washer inventory | All twelve bolts represented | FR-3 and fresh case |
| `directional_edges` | CAD/design check | Force-directed edge/end-distance margins | Margin ≥ 0 | Fresh case |
| `steel_direct` | Design calculation | Direct steel resistance | Ratio ≤ 1.0 | Fresh case |
| `washer_bearing` | Design calculation | Timber washer-bearing resistance | Ratio ≤ 1.0 | Fresh case |
| `washer_bending` | Design calculation | Washer bending resistance | Ratio ≤ 1.0 | Fresh case |
| `receiver_fit` | CAD check | Actual receiver, bore and washer-seat geometry | Every modeled receiver passes | FR-3 and fresh case |
| `overlap_contact` | Design check | Applicable member-overlap contact inventory | Boolean true | Fresh case |
| `all_machining_represented` | CAD check | Openings and cuts represented in member sections | Boolean true | FR-3 and fresh case |
| `sampled_member_stability` | Design calculation | All sampled member sections avoid checked failure | Boolean true | Fresh case |
| `all_bolt_centres_sampled` | Design check | Every bolt bore covered by section samples | Boolean true | Fresh case |
| `angle_rated_force_components` | Design calculation | Listed ML24Z force-component interaction at all 24 stations | Maximum ratio ≤ 1.0 | Every fresh case |
| `floor_rail_wood_bearing` | Design calculation | Explicit floor-cell timber bearing | Ratio ≤ 1.0 | Fresh case |
| `actual_kicker_cutouts` | CAD/native identity | Whole-kicker inventory for this candidate | Exact expected inventory | FR-3 and fresh case |
| `taper_native_actual_taper` | CAD/native identity | Native model contains actual recess | Boolean true | Fresh case |
| `taper_native_matches_cad_taper` | CAD/native identity | Native recess equals selected CAD | Boolean true | Fresh case |
| `taper_actual_mesh_volume` | Numerical/CAD check | Meshed recess volume matches selected geometry | Boolean true | Fresh case |
| `taper_taper_at_least_one_in_ten` | Geometry check | Existing slope-screen comparison | Boolean true | FR-3 and fresh case |
| `taper_intended_stock_and_runout` | Geometry check | 4×6 stock and 1:12 runout identity | Boolean true | FR-3 and fresh case |
| `taper_taper_bounds_sampled` | Numerical check | Recess-region section coverage | Boolean true | Fresh case |
| `taper_actual_net_section_normal_resistance` | Design calculation | Actual retained net-section normal resistance | Ratio ≤ 1.0 | Fresh case |
| `taper_sampled_rectangular_shear_torsion` | Design calculation | Sampled retained rectangular shear/torsion | Ratio ≤ 1.0 | Fresh case |
| `taper_taper_region_unbored_torsion_applicable` | Design/CAD check | Torsion method restricted to unbored taper region | Boolean true | Fresh case |
| `component_layouts` | CAD/design check | Every local component layout passes its existing spacing screen | Boolean true | FR-3 and fresh case |
| `flush_face_normal_contact` | Load-path check | Six exact rim/leg, post/runner and leg/runner interfaces; saved compression-only response | Every interface present and valid | Every fresh case |
| `flush_face_wood_bearing` | Design calculation | Bearing at those six exact interfaces | Maximum ratio ≤ 1.0 | Every fresh case |
| `flush_sampled_taper_top_clearance` | Numerical/CAD check | Exact 18-monitor taper-top clearance inventory | Every saved deformed gap positive | Every fresh case |
| `finite_floor_friction_law` | Conditional diagnostic | Distributed Coulomb-law reconstruction | Required only when that nonselected law is present | Historical/sensitivity only |

Native identity, source hashes, equilibrium, residuals, active-set convergence
and complete connection/contact inventories are case prerequisites, not optional
rows that can be omitted from this table and counted as passes.

## Retired release scalar

`base_end_cut_geometry` is preserved under `non_adopted_sensitivities`, including
its recorded value and the historical approximately −4.970 mm margin. It is not
an adopted pass/fail criterion because the quarter-depth projected-seat analogy
has no established mapping to the supported terminal bevel. Removing that one
scalar does not remove the adopted actual retained-section, base-bearing,
end-notch shear, member stability, interface-contact or gross/net checks listed
above.

## Disclosed limits

ML24Z listed interactions must remain at or below 1.0. Separation and an
independent force-parallel flange couple are not listed catalog capacities and
must be reported without calling them manufacturer-qualified. The nominal
rear-leg cut-face transverse stress inference remains a local-fracture method
limitation paired with stock and cut inspection controls; it is not converted
into a numerical pass. The owner's no-slip support condition is an analytical
assumption, not measured floor friction or an anchor.

The owner-selected [master plan](floor-runner-mvp-master-plan.md) is the
authority for treating unlisted ML24Z separation/couple actions as disclosed
DIY limitations instead of an automatic redesign trigger. This is a scope
disposition, not a resistance value, risk waiver or manufacturer qualification.
Any listed interaction above 1.0, changed fastening schedule or missing physical
load path still stops the work.

`floor_flush_angle_ledger.py` authenticates and reconstructs demands only. Its
successful execution is not resistance acceptance. Each fresh assessment must
separately pass `angle_rated_force_components` at all 24 stations, while the
six-case aggregate records the unlisted separation and couple demands.

The exact six-interface inventory and compression-only response provide the
finite runner/leg load-path obligation. Remaining point-sampling and penalty-
stiffness limits are disclosed model limits, not an open-ended refinement
campaign, provided every adopted contact, bearing, clearance and numerical
criterion passes. A missing interface or force path remains a stop condition.

Shop checks are separate from calculation passes. FR-3 must establish paired-
hole pitch/registration, maximum washer seating and all 66 Hillman axes. At
receiving and installation, record delivered full-body/thread transition, nut
engagement, washer dimensions/seating, finished hole positions, sound recess
stock and cut condition. Reject or reassess deviations; do not credit SPAX
capacity or stiffness to the Hillman screws.

| Identifier | Classification | Check or evidence | Acceptance/disposition | Stage |
| --- | --- | --- | --- | --- |
| `selected_cad_and_datums` | CAD check | `scripts.floor_flush_shop_checks`, all 12 bolts, 24 receiver seats, 24 left/right member datums and six contact pairs | Exact inventory and maximum catalog washer outside diameters supported on nominal finished CAD; this does not certify a delivered washer/stock | FR-3 |
| `front_pair_fixture` | Installation observation | Registered paired-hole fixture; measured finished pitch, midpoint and perpendicular offset | Pitch 39.0–40.0 mm, midpoint offset ≤0.5 mm, each perpendicular offset ≤0.5 mm; minimum 4D margin 0.9 mm and maximum axis displacement 0.9014 mm under this stack. Reject or reassess deviations; never elongate | FR-3 rule; installation |
| `delivered_bolt_stacks` | Delivered-material check | Measure full body through first thread transition, actual wood grip, usable nut threads, washer dimensions, seating and tip projection | Meet the existing upper/front/rear budgets and full washer support; reject incompatible delivered pieces | Receiving and installation |
| `hillman_66_axes` | CAD and installation check | `scripts.floor_flush_shop_checks` and delivered 63.5 mm screw inspection at each panel/kicker axis | All 66 enter assigned raw receivers without tip protrusion; current minimum rear-tip reserve 94.45625 mm. Verify actual clearance and no SPAX strength/stiffness transfer | FR-3; installation |
| `recess_stock_and_cut` | Installation observation | Marked 1:12 cut and finished stock inspection | Sound/check-free timber, smooth continuous transition, no overcut, splits or damage; reject/reassess defects | Receiving and installation |
| `ml24z_unlisted_actions` | Disclosed analytical limitation | Six-case force ledger at every angle station | Report separation and independent force-parallel couple without invented resistance; owner-selected MVP scope does not make this a listed capacity pass | FR-6 and final package |
| `missing_load_path_or_failed_adopted_criterion` | Stop-work/reassessment trigger | Exact geometry, native case and shop review | Stop on absent required path, failed accepted ratio/margin, failed measured fit or changed load/geometry | FR-3–FR-8; installation |

`scripts.floor_flush_shop_checks` reproduces nominal fit and a conservative
finished-fixture displacement bound; it does not measure a delivered bolt or
inspect installed holes. Those observations remain explicit owner/shop records.

Changing this ledger, geometry, load inputs, material basis or physical load
path requires an explicit revision and affected fresh cases. Documentation or
viewer changes alone cannot change a case result.
