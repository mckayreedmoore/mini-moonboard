# Finite beam connection shear completion

## Readiness and frozen scope

**Parent attempt01 completed with exit 0. The saved reduced-depth beam
comparison has eight actual-edge post exceedances under both duration
references; complete-joint acceptance is not established.** The producer is
[`beam-connection-shear-completion.py`](beam-connection-shear-completion.py).
It completes the finite reduced-depth comparison identified by the frozen
[`beam-connection-shear-applicability.md`](beam-connection-shear-applicability.md),
using the existing six simultaneous states and member action extraction.
It does not call another producer's engineering workflow.

This document adds a primary-source interpretation and postprocessing of the
parent's saved results. The producer, frozen applicability map and all raw
numerical artifacts remain unchanged. The raw producer reports zero matching
rows because its label requires every named limit to be absent. That label
is more restrictive than the NDS transverse-component requirement: separate
axial/washer and combined-load duties do not automatically make the component
unavailable. The interpretation below does not change a saved label or claim
an old `matching_component_pass`.

The preparation at `rawlocal/beam-connection-shear-completion/prepare01`
completed `PREPARED_NOT_NUMERICALLY_RUN`, with **255 source pins and four
authenticated outputs**. Its producer snapshot is byte-identical to the
prepared source. Preparation uses standard-library JSON, identity and
provenance work; it hashes array files without decoding their values or
importing NumPy. Source syntax was parsed with `ast.parse`. No worker
engineering build, software test, review, frame/native/CAD operation, staging
or commit was performed.

| Frozen leaf or preparation artifact | SHA-256 |
| --- | --- |
| Producer `.py` | `69269ba9b0853127e569fcd43c3979b2846ad9d7db3d4ce93c6b4fd6e32160a4` |
| Applicability map, unchanged | `b689b6f1a759ba0b86b6ace600f78e49b8e8c60f8f37bfbf46b6241094b7d9bb` |
| `prepare01/receipt.json` | `fe8f7f063a7a509e6e43468478f1def8ac0ec91863d95d2163a0222b3fd5608c` |
| `prepare01/inventory.json` | `40a74b3464eecf38358d15c6c846331469d37451a1f1c6ad13871dc0cf19fbd7` |
| `prepare01/report.json` | `c02a8dd61328ba5a6d012dc11895807f4c33a3b283034178e87d545d9855848f` |
| `attempt01/receipt.json` | `7b88e4ba5c9a64a6552880877970ebc4f7371080f126cedc9e40b46f0a5ede60` |
| `attempt01/report.json` | `f718352feed4a903a27da803831f21b78f335c7cfb60aad493725bd102c556b8` |
| `attempt01/group-case-states.jsonl` | `551a24999d6400e1c17c19cdf16a746da75ce2f75b6c3fb90595c6ca9a3882fb` |
| `attempt01/body-case-closure.json` | `f290f1ca671c4b7fabc2543214c0411ab91355ef0fc5491f0fb377cd3e12510d` |

## Frozen API

```python
prepare(output: pathlib.Path | str) -> dict
build(output: pathlib.Path | str) -> dict
```

Importing the module is inert. `prepare` authenticates sources and writes the
join inventory. **Only the parent calls `build`.** Both entry points require
a new immediate child of this producer's owned
`rawlocal/beam-connection-shear-completion/` directory. Existing attempts are
never overwritten. A failed call preserves its STOP report, receipt and any
partial group-state stream, then raises a `ValueError`.

The prepared parent CLI command was:

```bash
timeout 120s uv run python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/beam-connection-shear-completion.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/beam-connection-shear-completion/attempt01
```

The CLI's `--prepare` selects provenance preparation instead. There are no
load, geometry, stiffness, material, gap or favorable-edge override arguments.
Use the repository's existing numerical environment; the actual report records
Python and NumPy versions. `timeout` bounds the parent's process and does not
alter the engineering inputs.

## Census and outputs

