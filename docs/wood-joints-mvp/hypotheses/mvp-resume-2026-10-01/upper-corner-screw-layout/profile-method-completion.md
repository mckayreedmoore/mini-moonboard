# N07 and N19 profile method completion

The parent's serialized [Attempt 02](rawlocal/profile-method-completion/attempt02/checks.json)
completed with exit 0 and a frozen receipt. Its 179 authenticated sources
support **1,248 finite profile cuts and 2,496 duration records**, with zero
reference exceedances. The deep-recess notch method, terminal sections and
exact finished compliance retain the specific limits below; complete joint
acceptance and release remain false.

The [producer](profile-method-completion.py) has inert import and standard-library
`prepare(output)` authentication; `build(output)` remains parent-only.
This worker performed source/receipt joins, preparation, AST parsing and Ruff,
and annotated the parent's saved result. It performed no numerical engineering
build, native run, frame solve, CAD, coupon, software test or review loop.

The scope is the **unadopted 108-axis proposal**, with 50 bodies, 44 timber
blanks, 24 blocks and 66 Hillman axes. The reviewed 104-axis basis remains
separate. Actions retain **250 lb × 2, signed 300 N, the original 100 mm hold
lever, gravity and the proportional 25 kg allowance**. The fresh modeled mass
is 225.19791414318078 kg and dead factor is 1.1110134616260479. Geometry,
hardware, loads, stiffness, material, duration hypotheses, authority and
release flags are unchanged.

## Actual surviving cuts and supported comparisons

There are two surviving lower rear-leg side recesses with continuous **1:12
runouts**. Each removes 38.1 mm from the 88.9 mm section_u dimension, leaving
50.8 mm through the fully recessed foot. The run is 457.2000000015126 mm.
The absolute grain limits are -211.85354460811698 and 245.34645539339562 mm;
the saved member-local limits are 180.34266111706836 and
637.542661118581 mm. These are different station datums for the same cut.

The frozen outward faces and cut recipes identify **no additional current
square shoulder notch**. The historical tabbed knee parts are absent. Current
principals and side rims retain convex level/plumb end trims; runners and leg
tops retain their recorded planar end trims. Removing the historical square
notch from the current inventory does not pass `base_end_notch_shear`: terminal
load introduction still needs an applicable local shear method.

The producer checks saved face normals and finite grain intervals, excludes
single-circle blind-bore caps from the external profile, and stops if an
unresolved interior square shoulder appears. The two new spine STEP overlays
supersede bore identities only; the saved original spine outer-profile record
is labeled separately from the effective proposal STEP. Four corner
corrections likewise retain their actual effective STEP bindings.

Each leg has two 11.1125 mm bores in the fully recessed foot and two
14.2875 mm bores above the ramp. The exact saved local intervals are:

| Location | Member-local grain interval, mm |
| --- | --- |
| Lower bore 1 | 82.71323504836657–93.82573504836658 |
| Lower bore 2 | 118.51738957358725–129.62988957358726 |
| Upper bore 1 | 1800.589659570766–1814.8771595707658 |
| Upper bore 2 | 1847.7695546505643–1862.0570546505642 |

**No saved bore intersects the ramp or its runout.** That is an exact interval
comparison on these unchanged leg STEP descriptors. It permits the existing
unbored rectangle arithmetic at supported ramp slices; it does not establish
uniform torsion through a taper or bore/load-introduction resistance elsewhere.

The authenticated parent result retains the following partition across both
legs, from the foot through the ramp endpoint. Each station retains six cases
and both before/after limits.

| Saved section applicability | Stations | Signed limits | Parent disposition |
| --- | ---: | ---: | --- |
| Bore-free retained profile rectangle | 102 | 1,224 | Finite normal and signed shear/torsion references computed |
| Bore-free full rectangle at runout | 2 | 24 | Same finite references computed |
| Actual opening interval | 24 | 288 | Preserve actions; opening resistance belongs to Gibbs |
| Clipped end with point load interpretation | 12 | 144 | Preserve exact terminal method gap |
| Incomplete terminal profile | 2 | 24 | Preserve exact terminal method gap |
| **Total** | **142** | **1,704** | **1,248 finite nominal comparisons; 456 outside this arithmetic** |

