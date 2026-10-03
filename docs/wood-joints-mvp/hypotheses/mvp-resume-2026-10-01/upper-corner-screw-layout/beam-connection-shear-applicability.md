# Beam connection shear: actual receiver applicability

## Disposition

**An additional finite NDS reduced-depth comparison is required.** The existing
gross and finished-rectangle shear screens do not establish NDS 2024
§3.4.4.1 connection shear. They supply reusable signed member actions and
conditional `Fv` references. This note identifies the receiving-member
components for which that comparison can be prepared without changing the
frame, loads, stiffness, hardware or geometry. It calculates no capacity or
new engineering result.

The current inventory is **50 transport bodies: 44 timber and six plywood**.
The timber comprises 20 frame members and 24 connection timbers. The N03
attempt02 inventory contains 216 axis/host geometry records and 1,296
case/host records. The **104 global axes and four additional internal axes
remain distinct**; 108 is the proposal inventory, not the global lateral
register. Plywood and the additional axial ties receive no beam-connection
shear allowance from this map.

There are **58 distinct frame receiver / physical bolt-pair joins**. This
counts both timber receivers of the six retained frame-to-frame pairs and
counts each continuous side pair once on its middle frame receiver, retaining
its two interfaces. Of these, **50 are rectangular component candidates on
18 frame bodies**: 14 have far-end geometry and 36 have near-end geometry.
The remaining eight joins retain the explicit terminal/recess guards below.
These are applicability counts, not 50 accepted connections or a numerical
pass. A rectangular receiving member does not make its attached short cleat
an ordinary beam.

## Primary rule and input contract

The inspected primary source is NDS 2024 Chapter 3, printed p.21 / PDF p.7,
§3.4.4.1 and Figure 3E. Its scope is rectangular bending members joined by
bolts, lag screws, split rings or shear plates. The required induced shear
comes from engineering mechanics. For bolts and lag screws:

```text
de = d - a
a  = distance from the unloaded edge to the nearest fastener center

connection less than 5d from an end:
Vr' = (2/3) Fv' b de (de/d)^2                         (3.4-6)

connection at least 5d from its ends:
Vr' = (2/3) Fv' b de                                  (3.4-7)
```

The printed convention is inches, psi and pounds. Consistent mm, MPa and N
give the same equations. Concealed bearing-plate notches follow the separate
§3.4.3.1 provision. [NDS 2024 Chapter 3](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf).

The March 2026 errata corrects the former §3.4.3.3 cross-reference to
§3.4.4.1. Its current C12.5.1 excerpt confirms the reduced depth measured
to a fastener **center** for perpendicular connections. This is current
Commentary evidence; the historical 2018 p.208 discussion is not attributed
to unsupported 2024 C3.8.2 p.222. [AWC March 2026 errata, PDF pp.1–2](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf).

The following are prerequisites for applying that rule to this inventory:

| Input | Required join or interpretation in the present model |
| --- | --- |
| Receiving member and bending plane | Identify the actual timber body, its grain axis and the transverse component being resisted. A bolt axis perpendicular to grain does not imply its force is perpendicular to grain. Retain longitudinal action, the other transverse component, torsion and moments separately. |
| `d`, `b` | Use the rectangular receiving-member outline in that plane: `d` along the relevant transverse force direction and `b` across it. The primary lateral components below use `d=139.7 mm`; the header uses its geometric `u` depth, while the other listed frame members use `v`. Dimensions in the table are declared geometry, not inspected wood. |
| `de` | Select an actual physical unloaded edge using the signed transfer. Within one identified group, use the center nearest that edge. For a constant-depth rectangle this is the farthest center from the loaded edge. Do not subtract a bore radius or use the nearest center to the loaded edge. |
| Group | Use the actual two-axis receiver/interface identity. Do not merge all bores in a body. The continuous knee middle receiver has two interfaces on each pair: preserve their actions and shared pair identity. |
| `5d` branch | Establish the position of the entire group relative to the actual timber ends. Use both bolt centers and the saved end/profile witnesses. A station label, nominal connection span or distance to another support is insufficient. Here `5d=698.5 mm` for the stated lateral components. |
| `V` | Use the induced section shear for the identified transfer path, from the complete simultaneous member action inventory. Inspect both sides of the group and any intervening force jumps. A bolt magnitude, a cancelled pair resultant, an opening cut-hull scalar or an independent case envelope is not that input. |
| Support and loading | Retain the saved bolt, contact, washer/tie, nodal gravity/live-load and free-couple actions at their saved points. Identify which support and load path creates each section shear. Do not import a simply supported beam or replace the no-slip floor law. |
| Adjusted `Fv'` | Reuse the receiving member's recorded conditional DF-L No.2 basis and its separate duration scenarios. No EC5 coefficient, fracture property, invented perpendicular tensile value or glulam `Cvr` is introduced. |