The body inventory remains 50 transport bodies, including 44 timber and six
plywood. This producer evaluates the **20 frame receiving members** and does
not assign a beam allowance to every connection timber.

| Item | Frozen count |
| --- | ---: |
| Global physical axes | 104 |
| Additional internal proposal axes | 4 |
| Proposal physical axes | 108 |
| Frame receiver / physical pair joins | 58 |
| Rectangular geometry candidates | 50 on 18 bodies |
| Guarded terminal/recess joins | 8 |
| Nominal simultaneous cases | 6 |
| Actual group/case records | 348: 300 candidate and 48 guarded |
| Actual authenticated body/case closures | 120 |
| Candidate end branches | 36 near, 14 far |
| Actual finite indices per duration | 461 |
| Saved CD1 / CD1.25 exceedances | 27 / 21 |
| Saved matching rows | 0; all 545 comparison entries have the diagnostic label |

The 104 global axes and 108 proposal axes remain separate. The four internal
spine ties have no new global lateral rows and receive no NDS beam-connection
capacity here. A continuous knee side pair is counted once on its middle
frame receiver while retaining both interface forces.

Preparation writes `inventory.json`, `report.json`, `producer.py.snapshot`
and `.gitignore`, plus a receipt. The actual build additionally writes:

- `group-case-states.jsonl`: one record for each of the 348 joins/cases,
  including every global lateral plane, local N03 direction witness, signed
  cut demands, physical edge/depth geometry and both duration scenarios.
- `body-case-closure.json`: the 120 authenticated whole-body and nodal-load
  closures, joined back to the existing saved closure evidence.
- `report.json`: actual counts, named limits and maximum indices with complete
  same-state witnesses, separated by scenario and comparison role.

The actual receipt binds six outputs, excluding itself. Individual zero or
opposing transfers can produce two hypothetical edge diagnostics within their
single group/case record; these do not increase the 348-record census.

## Numerical method and applicability

### Exact current demand and wrench scope

The demand authority remains the `ce69…` gravity operators, `c3a8…` response
comparison and `62bd…` response. The producer reuses the existing pure
`basis`, `cut_vectors`, `saved_actions` and `wrench` definitions, through the
already frozen definition loader. It calls the preserved
`knee-bridge-members.py::validate_actions` contract for each of 120 body/case
states. This checks every incident signed global row, its physical point and
ownership, nodal dead/live loading, free couples, whole-body balance, both
cut halves and the saved section-action extraction. No frame response is
recomputed.

For each actual pair, the global lateral interface rows are joined to N03's
saved `global_plane_actions`, including force, point, partner and row IDs.
Their signed forces are projected into the receiving member's grain/u/v
frame. Both interfaces of the middle continuous-shaft receiver remain visible;
they are not replaced by a cancelling resultant.

The induced component demand is the largest absolute signed section shear
among **all saved before/after cuts across the complete interval of the
pair's actual global force stations**. Every interface station must be present
in the saved cut inventory. This retains both sides of the group and every
intervening force jump. The demand witness carries its original six-component
`[N, Vu, Vv, T, Mu, Mv]` vector, cut index, trace and section status. This is
a finite group-interval envelope, not a bolt-force magnitude or opening-hull
scalar. Every force, contact and couple contributing to the original cuts
remains in the accounting.

The primary lateral plane is grain–u for the header, with `b=38.1 mm` and
`d=139.7 mm`; it is grain–v for the other candidate frame members. The other
u/v section demand is retained explicitly, with a null capacity: the fastener
shaft/washer direction does not receive a second invented lateral allowance.

### Physical edges, `de` and branch

The producer checks that the actual shaft is perpendicular to grain and
normal to the chosen lateral beam plane. It joins N03's transverse rays to
the physical member axis, instead of assuming that `cross_plus` names the
same edge in every case. For the 50 candidates, both rays must sum to the
declared depth, have constant-prism references and identify the actual
parallel depth faces. The group branch is near when any saved bolt-center
end reference is below `5d`; otherwise it is far. The resulting 36/14
candidate branch census must match the frozen map.