Attempt 02 published **2,496 duration records**, 1,248 at each existing
C_D=1 and C_D=1.25 hypothesis. Each metric below has 1,248 finite records and
**zero exceedances** per scenario. These are finite nominal reference outcomes,
not complete recess, member or joint acceptance.

| Recorded maximum reference | C_D=1 | C_D=1.25 |
| --- | ---: | ---: |
| Normal reference sum | 0.14277214254210033 | 0.11421771403368028 |
| Compatible face peak / F'_v | 0.19601761113242763 | 0.1568140889059421 |
| Scalar shear bound / F'_v | 0.19784489735623426 | 0.1582759178849874 |
| Sufficient rectangle bound / F'_v | 0.19784489735623426 | 0.1582759178849874 |

The normal maximum occurs on the left leg in `a12-left`, before the saved
180.34266111703587 mm station. Both face and bound maxima occur on the left
leg in `a12-forward`, before 98.77331921575507 mm. Each of the four leg/taper
endpoint identities retains 24 finite duration records; the recorded endpoint
and saved station are joined at the existing geometry tolerance.

The remaining **456 signed limits** comprise **168 terminal traction method
gaps** and **288 opening limits owned by Gibbs**. They retain explicit
non-pass outcomes with no fabricated resistance. Parent Attempt 01 remains
serialization STOP evidence, with its complete raw cuts preserved.

The broader saved 42-body partition retains its 1,176 terminal signed limits
and 264 unmachined station-exclusion limits. Those totals overlap the current
partition where applicable and must not be added as disjoint new obligations.

## NDS applicability and the genuine notch method limit

The primary basis is **NDS 2024 §3.4.3.1 and §4.4.3.1**, with Figure 3D and
Figure 4B. Section 3.4.3.1 restricts its notch equations to permitted end cuts;
the tension-side taper route in §3.4.3.1(c) uses the rectangular tension-side
expression from §3.4.3.1(a):

`V_r = (2/3) F'_v b d_n (d_n/d)^2`.

