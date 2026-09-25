# Representative WJ-04 directional bolt end/edge audit

Status: read-only geometry and conditional detailing screen, 2026-09-24. This
audit covers the eight provisional ordinary bolts in the lower and upper
right-inner full-stock G7 WJ-04 cleats. It establishes no signed demand,
resistance, case pass/failure, fabrication tolerance, or release. It is a
bounded input for the parent readiness decision before native mechanics.

## Current geometry binding

The source is the archived [WJ-16 full-stock mechanics input report](hypotheses/wj16-full-stock-mechanics-inputs/mechanics-inputs.json)
and its [execution binding](hypotheses/wj16-full-stock-mechanics-inputs/execution.json).
For each `physical_bolts[]` record, the relevant contract is:

- `physical_bolt_id`, `station_id`, `interface_id`,
  `world_axis_direction_head_to_nut`, and `receivers_head_to_nut`;
- `member_geometric_boundaries[]`, especially `member_id`,
  `grain_axis_global_xyz`, `bolt_midpoint_boundary_distances_mm`, and
  `grain_and_cross_grain_geometric_distances.grain_end_distances_mm`;
- `grain_and_cross_grain_geometric_distances.cross_grain_boundary_distances_mm`,
  treated only as an axis inventory: the WJ16 producer currently includes
  both member axes other than grain, including the bolt-axis dimension. Select
  only the member-frame axis perpendicular to both grain and bolt axes;
- `signed_end_edge_and_bolt_load_classification`, which remains unresolved
  pending fresh signed bolt actions.

These are center-to-projected-boundary distances, with the two end values in
low/high member-coordinate order. The WJ16 producer explicitly limits them to
the finished-solid projected bounds; it excludes nearer local cut transitions
or neighboring features from this classification. They describe analysis
geometry, not received stock or drilled holes.

There is a field-label limitation in this contract: `scripts/wood_joint_wj04_full_stock_mechanics_contract.py::_member_boundary_distances`
constructs `cross_grain_boundary_distances_mm` from every axis other than
grain, without excluding the bolt axis. The named per-axis values in
`bolt_midpoint_boundary_distances_mm` are usable when joined to
`world_axis_direction_head_to_nut`; the summary key alone is not a unique
cross-grain edge record. For example, the rail host's `T` distances of
19.05/19.05 mm lie along its bolt axis and are not lateral wood edges. The
directional classifier in [`wood_joint_directional_geometry.py`](../../mini_moonboard/wood_joint_directional_geometry.py)
does identify the unique cross-grain axis after excluding both grain and bolt
axes.

This geometry is retained in current WJ-24. WJ-16 and current [WJ-24 composition](hypotheses/wj24-integrated-static/composition.json)
name the same `family_trial_ids.wj04_g7` trial,
`upper_g7_clearance_n86p9_reversed_rail_hypothesis`. Their 39
`family_source_fingerprints_sha256.right_rail` path/value pairs match. The two
WJ-04 `parts.finished_candidate_parts` WJ-16 shape hashes match current
`candidate_parts[...].finished_shape.shape_sha256` in WJ-24:

| Member | Finished shape SHA-256 | WJ-16 / WJ-24 bounds (global XYZ mm) |
|---|---|---|
| `wj04_lower_full_stock_cleat` | `996fa8e6acf3272cc81fe88b010c45aa5774faf12c4bec0acf64f3ca82f7f7f1` | `[89.05,177.95] × [602.489602,751.328941] × [1184.866683,1329.909711]` |
| `wj04_upper_g7_crosscut_full_stock_cleat` | `05dd3e2030c628d5a88c400fadb3d1b9f41dbe34d4468ffc624cfeab20cbaaee` | `[89.05,177.95] × [695.083157,818.796238] × [1316.298819,1440.258413]` |

All eight `candidate_axes["wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/<stack>"].bore_shape.shape_sha256`
values also match the WJ-16 `candidate_axes[...].bore.shape_sha256` values.
The WJ-24 [parent audit](hypotheses/wj24-integrated-static/parent-audit.json)
verifies its 68 source inputs, while explicitly recording no native solve and
no release. The WJ-16 mechanics report remains input-only and does not become
current demand or structural evidence by this binding.

## Member-specific distances

The provisional candidate is a nominal 1/4-inch bolt, so the NDS screen uses
`D = 6.35 mm`. The WJ-16 hardware record identifies a 1/4-20 candidate and a
published body-diameter range of 6.223–6.35 mm; no delivered bolt is verified.
The cleat candidate is Douglas fir, but actual wood species/grade and condition
remain unverified.