For a unique nonzero signed depth transfer, the unloaded edge is the opposite
physical edge. `de` is `d` minus the minimum center-to-unloaded-edge distance
within that physical pair. This measures to the bolt center, not the bore
surface. The adjusted capacity uses NDS 2024 §3.4.4.1 equations 3.4-6 or
3.4-7, with coherent mm/MPa/N units, as established by the pinned primary
source and [frozen applicability map](beam-connection-shear-applicability.md).

Zero depth transfer leaves the physical unloaded edge undefined. Opposing
signs also leave no single unloaded edge. Both physical-edge calculations
remain diagnostics; neither receives `matching_component_pass=true` merely
because its index is below one. Individual plane signs remain in the record.
The inherited `1e-4 N` direction resolution is documented and does not zero
or modify the saved forces or section demand.

### Frozen producer labels and component interpretation

`MATCHING_PLANAR_NDS_TRANSVERSE_COMPONENT` requires a candidate rectangle,
the actual established plane, a unique nonzero loaded edge and no recorded
nonordinary transfer limit. Every other row is
`EXPLICIT_TRANSVERSE_COMPONENT_DIAGNOSTIC`. Applicable candidate geometry
still supplies finite equation indices for the latter, with named limits;
these are not complete NDS joint capacities.

Those are the frozen implementation's labels. **The presence of any separate
joint duty is not, by itself, a reason to withhold the rectangular transverse
beam comparison.** NDS §3.4.4.1 identifies rectangular bending-member
connections and requires mechanically determined induced shear; it does not
require pure transverse fastener forces or absence of other actions. Section
3.9 separately addresses members carrying axial force and bending. Interpreting
these provisions together supports keeping the established transverse `V`
comparison while retaining the other checks. This is a component interpretation,
not a new combined-load resistance law. The pinned p.21/PDF p.7 text and
Figure 3E were re-inspected directly, including its unloaded-edge diagrams.
[NDS 2024 Chapter 3, §§3.4.4.1 and 3.9](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf).

The NDS connection provisions additionally require all applicable member
checks and local connection mechanics. Eccentric perpendicular-tension paths
remain separate obligations. Thus an axial washer/tie action, orthogonal shear
or torsion cannot be credited as resisted by this scalar equation; neither
does its mere presence erase the authenticated transverse component.
[NDS 2024 Chapter 11, §§11.1.2–11.1.3, printed p.70](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf),
[AWC March 2026 errata, PDF pp.1–2](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf).

In the saved records, `ASSOCIATED_AXIAL_WASHER_OR_TIE_ACTION_SEPARATE`
refers to an axial **fastener** duty, which can be orthogonal to the member's
grain. It is not proof that the member lacks a bending/shear duty.
`OBLIQUE_LOAD_TRANSVERSE_COMPONENT_ONLY` says the bolt vector also has a
grain-direction component. With an established transverse plane and unique
actual edge, that flag preserves the angle/group and combined-member duties;
it does not prohibit the already identified transverse `V` comparison.

Read-only selection of the saved fields identifies **111 finite comparison
rows** with a unique actual unloaded edge and no flags beyond those two.
They have the established rectangular frame-member plane, `b/d/de`, end branch
and complete-action section `V`. **Eight exceed under both CD1 and CD1.25;
103 have indices at or below one under both references.** These are available
conditional beam-component results. They are not unavailable merely because
the remaining joint duties are unfinished, and they are not reclassified raw
matching passes. Short frame posts remain the solid rectangular frame
receivers mapped here; this interpretation assigns no universal allowance to
the separate short crossed cleats.

True input/method guards remain: no unique loaded edge, an unproved oblique
transfer plane/edge, truncated or recessed sections, an unsupported support
path, or transferring one force-placement allocation to a different local
model. An oblique **vector with an established transverse component** is
different from an unproved plane or edge. The saved full-action `V` includes
the other actions; no action or couple is removed to obtain a component result.