NDS §3.4.4.1 is not an angle-interpolation rule for fastener lateral resistance.
The Figure 3I reference accommodates inclined member/bearing arrangements;
it does not qualify every three-dimensional force combination. A transverse
beam component can be assessed while the actual longitudinal and other actions
remain in their existing checks. The N03 oblique edge-distance hypothesis
does not become an adopted `Cdelta` through this route.

## Actual receiver map

The rows below enumerate physical pair joins, not interface capacities.
`*` means the actual left/right names in the frozen N02 group inventory.
Resolve full axis IDs from that inventory as described below. `Near` and
`Far` are geometric branch candidates; a mechanics comparison and the
signed loaded-edge assignment remain outstanding.

### Rectangular component candidates: 50 joins

| Receiving body or bodies | Actual pair partners / axis families | Joins | `b`, depth axis; `d=139.7 mm` | End branch / local condition |
| --- | --- | ---: | --- | --- |
| `base_header` | `center_post_cleat_left/right`: `center_post_header_*_1/2`; `center_principal_cleat_left/right`: `center_principal_header_*_1/2` | 4 | 38.1 mm, `u=Y`; bolt axis `Z` | Far. Nearest saved end distances exceed 990 mm. |
| `base_header` | `knee_outer_left/right_inner_frame_block`: `knee_outer_*_inner_header_1/2` | 2 | 38.1 mm, `u=Y`; bolt axis `Z` | Near. Saved distance to the close header end is 133.35 mm. |
| `base_rail_bottom_left/right` | `bottom_center_*_cleat` and `bottom_outer_*_cleat`, each `/rail_1/2` | 4 | 38.1 mm, `v`; bolt axis `u` | Near; square-ended rail outlines. |
| `base_rail_service_lower_left/right` | Left `left_service_inner_lower_cleat`, `left_service_outer_lower_cleat`; right `wj04_lower_full_stock_cleat`, `wj06_outer_lower_right_cleat`, each `/lower_rail_1/2` | 4 | 38.1 mm, `v`; bolt axis `u` | Near; each receiving rail has a pair at either end. |
| `base_rail_service_upper_left/right` | Left `left_service_inner_upper_cleat`, `left_service_outer_upper_cleat`; right `wj04_upper_g7_crosscut_full_stock_cleat`, `wj06_outer_upper_right_cleat`, each `/upper_rail_1/2` | 4 | 38.1 mm, `v`; bolt axis `u` | Near; preserve the actual reversed-rail group geometry. |
| `base_rail_top` | `top_center_left/right_cleat`, each `/rail_1/2` | 2 | 38.1 mm, `v`; bolt axis `u` | Far; saved near-end distances are about 995–998 mm. |
| `base_rail_top` | `top_outer_left/right_cleat`, each `/rail_1/2` | 2 | 38.1 mm, `v`; bolt axis `u` | Near; close end distance 45.45 mm. |
| `base_post_center_left/right` | `center_post_cleat_left/right`: `center_post_*_1/2` | 2 | 38.1 mm, `v=Y`; bolt axis `X` | Near; entire post length is 238.9 mm. |
| `base_post_outer_left/right` | `knee_outer_left/right_spine`: `knee_outer_*_post_1/2`; `base_floor_left/right`: `rail_front_bolt_*_1/2` | 4 | 38.1 mm, `v=Y`; bolt axis `X` | Near; entire post length is 238.9 mm. These are two distinct duties on each post. |
| `base_floor_left/right` | `base_post_outer_left/right`: `rail_front_bolt_*_1/2` | 2 | 38.1 mm, `v=-Z`; bolt axis `X` | Near, square front end. Retain floor support/contact actions. |
| `base_floor_left/right` | `lumber_leg_left/right`: `rail_rear_bolt_*_1/2` | 2 | 38.1 mm, `v=-Z`; bolt axis `X` | Near, oblique rear end. Both bolt-center cross rays reach the full parallel depth faces; the actual end-plane witness must remain attached. This says nothing about the recessed rear-leg receiver. |
| `base_principal_center_left/right` | `bottom_center_left/right_cleat`, each `/principal_1/2` | 2 | 38.1 mm, `v`; bolt axis `X` | Near; lower end is oblique, but these bores are in the full rectangular outline above its termination. Saved close end distances 256.715 and 289.715 mm. |
| `base_principal_center_left/right` | Left `left_service_inner_lower/upper_cleat`; right `wj04_lower_full_stock_cleat`, `wj04_upper_g7_crosscut_full_stock_cleat`, each `/lower_principal_1/2` or `/upper_principal_1/2` | 4 | 38.1 mm, `v`; bolt axis `X` | Far; both centers' saved distances to both ends exceed 1,040 mm. |
| `base_principal_center_left/right` | `top_center_left/right_cleat`, each `/principal_1/2` | 2 | 38.1 mm, `v`; bolt axis `X` | Near; square grain-normal top end, saved close distances 60.9 and 27.9 mm. |
| `base_side_left/right` | `bottom_outer_left/right_cleat`, each `/side_1/2` | 2 | 88.9 mm, `v`; bolt axis `X` | Near; retain the oblique lower termination. These bores are above the truncated terminal region. |
| `base_side_left/right` | Left `left_service_outer_lower/upper_cleat`; right `wj06_outer_lower/upper_right_cleat`, each `/lower_side_1/2` or `/upper_side_1/2` | 4 | 88.9 mm, `v`; bolt axis `X` | Far; both centers' saved distances to both ends exceed 1,080 mm. |
| `base_side_left/right` | `lumber_leg_left/right`: `lumber_leg_bolt_*_1/2` | 2 | 88.9 mm, `v`; bolt axis `X` | Near; saved top-end distances approximately 586.653 and 534.457 mm. |
| `base_side_left/right` | `top_outer_left/right_cleat`, each `/side_1/2` | 2 | 88.9 mm, `v`; bolt axis `X` | Near; square grain-normal top end, saved close distances 141.875 and 74.025 mm. |

