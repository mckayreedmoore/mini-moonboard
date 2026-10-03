# N08 remaining finished-opening arithmetic

## Executed parent API

The parent ran attempt 01 from source
`0aebc68c403301e673336d9ce3bc18b9e00072ecb485897c07503e23bc263d83`.
It stopped at the original action helper's ownership-sign guard before a
completed comparison. That attempt and its exact producer snapshot remain
preserved. The parent then executed attempt 02 from the repaired, frozen
producer `5db858b30a69f393f46b493bc06c46ca2b786e85ed4ac520475d29cf51b25e62`.
It exited 0 with status
`COMPLETE_SUPPORTED_ARITHMETIC_WITH_EXPLICIT_INAPPLICABLE_TARGETS`.
The [actual checks](rawlocal/member-opening-remainder/attempt02/checks.json)
report **582 supported stations / 6,984 finite signed limits**, and
**278 method-inapplicable stations / 3,336 signed limits**. All ten reference
metrics are at or below 1.0 at every supported cut in both duration scenarios.
Inapplicable cuts do not receive a strength pass.

The [producer](member-opening-remainder.py) provides parent-run
`build(output)`. Import is inert. `--prepare` performs only standard-library
authentication and identity joins. This agent has not imported its numerical
helpers or executed geometry or strength arithmetic.

Runtime preparation used **Python 3.12.3**, with **NumPy 2.5.2** installed.
Numerical elapsed time is not recorded here. The executed workload was 860
stations, 10,320 simultaneous signed limits and 20,640 duration records:
**13,968 finite supported records** and **6,672 explicit inapplicable records**.
Unsupported stations retain signed-cut records and inapplicable outcomes.