Limits include opposing directions, zero direction, oblique grain/depth force,
out-of-plane action, multiple interfaces, associated free couples, separate
axial washer/tie action and a discrepancy between the global cut allocation
and the N03 physical-corner replay allocation. Local replay vectors and their
difference from the global bore vectors are preserved. They are not substituted
into the global member cuts. An unexplained source discrepancy stops the run.

The eight guarded joins preserve their actual u/v demands, profile planes
and recess sources, with **null NDS `b`, `d`, `de`, capacities and indices**.
Gross rectangular references are labelled as references only. Their named
guards are the principal foot truncation, side knee terminal corner,
upper rear-leg trimmed bearing reference and recessed rear-leg foot.
No whole-face, gross-width or square-ended substitution removes those limits.
End-grain cleats, modified spines, internal tie anchorage, complete splitting
and their other paths remain outside this beam component producer.

### Material and duration, once

The actual receiving body's saved `material_strength_binding` and
`references` are reused. Normal-duration `Fv` and the `C_D=1.25` sensitivity
are read as separate already adjusted values. The producer checks their
source relation and applies **no additional duration multiplier**. Each
scenario reports its own `Fv`, capacity and index against the same saved
`V`, `b`, `d` and `de`.

The original conditional DF-L No.2 assumptions and unobserved duration
hypothesis remain. Permanent-load duration and global stability are parent
work. There is no EC5/ASD hybrid, invented fracture/tension allowance,
changed material stiffness or torsional resistance. A finite component index
does not establish a common physical pose, delivered wood/hardware condition
or complete member/joint acceptance.

## Source authentication and remaining result boundary

The complete 255-pin map is in `prepare01/receipt.json::source_sha256` and
`prepare01/report.json::source_sha256`. It includes the frozen code and
geometry map, N03's recursive consumed sources/outputs, the original member
extraction closure, its independent frame classifier and the completed member
reference receipt. N02's pair table is authenticated for **identities only**;
its force/resistance scenario dependencies are not a replacement demand
authority. Sources are reauthenticated before and after the actual build.

| Key consumed source | SHA-256 |
| --- | --- |
| Gravity assessment | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| Response comparison | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| Response arrays | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| Saved member actions/cuts | `3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596` |
| Saved member geometry | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| Completed member references | `0d623eb62605ddac9aa5111e2469a1c63f4857e356fe607741fc425d5ea59e65` |
| N03 geometry bindings | `c883691261a365125cedde76add0a3bf0406bd1c3c0b5fbfc1dc4b0aa25fa8ed` |
| N03 host states | `07f086dff6a9691d06370888e43adf4bcd8c016b40c73c9dd5e614be6948a998` |
| NDS 2024 Chapter 3 | `205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644` |

Actual indices, exceedances, matching-component counts and their same-state
witnesses are preserved in the parent's attempt01. Its six output hashes were
independently checked against receipt `7b88…`; all match. The actual runtime
was Python 3.12.3 / NumPy 2.5.2. The following interpretation uses only saved
fields, comparisons and witnesses; no force, capacity or index was recomputed.

## Actual exceedances and applicability

The saved 461 finite entries comprise 139 actual unique-edge entries, 268
zero-transfer edge hypotheses and 54 opposing-transfer edge hypotheses.
The 21 CD1.25 exceedances comprise **12 actual-edge rows and nine zero-transfer
hypotheses**. None comes from an opposing-sign edge hypothesis. At CD1 the
corresponding exceedance counts are 13 actual-edge rows and 14 zero-transfer
hypotheses. Hypothesis counts are equation diagnostics, not proof of a failed
actual loaded-edge condition.

The table lists all 21 saved CD1.25 exceedances, in descending saved index.
All use the near-end equation, with `b=38.1 mm`, `d=139.7 mm`, primary component
`v`. Values are display-rounded only; exact values and complete witnesses
remain in the hashed JSONL. Edge signs are physical `v` signs: for posts this
is global `Y`; the top rail uses its saved inclined `v` axis.

