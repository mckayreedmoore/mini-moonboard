# Floor-runner MVP completion ledger

## Status and claim boundary

Selected candidate: `compact-floor-flush-development`. The authenticated
[six-case aggregate](floor-runner-mvp-evidence.json) records six fresh no-slip
cases passing all 36 [frozen adopted criteria](floor-runner-mvp-criteria.md)
each. FR-0 through FR-7 are complete in the [MVP master
plan](floor-runner-mvp-master-plan.md). This ledger records the evidence
checkpoint and remaining FR-8 checks; it does not rerun a native solve or
claim a browser or physical inspection.

This is an engineer-unreviewed conditional DIY assessment of the exact
selected assembly under recorded loads, materials, partially threaded bolt
conditions and assumed no-slip floor support. Normal floor contact may open.
It is not a fabrication release, manufacturer qualification, inspected build,
verified floor, comprehensive climbing-load envelope or climber weight rating.
Unlisted ML24Z/SDS separation and force-parallel flange-couple actions remain
disclosed analytical limitations, not capacity passes. See the [criteria
ledger](floor-runner-mvp-criteria.md) and [angle-demand
ledger](floor-runner-mvp-angle-demands.json).

## Selected configuration and authority

The [build package](floor-flush-build-package.md) and [assembly
guide](floor-flush-assembly-guide.md) describe solid nominal 4×6 rear legs and
outer rims, compact single-2×6 header/posts, two outboard 2×6 floor runners,
whole kickers and a retained 1:12 rear-leg recess. Runner ends meet outer-post
and rear-leg faces, lower rim ends meet the post/header plane, and rear-leg
tops meet side rims. The prior 7 mm rim-end and 18 mm leg-top reserves are
absent. The model has 20 timber pieces, six plywood panels, twelve complete
outward-facing bolt stacks, 24 ML24Z angles, 144 specified SDS25112 screws
and 66 panel/kicker attachment axes. The upper bolt pair retains 56 mm pitch.
No raised knee or custom steel shoe belongs to this candidate.

The 66 panel/kicker axes use purchased Fas-n-Tite/Hillman 42605 #10 ×
2½-inch deck screws: 48 main-panel and nine per kicker. These are separate
from SDS screws in the angles. The viewer shows nominal length/body visuals;
product-specific resistance, exact head/thread geometry and installed
stiffness are not established. Native response retains its recorded proxy
stiffness. SPAX resistance and stiffness do not transfer. See the [purchase
record](current-panel-screw-purchase.md).

The 277 mm main-face datum includes a 127 mm pad allowance and 150 mm exposed
kicker. Two loose 48 × 72 × 5-inch pads sit side by side with a front-to-back
centre seam. The [owner-reported stack](current-crash-pad-construction.md) is
two ½-inch polyethylene sheets above and below a 3-inch, 44-ILD polyurethane
core in each pad. Pads are viewer-only placement objects, excluded from frame
mass and structural support; no impact certification is claimed.

| Authority | File or module |
| --- | --- |
| Selected candidate and assessment pointers | [`current-candidate.json`](../current-candidate.json) |
| Frame model | `mini_moonboard.compact_floor_flush_frame` |
| Viewer exporter and manifest | `scripts.floor_flush_exports`; [`manifest.json`](../site/hybrid/compact-floor-flush-development/manifest.json) |
| Construction exporter and manifest | `scripts.floor_flush_construction`; [`manifest.json`](floor-flush-construction/manifest.json) |
| Aggregate and angle demands | [`floor-runner-mvp-evidence.json`](floor-runner-mvp-evidence.json); [`floor-runner-mvp-angle-demands.json`](floor-runner-mvp-angle-demands.json) |
| Acceptance and scope | [`floor-runner-mvp-criteria.md`](floor-runner-mvp-criteria.md); [`floor-runner-mvp-master-plan.md`](floor-runner-mvp-master-plan.md) |

The aggregate's common geometry SHA-256 is
`e62f402f10403e205f279e60fe991ef8d0b9b13ff73efb981ff33090e389e747`.
The selected geometry pointer has a historical directory name in
`current-candidate.json`; that does not promote a finite-friction response.
Current force evidence comes only from the six `fea/results/floor-runner-mvp/`
archives.

