# N15 lower-panel and kicker load paths

**The parent completed the frozen saved-path assessment; complete load-path
resistance remains partial.** The [producer](kicker-path-completion.py) completed
`rawlocal/kicker-path-completion/parent-attempt01` with exit 0 and status
`COMPLETE_SAVED_PATH_ASSESSMENT_WITH_EXPLICIT_RESISTANCE_LIMITS`. The parent
independently authenticated all 94 source bindings and 13 output artifacts.
The result contains 396 simultaneous screw states, 300 body balances, 240
panel/receiver group states, 264 receiver/case states for all 44 timbers, 1,140
bearing states and four exact edge recipes. Counts, bore matches and balanced
actions establish the stated accounting, without supplying missing resistance.
The preceding standard-library preparation remains preserved in
`rawlocal/kicker-path-completion/prepare02`.

The [qualification register](qualification-register.md) assigns N15 to both
inner kicker edges and the current receiver/backer paths. The
[edge obligation](../../../current-kicker-edge-obligation.md) does not adopt
continuous direct backing as a criterion. The reviewed 104-axis basis and the
unadopted 108-axis knee-bridge proposal remain separate. These fresh forces
belong to the proposal. Four same-spine internal ties are absent from its
104-axis global receiver rows; their separate STEP overrides are preserved in
the cut-authority leaf, without transferring their local resistance.

## Actual receivers and connection routes

Preparation joins 62 frozen finite bore-patch records and four exact saved
post-move cylinder-intersection records. There are 16 distinct timber screw
receivers. The eight earlier moves remain in the map: four lower-edge screws
enter the raised bottom rails and four kicker-center screws enter the moved
center posts. Four later upper-row moves use their separate saved geometry
checks. A retained original bore on a corrected member is explicitly joined to
the current geometry recipe; it is not presented as an unchanged whole STEP.

There are 48 main-panel screws and **18 kicker screws total, nine per kicker**.
The source occupied-length field of 50.8 mm, modeled cylinder interval and
purchased nominal 63.5 mm length retain separate meanings. None measures
delivered thread engagement. The removed `inner_kicker_backer_left/right`
members and their old backer-header bolts supply no current receiver path.

| Panel group, on both sides | Actual timber receiver | Existing onward interfaces retained by the producer |
| --- | --- | --- |
| Five `kicker_header_*` screws per side | `base_header` | All signed header contact, lateral-bolt and outer-seat axial groups into posts, cleats, principals and sides. |
| Two `round_kicker_*_center_*` screws per side | `base_post_center_*` | Distinct direct post/header compression seat; two `center_post_*_1/2` post/cleat bolts and contact; two `center_post_header_*_1/2` cleat/header bolts and contact; existing assumed no-slip floor rows. |
| Two `round_kicker_*_rim_*` screws per side | `base_post_outer_*` | Knee-spine bolts/contact, retained front runner bolts/contact, header seat and existing floor rows. |
| Two moved `round_panel_lower_*_edge_*` screws per side | `base_rail_bottom_*` | Two bolts and contact into each bottom center/outer cleat; separate rail/principal and rail/side contact; cleat connections onward into those frame members. |
| Remaining lower-panel center, rim and service-row groups | Current center principals, sides and lower service rails | Their actual incident bolt, seat and contact rows, continued through all 44 timber bodies to the saved frame/floor interfaces. |

These are named source routes, not resistance inferred from adjacency. The
completed parent result retains each receiver's complete signed six-component actions
and records missing complete connection resistance explicitly. The direct
post/header seat and post/cleat/header route are evaluated simultaneously; the
same kicker demand is not applied to both as an additional load.

For example, in the saved A12-rear state the direct header seat contributes
zero wrench on `base_post_center_left`, while its right counterpart contributes
`Fz = -59.25253512911381 N` on `base_post_center_right`. The left and right
post/cleat axial and contact groups remain separately recorded, along with
their free couples and the existing floor rows. These are complete-body
simultaneous actions; the seat force is not an isolated allocation of the
kicker group or evidence that the other route has spare resistance.

The same state's combined screw/contact group forces **on the panels** are
shown below. All six components about the global origin, separate screw and
contact wrenches, and reciprocal receiver actions remain in the saved leaves.
Displayed forces are rounded to six decimals; they are examples, not envelopes.