Reason codes:

- **P — available post component:** actual unique edge and unchanged global
  allocation; the only raw flags are separate axial washer/tie duty and
  oblique transverse-component scope. The NDS beam comparison remains
  applicable under the recorded elementary frame/material assumptions.
- **R — global-model rail component, allocation limit retained:** actual
  unique global edge, but the local physical-corner replay allocation differs
  from the allocation used by these global member cuts. Its global-model
  component exceedance is retained; physical-corner qualification is not
  transferred from it.
- **Z — hypothesized edge only:** source depth transfer is directionless at
  the inherited `1e-4 N` resolution. The negative-edge calculation is not an
  established actual unloaded edge. The opposite hypothesis was also saved;
  no favorable edge is selected as a pass.

| # | Receiver / pair partner | Case | Reason | Loaded `v` edge | `de` mm | Saved `V` N | `Vr'`, CD1.25 N | Index CD1.25 | Index CD1 | Cut / trace |
| ---: | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | `base_post_outer_left` / `knee_outer_left_spine` | `a12-left` | P | − | 38.100000 | 984.986991 | 111.665067 | 8.820905354 | 11.026131693 | 103 after |
| 2 | `base_post_outer_left` / `knee_outer_left_spine` | `a12-forward` | P | − | 38.100000 | 974.815507 | 111.665067 | 8.729816131 | 10.912270163 | 103 after |
| 3 | `base_post_outer_right` / `knee_outer_right_spine` | `k12-right` | P | − | 38.100000 | 969.499666 | 111.665067 | 8.682210902 | 10.852763627 | 103 after |
| 4 | `base_post_outer_left` / `knee_outer_left_spine` | `a12-rear` | P | − | 38.100000 | 358.675977 | 111.665067 | 3.212069680 | 4.015087101 | 103 after |
| 5 | `base_post_outer_right` / `knee_outer_right_spine` | `k12-rear` | P | − | 38.100000 | 347.382260 | 111.665067 | 3.110930463 | 3.888663079 | 103 after |
| 6 | `base_post_outer_left` / `knee_outer_left_spine` | `a1-rear` | Z | − | 38.100000 | 226.271323 | 111.665067 | 2.026339380 | 2.532924225 | 95 after |
| 7 | `base_post_center_left` / `center_post_cleat_left` | `a12-forward` | Z | − | 44.450000 | 316.127807 | 177.319991 | 1.782809734 | 2.228512168 | 71 after |
| 8 | `base_post_outer_left` / `knee_outer_left_spine` | `k12-rear` | Z | − | 38.100000 | 172.421301 | 111.665067 | 1.544093469 | 1.930116837 | 103 after |
| 9 | `base_post_outer_right` / `knee_outer_right_spine` | `a12-rear` | Z | − | 38.100000 | 168.403094 | 111.665067 | 1.508109010 | 1.885136262 | 103 after |
| 10 | `base_rail_top` / `top_outer_right_cleat` | `k12-rear` | R | + | 76.350000 | 1042.812583 | 898.606446 | 1.160477524 | 1.450596904 | 464 before |
| 11 | `base_rail_top` / `top_outer_right_cleat` | `k12-right` | R | + | 76.350000 | 1031.251584 | 898.606446 | 1.147612048 | 1.434515060 | 464 before |
| 12 | `base_post_outer_left` / `base_floor_left` | `a12-left` | P | + | 69.527859 | 778.748113 | 678.607996 | 1.147566957 | 1.434458696 | 53 after |
| 13 | `base_post_outer_right` / `base_floor_right` | `k12-right` | P | + | 69.527859 | 770.099627 | 678.607996 | 1.134822507 | 1.418528134 | 53 after |
| 14 | `base_post_outer_right` / `knee_outer_right_spine` | `a12-left` | Z | − | 38.100000 | 125.170020 | 111.665067 | 1.120941607 | 1.401177009 | 95 after |
| 15 | `base_post_outer_left` / `base_floor_left` | `a12-forward` | P | + | 69.527859 | 752.363191 | 678.607996 | 1.108686010 | 1.385857512 | 53 after |
| 16 | `base_post_center_right` / `center_post_cleat_right` | `k12-right` | Z | − | 44.450000 | 188.271047 | 177.319991 | 1.061758723 | 1.327198404 | 79 after |
| 17 | `base_post_outer_left` / `knee_outer_left_spine` | `k12-right` | Z | − | 38.100000 | 117.783367 | 111.665067 | 1.054791523 | 1.318489404 | 95 after |
| 18 | `base_post_center_left` / `center_post_cleat_left` | `a12-left` | Z | − | 44.450000 | 186.352896 | 177.319991 | 1.050941265 | 1.313676581 | 79 after |
| 19 | `base_rail_top` / `top_outer_left_cleat` | `a12-left` | R | + | 76.350000 | 924.431672 | 898.606446 | 1.028739195 | 1.285923994 | 19 after |
| 20 | `base_rail_top` / `top_outer_left_cleat` | `a12-rear` | R | + | 76.350000 | 916.890292 | 898.606446 | 1.020346889 | 1.275433612 | 19 after |
| 21 | `base_post_center_right` / `center_post_cleat_right` | `a12-forward` | Z | − | 44.450000 | 177.820857 | 177.319991 | 1.002824644 | 1.253530806 | 79 after |

