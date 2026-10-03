# Permanent nominal-gap cycle: bounded alternate initializer

[knee-bridge-permanent-resolve.py](knee-bridge-permanent-resolve.py) exposes
`run(output: Path) -> dict`, `source_pins()` and `contract(pins)`.
The output must be a fresh immediate child of
`rawlocal/knee-bridge-permanent-resolve/`. Preparation imports no mechanics.
Only the parent executes the initializer, final solve and member recovery
under the existing serialized analysis slot. The parent executed producer
`0faa17` in attempt01; it stopped in proposal geometry validation after the
nominal solve. The parent then executed the single private-schema correction
`cddc75` in attempt02, exit 0,
`COMPLETED_BOUNDED_NUMERICAL_COMPARISON_WITH_EXPLICIT_GAPS`.
The original permanent STOP and resolver attempt01 remain preserved.
No further retry is requested.
This worker has executed no mechanics, coupon, frame, native or CAD work.

## Existing STOP and the bounded change

The original `knee-bridge-permanent.py`, its maintained note and
`rawlocal/knee-bridge-permanent/attempt01` remain frozen. The saved zero-gap
state passed the conditional laws at rigid rank 300. The saved nominal state
raised `normal active-set cycle`: `right_corner_clearance.solve()` encountered
a previously visited tuple of unilateral normal rows before the final audit.
Its nominal branch history and repeated tuple were not saved. This exception
does not establish a physical strength or stability failure.

Read-only inspection of the saved last iterate found finite vectors with
**1,612 forces, 1,612 motions and 300 rigid coordinates**. Its eight floor
normal forces are:

```text
66.53834368230432, 64.46720597996394,
389.44229362805544, 389.8783308897403,
214.6105167272362, 215.10617504209267,
556.3703338298482, 557.1901749529662 N
```

They all exceed the existing initializer's 0.01 N bearing selector, so this
initializer starts with all eight existing floor footprints held. Their
saved normal motions are positive, between 9.319284707708239e-6 and
0.0007623503301144715 mm; these observations do not accept the failed iterate.
At parent execution, the resolver also checks the saved identity
`q = D a + e - H f` against the existing 1e-8 mm guard for the exact current
permanent operators. It uses the saved `f` for the initializer and retains
`q/a` as authenticated compatibility evidence.

The existing zero-gap OSQP seed path was inspected. Its fixed-law QP supplies
a guess without nominal circular clearance. The existing
`conic_frame.convex_seed()` instead includes the current circular clearances
and all unilateral finite laws in a single fixed-floor convex initializer:

```text
min_f  1/2 f' (H + diag(1/k)) f - e'f + sum_i gap_i * ||f_pair_i||
subject to D'f = W and unilateral finite forces >= 0
```

The resolver calls that preserved function once using the saved failed
nominal forces. The fixed-floor initializer is a numerical force guess.
`Solved`, `AlmostSolved`, `InsufficientProgress` or `MaxIterations` transfers
no physical acceptance. Only the original final equations and audits decide
the nominal result. If the initializer selects the same initial unilateral
normal branch as the original failed solve, the resolver stops before calling
the deterministic original solver again. A different branch is permitted to
engage or release contacts and floor support through the unchanged solver.

## Unchanged inputs and acceptance

The gravity assessment remains
`ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95`.
The same **225.19791414318078 kg** modeled mass and proportional **25 kg**
equipment allowance use factor **1.1110134616260479**, once. Only permanent
gravity column zero supplies the loads. There is no climber, horizontal hold
force, hold moment or load variant. H, D, F/e/W, k, material orientation,
geometry, circular gaps, contact laws and no-slip floor contract retain their
original pins. C_D stays 0.9 for the existing permanent wood comparisons.

The census remains **1,888 raw rows, 88 clearance planes, eight floor
footprints, 300 rigid coordinates, 104 global bolts and 66 screws**. The
108-bolt proposal still includes four internal static bolts with no global
connector rows. They gain no stiffness, brace, load-allocation or local
compatibility acceptance from the numerical initializer.