| Panel / receiver | Saved panel-side `(Fx, Fy, Fz)`, N | Canonical screw rows | Canonical contact rows |
| --- | --- | --- | --- |
| `kicker_left` / `base_post_center_left` | `(28.005911, 89.468705, 256.746155)` | 220–223, 1448–1449 | 484–489 |
| `kicker_right` / `base_post_center_right` | `(10.239976, 90.423436, 236.266898)` | 228–231, 1452–1453 | 494–499 |
| `main_lower_left` / `base_rail_bottom_left` | `(83.537665, -2.643890, -46.511610)` | 244–247, 1460–1461 | 704–725 |

## Parent arithmetic and accounting

`prepare(output)` uses only standard-library JSON, hashing and AST inspection.
Import reads no source files and imports no numerical packages. Output must
be a fresh immediate child of the owned ignored raw directory. `build(output)`
imports NumPy only when called and consumes the frozen saved nominal arrays.
It calls no frame, CAD, native, coupon, software-test or historical producer
pipeline. Parent owns its execution, staging and commits.

The following is the recorded, already completed parent invocation. Preserve
its existing output; no duplicate run is requested.

```bash
uv run python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/kicker-path-completion.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/kicker-path-completion/parent-attempt01
```

Each raw row is written once per case in `signed-rows.jsonl`, identified by
case and numeric row index. Some component row names are duplicated in the
source, so row names alone cannot identify an action. Full `D` projection
recovers forces and moments on both incident bodies. Free couples are retained
after subtracting the point-force moment. Both sides must be reciprocal about
the same global origin. All 300 saved body/case states balanced their matching
fresh `W` loads within the existing 0.1 N / 2 N mm limits. No new force allocation
was supplied. Parent runtime was Python 3.12.3 / NumPy 2.5.2.

The 396 `screw-wrenches.json` records reproduced the separately saved
axial and simultaneous lateral screw forces. `panel-receiver-groups.json`
includes all incident contacts, including receiver pairs without screws and
panel/panel interfaces. Screw and contact wrenches remain separate, with their
combined same-state wrench also recorded. All receiver connection views refer
to the canonical raw rows; they are not extra applied loads.

`receiver-connections.json` continues through every timber body and joins the
existing fresh [member references](knee-bridge-members.md). The 42 unchanged
timbers retain their finite CD1 and conditional CD1.25 comparisons, station
and method applicability, opening exclusions and restraint limits. The two
modified spines do not inherit those references. Their existing separate
proposal work remains a distinct connection/member scope.

`contact-bearing.json` reuses the actual perpendicular-grain bearing
expression in `scripts/floor_flush_checks.py`: compression divided by active
represented area and the unchanged conditional 625 psi DF-L reference.
Positive saved contact-cell forces define the represented active area. A
perpendicular mean is recorded only when the signed face normal is
perpendicular to the saved receiver grain. Inactive, parallel and oblique
faces retain explicit null comparisons. No duration multiplier is applied to
perpendicular bearing. Plywood bearing, pressure peaks and local edge
fracture are not supplied by that timber mean.

Of the 1,140 bearing states, 813 have finite conditional perpendicular means,
219 have no active area, and 108 retain
`PARALLEL_OR_OBLIQUE_METHOD_NOT_SUPPLIED`. Every finite mean is below one.
The maximum saved ratio is `0.21552626107373865` at `base_side_right` against
`base_rail_top`, K12-rear, face identity `81`, raw rows 900–903, with
`1235.8352701039835 N` over `1330.6425000098448 mm²` represented active area.
This is a timber mean reference comparison only. The inactive and unsupported
states are not counted as resistance passes, and complete connection resistance
remains null in the receiver records.

N14 separately owns screw head pull-through, withdrawal, lateral/steel
interaction, plywood bending and compatible contact sharing. This producer
does not import its files or recompute its comparisons.

## Exact geometry and cut authority

[Current selected authority](../../../../../current-candidate.json) points to
the [kerf-right shop packet](../../../../floor-flush-construction-kerf-right/)
for 4×8 rips. The wood-joint candidate uses its own reviewed geometry and
recorded screw moves. The selected packet supplies cut outlines; its original
angle-frame passes are not wood-joint acceptance.