### Governing available component and retained limits

The governing available row is outer post left / knee spine left,
`a12-left`. Both bolt actions have negative `v=Y` components, establishing
the positive-Y unloaded edge. The two centers are each 101.6 mm from that
unloaded edge, giving the saved `de=38.1 mm`. The closest grain-end reference
is 25.4 mm against `5d=698.5 mm`, so the near-end reduction is applicable.
Its source cut is index 103, after station 192.0 mm, with signed
`[N, Vu, Vv, T, Mu, Mv]`:

```text
[85.325577637, 133.073723724, -984.986990953,
 -183.149449396, 6234.671624981, 4642.507064337]   N and N mm
```

The CD1.25 allowance is 111.665067408 N and the saved index is
8.820905354002754; the normal-duration index is 11.02613169250344.
The oblique bolt vectors, axial washer/tie actions, other component and
torsion remain in the complete state. They do not supply missing strength
credits and do not make this mechanically determined `Vv` unavailable.
The demand is the induced section shear from all actions, not the sum of the
two bolt lateral components. The recorded `NON_APPLICABLE_BORE_OR_PASSAGE`
cut status means the earlier plain-rectangle local stress screen was withheld
there; the NDS bolted-connection allowance is the separate reduced-depth
comparison being evaluated. It does not establish a local wood stress peak.

Rows P comprise five knee/post and three front floor/post witnesses. They
are **conditional component exceedances**, not dismissible unavailable rows.
Rows R are four additional exceedances in the frozen global point-action
scope, retaining the local replay/allocation limit. Rows Z are nine edge
hypotheses and do not establish nine additional actual-edge failures.
The six normal-duration-only exceedances are five zero-edge hypotheses and
one additional top-rail allocation-limited row (`a12-forward`, left outer
pair; CD1 index 1.062952687, CD1.25 index 0.850362150).

The remaining full-joint obligations, true oblique/edge/support limitations,
eight guarded receiver joins and conditional material/duration basis remain.
No capacity, force, gap, stiffness, geometry or hardware was changed to
remove an exceedance. These results stop a blanket reduced-depth pass under
the current simple model; they do not select a hardware remedy or demonstrate
physical fracture. Parent integration should preserve the eight available
post exceedances, four rail allocation limits and nine edge hypotheses as
distinct evidence, alongside the other joint duties. Only this completion
MD was annotated; the producer, map and numerical raw remain frozen.