## Six authenticated fresh cases

Every archived report is recorded as numerically accepted under the selected
250 lb inquiry and no-slip support formulation. Case identity, source hashes,
equilibrium, residuals, compression-only active-set convergence and complete
connection/contact inventories are prerequisites, not extra adopted passes.
The [case record](floor-runner-mvp-case-log.md), [aggregate](floor-runner-mvp-evidence.json)
and each archive manifest identify the saved inputs and results.

| Case | Contact cycles | Adopted checks | Bolt lateral ratio | Net member ratio | Listed ML24Z maximum | Archive |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| A12 left | 14 | 36/36 | 0.782215 | 0.682788 | 0.470956 | [`a12-left`](../fea/results/floor-runner-mvp/a12-left/manifest.json) |
| A12 rear | 15 | 36/36 | 0.763251 | 0.656642 | 0.516142 | [`a12-rear`](../fea/results/floor-runner-mvp/a12-rear/manifest.json) |
| A12 forward | 69 | 36/36 | 0.754919 | 0.537592 | 0.413041 | [`a12-forward`](../fea/results/floor-runner-mvp/a12-forward/manifest.json) |
| K12 right | 13 | 36/36 | 0.768869 | 0.677095 | 0.516174 | [`k12-right`](../fea/results/floor-runner-mvp/k12-right/manifest.json) |
| K12 rear | 10 | 36/36 | 0.754388 | 0.648895 | 0.569078 | [`k12-rear`](../fea/results/floor-runner-mvp/k12-rear/manifest.json) |
| A1 rear | 12 | 36/36 | 0.128982 | 0.211091 | 0.286071 | [`a1-rear`](../fea/results/floor-runner-mvp/a1-rear/manifest.json) |