`cut-authority.json` preserves both kerf-right and official full-width cut
records and the separate proposal spine STEP overrides. It does not substitute
an alternate outline into the saved current response. The full-width
alternative lacks a matching current wood-joint support/receiver mechanism
and same-configuration six-case actions; its result is explicitly null.

`edge-support.json`, produced only by the parent build, derives the two inner
kicker backface edges from the exact seam boundary recipe. It derives each
lower-panel bottom backface edge from the corresponding exact seam and
outer-side contact boundaries. Support is clipped against coplanar finite
straight outer loops, subtracting full circular holes. AABB overlap, convex
hulls, whole-face area alone and the old three-point backer screen are not
used as support. Unsupported boundary curves remain null.

Each edge has covered intervals and gaps, plus a separate inward 19.05 mm
probe. That offset is a geometric diagnostic, not a criterion or a member
change; two probe lines do not prove full two-dimensional strip support.
Potential backing is distinct from active signed contact. Panel/panel seam
contact and zero-area cleat tangencies are not counted as direct timber
backing. The producer also reports the exact seam-to-center-post boundary
gap, for N14's panel transfer assessment. Existing geometry records describe
the same gaps; the completed exact recipes report **141.0725 mm left and
142.8875 mm right** from seam X `-1.5875 mm` to the respective center-post inner
face boundaries X `-142.66 / 141.3 mm`. Both post faces span Z `0–238.9 mm`.

The two boundary probes report the following direct potential backing. Lower
panel stations run from the outer edge toward the seam; kicker stations are
global Z from the bottom. The 0 and 19.05 mm probes have the same intervals
within each row. Values below are rounded only for display.

| Current edge | Exact receiver-boundary coverage, mm | Intervals without direct timber backing on the probes, mm |
| --- | --- | --- |
| Lower left bottom backface, length 1217.6125 | Side `[0, 88.9]`; center principal `[1130.15, 1168.25]` | `[88.9, 1130.15]`, `[1168.25, 1217.6125]` |
| Lower right bottom backface, length 1217.6125 | Side `[0, 88.9]`; center principal `[1126.975, 1165.075]` | `[88.9, 1126.975]`, `[1165.075, 1217.6125]` |
| Left inner kicker backface, length 277 | Header `[238.9, 277]` | `[0, 238.9]` |
| Right inner kicker backface, length 277 | Header `[238.9, 277]` | `[0, 238.9]` |

No boundary recipe was unsupported for these four reported edges. Their
`complete_support_result` and `panel_bending_or_seam_resistance` remain null.
Two boundary probes do not establish full-strip support or a failure, and do
not create a seam or continuous-backing criterion. The current kerf-right
whole-kicker outlines and hardware remain unchanged. The missing mechanical
question is the existing panel transfer through its actual screws and contact
interfaces over these recorded distances, within N14's supported panel method.

## Frozen sources and preparation leaves

Paths beginning `rawlocal/` are relative to this directory. All SHA values
below are SHA-256. Preparation authenticates 94 consumed leaves and saved
output bindings before and after writing. Frozen upstream source maps are
preserved as lineage; unused shop prose ancestry is not replayed. This avoids
treating later edits to `assembly-package/hardware-engagement.md` as a change
to the consumed saved force/geometry arrays.