The header, seven rails and four posts supply 28 joins with square-ended
ordinary rectangular member geometry. The remaining 22 candidates above
belong to ordinary frame members with an oblique terminal face somewhere in
their geometry. The actual profile witnesses must accompany the relevant
end/section selection; no square-ended distance is substituted for them.

### Eight joins needing additional geometry/method guards

| Receiving body / physical pair | Saved evidence and exact unresolved condition |
| --- | --- |
| `base_principal_center_left/right`, `center_principal_*_1/2` — two joins | Bolt 1's cross ray toward `facet017` reaches the oblique foot end at **76.8681066927 mm**, while the opposite ray reaches the longitudinal edge at about 44.45 mm. This is not a full 139.7 mm rectangle at that station. Bolt 2 does reach the parallel depth faces, approximately 95.25 and 44.45 mm away. The pair needs an actual terminal-section/path mapping; do not substitute `76.868 + 44.45` as a new beam depth and silently apply the prism equation. |
| `base_side_left/right`, `knee_outer_*_side_1/2` — two joins | The first bolt's 84.5 mm cross reference reaches the joint end/edge corner (`facet018` and `facet035`). Its saved `first_exterior_exit` is null because of simultaneous corner hits; the finite reference has convexity and affine-plane witnesses. This is not missing geometry or a zero distance. The second bolt has ordinary parallel-face references 55.2/84.5 mm. Preserve the oblique terminal corner and both interfaces on the shared middle receiver before asserting a beam-like transfer path. |
| `lumber_leg_left/right`, `lumber_leg_bolt_*_1/2` — two joins | These upper bores are in the full-width part of the rear legs, with an oblique upper end. N03 provides `EXACT_TRIMMED_MID_BEARING_REFERENCE`, not a certified through-depth minimum. Saved close grain-ray distances are about 119.282 and 94.152 mm. A local rectangular component is possible, but its actual depth/end profile and transfer into the inclined leg must be established across the bearing/path before assigning `b=88.9`, `d=139.7` as a qualified allowance. |
| `lumber_leg_left/right`, `rail_rear_bolt_*_1/2` — two joins | Lower receiver lies in the retained **50.8 mm** portion of the original 88.9 mm width, followed by the 1:12 transition and an oblique floor foot. Saved references are trimmed midpoint references. Full gross width is unavailable; neither a midpoint depth sum nor the existing elementary recess screen establishes §3.4.4.1/§3.4.3.1 applicability for the whole path. Reuse the actual saved recess/profile dispositions. |