In the table, end pairs are `−grain / +grain`, and edge pairs are `−cross / +cross`.
The selected cross axis is the one perpendicular to both bolt axis and grain:
rail host `N`, rail cleat `X`, principal host `N`, principal cleat `T`. This
avoids treating a distance measured along the bolt axis as an edge distance;
the table was derived from the per-axis bounds after this filter, not by
copying the over-inclusive summary object.
The bound WJ-04 frame in [`wood_joint_wj04_config.py`](../../mini_moonboard/wood_joint_wj04_config.py) is
`X=(1,0,0)`, `T=(0,0.642787609687,0.766044443119)`, and
`N=(0,-0.766044443119,0.642787609687)` in global XYZ; rail bolts align with
the `T` axis line, principal bolts with the `X` axis line, and each grain
vector is the named positive axis shown below. The head-to-nut sign remains
per bolt in `world_axis_direction_head_to_nut`.

| Physical bolt | Wood member | Grain / bolt-axis line | End distances (mm) | Cross-grain edge distances (mm) |
|---|---|---|---:|---:|
| `lower_rail_1` | `base_rail_service_lower_right` | `X / T` | `45.45 / 992.625` | `63.35 / 76.35` |
| `lower_rail_1` | `wj04_lower_full_stock_cleat` | `N / T` | `43.35 / 76.35` | `45.45 / 43.45` |
| `lower_rail_2` | `base_rail_service_lower_right` | `X / T` | `45.45 / 992.625` | `96.35 / 43.35` |
| `lower_rail_2` | `wj04_lower_full_stock_cleat` | `N / T` | `76.35 / 43.35` | `45.45 / 43.45` |
| `lower_principal_1` | `base_principal_center_right` | `T / X` | `1287.11712 / 1219.05` | `79.85 / 59.85` |
| `lower_principal_1` | `wj04_lower_full_stock_cleat` | `N / X` | `59.85 / 59.85` | `28.0 / 60.9` |
| `lower_principal_2` | `base_principal_center_right` | `T / X` | `1320.11712 / 1186.05` | `79.85 / 59.85` |
| `lower_principal_2` | `wj04_lower_full_stock_cleat` | `N / X` | `59.85 / 59.85` | `61.0 / 27.9` |
| `upper_rail_1` | `base_rail_service_upper_right` | `X / T` | `45.45 / 992.625` | `79.75 / 59.95` |
| `upper_rail_1` | `wj04_upper_g7_crosscut_full_stock_cleat` | `N / T` | `26.95 / 59.95` | `45.45 / 43.45` |
| `upper_rail_2` | `base_rail_service_upper_right` | `X / T` | `45.45 / 992.625` | `112.75 / 26.95` |
| `upper_rail_2` | `wj04_upper_g7_crosscut_full_stock_cleat` | `N / T` | `59.95 / 26.95` | `45.45 / 43.45` |
| `upper_principal_1` | `base_principal_center_right` | `T / X` | `1431.16712 / 1075.0` | `96.25 / 43.45` |
| `upper_principal_1` | `wj04_upper_g7_crosscut_full_stock_cleat` | `N / X` | `43.45 / 43.45` | `28.0 / 60.9` |
| `upper_principal_2` | `base_principal_center_right` | `T / X` | `1464.16712 / 1042.0` | `96.25 / 43.45` |
| `upper_principal_2` | `wj04_upper_g7_crosscut_full_stock_cleat` | `N / X` | `43.45 / 43.45` | `61.0 / 27.9` |

## Conditional NDS screens