| Source | Exact SHA-256 |
| --- | --- |
| Fresh gravity `rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| Fresh six-case `rawlocal/knee-bridge-frame/attempt02/response/comparison.json` | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| Matching `response.npz` | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| Fresh saved screw leaf `rawlocal/knee-bridge-working-package/attempt02/panel-actions.jsonl` | `180fd06af021ea79fea9d694a7e4e8ecc13c6753bb6bf56e87df6a622847c3fb` |
| Fresh member reference `rawlocal/knee-bridge-members/attempt01/checks.json` | `0d623eb62605ddac9aa5111e2469a1c63f4857e356fe607741fc425d5ea59e65` |
| Saved exact contact recipes `mvp-acceleration-2026-09-28/reduced-static-attempt01/contact-geometry.json`, relative to the hypotheses directory | `034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151` |
| Current member geometry `../member-screen-attempt02/knee-bridge-gravity01/geometry.json` | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| Current receiver feature register `current-finished-feature-register-2026-10-01/axis-features.json`, relative to the hypotheses directory | `bebb4274cdecfb6ad0b0f26850d85a16570c245ea9f7d478c0b05c12b4513e19` |
| Kerf-right `stock-profiles.json` | `65a4301c639a6eff14cb4365f321d4ab4712746dd3c916ffc14b00645841dfa8` |
| Official alternate `stock-profiles.json` | `8d02e22de871e04a20e25f253639f360ac974aa71824a40986e0e2a317dfca3d` |

The completed preparation uses producer SHA
`a1483fc420f463d0b5b692b231258c904f849b696851b7b3e227efa30b4256ff`.

| Leaf under `rawlocal/kicker-path-completion/prepare02/` | Exact SHA-256 |
| --- | --- |
| `report.json` | `db9ac0208f270b68cd3eafa05d730df98c8d482a58ea484a404325d63dd6a5e9` |
| `receipt.json` | `4f6119c1ad68d2a1820e214b42b58c5ffc3937c945dbeca8b80907ad43156e6e` |
| `backing-identities.json` | `d6f14bc296a86e24731dd92f6ff14c22a5f5bc07deb00b42af3f2fff6370a95a` |
| `saved-screw-states.json` | `a9b4ec4019627ebb7f6d86f06daebcf4eec7995fb5fee11b6f30f9c936195d9e` |
| `saved-member-reference-join.json` | `35c303a0ae9cc88a1c6bf599ccb7da8f467ed6bfe40cf2651de5c3f420a371e1` |
| `cut-authority.json` | `40a5c33fb3dc586da2a63b487050f24fe80919f2917dbd6c89abfee28732acbc` |

The completed parent receipt is
`c589a8227000b2afe9ac536cbb7b99e4000f7b6e8b1024066a7e8b43109da402`.
Its producer and the shared backing, cut-authority, saved screw and saved
member leaves retain the exact preparation hashes above. Its remaining
output identities are:

| Leaf under `rawlocal/kicker-path-completion/parent-attempt01/` | Exact SHA-256 |
| --- | --- |
| `report.json` | `ed568d974c649e052cdde4c604482c23e611900cea7314f26e9426192a1f03e8` |
| `signed-rows.jsonl` | `fdee4ed9332a3b70c0ea434790a23fb7b318516f27971356fafd07f7ca008878` |
| `screw-wrenches.json` | `91d059297c106815030513f3b82e8fccb6fa8e6b6507730d13804cec3b3f3a6b` |
| `panel-receiver-groups.json` | `07e1467ab7ea46516b71dbda221f964f3de22fa2b345e22039a266d654f07118` |
| `receiver-connections.json` | `fd6fb6bdf345f642ac61f8e9820a8b8cff38039b08d7bc120bff5dc0b70dec81` |
| `body-balances.json` | `753679d69ed192eeee475811746852032bff5c49af23ff9f4bec481fa17483ad` |
| `contact-bearing.json` | `e6d71fdd4355c001a6dcf8ce6a5288e4b68c6bdfe4975cae46be13c37b322dea` |
| `edge-support.json` | `73d2362829e0dc4e0f5edaad70ac136507234567fa51a27e327de09b8d6cf301` |

AST parsing and Ruff passed before the parent build. This annotation changed
only this owned document; the producer and all saved leaves remain frozen.
No duplicate arithmetic, tests, coupons, CAD/native execution or review was
performed during annotation. The parent result and preparation leaves stay
active as evidence; `prepare01` preserves the earlier preparation. No raw
output, temporary input, foreign work or history was pruned.

The narrowly missing continuation is to join N14's supported lower-panel and
whole-kicker transfer comparisons to these same-case canonical screw/contact
groups and exact boundary distances, then supply applicable resistance for
the genuinely unsupported receiver modes. The 108 active parallel/oblique
bearing states, local opening/edge and complete receiver-joint resistance,
and separate proposal spine compatibility retain their declared method limits.
The 219 inactive-area states do not create an additional resistance obligation.
The alternate full-width mechanism remains unavailable; selected angle-frame
passes cannot supply it. No new model, hardware, seam/support criterion or
engineering run is requested by this continuation. All formal obligations and
authority/release flags remain unchanged. This annotated packet is frozen for
parent publication.