An oblique end is not declared categorically prohibited by §3.4.4.1. It is
a geometry input and, where it truncates the loaded section or support path,
a method limitation. N03's Table 12.1 square-cut `e` limitation is not a
substitute for that distinction.

All 24 connection timbers remain outside a blanket beam allowance. This
includes short crossed cleats, end-grain axes, the four modified corner
blocks and the two modified spines. A component route for a particular cleat
or spine may exist, but would require its own retained geometry and complete
shared loading/support map. Their end-grain, eccentric opening, washer/tie
anchorage and splitting dispositions remain with the root splitting work.
The four new internal spine ties are axial allocations, not four additional
global lateral beam connections.

## Signed geometry and mechanics witnesses

For `a12-rear`, the ordinary `base_rail_bottom_left` receiving pair is
`bottom_center/clip_horizontal_bottom_left_2/rail_1/2`. Both bores lie
43.45 mm from the close rail end. Their center-to-edge distances in the
same physical transverse direction are respectively 53.35 and 86.35 mm;
opposite distances are 86.35 and 53.35 mm. N03 records both actions toward
that first physical edge. Thus the nearest center to the unloaded edge is
53.35 mm away, giving **`de=86.35 mm`**, with `b=38.1`, `d=139.7` and the
near-end branch. This is a geometry witness, not a computed shear index.
The current induced section `V` still has to be joined to it.

For the same case, the two rear-floor bolts on `base_floor_left` carry saved
global `Z` components **+65.5840842102 N** and **−51.0237134772 N**. These
are opposing depth-direction actions, not one uniform loaded-edge direction.
A cancelled net pair component would erase part of the local transfer and
couple. Their beam component requires signed load-path treatment at the
individual force jumps, retaining the other force components and full wrench.
The rectangular floor receiver survives the geometric test; a single loaded
edge chosen from the resultant does not complete its mechanics test.

The N03 `cross_plus`/`cross_minus` names are selected relative to the saved
direction; they can exchange physical sides between cases or bolts. Use
`ray_unit_xyz` and the physical profile plane to join sides. For a zero
direction, keep both possible physical edges or document the absence of that
transfer; do not choose the edge that gives the larger allowance. If a later
authoritative same-state force allocation differs from this N03 snapshot,
reuse its geometry and recompute the signed assignment from that authority.

## What the previous Fv cuts do and do not establish

The existing `member_stability.py::shear_check` accepts the signed cut vector,
rectangle width/depth, `Fv` and torsion orientation. It computes parabolic
transverse shear `1.5*abs(Vu or Vv)/(width*depth)`, torsional face additions
and a component rectangle bound. It has **no fastener group, loaded edge,
`de` or `5d` input**. `knee-bridge-members.py` applies it to saved intact
rectangles and shifts moments to their centroids. Opening/profile refreshes
address local section limitations; they do not add the missing connection
allowance.