A12-forward's first three searches did not converge the compression-only
active set and are diagnostic only. The fourth, 69-cycle one-contact-pivot
result supplies accepted force evidence; geometry, load, no-slip physical law
and final acceptance criteria were unchanged. See the [search
history](floor-runner-mvp-case-log.md#numerical-search-history).

## Frozen adopted criterion inventory

The exact machine-readable set is
`scripts.floor_flush_checks.FROZEN_ADOPTED_CRITERIA`. Each identifier below is
`true` in all six saved `flush-checks.json` assessments. These are recorded
calculation, numerical, load-path or nominal-CAD passes, not observations of
fabricated work. Ratio limits are at most 1.0; margins have zero lower bounds
where applicable. The [criteria ledger](floor-runner-mvp-criteria.md#complete-criterion-inventory)
defines each check.

| No. | Exact identifier | Saved result |
| ---: | --- | --- |
| 1 | `actual_angle_lateral_CD_1` | 6/6 true |
| 2 | `additional_group_reduction_sensitivity` | 6/6 true |
| 3 | `local_parallel` | 6/6 true |
| 4 | `supplemental_EC5_splitting` | 6/6 true |
| 5 | `sampled_net_member` | 6/6 true |
| 6 | `header_gross_full_length_stability` | 6/6 true |
| 7 | `base_bearing_average` | 6/6 true |
| 8 | `base_bearing_quarter_area_sensitivity` | 6/6 true |
| 9 | `base_end_notch_shear` | 6/6 true |
| 10 | `group_spacing` | 6/6 true |
| 11 | `catalog_washer_bounds` | 6/6 true |
| 12 | `directional_edges` | 6/6 true |
| 13 | `steel_direct` | 6/6 true |
| 14 | `washer_bearing` | 6/6 true |
| 15 | `washer_bending` | 6/6 true |
| 16 | `receiver_fit` | 6/6 true |
| 17 | `overlap_contact` | 6/6 true |
| 18 | `all_machining_represented` | 6/6 true |
| 19 | `sampled_member_stability` | 6/6 true |
| 20 | `all_bolt_centres_sampled` | 6/6 true |
| 21 | `angle_rated_force_components` | 6/6 true |
| 22 | `floor_rail_wood_bearing` | 6/6 true |
| 23 | `actual_kicker_cutouts` | 6/6 true |
| 24 | `taper_native_actual_taper` | 6/6 true |
| 25 | `taper_native_matches_cad_taper` | 6/6 true |
| 26 | `taper_actual_mesh_volume` | 6/6 true |
| 27 | `taper_taper_at_least_one_in_ten` | 6/6 true |
| 28 | `taper_intended_stock_and_runout` | 6/6 true |
| 29 | `taper_taper_bounds_sampled` | 6/6 true |
| 30 | `taper_actual_net_section_normal_resistance` | 6/6 true |
| 31 | `taper_sampled_rectangular_shear_torsion` | 6/6 true |
| 32 | `taper_taper_region_unbored_torsion_applicable` | 6/6 true |
| 33 | `component_layouts` | 6/6 true |
| 34 | `flush_face_normal_contact` | 6/6 true |
| 35 | `flush_face_wood_bearing` | 6/6 true |
| 36 | `flush_sampled_taper_top_clearance` | 6/6 true |

Rows 2 and 8 remain adopted despite `sensitivity` in their names.
`finite_floor_friction_law` applies only to historical or sensitivity runs
using that law; it is not a 37th selected-case check. The historical
`base_end_cut_geometry` projected-seat scalar and full-thread-root bolt
sensitivity are non-adopted and are not relabelled as passes.

## Governing values and saved-view distinction

Values below are rounded; the [aggregate](floor-runner-mvp-evidence.json)
retains full precision.

| Quantity | Value | Case and location |
| --- | ---: | --- |
| Adopted actual-angle bolt lateral ratio | 0.782215146 | A12 left; `rail_front_bolt_left_2` |
| Sampled net member | 0.682787902 | A12 left |
| Full-length header stability | 0.270498281 | K12 rear |
| Base end-notch shear | 0.299338738 | A1 rear |
| Listed ML24Z force interaction | 0.569078134 | K12 rear; `clip_single_top_right_2` |
| Flush-interface wood bearing | 0.137890278 | K12 right |
| Minimum directional edge/end reserve | 0.497141072 mm | A12 left |
| First-stage nominal lateral maximum | 0.834252733 | A12 rear; separate from adopted actual-angle maximum |
| Non-adopted full-root lateral sensitivity | 1.049814681 | A12 rear; exceeds 1.0 |

The nominal group-spacing margin is 1.4 mm. The finished front-pair fixture
rule separately preserves a minimum 0.9 mm 4D margin under its specified
tolerance stack. Neither residual margin is an extra drilling allowance.

All 24 listed ML24Z force interactions pass in each case. The [angle-demand
ledger](floor-runner-mvp-angle-demands.json) contains 144 station-case and
288 flange-case records. Maximum catalog-unlisted separation demand is
164.912492 N at `clip_timber_header_outer_left` in A12 rear. Maximum absolute
independent force-parallel flange couple is 12,476.541318 N·mm at
`clip_angle_base_right` in K12 rear. No capacity is assigned to either action.
The ledger audits demands, not resistance; native solves were not replayed
when it was made.

The archived `checks.json.metrics` and `flush-checks.json.stage_one.metrics`
are different saved washer-metric views in all six cases. For example, A12
left records washer bearing/bending as 0.252264177/0.287614943 in
[`checks.json`](../fea/results/floor-runner-mvp/a12-left/checks.json), versus
0.258121734/0.606447716 in the embedded stage-one view of
[`flush-checks.json`](../fea/results/floor-runner-mvp/a12-left/flush-checks.json).
Both saved views remain below 1.0. This ledger does not assume they are
identical, infer an undocumented cause, choose a new resistance or modify the
authenticated archive. Adopted Boolean status comes from
`flush-checks.json.criteria`; the aggregate's `first_stage_metrics` are the
separate `checks.json` snapshot.

## Recorded verification and remaining FR-8 work

The [master plan](floor-runner-mvp-master-plan.md) records FR-1/FR-2 selection
and criteria, FR-3 nominal CAD/shop checks, FR-4–FR-6 authenticated cases and
demands, and FR-7 rebuilt viewer/construction artifacts. The prior checkpoint
recorded **805 tests passed, 16 historical tests deselected**, Ruff and
CAD/export rebuild passed, and independent review findings addressed. That
review is not professional engineering sign-off. This ledger's creation did
not itself rerun those commands.

Selected-candidate browser smoke loaded all 725 CAD meshes at
`?model=compact-floor-flush-development&view=rear`, with no page errors or
failed mesh requests observed. Inventory inspection found twelve bolt-stack
connection names, both floor rails and two separate pads. Pad toggle hid the
pads once; restoration and representative hardware selection were not
completed. Current document links, including this ledger, appeared in the
viewer. This is a partial browser check, not FR-8 browser completion.
Historical browser records for other candidates do not transfer. Post-edit
focused tests, the default non-historical suite, Ruff, selected export
comparison, viewer module syntax and `git diff --check` passed as recorded
below. No native solve was rerun.
Do not change archived JSON merely to remove case-local `OPEN` labels: each
assessment covers one case, while the authenticated aggregate establishes the
complete six-case set.

## Receiving and installation observations

The repository has not measured actual wood, cuts, finished holes, delivered
hardware, pads or floor. The [criteria ledger](floor-runner-mvp-criteria.md)
and [assembly guide](floor-flush-assembly-guide.md) control these owner/shop
observations; nominal CAD passes do not fill them in.

| Item | Control | Status |
| --- | --- | --- |
| Timber and 1:12 recess | Match material/section basis; require sound, check-free stock, smooth transition and no overcut, split or damaged bearing surface. | Not inspected |
| Finished front pairs | Registered fixture; pitch 39.0–40.0 mm, midpoint offset ≤0.5 mm, each perpendicular offset ≤0.5 mm. Never elongate holes. | Not measured |
| All bolt receivers | Match member-local datums, edge/end distances, mating registration and 24 complete washer seats; occupied CAD diameters are not drill-bit instructions. | Not inspected |
| Delivered bolt stacks | Verify actual grip, full body to first thread transition, runout, usable nut threads and tip projection; fully threaded substitutes are not qualified. | Not measured |
| Washers | Check delivered sizes, concentricity and complete flat support on sound timber; reject rocking or unsupported seats. | Not inspected |
| ML24Z/SDS connections | Retain all 24 angles and 144 specified SDS25112 screws at documented locations and physical load paths; Hillman screws are not SDS replacements. | Not inspected |
| Hillman panel/kicker screws | Retain all 66 axes; verify actual length, receiver containment and no tip protrusion. Nominal penetration is 45.24375 mm, leaving 94.45625 mm rear-tip reserve in the modeled direction. | Not inspected |
| Interfaces, services and pads | Preserve intended bearing faces, gaps, clearances and wiring access; pads do not support timber. | Not inspected |

The [build package](floor-flush-build-package.md) records minimum full-body
length to first transition as 158.928 mm upper, 69.317 mm front and 78.842 mm
rear; extra thread/runout budgets as 1.600, 5.359 and 7.518 mm; and
shortest-stack tip budgets beyond the nut as 2.743, 10.033 and 9.017 mm.
These are conditional budgets, not guaranteed delivered dimensions or spare
timber-oversize allowances. No floor-friction measurement or floor test is
added; actual no-slip support remains an unverified assumption.

The nominal rear-leg cut-face stress inference, finite section/contact
sampling, contact penalty idealization and historical approximately −4.970 mm
projected-seat result remain disclosed limitations or non-adopted diagnostics
under the [criteria ledger](floor-runner-mvp-criteria.md). An adopted failure,
missing physical load path, failed measured fit or changed geometry, loads or
materials requires reassessment. Documentation alone cannot change a case
result.

## FR-8 closure checklist

- [x] Record six authenticated cases and all 36 adopted identifiers.
- [x] Separate passes, non-adopted sensitivities, analytical limits and shop
  observations.
- [x] Preserve checkpoint verification and archive-view discrepancies accurately.
- [ ] Complete selected-candidate browser interaction: pad restoration,
  representative hardware selection and remaining visual checks. Partial
  725-mesh load, error check, first pad toggle and document-link check recorded.
- [x] Post-edit verification: focused aggregate tests 2 passed; default suite
  792 passed, 16 historical deselected; Ruff passed; selected export comparison
  passed; viewer module syntax and `git diff --check` passed. The 13-test
  difference from the earlier 805-pass checkpoint is removal of the obsolete
  publication-window test after its hook was removed.

FR-8 documentation/software closure would not certify installed work, supply
unlisted ML24Z capacities or establish fabrication release or a climber rating.