The method basis is [ANSI/AWC NDS-2024](https://awc.org/resources/2024-nds/),
Chapter 12 ([AWC Chapter 12 source](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)).
The repository's [source correction record](bolt-dimension-source-correction.md)
pins the inspected Chapter 12 PDF at SHA-256
`5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a`.
NDS §§12.1.2.1–.3 define center-to-edge/end/spacing geometry; §12.1.3.4
directs bolt placement to Tables 12.5.1A–D. For nominal `D = 6.35 mm`,
`4D = 25.40`, `7D = 44.45`, `3.5D = 22.225`, and `1.5D = 9.525 mm`.

For `D ≥ 1/4 in`, Table 12.5.1A and §12.5.1.2 apply a geometry factor
`CΔ` when an end distance is below the `CΔ=1.0` minimum but at least the
`CΔ=0.5` minimum. Softwood parallel-grain tension uses 7D for `CΔ=1.0` and
3.5D for `CΔ=0.5`; compression uses 4D and 2D. Perpendicular-to-grain loading
uses 4D and 2D. Where applicable, the softwood tension factor is actual end
distance divided by 7D; the smallest factor in a fastener group governs that
group. §12.5.1.2(b) separately requires a shear-area comparison for loading
at an angle to the fastener. The following sign screen does not substitute
for that angled-load calculation.

| Interface member under a possible pure grain-parallel tension component | Shortest end distance in the two-bolt group (mm) | Conditional result if tension points to that end |
|---|---:|---|
| Lower rail host | 45.45 | 7D clears by 1.00 mm; `CΔ=1.0` screen |
| Lower rail cleat | 43.35 | 1.10 mm below 7D; above 3.5D; group `CΔ≈0.975` |
| Upper rail host | 45.45 | 7D clears by 1.00 mm; `CΔ=1.0` screen |
| Upper rail cleat | 26.95 | 17.50 mm below 7D; above 3.5D; group `CΔ≈0.606` |
| Lower principal host | 1186.05 | 7D clears |
| Lower principal cleat | 59.85 | 7D clears |
| Upper principal host | 1042.00 | 7D clears |
| Upper principal cleat | 43.45 | 1.00 mm below 7D; above 3.5D; group `CΔ≈0.978` |

For either grain-force sign, the two upper rail-cleat bolts swap which bolt
has the 26.95 mm near end; the group minimum remains 26.95 mm. The lower
rail-cleat minimum similarly remains 43.35 mm, and the upper principal-cleat
minimum remains 43.45 mm, across both signs. These are conditional CΔ screens,
not automatic failures: all recorded end distances exceed the applicable
softwood-tension `CΔ=0.5` minimum and the compression `CΔ=0.5` minimum. If a
case has a pure parallel-grain compression component, all shortest endpoints
also exceed 4D. Oblique demand still needs the NDS shear-area method and the
actual sign on each bolt.

Table 12.5.1C requires 4D at the loaded edge for perpendicular-to-grain
loading and 1.5D at the unloaded edge. For parallel-to-grain loading, the
applicable minimum is 1.5D here (`ℓ/D = 38.1/6.35 = 6.0`, the lesser wood
bearing length for each stack). The smallest recorded cross-grain edge is
26.95 mm at `upper_rail_2` in the upper rail host, 1.55 mm above 4D; the next
smallest is 27.9 mm at `lower_principal_2` / `upper_principal_2` in the cleat,
2.50 mm above 4D. Thus the projected box distances clear the Table 12.5.1C
loaded-edge screen for either cross-grain sign under a pure
perpendicular-to-grain loading classification, with narrow nominal margins.
They clear the 1.5D parallel-load edge screen as well. No NDS edge-distance
reduction factor is applied to excuse a short loaded edge. Those Table
12.5.1C comparisons are pure-direction screens. For an oblique
grain-direction resultant, do not infer an NDS edge factor by interpolation;
identify the applicable member check before acceptance.

WJ-04 members have different material axes. For the rail group, a global `X`
component is parallel to the rail host grain and cross-grain in the cleat;
the orthogonal `N` component is cross-grain in the host and parallel to the
cleat grain. For the principal group, `T` is parallel-grain in the principal
host and cross-grain in the cleat, while `N` is cross-grain in the host and
parallel-grain in the cleat. Apply the equal-and-opposite action to the other
member in its own frame. The exact geometry-only classifier
[`classify_member_fastener_load`](../../mini_moonboard/wood_joint_directional_geometry.py)
preserves those signed components and identifies the loaded end/edge; it does
not apply NDS detailing or evaluate cuts, demands, or resistance.

## Readiness implication and remaining checks

There is no obvious outer-box end or loaded-edge shortfall below the minimum
geometry-factor floor in Table 12.5.1A or below the 4D loaded edge in Table
12.5.1C, so this screen alone does not justify declaring all WJ-04 cases
failed or force a geometry revision before any signed actions exist. It does
expose a significant conditional reduction: if upper rail-cleat tension
loads along `±N`, the current two-bolt group has `CΔ≈0.606`; the selected
analysis must either retain that factor in the connection resistance check or
revise the geometry if a full-factor design is required. Small-strain mesh
convergence cannot resolve that detailing condition. The lower rail-cleat
and upper principal-cleat also lose roughly 2.5% and 2.2% of the parallel
softwood tension reference value, respectively, in the signs that point to
their 43.35/43.45 mm ends.

If WJ-04 later adopts a requirement for the full 7D softwood-tension factor
in both signs at the upper rail-cleat row, the 86.9 mm cut length cannot meet
it at the present 33.0 mm bolt pitch: the two end distances plus that pitch
require about 121.9 mm, 2.2 mm longer than the 119.7 mm uncropped candidate
stock length. This is a conditional geometry constraint, not an NDS failure
when a reduced `CΔ` is allowed and supported by a resistance check.

Before interpreting native results, bind fresh signed six-component interface
and per-bolt actions, project them separately onto each member's bolt/grain
axes, classify each nonzero component with both member frames, and evaluate
the applicable Table 12.5.1A factor or §12.5.1.2(b) angled-load shear area.
Also resolve member-specific Tables 12.5.1B–D spacing, local cut/nearest
boundary effects, actual bore and delivered bolt dimensions, as-built center
locations/tolerances, wood species/grade/condition, and the corresponding
resistance inputs. The 7.5 mm WJ-16 bore is only an analysis envelope; NDS
§12.1.3.2 permits a bolt hole 1/32–1/16 in. larger than the bolt, or
7.14375–7.9375 mm for a 1/4-in. bolt; 7.5 mm falls inside that nominal band,
but it is still only an analysis envelope. Hole fit and any drilling
instruction need separate delivered-part and shop verification. None of
these input or strength checks is inherited from the WJ-16 or selected-baseline
load studies.

No CAD regeneration or native solve was run for this audit.