For the same `V`, `Fv'`, `b` and `d`, let the gross rectangular shear capacity
be `(2/3) Fv' b d`. The near-end connection allowance is that capacity times
`(de/d)^3`; the far-end allowance is that capacity times `de/d`. A gross
utilization below 1 therefore does not establish the connection comparison.
An existing authenticated gross upper bound can be reused only after it is
shown to bound the relevant current `V`, with the same section/material basis,
and compared with the applicable reduction. No such group-bound comparison
is recorded by the prior producer. An exceedance of a conservative bound
would require the actual component value; it would not by itself prove a
physical failure.

The recorded member references are
`references.cd1.Fv_mpa = 1.241056312770305` and
`references.cd1_25.Fv_mpa = 1.5513203909628812`, under the existing conditional
DF-L No.2, dry, unincised, normal-temperature scenarios. Their provenance
also records `design_resistance_established=false` and
`duration_adoption_complete=false`. Keep those two comparisons separate;
do not promote a duration sensitivity or mix an EC5 characteristic/ULS
allowance into the ASD comparison. Permanent-load duration and global
stability remain parent-owned.

The smallest outstanding engineering work is a **finite comparison using
the saved six-case actions**, initially for the 50 rectangular candidates,
after the signed transfer/path joins. The eight guarded joins need their
specific profile/mechanics disposition. No new load case, frame response or
hardware change follows from this applicability map. The result can be a
conditional comparison, an exact exceedance or an identified unsupported
path; this note does not predict a pass.

## Minimal existing data and joins

Paths in this section are relative to this directory.

1. **Body and physical pair identities.** Use
   `rawlocal/knee-bridge-integration/attempt02/manifest.json`:
   `geometry.effective_members[].body` and its current/effective STEP bindings;
   `existing_bolt_axes[].axis_id`, `interfaces[].plane_id`, `receivers`,
   `component_rows`, `component_row_ids`, `component_directions_xyz` and
   interface point. Resolve the named pairs through
   `rawlocal/bolt-group-completion/attempt01/checks.json::groups[]`, keyed by
   `(case_id, receivers, axis_ids)`. Deduplicate on receiving body and physical
   axis pair, while retaining all interfaces. The integration manifest's
   historical force records are not the current demand authority.
2. **Actual bore/end/edge geometry and signed directions.** Join
   `rawlocal/bolt-detailing-completion/attempt02/geometry-bindings.json`
   on `(axis_id, body)` and its effective STEP hash. Join
   `host-states.jsonl` on `(case_id, gap_scale=1, axis_id, body)`. Use
   `detail.mid_bearing_xyz_mm`, `reference_rays`, physical ray vectors,
   `first_exterior_exit` or the certified affine/corner witnesses, and
   `through_depth_minimum_established`. Retain `global_plane_actions` and
   `per_interface_details` where present. Loaded/unloaded edge labels are
   direction witnesses, not adopted resistance or complete group partitions.
3. **Member axes, retained profile and sections.** Join body names to
   `../member-screen-attempt02/knee-bridge-gravity01/geometry.json::members`.
   Use `geometry.axis/section_u/section_v`, `start/end`, `profile_planes`,
   `recess_source`, `bore_or_passage_intervals`, `stations_mm`,
   `rectangle_at_station` and the point-action identity lists. The header's
   `width_mm=139.7`, `depth_mm=38.1` are **not** this check's `b,d` ordering.
   Do not use a gross rectangle where the saved finished profile rejects it.
4. **Existing induced section actions.** Reuse
   `../member-screen-attempt02/knee-bridge-gravity01/member-results.json`
   and `action-section-arrays.npz`. The array prefix is `case_id__body`;
   `__internal_negative_grain_u_v` and its positive counterpart contain
   `[N, Vu, Vv, T, Mu, Mv]`, with before/after rows for each saved station.
   Point arrays contain forces and free couples at the saved points. Join
   the physical group to these action stations and both adjacent traces;
   do not presume the first available bore-free cut bounds every intervening
   transfer. Use the existing point inventory if a required group cut is not
   represented. No altered response is needed for that accounting.