This is the cubic retained-depth expression already used by the historical
`scripts/compact_thick_results.py:base_comparisons`; its historical forces and
support recipe are not reused. Section 4.4.3.1 limits tension and compression
side end tapers at end bearing to d/4. The taper reduces the square-corner
concentration but supplies no exception to the depth limit.
[Official NDS 2024 Chapter 3](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf),
[official NDS 2024 Chapter 4](https://web-media.awc.org/wp-content/uploads/2021/12/17210008/AWC_NDS2024_20241011_AWCWebsite_Chapter4.pdf).

If the side recess is mapped to weak-plane bending, the removed dimension is
the bending depth: **d=88.9, b=139.7, d_n=50.8 mm**. Removal is 3/7 of depth,
exceeding the **22.225 mm** quarter-depth limit by **15.875 mm**. The actual
floor contact is on the oblique grain foot at global Z=0, whereas Figure 3D
shows end bearing along a grain-parallel beam face. A support equivalence is
not supplied. Selecting the compression formula would leave both applicability
issues unresolved.

The output therefore reports **method-inapplicable**, with null notch
resistance and utilization. The exceeded permitted-cut depth is an
applicability boundary for this NDS formula; no current-recess notch resistance
failure is computed. Attempt 02 records
`INAPPLICABLE_PERMITTED_END_CUT_AND_SUPPORT_ROUTE` and leaves
`all_recess_strength_comparisons_complete=false`. It records the depth-limit
comparison and the formula's precise boundary. The missing basis is a
resistance relation for this recorded deep side recess with actual oblique end/contact loading and
simultaneous signed N, V_u, V_v, T, M_u and M_v, including bore and connection
effects. Fracture, splitting and anchorage remain the splitting peer's scope.
This is not a generic new-native-solve prerequisite.

The small-notch stiffness exception in §3.2.3.2 concerns depth no greater than
d/6 and length no greater than d/3. The deep recess and its 457.2 mm ramp do
not satisfy that exception. The producer neither uses it to qualify H nor
applies the older EC5/DF-L hybrid in `scripts/floor_taper_checks.py` as a new
AWC notch capacity. The existing coefficient-5 torsion alternative remains a
separate diagnostic, not the adopted signed rectangle method.
[Official NDS 2024 Chapter 3](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf).

## Reused arithmetic and load extraction

Parent `build` reuses the following existing functions without invoking their
producer, solve, coupon or review entry points:

- `member_screen.py:rectangle_at`, obtained through
  `top-host-net-sections.py:outer_rectangle_function`, interprets the frozen
  finite outward planes and refuses bored or terminal profiles. The exact
  saved applicability status must match the replayed status.
- `knee-bridge-remaining-sections.py:actions_for` restores fresh ce69/c3a8
  point actions and free couples, checks signed row ownership against D and
  response forces, binds mapped gravity/live load to W, and checks whole-body
  and opposed-half balance. Its original ownership guard remains unchanged;
  the private floor metadata adapter below supplies its expected physical
  force direction. Body weight enters once.
- `top-host-net-sections.py:global_cut` recovers each complete signed
  before/after cut and matches the fresh saved negative-grain array.
- `corner-net-section.py:nominal_section` uses the actual retained rectangle
  coordinates and translates the complete wrench to its centroid. It
  reconstructs the original signed force and moment, without dropping torque
  or adding a balancing couple.
- `knee-bridge-top-rail.py:duration_results` supplies the existing normal
  reference sum, evaluated signed face shear, scalar shear bound and
  sufficient rectangle bound. Material values and the two existing duration
  hypotheses are checked through `material_for`.

The elementary normal, isotropic rectangular torsion and face comparisons are
nominal stress references. They do not supply notch concentration, orthotropic
nonuniform taper torsion, continuous section maxima or fracture capacity.
Above-one sufficient bounds and evaluated-face exceedances remain distinct.
Every finite metric records its own same-state witness and outcome; an empty,
null, unsupported or uncomputed family never reports a pass.

### Restored floor constraint orientation

The pre-build inspection confirmed the same lost-orientation schema issue
reported by Gibbs. The compact floor metadata retains the positive constraint
axis but omits the saved `owner_point_rigid_row_sign=-1`. Both profile legs
are affected: left floor rows **1784–1791**, right rows **1792–1799**. They join
exactly to the authenticated original projection contract by row ID, source
group and source element; ownership points, roles, axes and laws match.

The new private adapter in this producer restores the contract orientation
for all **200 floor rows** in a copied action context. It does not modify the
saved compact row file, D, W, scalar response forces or any shared helper.
The physical first-body force direction expected by `actions_for` becomes
`saved_sign * source_constraint_axis`, retaining the original guard against
`-D`. The sign is recovered from the saved contract, never chosen from the
observed D row to make a comparison agree.

Before using that context, parent `build` independently checks every complete
floor D row. Its six first-body coefficients must equal
`saved_sign * [-axis, -cross(point-center, axis)/1000]` within 1e-8; all other
body coefficients must be below 1e-12. Finite coefficients, exact row identity
and body ordering are required. The unchanged `actions_for` then checks the
signed source forces and couples, W binding and body balance. These numerical
joins remain **unexecuted by this worker**. Preparation records
`full_D_join_executed=false`; Attempt 02 records the successful parent join as
true in `ownership-direction-map.json` and the result summary. All 200 floor
D rows were checked; the original signed ownership guard ran for both leg
action contexts. Source metadata remains unchanged.

The original **475084** producer snapshot and Preparation 02 receipt remain
byte-identical. Preparation 03 supersedes them only for the parent API with
the private schema adapter. Preparation 04 adds only the two explicit integer
counter conversions described below. All profile target counts, applicability
limits, fixed loads and geometry remain as recorded above.

## N19 native, profile and volume applicability

Existing source-mesh evidence supplies all **50 saved mesh volumes**. The
adapter `/gravity_load_audits/member_self_weight_rows` records actual mesh
volume and centroid; `/body_geometry` records the source profile recipe.
The pure-solid native model binds that adapter by source hash. Its 1,903
element records equal the fresh proposal's inherited physical connectivity.
Parent audit compares the corresponding node coordinates at the existing
1e-5 mm geometry tolerance; this is separate from exact equality.

For each leg the source native mesh is
`ACTUAL_STEP_DERIVED_1_TO_12_LEG_RECESS_C3D20`. Recorded filled-profile expected
volume is approximately **21,769,593.975688 mm³**. Saved source-mesh volumes are
**21,769,593.975638486 mm³** left and **21,769,593.975638494 mm³** right.
The approximately 0.000049 mm³ difference is within the existing 0.05 mm³
source geometry tolerance. This supports the saved **filled-bore outer
profile** comparison.

Each drilled STEP is approximately **21,731,234.240194 mm³**. The difference
is the explicit **38,359.73549377075 mm³** four-bore omission. Therefore
`taper_actual_mesh_volume` must identify which volume it compares; the drilled
STEP and filled mesh are not equal. The producer keeps expected recipe,
actual saved mesh, effective drilled volume and omitted bore volume separate,
and records finite native-node observations against every saved leg profile
plane. It claims neither an exact continuous finished-surface match nor exact
finished-hole H.

There are **six effective STEP bindings different from inherited native
descriptors**: both side hosts, both top outer cleats and both modified knee
spines. Current volumes come from the frozen four-corner correction and
two-spine proposal records, rather than silently retaining old descriptors.
The larger top cleat profiles are especially distinct from the original
native blank dimensions. Each audit row reports the signed current versus
inherited volume difference and the saved native versus effective finished
volume difference. A volume discrepancy is not automatically a bore-only
omission or a resistance failure.

The gravity source explicitly retains unchanged filled-bore gross H/D/B and
connector stiffness while updating gravity. Thus exact finished-hole/profile
compliance remains a bounded approximation. The 50 STEP inventory, unbored
runout, saved filled-profile volume agreement and finite nominal comparisons
cannot individually close `all_machining_represented` or complete joint
acceptance. Named omitted geometry and inapplicable sections remain visible;
no blanket native rerun is introduced.

Attempt 02 authenticated all 50 effective STEP bindings and joined the saved
native filled-profile evidence. Its N19 result explicitly retains
`exact_finished_geometry_and_H=false` and
`all_machining_represented_in_native=false`. The six changed bindings are
`base_side_left`, `base_side_right`, both `knee_outer_*_spine` bodies and both
`top_outer_*_cleat` bodies. Exact hole/profile omissions and sampled/terminal
method boundaries remain the named limits; the successful finite references
do not close those limits or introduce a blanket native prerequisite.

## Authentication, parent API and artifacts

[Preparation 04](rawlocal/profile-method-completion/preparation04/preparation.json)
and its [receipt](rawlocal/profile-method-completion/preparation04/receipt.json)
authenticate **179 sources** before and after standard-library preparation and
publication. Preparation 01 and the original 177-source Preparation 02 remain
preserved, together with Preparation 03 and its orientation-adapter snapshot.
The two pins added in Preparation 03 authenticate the original projection
contract and the original compliance input manifest binding that contract.

The parent completed Attempt 02 with the same 179-source closure and producer
snapshot. This document is absent from the consumed source manifests in its
preparation, checks and receipt; the annotation does not alter any pinned input.
All consumed sources and receipt-bound outputs were authenticated before this
annotation. Their frozen hashes remain unchanged afterward.

### Preserved Attempt 01 serialization STOP

The parent's actual `attempt01` stopped writing `checks.json` with
`TypeError: Object of type int64 is not JSON serializable`. Its partial JSON
ends at `comparison_summary/original_CD1/metrics/normal_reference_sum/exceedance_count`;
it has no receipt and is **not an accepted result**. Every existing file in
that attempt remains byte-identical, including its original producer snapshot
and complete compressed raw cuts: 1,704 cut records, comprising 1,248 finite
profile records, 288 Gibbs opening exclusions and 168 terminal method gaps,
with 2,496 saved duration records. No worker numerical replay was performed.

The producer changes only `summaries`' metric `exceedance_count` and the
endpoint `finite_signed_comparison_count` to explicit `int(sum(...))`.
NumPy boolean accumulation can return a NumPy integer; these two known count
fields now publish Python integers. Strict `json.dump(..., allow_nan=False)`
remains unchanged, with no generic serialization default or schema coercion.
Shared helpers, forces, ownership orientation, profile recipes and comparison
arithmetic are unchanged. The parent subsequently completed the fresh
`attempt02`; Attempt 01 remains preserved as STOP evidence.

| Source or leaf | SHA-256 |
| --- | --- |
| Current producer | `37d396d5cc447d9f95125af345b9a62a511aa33ee0de0387864a0c3d3bb540ed` |
| Actual Attempt 02 checks | `d619b34c02402963540b1b34696be0a09ba2fb339790b3aa7335f9e16d5a6d12` |
| Actual Attempt 02 receipt | `15236a2a44955ba63aba7075c491debee651a48dd083e4affb72cba07fedd36b` |
| Actual Attempt 02 complete raw cuts | `5cbcfb042f1b5b68d4b7c596eabe710a4142c2f932dbcf00252c3e1e9fd852d4` |
| Actual Attempt 02 geometry/method audit | `d900a86139604cbe278bd3b52774ef33bdfb468f4813778e6117d0a5414e78d5` |
| Actual Attempt 02 ownership direction map | `e37a2b006cc59c45f8e25d797e046dda601a742718de549f51b29d9021a98e72` |
| Actual Attempt 02 action audits | `bc7a055610bc5da1e0fcd42d83d35770e59063709f230745248384034e42fbd6` |
| Preparation 04 | `c5d6b689458e9f99883ea41b4fcf7e4d1510ad826fe7195ad307d2dcf43116cf` |
| Preparation 04 receipt | `d7d0bd87e384d4fa16bf6e4b2870e30f7db31da6088179b1a68258aac716d1f7` |
| Preserved Preparation 03 and Attempt 01 producer snapshot | `3e01d3a9f8e0d8d71f93b8be070f83d1461f15ff9f51a368b4815dc0148ad01b` |
| Preparation 03 | `cd923b0974db48cc851926e9329e1eaa82f887450e3ad8a79f1c36786e07a5c2` |
| Preparation 03 receipt | `91243d2afb186388063c18c6dc0ba64e138b956718edb62ac42262d7c99d81a7` |
| Preserved STOP Attempt 01 complete raw cuts | `3695f4f25c46e46e495dfc61f24394a1a177077554cfb6402af7f4977a9c63b3` |
| Preserved STOP Attempt 01 partial checks JSON | `5948524bc74832d91cf2d147694d273c3d0836f60e99c14cfaec22b13f82cebe` |
| Preserved Preparation 02 producer snapshot | `475084e82894de6df91c8b6709e2d0e975c101e16bd14f437c87e994d9db3cb7` |
| Preparation 02 | `f9392bc027bda24a8a8187df2e252361f5164cb2eccfddeeaecd94f863441c27` |
| Preparation 02 receipt | `d662cb3b5476537a0f47722153ccde3fa9e881ec2a9b4e56c34eb48291778e8c` |
| Original projection ownership contract | `4ceca771e26e1f1d0bf8efca8e3d77dc6d94194553d95e1fd75652ecf2f3f2d3` |
| Original compliance inputs | `3d17f953df265035e95fdb3543e19eb0f7505d81778067f28783e4bb9b0b3208` |
| Unchanged fresh compact row identities | `cdf218780bdabdb8774174c79b37d7c9f554abc6be2e1f817999635e56868b27` |
| Unchanged signed action helper | `e2a08ca075fdb397696889d22d8cbbfb30d83a3d4bb5e3af1726574c38ca2e15` |
| Fresh gravity assessment | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| Fresh signed frame comparison | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| Fresh signed frame response | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| Saved fresh action/cut arrays | `3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596` |
| Saved fresh member extraction | `5178d1a246aa04044429c1c2bc81709214ae9abd713313d07a949a2848de3dd0` |
| Saved current profile geometry | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| Finished surface register | `33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb` |
| Effective 108 package | `4c0d10a86a6018813b5f8efcd7f438662037e458ef3f2ce535d1e0860ca25bd0` |
| Saved native source adapter | `61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8` |
| Pure-solid native mesh model | `89354d05f089c6eb8de3b90891ccadd547d18c89ba4faaa30b86c7366af217dc` |
| Left unchanged leg STEP | `1416e3aec21eea2993542f8266649ebe0aec50b3ec6444f445f18f88cbffa065` |
| Right unchanged leg STEP | `e346646efb8bdf9c03d45dfa024900622abcd65fe0d58bf11c6dcd3735bedff4` |
| Official NDS 2024 Chapter 3 | `205df74e16f632dfe78211e99bfa5dfa8b9f8dd316e9c5fa1316493f795ec644` |
| Official NDS 2024 Chapter 4 | `52feedd07d3b672f0dd2666903cf8b481687d3da975cd3fccac545f66dfeb9ec` |

The complete source manifest includes exact paths and hashes for all helpers,
source artifacts, effective 50 STEP bindings and original native provenance.
Any changed source, conflicting pin, lost binding or changed output stops
publication. A changed receipt is never repinned. Outputs must be fresh
immediate children of the owned ignored folder; the `sources` directory and
existing attempts are refused before source consumption.

The parent's completed finite arithmetic command, recorded for provenance:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/profile-method-completion.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/profile-method-completion/attempt02
```

The completed output is immutable and the producer refuses existing attempts.
The API accepts `--prepare` with a fresh output for source-only authentication.
Neither API invokes any preserved producer pipeline. `build` returns the
`checks.json` dictionary and writes:

- `geometry-method-audit.json`: current profile identity, historical recipe
  disposition, all 50 geometry/native volume joins, explicit omissions,
  sampled leg planes, bore/runout applicability and NDS depth/support gaps.
- `cuts.jsonl.gz`: all 1,704 complete signed limits, 2,496 supported duration
  records, retained centroids, normal corners, torque, signed face vectors and
  explicit peer-owned or method-inapplicable outcomes.
- `checks.json`: finite metric counts and maxima, exceedance witnesses,
  exact excluded cut identities, endpoint coverage and remaining N07/N19
  limits. No notch, inventory or null-output pass is manufactured.
- `ownership-direction-map.json`: all 200 authenticated floor orientation
  mappings, the 16 profile-leg row indices and successful parent full D join.
- `action-audits.json`, `preparation.json`, producer snapshot and `receipt.json`:
  source/load identity, implementation bytes and output hashes.

The next action is parent publication and result integration. N07's finite
profile comparison arithmetic is complete; its deep-recess/support method gap
and terminal traction gap remain. N19 retains exact finished compliance and machining
omissions. Gibbs owns actual opening strength and the splitting peer owns
fracture/anchorage. A separate read-only GPT6.1 Sol investigation supplied the
official source URLs and notch applicability facts; it wrote no files and
performed no review loop.

Only this producer, this document and the owned ignored raw folder belong to
this task. They remain active inputs. The two official PDF copies total about
1.9 MB and stay ignored, recoverable from the pinned official URLs. Existing
geometry, source/native evidence and all raw attempts remain active references;
nothing is pruned, archived or repacked. Foreign tracked/untracked work is
preserved. Parent owns staging, commits and release authority.