The final solve calls the preserved `dead-load-check.solve_state()` and
`right_corner_clearance.solve()` with the original circular projection worker.
It keeps the 0.1 N/2 Nmm body-balance gates, 1e-4 N finite-law/nonnegative
gates, 1e-8 mm held-floor gate, exactly zero released-floor force, 10 mm
positive-normal domain, circular-gap audits, rigid-rank gate and existing
nominal bounded-seating exception. The latter only handles
`unrestrained rigid coordinate`; a cycle or any other failed gate remains a
STOP. There is no new disk initializer, stiffness scale or tolerance change.

The original permanent producer is imported privately. Its orchestration,
source/geometry validation, six-bore exclusions and complete member recovery
are reused. Only disposable producer/dead module callables are adapted; no
shared mechanics global or frozen file is changed. The original zero state
is reused without solving. The floor map recovers its lumped forces using
the diagonal of `T T'`, since `T @ raw` alone would scale weighted floor
forces. Its authoritative raw forces are restored exactly before member
recovery, and its three output arrays are copied exactly into the final
response. Its audit is retained for the identical frozen inputs.

Every output child first receives byte-identical `original-stop.json` and
`original-response.npz`, preserving both original states even on an environment
or seed failure. The final comparison/STOP always names the reused zero state
and the attempted or unreturned nominal state. A nominal failure retains any
last iterate and the new original-solver branch history, iteration and active
row identities in the method receipt when available from the terminal frame.
On success, the original two-state member replay still exposes all strength
and domain exceptions and missing opening/compatibility bases. Full member or
joint acceptance is not inferred from resolving the cycle.

## Executed attempt01 and private schema correction

The parent ran resolver producer
`0faa17c6acf94f59eb7bb5cd3505e5f31f23e8917c76e0daa9dbd6e7de07292c`
with matching Clarabel 0.11.1 in an isolated target. The authenticated saved
evidence establishes that this STOP occurred **after**, rather than before,
the numerical initializer and final nominal solve:

- `resolution-method.json` records `seed_calls=1`, `nominal_calls=1` and
  phase `one_original_nominal_solve`;
- the cone returned `Solved` in 21 iterations, with recorded solve time
  7.795264216 s and saved-iterate compatibility error exactly zero;
- zero retains `PASS_CONDITIONAL_COUPLED_LAWS`, rank 300;
- nominal retains `PASS_CONDITIONAL_WITH_BOUNDED_SEATING`, force-bearing
  rank 296, nullity four, under the unchanged existing bounded certificate;
- nominal force/moment residuals are 9.890754881780595e-12 N and
  5.512063830432766e-9 Nmm; finite/circular law errors are
  2.2147779077386076e-7 N and 4.905826855861051e-10 N;
- the outer result is `STOP_PERMANENT_COMPARISON`, exception
  `unsupported cylinder fields or trims`. No member replay or opening
  resistance acceptance followed.

The original producer's orchestration saves both returned frame states and
`response.npz`, requires two returned states, then calls
`proposal_records(method)`. Its geometry-helper call fails at
`longitudinal-bore-geometry.validate_geometry()` line 133. The original
permanent attempt01 never reached this call because its nominal active-set
cycle stopped the comparison earlier. Its producer, note and STOP stay frozen.

Each spine's four retained old bores contains these legacy fields:
`axis_origin_global_xyz_mm`, `axis_unit_global_xyz`,
`saved_axis_parameter_interval_mm`, and `saved_grain_interval_mm`.
The original helper accepts equivalent grain-frame source origin/direction
and `axis_parameter_interval_mm`, but rejects these legacy field names.
The two proposed bores already use the supported minimal transverse schema.
The saved descriptors expose no extra physical cut or trim needing a new
geometry method; the original helper still decides that support at execution.