5. **Authenticate the same-state force and support closure.** The existing
   member extraction is bound to gravity operator assessment `ce69…`,
   frame comparison `c3a8…` and response `62bd…`. Its producer's source
   closure includes the physical row identities, model and operator/load
   arrays. `rawlocal/knee-bridge-gravity/attempt01/row-identities.json`
   joins component rows to ownership and saved points. Reuse the existing
   `knee-bridge-members.py::validate_actions` accounting contract if a parent
   prepares arithmetic: full signed row projection, nodal gravity/live loads,
   free couples, whole-body balance and opposite cut-half closure. N03 fresh
   physical corner bore forces may place a local force differently from a
   coarse global row; retain their existing replay/wrench source join instead
   of silently replacing the member action inventory with the N03 bolt list.
6. **Material reference.** Join the receiving body to
   `rawlocal/knee-bridge-members/attempt01/checks.json::members[]` for
   `material_strength_binding`, `references` and existing section limits.
   This source evaluates all 20 frame members and 22 unchanged connection
   timbers; the two modified spines are excluded, reinforcing their separate
   component/method disposition.

### Read source pins

These pins identify the evidence inspected for this map. They do not replace
the producers' complete recursive source authentication before a future run.

| Source | SHA-256 |
| --- | --- |
| `splitting-reference-scope.md` | `c8c27ae63d5aaefbf78e2f46ca29bc3c564aa4b5a89b22af49605a45fe572d7f` |
| `rawlocal/profile-method-completion/sources/nds2024-chapter3.pdf` | `205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644` |
| `rawlocal/knee-bridge-integration/attempt02/manifest.json` | `1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c` |
| `rawlocal/bolt-group-completion/attempt01/checks.json` | `4db21cc2d7fa76cebc021ef8574331d520f247b78de5acb4270ac90dc80713de` |
| `rawlocal/bolt-detailing-completion/attempt02/receipt.json` | `28c00cefe1d95f86d75b837304a958ff5242690f88017e685a959ba7c1b15a59` |
| `rawlocal/bolt-detailing-completion/attempt02/summary.json` | `ed4ca499ec9e10ef8550f01071a42fec8797c34cb5ec24d1f95516d5c37ede94` |
| `rawlocal/bolt-detailing-completion/attempt02/geometry-bindings.json` | `c883691261a365125cedde76add0a3bf0406bd1c3c0b5fbfc1dc4b0aa25fa8ed` |
| `rawlocal/bolt-detailing-completion/attempt02/host-states.jsonl` | `07f086dff6a9691d06370888e43adf4bcd8c016b40c73c9dd5e614be6948a998` |
| `../member-screen-attempt02/knee-bridge-gravity01/geometry.json` | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| `../member-screen-attempt02/knee-bridge-gravity01/action-section-arrays.npz` | `3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596` |
| `../member-screen-attempt02/knee-bridge-gravity01/member-results.json` | `5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0` |
| `rawlocal/knee-bridge-members/attempt01/checks.json` | `0d623eb62605ddac9aa5111e2469a1c63f4857e356fe607741fc425d5ea59e65` |
| `../member_stability.py` | `eb70dbe72c1ed3b9518739915193083fd6a07ebd064ba17d0c07f299f6786b72` |
| `rawlocal/knee-bridge-gravity/attempt01/row-identities.json` | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| `rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| `rawlocal/knee-bridge-frame/attempt02/response/comparison.json` | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| `rawlocal/knee-bridge-frame/attempt02/response/response.npz` | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |

Only JSON/provenance reads, source inspection and primary-document inspection
were performed. No code, replay, numerical assessment, test, CAD/native run,
review, staging, commit, authority edit or new load/support law was performed.