The parent executed this command from the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/member-opening-remainder.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/member-opening-remainder/attempt02
```

For reproduction, the output must be a new immediate child of the owned
ignored directory; the completed `attempt02` cannot be reused. Existing
attempts are refused. The API returns the `checks.json` dictionary.
No helper producer, solve, coupon, CAD, test or review entry point is called.

## Source authentication

[Preparation 03](rawlocal/member-opening-remainder/preparation03/preparation.json)
and its [receipt](rawlocal/member-opening-remainder/preparation03/receipt.json)
authenticate **153 sources**, including the new producer. All pins matched
before and after the standard-library preparation and output writes.
Preparations 01 and 02 remain preserved as earlier implementation snapshots.
The actual attempt 02 [receipt](rawlocal/member-opening-remainder/attempt02/receipt.json)
binds the same **153 source pins and eight outputs**. All source and output
hashes were independently matched after completion and before this annotation.

| Source or prepared artifact | SHA-256 |
| --- | --- |
| Repaired remainder producer | `5db858b30a69f393f46b493bc06c46ca2b786e85ed4ac520475d29cf51b25e62` |
| Actual attempt 02 checks | `b328e9c19bd001bf542e79399f5b15f7b67c595e37d18ff035a9e13d177ae163` |
| Actual attempt 02 receipt | `db5a48bc43ab7d953da9fa57df99ddac507dfe0b389f0d1907c5c946a93e6931` |
| Preparation 03 | `0240736a9bc1b6129d6a41b4994a331f6c65389855c7e4f35f72eea66748ecb1` |
| Preparation 03 receipt | `7559d205ac6fd22ef6f3c4b4ebf836ef47b469c2053fca21c0ac1addb932d191` |
| Original projection contract | `4ceca771e26e1f1d0bf8efca8e3d77dc6d94194553d95e1fd75652ecf2f3f2d3` |
| Original compliance inputs binding that contract | `3d17f953df265035e95fdb3543e19eb0f7505d81778067f28783e4bb9b0b3208` |
| Frozen coverage ledger | `a9dc39d5dbd153c7928923caf79dcf678e653c0b707a35514e1177c8bd4337b2` |
| Current gravity assessment | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| Current frame comparison | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| Current frame response | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| Saved member geometry | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| Saved action/cut arrays | `3be032470253e872690637b09566076256374071adfe7d057ed4d329debef596` |
| Finished surface register | `33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb` |

The frozen `knee-bridge-members.py` supplies source pins, authentication and
receipt utilities. The saved fresh extraction supplies its provenance closure
and the current gravity operator outputs. Each of the 18 finished STEP
identities must agree with the saved surface register.

The remainder producer consumes no refresh producer, helper or result. This
document joins the separately accepted refresh attempt 02 only for coverage
accounting. Its [checks](rawlocal/member-opening-refresh/attempt02/checks.json)
have SHA-256 `40beca5a3a5863612a0fadcee4b259f1edacf55f9c58035bc058918c1d64f7e8`;
its [receipt](rawlocal/member-opening-refresh/attempt02/receipt.json) has
SHA-256 `1b31e5582c67c5374bbabcfbbd179957aea976701fbb991f41a0268084d3d694`.
Those hashes match the saved accepted packet. Historical source-104 forces
and numerical passes do not enter remainder demands.

Build authenticates before the numerical context, after recipe construction,
after arithmetic and after result/receipt writes. The numerical context must
use exactly the prepared closure. A conflicting hash or lost feature identity
stops execution. Output hashes are rechecked after receipt write.

## Attempt 01 STOP and private ownership adapter

The first offending action is `base_floor_left`, case `a12-rear`, saved point
index 66, current row **1600**, row ID
`floor_base_floor_left_0_friction/local-dof-2`, group `SPR1024`, element 2927.
Its role is `assumed_no_slip_floor`, with first body `base_floor_left`, second
body `floor`, and point `[-1228.725, 1592.1663124356317, 0]` mm. The scalar force
in that case is zero; the guard independently checks its unit direction.

The compact row metadata stores the geometric constraint axis `[0,1,0]`.
The actual negative D translational row is `[0,-1,0]` within roundoff. The
helper expects its direction field to mean physical force on the first body
per unit scalar reaction, so raw compact metadata violates that helper schema
for this row family. Private context had passed compact rows directly.

The frozen projection contract records the arbitrary orientation separately:
`owner_point_rigid_row_sign=-1` for all 200 floor tangent constraints.
Its owner-point row uses `(-axis on first, +axis on second)`; hence physical
restoring action `-D^T f` has force direction `sign * axis` on the first body.
The compliance producer preserves sparse rows but omits that sign when
emitting compact `row-identities.json`. Current corner/gravity operators
retain those floor rows. This adapts metadata semantics without changing a
constraint, scalar force or load.

`floor_direction_metadata` joins all 200 current rows to the frozen contract
by row ID, source group and element. Original ownership, point, law and role
must match exactly; the contract hash is independently bound by preserved
compliance inputs. It never selects a sign to fit observed D.

At parent execution, `private_action_rows` validates every corresponding full
six-component D row against the recorded sign, axis, current body-node mean
and point moment arm, using the existing 1000 mm rotational-coordinate scale.
All other body columns must be zero. It then supplies a private copy whose
direction field has the helper's expected force-direction semantics. The
original constraint axis and recorded sign remain in the mapping audit.

The original `actions_for` sign guard and full D/action force-moment guard
remain active and unchanged. Source rows, source geometry, D/W operators,
scalar force keys and values, body weights, case labels and load roles remain
unchanged. Non-floor rows retain original directions. Build writes
`ownership-direction-map.json` and binds this adapter in its action audit.

Worker diagnosis inspected saved coefficients and metadata only. The repaired
adapter's numerical D validation and strength build have not been executed
by this agent. Parent attempt 02 executed those guards and completed the
supported arithmetic; its saved mapping and action audits retain the bindings.

## Finite coverage partition

The [frozen coverage audit](member-opening-coverage.md) identifies 1,162
unfinished finished-opening stations: **13,944 signed traces**. The separate
accepted first refresh completed 1,008 four-cleat limits and 312 side-host
limits, **1,320 unique limits** in total, with 1,632 finite duration records
and no reference exceedances. Their removal leaves **12,624** finished-opening
limits before this remainder result.

This assignment targets **10,320** of those limits on the remaining 18 frame
members. The other **2,304** are remaining side-host limits outside this
assignment. The two side hosts and all four corner cleats are excluded from
this producer. No target overlaps the first refresh or an existing fresh
comparison in the audit.

| Frame body | Opening stations | Target signed limits | Finite supported limits | Inapplicable limits |
| --- | ---: | ---: | ---: | ---: |
| `base_floor_left` | 26 | 312 | 312 | 0 |
| `base_floor_right` | 26 | 312 | 312 | 0 |
| `base_header` | 78 | 936 | 312 | 624 |
| `base_post_center_left` | 24 | 288 | 120 | 168 |
| `base_post_center_right` | 24 | 288 | 120 | 168 |
| `base_post_outer_left` | 36 | 432 | 300 | 132 |
| `base_post_outer_right` | 36 | 432 | 300 | 132 |
| `base_principal_center_left` | 101 | 1,212 | 636 | 576 |
| `base_principal_center_right` | 103 | 1,236 | 660 | 576 |
| `base_rail_bottom_left` | 57 | 684 | 564 | 120 |
| `base_rail_bottom_right` | 50 | 600 | 480 | 120 |
| `base_rail_service_lower_left` | 57 | 684 | 564 | 120 |
| `base_rail_service_lower_right` | 50 | 600 | 480 | 120 |
| `base_rail_service_upper_left` | 57 | 684 | 564 | 120 |
| `base_rail_service_upper_right` | 50 | 600 | 480 | 120 |
| `base_rail_top` | 31 | 372 | 132 | 240 |
| `lumber_leg_left` | 27 | 324 | 324 | 0 |
| `lumber_leg_right` | 27 | 324 | 324 | 0 |
| **Total** | **860** | **10,320** | **6,984** | **3,336** |

Every target retains its actual feature IDs, station index, station value,
six case IDs and two saved trace indices. The 264 unmachined exclusion traces
and 1,176 original terminal method-inapplicable traces remain separate.
The finite and inapplicable columns count each unique signed limit once;
the two duration scenarios do not double the coverage count.

## Supported recipes and real arithmetic

`build` constructs and records a recipe for each of the 860 stations. Exact
through-slot recipes require all overlapping openings to be represented;
unsupported overlapping voids cannot be silently dropped.

1. The existing `member_screen.py:rectangle_at` definition, loaded through
   `top-host-net-sections.py:outer_rectangle_function`, supplies the finite
   outward-plane interpretation. Circular blind-bore cap planes are interior
   boundaries and are excluded from the outer timber profile. The helper's
   original clipped-end and source-bound rear-recess restrictions remain.
2. Each active cylindrical feature must be bore-like, transverse and aligned
   with one cut-section axis. Its saved angular span and wall area must
   support a whole cylindrical wall. Radius and grain bounds must match the
   saved opening interval. Its actual shaft ends must match both sides of
   the finished profile at this station.
3. The existing `corner-timber-sections.py:section` and `retained` functions
   subtract the exact circular chord strips, including overlapping strips
   and perpendicular slot unions. Profile offsets are retained in the region
   coordinates. No artificial subdivision of connected material or gross
   rectangle fallback supplies resistance.
4. `knee-bridge-remaining-sections.py:actions_for` binds complete fresh member
   actions to ce69/c3a8 response rows and D/W operators. It checks source
   ownership, signed row forces, all free couples, mapped gravity/live loads,
   whole-body balance and opposed-half balance. Body weight is used once.
5. `top-host-net-sections.py:global_cut` reconstructs every complete signed
   before/after cut and matches the fresh saved negative-grain array.
   `corner-net-section.py:nominal_section` recovers that full signed wrench
   after regional centroid translations.
6. `knee-bridge-top-rail.py:duration_results` supplies the existing normal,
   shear/torsion and signed rectangle-face comparisons at original C_D=1
   and the existing C_D=1.25 scenario. Material references retain each body's
   original CF recipe, checked against the pinned material inputs.

The source's 1e-6 mm before/after point partition is retained. A zero chord at
an authenticated bore tangent is recorded explicitly; a void-bearing cut is
not evaluated as an intact gross rectangle.

These are actual demand/resistance calculations at supported sections. The
packet is not another census that leaves their strength ratios null.

## Genuinely unavailable resistance recipes

A blind or partial shaft leaves a retained shape that the existing
whole-transverse-slot rectangular-ligament method does not represent. The
producer records **method-inapplicable**, including actual shaft ends and
profile bounds, and supplies no normal/shear/torque pass for that section.
It does not extend a blind cylinder through the remaining sound wood to
invent a new strip-subset model.

Other explicit method-inapplicable reasons are a trimmed cylinder lacking a
whole-wall certificate, an oblique or nontransverse opening, an unsupported
outer/terminal profile, an overlapping unmachined exclusion, a slot leaving
the authenticated profile, or no positive retained rectangular ligament.
These are specific recipe/resistance limits on named openings. Missing or
contradictory source identity instead stops the build.

Actual attempt 02 has exactly two inapplicable reason families:

| Actual unavailable recipe | Stations | Signed limits still uncalculated |
| --- | ---: | ---: |
| `BLIND_OR_PARTIAL_SHAFT_NOT_A_COMPLETE_TRANSVERSE_SLOT` | 264 | 3,168 |
| `OUTER_PROFILE_OR_TERMINAL_POINT_LOAD_MODEL_INAPPLICABLE` | 14 | 168 |
| **Total** | **278** | **3,336** |

The 14 outer-profile targets are saved station indices **12 through 18** on
each of `base_principal_center_left` and `base_principal_center_right`, with
feature identity `base_principal_center_left/facet008` or
`base_principal_center_right/facet008`. Their underlying profile disposition
is `NON_APPLICABLE_END_TRIM_POINT_LOAD_DISTRIBUTION`. These 168 signed limits
belong to the finished-opening gap, independently of the 1,176 original
terminal traces already excluded by the frozen audit.

The exact named station/feature sets are retained in
`checks.json:inapplicable_opening_identities` and
[section recipes](rawlocal/member-opening-remainder/attempt02/section-recipes.json),
including shaft ends and profile bounds. Each remains a missing strength
comparison. Closing them requires a resistance recipe that represents the
actual retained blind/partial shape, or a supported clipped-profile and
point-load interpretation, respectively. Null values supply no pass.

## Adopted hypotheses and result interpretation

The existing nominal model assumes a common longitudinal strain plane,
grain-end ligament continuity, transverse force shared in proportion to
regional area, equal longitudinal shear moduli, common regional twist and
nominal free warping. Whole signed torque and regional offset moments remain
in the wrench. No local bore concentration or fracture resistance is added.

Demand uses the saved point-placement interpretation. Physical bore-wall,
washer or contact-patch pressure cuts are not claimed for these members.
The source retains the same six simultaneous cases, fixed loads, duration
scenarios and stiffness/support hypotheses. There is no new frame solve or
load redistribution. The rear-leg 1:12 profile is reused where the original
helper admits it; an older square-notch source is not a second surviving cut.

Each metric has a finite value and explicit disposition, or an explicit
uncalculated/inapplicable record. Empty families never report a pass. Counts
are Python integers; NumPy comparison booleans are cast before aggregation.
All exported recipe booleans are ordinary Python booleans.

Normal reference sums remain the original diagnostic. Above-one sufficient
shear bounds are distinct from evaluated-face exceedances. A finite packet
may contain exceedances. Same-state signed face vectors and deciding
witnesses remain available without combining peaks from different cases.

## Actual reference comparisons and witnesses

All ten metrics have **13,968 expected and finite supported values**,
**zero uncalculated supported values** and **zero above-one values**.
There are therefore **no reference exceedance witnesses** in attempt 02.
The following controlling maxima are rounded to six decimals; the exact
values and full signed wrenches are in the actual checks and
[cut records](rawlocal/member-opening-remainder/attempt02/cuts.jsonl.gz).
These outcomes apply only to the supported nominal model.

| Reference metric | Original C_D=1 maximum | Existing C_D=1.25 maximum | Witness |
| --- | ---: | ---: | --- |
| Normal reference sum (diagnostic) | 0.400784 | 0.320627 | A |
| Total tension / Ft | 0.573369 | 0.458695 | A |
| Total compression / Fc | 0.318036 | 0.254429 | A |
| Absolute bending / Fb | 0.390099 | 0.312079 | A |
| Same-state shear bound / Fv | 0.528323 | 0.422658 | B |
| Transverse shear / Fv | 0.226379 | 0.181103 | C |
| Torsional shear / Fv | 0.342991 | 0.274393 | B |
| Compatible face peak / Fv | 0.527786 | 0.422229 | B |
| Scalar shear bound / Fv | 0.528323 | 0.422658 | B |
| Sufficient rectangle bound / Fv | 0.528323 | 0.422658 | B |

- **A:** `base_rail_top`, case `k12-rear`, station
  `1262.8000000000002` mm, `before`, saved trace index **288**.
- **B:** `base_post_outer_right`, case `k12-right`, station
  `171.44999999999996` mm, `before`, saved trace index **84**.
  The deciding compatible face is region 1, `u-`, at global point
  `[1177.925, -84.925, 171.44999999999996]` mm. Signed transverse and torsion
  shear contributions in section coordinates are
  `[0, -0.22934102094965325]` and `[0, -0.42567104160642777]` MPa,
  respectively; their same-state sum is `[0, -0.655012062556081]` MPa.
  The evaluated face ratio is `0.5277859318840682`; the distinct sufficient
  bound is `0.5283229594959108`.
- **C:** `base_rail_bottom_left`, case `a1-rear`, station
  `331.69599437074055` mm, `before`, saved trace index **96**.

Both duration scenarios retain those controlling body/case/station/limit
identities. No demand peaks from different states are combined.

## Outputs and closure

The completed parent build retained:

- `section-recipes.json`: all 860 station joins, exact retained rectangles,
  bore support checks and specific unavailable recipes.
- `cuts.jsonl.gz`: all 10,320 signed limits, both duration records, full signed
  wrenches, every finite nominal comparison, regional recovery and signed
  face vectors. Unsupported recipes receive explicit null comparison values
  with an inapplicable disposition.
- `checks.json`: supported/inapplicable counts, finite/null and above-one
  counts, per-body/per-duration coverage, maximum witnesses and exact
  remaining opening identities.
- `action-audits.json`, `preparation.json`, `producer.py.snapshot` and
  `receipt.json`: action/load bindings, implementation and source/output pins.
- `ownership-direction-map.json`: original floor constraint axes, recorded
  orientation signs and private helper directions for all 200 rows.

`finite_supported_arithmetic_complete` is **true**;
`all_assigned_opening_strength_comparisons_finite` is **false** because the
3,336 assigned inapplicable signed limits remain uncalculated.

The exact residual finished-opening partition is:

**13,944 frozen unfinished limits − 1,320 accepted refresh limits − 6,984
finite remainder limits = 5,640 unfinished limits.**

| Remaining partition | Stations | Signed limits |
| --- | ---: | ---: |
| This remainder: blind/partial shafts | 264 | 3,168 |
| This remainder: clipped principal profiles | 14 | 168 |
| Side hosts outside this assignment, after accepted refresh | 192 | 2,304 |
| **Finished-opening subtotal** | **470** | **5,640** |
| Original unmachined exclusions, separate from finished openings | 22 | 264 |
| Original terminal inapplicability, separate from finished openings | 98 | 1,176 |
| **Remaining original source-null scope** | **590** | **7,080** |

The accepted refresh is subtracted once. The side-host remainder is 1,152
signed limits per body; no refresh limit or duration record is counted again.
The 168 clipped-principal limits are included only in the finished-opening
subtotal, not added to the original terminal partition. The 264 unmachined
exclusions are not obligations to calculate absent finished cuts. No
formal-pending label substitutes for the exact missing comparisons above.

Worker preparation, saved-coefficient diagnosis, syntax parsing and Ruff lint
were performed. Worker numerical build, native/CAD/frame execution, tests,
reviews, staging and commits were not. Parent attempt 01 is the preserved
failed execution described above; it supplies no completed strength result.
Parent attempt 02 supplies the completed supported arithmetic recorded here.
Only these two new maintained leaves and their ignored raw output are owned.
All existing coverage, refresh, source, authority and temporary files remain
untouched. This result annotation changes only this Markdown leaf; the
producer and all raw attempts and preparation snapshots remain frozen.