The resolver's module factory now returns a private validation proxy solely
for that helper call. It deep-copies the proposal, maps global source origin
relative to the unchanged stock start through the existing grain-frame rows,
maps source direction through the same rows, and renames the saved shaft
parameter interval without changing its values or sign. The saved grain
interval is checked against station plus/minus radius using the helper's
existing 1e-6 mm tolerance. All stock dimensions, radii, stations, transverse
centers, axis identities and physical shaft endpoints remain unchanged.
Unknown fields and physical trims remain present for the original helper to
reject; incomplete or conflicting legacy metadata also stops. The unchanged
validator still checks source direction/center, full-through span, disk edge
clearance, cylinder disjointness and any saved-volume basis.

Neither the original source geometry nor the exported proposal record is
replaced. No helper constants or shared globals are patched. Successful
translations are recorded in `geometry_schema_validations` in the method
receipt. The new source closure pins the complete failed resolver attempt01
output set. Only the schema adapter changed; the solver method, loads, laws,
audits and runtime budgets are retained. The parent has authorized one scoped
retry and must account for the already consumed seed/final-solve pair.

| Preserved resolver attempt01 output | SHA-256 |
| --- | --- |
| `stop.json` | `2354ff0e77566a9e5744e5edc8065ed3e2cea2a82238beeaccc12afdfef666e7` |
| `resolution-method.json` | `ab5187eeea1020ce7c9435726a04fb51485345d6b745c3895257b3e540088549` |
| `response.npz` | `605ef2df67345633860a7d7d77da89e9ec85e94be62ad3c5cd4737c5a0084033` |
| `convex-seed.npz` | `06d380e3a53ff306ef571a440aaa322fb1c81db2cdbc914233649d53484c2c5e` |

## Executed corrected attempt02: permanent results and remaining limits

The parent executed `cddc75` in
`rawlocal/knee-bridge-permanent-resolve/attempt02`, using the same isolated
Clarabel **0.11.1** target and a 180 s outer execution cap. The saved method
receipt records **one cone seed and one nominal solve** for this attempt;
zero was reused without a solve. The cone returned `Solved` in 21 iterations,
recorded solve time 7.965304438 s. Both six-cylinder geometries passed the
unchanged helper through the private schema adapter; geometry export and
44-member recovery completed. The producer records post-execution source
authentication as true for **238 pins**. The 15 declared output hashes match
the saved files on read-only inspection for this annotation. Parent final
authentication, cut-count validation and whole-model disposition remain
separate parent work.

Gravity plus the 25 kg allowance, once, remains the only load. C_D remains
0.9, with the original no-slip floor, frame/contact laws, H/D/k, material
orientation, geometry and acceptance tolerances. The 104 global bolts,
66 screws, 108 proposal bolts, eight floor footprints, 88 clearance planes,
1,888 rows and 300 rigid coordinates are unchanged.

| Recorded state/gate | Zero gap, reused | Nominal gap |
| --- | --- | --- |
| State status | `PASS_CONDITIONAL_COUPLED_LAWS` | `PASS_CONDITIONAL_WITH_BOUNDED_SEATING` |
| Force-bearing rigid rank | 300 | 296 |
| Force residual, N | 2.4016344468691386e-12 | 9.890754881780595e-12 |
| Moment residual, Nmm | 1.3902021894773853e-9 | 5.512063830432766e-9 |
| Finite-law error, N | 2.484119028256515e-7 | 2.2147779077386076e-7 |
| Circular-gap-law error, N | 2.505632146210246e-9 | 4.905826855861051e-10 |
| Circular projection residual, mm | 0 | 1.1213252548714081e-13 |
| Held-floor motion, mm | 2.1186177812104745e-14 | 1.6519392190966764e-14 |
| Released-floor force, N | 0 | 0 |
| Maximum positive normal-domain motion, mm | 0.02080183283715989 | 0.04924946429215135 |

Nominal has **four null coordinates**, 64 free circular pairs and 24 bearing
pairs. Its preserved fixed-force certificate is bounded, with external-work
increment interval [-1.7639560027296372e-13, 2.271427005406963e-13] Nmm.
The certificate retains `frame_state_accepted=false`,
`force_bearing_rank_gate_satisfied=false` and
`strict_active_tangent_stability_established=false`. The bounded-seating
exception permits this conditional comparison; it establishes neither strict
frame stability nor a rank-300 nominal state. The disk worker's intermediate
SLSQP seed reports `Positive directional derivative for linesearch` after
240 iterations; the saved final circular projection and law audits above
pass without changing the method or tolerance.

### Applicable intact-reference wood comparisons

The saved CSV has **11,576 rows**, 5,788 per state. Every primary comparison
ratio is finite. These apply only at bore-free full/profile rectangles and
use the frozen conditional timber-restraint assumptions. They establish no
resistance at opening or excluded-profile cuts.

| C_D=0.9 metric | Zero-gap peak | Nominal-gap peak | Governing witness |
| --- | --- | --- | --- |
| Timber-braced normal interaction | 0.15606193610044344 | **0.17419444744636486** | `base_rail_top`, after 1190.7749999999999 mm / 1069.825 mm, respectively |
| End-only normal interaction, domain exceptions retained | 0.15616820056369884 | 0.17430270352617327 | Same two rail witnesses; both end-only domains are invalid |
| Timber-braced NDS 3.9.4 interaction | 0.026966069286540773 | 0.0269446572390164 | `lumber_leg_left`, before 45.085665280068326 mm |
| Face lower-bound shear/torsion comparison | **0.13276605773682887** | 0.0816398966650511 | `base_header`, after 1067.015 mm / before 1021.2711 mm, respectively |
| Component-bound sensitivity | 0.18168784662783413 | 0.11044898367319429 | Same two header witnesses |
| Coefficient-5 sensitivity | 0.21187493284577125 | 0.12924174823249138 | Same two header witnesses |
| R/T-swap sensitivity | 0.09081842617790518 | 0.07610239597270307 | `base_rail_top`, after 77.78750000000014 mm / before 49.20100000000004 mm, respectively |

The exception file retains **2,892 end-only normal-domain witnesses**:
1,405 zero and 1,487 nominal. They occur on `base_principal_center_left`
(870), `base_principal_center_right` (863), `base_rail_top` (749) and
`base_header` (410). No timber-braced normal-domain/strength or NDS 3.9.4
exceptions are recorded among the applicable rows; no face-shear or listed
sensitivity ratio exceeds 1.0. The end-only domain exceptions still prevent
unqualified acceptance under that restraint assumption. R/T-swap remains a
separate sensitivity with **936 null entries**, 468 per state, for sections
outside its stated orientation scope; these are not zero ratios.
The face metric remains the preserved lower-bound comparison; complete
torsion resistance is not established by that sampled-face value.

The two modified spines contribute **272 applicable rows total** (136 per
spine across both states). Their intact-sample timber-braced normal peaks
are 0.009336607338434215 left and 0.009255188928559222 right; their face
shear peaks are 0.026617909766342287 left and 0.026402673731326567 right.
All four are zero-gap witnesses. These intact results do not qualify any of
the six holes in either spine, and the original four-bore descriptors remain
provenance rather than a six-bore resistance basis.

### Opening, profile and compatibility coverage

The coverage file contains **18,488 signed cuts**, each with six finite
force/moment components. There are 11,576 applicable intact cuts and
**6,912 excluded cuts**: 6,520 bore/passage, 352 end-trim/point-load
distribution and 40 incomplete/terminal-profile cuts. This includes the
42 unchanged bodies and both modified spines across the two states;
88 body-balance records were exported. The modified spines contribute
560 signed cuts total: 272 applicable and 288 excluded. Their changed-hole
regions are explicitly excluded from intact-rectangle ratios.

The opening register names **318 openings**, including all **12 spine
openings** (four retained and two added per spine). Every opening has saved
signed-demand witnesses in both states, and every opening resistance ratio
remains **null**. Per spine, retained facets 006/007/008/009 have 28/20/20/32
witnesses and proposed v-bridge holes 1/2 have 24/20, across both states.
These are finite sample counts, not continuous opening-region coverage or
local resistance checks.

Exact remaining limits are:

- Resistance/concentration and ligament-transfer basis at all finite
  openings and excluded profiles, including the actual six-bore spines;
  local traction and connection bearing/transfer cannot be assigned intact
  rectangular capacities from these saved cuts.
- Permanent-state load allocation and local compatibility for the **four
  internal static bridge bolts**. They remain absent from the global
  connector rows and gain no global brace/stiffness or force-allocation pass.
- Actual changed-hole elastic stiffness. Existing frame operators remain
  frozen, so this run establishes no six-bore stiffness correction.
- Complete member/joint/hardware qualification and formal torsion basis.
  Conditional intact-reference ratios and sensitivities do not close these
  modes or adopt the proposal.
- Strict frame stability and the whole-model register, owned separately by
  the parent. The nominal bounded certificate retains its rank/nullity limits.

All recorded complete member/joint/frame acceptance, changed-hole stiffness,
local bridge compatibility, opening resistance, strict stability and physical/
fabrication release flags remain false. No loading or safety flag is changed
by this annotation. The numerical comparison is complete within its stated
scope; it does not require all exception categories to pass.

| Frozen corrected attempt02 output | SHA-256 |
| --- | --- |
| `comparison.json` | `3179d7d40d60a3e21f101610c83acfb588f7e9612941cd253123c9881bbd708a` |
| `resolution-method.json` | `d0c517ed2c7ad7066626bbcb2296f5e1ffa731c2b58aceabe16395f5af9287f7` |
| `response.npz` | `605ef2df67345633860a7d7d77da89e9ec85e94be62ad3c5cd4737c5a0084033` |
| `same-cut-states.csv` | `74a8cfe7f1741314a26fc37c93598a05c71589de0da69a0f177118d4b43960e0` |
| `section-coverage.json` | `5696f838bec214ea0d54f5fdfeeb3be358bf2b1e5093397bb5b5ef4ad9c43ad2` |
| `opening-register.json` | `cf835e7e8fca3f78ae7ebd2636d7d83ae86d8097efba242dc4eab84af332af78` |
| `exceptions.json` | `cc6eb3435df710a9898451bf25c0ec6e5e91a06c0553a08f39b1880f24ac48b6` |
| `geometry.json` | `f844524aab764b35d7880f93f280f3ee5484674c6542182c2a7af743b6b65596` |
| `member-actions.npz` | `e1f3c22a02b7072bf1941ce02be9d3437d7a709dc00cbf802b8327697cb956e8` |

## Recorded known answers and version basis

The initializer is imported directly from the unchanged `conic_frame.py`;
no Clarabel API behavior is added. The local pinned
[method description](panel-orientation-comparison.md) records its convex
formulation and Clarabel **0.11.1** interface and cites the
[official Python API documentation](https://clarabel.org/stable/python/getting_started_py/).
That primary documentation confirms the `Ax + s = b` convention, zero,
nonnegative and second-order cones, upper-triangular CSC objective input,
`DefaultSolver`, primal `x`, dual `z` and configurable time limits. Version
0.11.1 is tied to the [official release](https://github.com/oxfordcontrol/Clarabel.rs/releases/tag/v0.11.1)
and the exact recorded helper/coupon hashes below. The local recorded evidence
was read first; the primary interface and release pages were then checked.
The existing saved `rawlocal/load-lever/frame-attempt01/conic-seeding.json`
binds this exact helper and original solver, with recorded analytic evidence:

- 3/4 N circular force, k=1000 N/mm, gap=1.15 mm: motion [0.693, 0.924] mm;
- zero-load unilateral spring with imposed negative opening: remains open;
- circular disk projection: offset [0.6, 0.8].

These establish the existing cone direction and dual-pose sign within their
recorded limits. They do not establish resolution of the current full frame.
No additional tiny coupon is required for directly reusing this function;
none is run by preparation or by the resolver API.

| Frozen source | SHA-256 |
| --- | --- |
| Original permanent producer and executed snapshot | `3eddb384ac05820203bed59369ee270661b643bdc07e69159baec904eb5979a7` |
| Original permanent maintained note | `79fca9fdb96c2e88860aa7ef33ce89d3adc1ebebbdd2be4d97c6cac3e7203a10` |
| Original attempt01 STOP | `c3e568102c6cc921e09e526955f55860c01aa7be3e8f9b08b7ba8724f4918b7e` |
| Original attempt01 response | `df426ebdf6a8e6fe6ba9e7dbd36cbcf06aea3296a587bd96707c73b0e08bcaa1` |
| Original attempt01 inputs | `0fd81c9f7c6ddcc4cabfaebb4da61a2bc10c3ba74d741a47c361dc5f2ab8da2f` |
| Preserved convex initializer | `445574a04559e8faa28a3b69bfdbf1a439f6fc25940e0f02837b0927c48f0025` |
| Recorded cone/direction/dual-sign evidence | `4f04814e435742108b4cb6aa80562ea2fb7faca1bb27d94f082b2e0a94576ea7` |
| Local interface/method description | `145e94349a0c8cb632d2388da7232bd33edf91d98b7618aca8b8ad1ef3c4a02f` |

`source_pins()` authenticates these and the original permanent source closure.
The resolver also authenticates sources after execution, including a STOP.
The method receipt records whether this final authentication succeeded.

Original preparation authenticated **229 pins** in sourcepin-attempt02, SHA-256
`d947a90d25a664dd9d029f16702e7d3cda653ecf501efaa3561e3ef64776a04c`.
The schema correction authenticates **238 pins** and Ruff passed. Its current
freeze is `rawlocal/knee-bridge-permanent-resolve/sourcepin-attempt03/api-freeze.json`.
Its SHA-256 is
`9f6652c939a575417fb7a0b3803cbbad19823f1ea9d9baaaf393e3ccad0103ef`.
Resolver producer SHA-256 is
`cddc75df222c82fadef13218286a2bc375539c98d1d4902c3262cea9e5384ee4`.
Both earlier preparation snapshots and executed attempts01/02 remain
preserved. No preparation child contains a new mechanics result. The original
permanent producer/note and geometry helper hashes remain unchanged.

## Bounds and parent execution

Runtime pins are Python **3.12.3**, NumPy **2.5.2**, SciPy **1.18.1**,
OSQP **1.0.4** and Clarabel **0.11.1**. The current repository virtualenv has
the recorded OSQP package but no Clarabel package was found there during
read-only preparation. The parent supplied matching Clarabel 0.11.1 through
an isolated target for both executed attempts; this worker installs no packages.

Bounds are **one cone initializer**, at the helper's existing **150 iterations
and 30 s** limit, then **at most one original nominal solve** with its existing
**30 normal-branch iterations and cycle guard**. The existing disk projection
limits remain 500 SLSQP iterations, 200 least-squares evaluations and, when
already needed by that worker, 400 polish evaluations. Zero has no solver
call; no floor-mask search, seed retry, longer budget or alternate load follows
a failure. These are solver limits, not a total wall-clock guarantee for matrix
work, rank/certificate evaluation and member recovery.

Preparation command:

```sh
python3 -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-permanent-resolve.py \
  --sourcepin-only \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-permanent-resolve/<fresh-preparation-child>
```

The parent uses the declared environment and serialized slot for
`run(fresh_output)` or the CLI `--run --output <fresh-execution-child>`.
The CLI acquires the existing analysis lock and requires its slot to be idle.
The output retains `resolution-method.json`, initializer forces when available,
the original artifacts, the new response/STOP and, only after nominal
acceptance, the existing member/section/opening exports. All are ignored local
evidence with source snapshots and hashes. This maintained adapter/note stays
active; no old evidence is pruned or archived.

The scoped retry is complete. Remaining work is parent validation/publication
of the saved results and the explicit opening, internal-bridge compatibility,
changed-hole stiffness and structural qualification gaps above. No further
retry is requested. This worker performs no software tests, reviews, staging,
commit, source-authority edits or mechanics execution. The producer and both
raw attempts remain frozen; only this maintained note records the new result.
