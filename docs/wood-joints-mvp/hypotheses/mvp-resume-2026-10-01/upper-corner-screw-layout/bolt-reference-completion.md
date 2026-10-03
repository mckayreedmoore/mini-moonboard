# Fresh bolt reference completion: N01 and N10

## Final bounded assessment

The parent completed `two-recovery-attempt01`, receipt
`353f5890dd8cccc8db5cbf29bd7f2daa1de8877e3031825343a807a47421aa22`,
summary
`776f597ec63e31be4c45a87302f0d849222cc6f4346361dda6d2bf8df04c43b0`.
All **159 source bindings and ten output bindings** authenticate exactly.
This is the final bounded N10 assessment in this packet; no additional
producer recovery or solver iteration is prepared.

| Final comparison/source | Completed | Numerical nulls | Maximum finite index | Exceedances |
| --- | ---: | ---: | ---: | ---: |
| Same-state isolated shaft axial/bending/shear steel | **503/504** | **1** | **0.11193008492743632** | 0 |
| Simultaneous average T/V reference | **504/504** | 0 | **0.04052274152621833** | 0 |
| Nominal thread tension reference | **504/504** | 0 | **0.018390332348961952** | 0 |
| Independent signed own-end T/M and pressure-wrench sources | **1,006/1,008** | **2** | Not a washer capacity comparison | Not applicable |

Bottom center `k12-right` recovered. The only remaining shaft null is
`wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/upper_rail_1`,
case `a12-left`, **T=0 N, V=1.9755775926692833 N**. Its geometry remains
applicable to the recorded two-host model; the null is a numerical method
limit, not a geometry exclusion or physical capacity failure. Its combined
steel index and two end-source rows remain null. The finite T/V-only value
does not complete its missing shaft bending comparison.

The final outputs preserve all **502 accepted shaft rows and 1,004 accepted
end rows** from recovery01 byte-exact, including all original **499/998**.
The 40,160 previously accepted shaft fields remain a byte-exact prefix;
bottom center adds 80, for **40,240 saved field samples**. N01's 72 rows remain
byte-exact. `N10_comparisons_complete` and `N09_end_sources_complete` stay
false; `N09_complete` stays false because this producer supplies sources only.
The washer consumer joins against the final receipt above and retains the
two explicit G7 end nulls.

### Read-only explanation of the G7 numerical limit

The analytic QP prerequisite passed: maximum pose error
**6.817869836403534e-13 mm**, force error **6.81786982426047e-9 N**.
Bottom center's QP returned `Solved` in 29 iterations; its original shaft
function accepted the seed at iteration 0 with scaled gradient
**6.491207016345868e-10 N**, passing the unchanged residual and field guards.

G7's QP instead returned **`InsufficientProgress` after eight iterations**,
well before its 150-iteration or 5-second caps. Its positive-part indentation
lift error is **0.006559858368884921 mm** and its recomputed original-energy
gradient is **1.9755775926692833 N**. That gradient and energy
**-2.334140474979057 Nmm** exactly equal the original shaft function's first
evaluation at the unchanged saved seed. Only cleat bore sample 24 is then
active, and the host-translation residual is exactly **-V**. Thus the QP
candidate was not stationary; there is no observed QP/original-law mismatch
or transfer of QP convergence into shaft acceptance. The saved QP report
lacks primal/dual residual history, so its internal stopping cause cannot
be specified beyond `InsufficientProgress` and the recorded lift/gradient.

The unchanged shaft solver activates samples **23 and 24**, then remains
on that branch for 150 iterations. Its terminal scaled gradient is
**0.019479853108517898 N**, with two tangent null modes. The last regularized
step has norm **1.2077532721450334e-6 scaled mm** and is accepted at full
fraction; the remaining moment residual barely changes.

The residual has a direct algebraic explanation. At T=0 both end contacts
are inactive and supply zero moment under the recorded law. Host sample 23
is **1.2523972581577472 mm** from the interface. With no other active host
sample, its force cannot balance both a nonzero interface shear and zero
host moment. From the saved host-translation gradient, its signed helper
bore force is **-1.975364712096814 N**. Therefore

`scaled host-rotation gradient = force * lever / grip length`

is **-0.01947985310851797 N**, matching the saved DOF-35 residual to
**7.29e-17 N**. This identifies the missing balancing reaction on the active
numerical branch. It is not a demand/capacity exceedance or permission to
ignore the moment residual. No compatible stationary pose, inactive-contact
certificate or complete 80-field G7 witness was produced. The final
disposition is **one applicable modeled state with a documented numerical
method limit**, preserving its unavailable fields as null.

Only saved-data authentication, byte comparison and this scalar statics
explanation were performed here. The consumed producer remains byte-exact
at **b0d450**, along with every receipt, helper and generated raw output.
The consumed preparation documentation d2ef9 remains in its existing
`preparation-two-convex-recovery/documentation.md.snapshot`; this maintained
document records the later actual result. No additional solve, implementation,
test, stiffness/domain/tolerance change, review, staging or commit occurred.

## Preserved execution history

The parent completed recovery-attempt01 with receipt
`bd46885849c203001d4e520a0601f16cf1be950da4d3cab44045da2cf8630173`:
**three of five recovered, 502 total solved shafts, 1,004 completed ends,
two numerical nulls and four null ends**. It preserved the original 499 steel
and 998 end rows byte-exact. That result supplied the two states subsequently
consumed by the final attempt above.

The parent completed full-attempt01 with receipt
`54125505dce1a499e964ef6b708f3148de7eac934e50f0c00e3bda28fd3ca274`:
**504 calls, 499 solved shafts, five numerical iteration-limit nulls,
998 completed own-end sources and ten null ends**. There were **zero geometry
nulls**, and all **16 normalized axes / 96 states** entered the replay.
The finite same-state steel peak is **0.111930085**; all 504 direct average
T/V and nominal thread peaks are **0.040522742** and **0.018390332**.
There are **zero exceedances**. The original five uncompleted bends were
numerical nulls. One now remains; it is not a physical failure or completed
T/V-only steel comparisons.

The consumed [producer](bolt-reference-completion.py) retains the bounded
`recover(output)` API described below as its frozen reproduction contract.
Parent execution of that contract is complete; no further call is pending.
The separate N01 attempt02 completed **72 comparisons, 65 bindings, four
outputs**, receipt
`cf86636b75b3d29faf632c5a68df9ccacf7e31df272e4bb3ccf6827fcee3dcac`.
N02 consumed that result and preserved its a007 producer/7101 documentation.

The consumed f5 producer normalized only the 16 matched numerical endpoint
discrepancies within the original **1e-6 mm** geometry precision. Its original
full closure has **138 bindings**. The consumed two-state recovery authenticated the bd468
receipt and its complete source/output closure, preserving f5 and resolving
509's maintained producer path to its bound consumed snapshot. It exports
combined **504 steel / 1,008 end rows** while preserving all **502 accepted
steel rows, 1,004 accepted end rows and 40,160 shaft fields byte-exact**.
Separate comparison proves the original full01 **499/998/39,920** subset
stays byte-exact as well. N01's 72 full01 rows are copied
byte-exact without arithmetic. These remain conditional isolated references,
not joint qualification. `mode="n01"` remains the separate 65-binding subset.

Consumed full01 `build(output, *, mode="full")` producer SHA-256:
`f5a881203dcd21a446fb05c9e99aa997f7590542b59d55d0bcb5f929bb692d49`.
The amended producer/documentation snapshots and exact per-mode source
manifest are in `rawlocal/bolt-reference-completion/preparation-full-precision/`.
Full01 also binds its own byte-exact f5 `producer.py.snapshot`. The consumed
documentation SHA-256 is
`ba1938f35b0050169f1e704b0792ed2cbb225fdb8280007f20a4e02e81532754`,
preserved in the preparation's `documentation.md.snapshot` before editing.
The consumed recovery01 producer is
`509af84792f319b04883bebc9dbb9b1a78804129b1bfda7e48bd3e532b28b0f0`;
its documentation is
`b69d725999c22265dfeb3467d045ae403088fa2e6a0d426e22677fafd1d6c017`.
These snapshots and the original manifest remain unchanged under
`rawlocal/bolt-reference-completion/preparation-five-recovery/`; recovery01
also binds its own 509 snapshot. All were authenticated before editing.
The new two-state preparation is frozen under
`rawlocal/bolt-reference-completion/preparation-two-convex-recovery/`.

## Consumed two-state convex initialization

Each recovery01 failed state had 451 authenticated trace events. They established the inputs to the final attempt:

| Remaining state | Terminal scaled force residual, N | Active bore samples | Tangent nullity | Last accepted fraction | Observed deficit |
| --- | ---: | --- | ---: | ---: | --- |
| `a12-left`, `wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis/upper_rail_1` | **0.019479853108518328** | 23, 24 | 2 | 1 | Residual plateau from iteration 5; tiny regularized null-mode advances. The largest residual is host rotation DOF 35. |
| `k12-right`, `bottom_center/clip_horizontal_bottom_left_2/rail_2` | **7.037594969006022e-5** | 0, 23, 24 | 1 | **1.4901161193847656e-8** | Plateau after iteration 2; final step norm is 4.3637544e-9 scaled mm, then line search nearly freezes it. |

G7's last 100 iterations move the pose only **0.0001219831 scaled mm**;
bottom center moves only **4.3636081e-9 scaled mm**. Neither reaches the
unchanged **1e-6 N** gate. The available trace proves stagnation on rank
deficient contact branches; it does not supply the full tangent eigenbasis.
The inference is that a global contact initializer is preferable to repeating
the same donor pose or enlarging the iteration budget. No capacity failure
or deficient physical hardware is inferred.

### Primary method and exact energy

The initializer follows Clarabel's documented
[canonical convex QP and inequality convention](https://clarabel.org/stable/python/getting_started_py/)
and [iteration/time/accuracy settings](https://clarabel.org/stable/api_settings/).
Require **Clarabel 0.11.1**, the version already used by the common saved
`conic_frame.py` method. Its existing analytic circular-force/dual-motion
evidence is bound at `rawlocal/load-lever/frame-attempt01/conic-seeding.json`,
SHA-256 `4f04814e435742108b4cb6aa80562ea2fb7faca1bb27d94f082b2e0a94576ea7`.
That record reports `[3,4] N` and `[0.693,0.924] mm`; it authenticates interface
and sign conventions only. No frame computation or acceptance is transferred.

Let z contain the existing scaled shaft pose, plus seat variables when T>0.
Each positive-part indentation is lifted to p, with **p >= Cz-g** and
**p >= 0**. Minimize

`0.5*z'K*z + l'z + 0.5*sum(w*p^2)`.

The 48 existing bore samples produce 96 signed springs, using the same
radial gap and `Kwood*D*quadrature_weight`. The padded K is the pinned
first-order beam matrix; no geometric stiffness is introduced. The drive
term remains `-V*host_u`. The seed supplies an initial pose only.

For T>0, keep each end's existing 256-point hardware and 256-point wood
annuli. Introduce two washer rotations and four **unrestricted** closures.
Hardware indentation is `d_head + (relative_tilt - washer_tilt)*x`;
wood indentation is `d_wood + washer_tilt*x`, with their original Khead/Kwood
and area weights. Add `-T` times each closure to the objective. Minimizing
closures recovers the original prescribed-force compression law; minimizing
washer rotations imposes the original series moment balance. This is the
same finite spring energy already reduced by `compression/series_contact`,
up to its irrelevant zero-tilt constant. Negative closures stay allowed;
there is no added rotation bound, pressure support, preload or stiffness.
At **T=0**, omit every seat variable and pressure spring, preserving the
existing inactive-contact rule rather than supplying artificial stabilization.

| Seed | Free variables | Positive-part spring variables | QP variables | Inequality rows |
| --- | ---: | ---: | ---: | ---: |
| G7, T=0 | 36 | 96 | **132** | **192** |
| Bottom center, T>0 | 42 | 1,120 | **1,162** | **2,240** |

Reuse `beam_model` and `annulus` directly; no helper code or source is copied
or changed. Symmetrization serves Clarabel's matrix format only. Its numerical
regularization and stopping values are seed settings, not a revised physical
spring or final acceptance threshold. A finite nonconverged QP candidate may
be tried as a seed; only the original shaft function can return a completed
state, under all its unchanged guards and **150 iterations / 50 backtracks**.

### Consumed prerequisite and finite execution bound

Before either target, parent ran the prepared analytic QP coupon:
a 1.15-mm bilateral clearance spring, 1,000 N/mm stiffness and +5 N drive,
combined with two prescribed +4 N compression springs at 10,000 and 20 N/mm.
Expected free variables are **[1.155, 0.0004, 0.2] mm**; independently
reconstructed spring forces are **[5,4,4] N**. Require QP `Solved`, pose error
<=1e-7 mm and force error <=1e-6 N. This validates the newly assembled
positive-part and closure-load signs; existing frame oracle is not rerun.
No target proceeds if this method prerequisite fails.

One coupon QP (150 iterations, 2 s), exactly two target QP attempts
(150 iterations, 5 s each), and at most two original shaft calls
(150 iterations each): **no retry, no 504-state replay, no altered law or
acceptance tolerance**. The two seeds and any remaining null reasons appear
in `recovery-trace.json`; `seed-known-answer.json` records the prerequisite.
The combined exporter then recovers only four new end rows, using the same
existing pressure arithmetic without another contact solve. The 40,160 saved
fields stay a byte-exact prefix with at most 160 added samples.

The preparation venv lacked Clarabel. The actual parent run used the pinned
**NumPy 2.5.2 / SciPy 1.18.1 / Clarabel 0.11.1** environment. No dependency
installation or method execution occurred in this worker.

## Preserved five-state preparation and actual result

This section describes the consumed 509 preparation. Parent's subsequent
recovery01 solved three of its five calls, leaving exactly the two states
listed above. The following initial missing-history statement refers to
full01; recovery01 now supplies the stagnation evidence.

The observed deficit is exactly the unchanged **150-iteration** convergence
gate. Full01 did not save failed poses, residual sequences, active-contact
history or accepted line-search fractions, so a more specific stall/rank
cause cannot be authenticated from that output. The pinned helper always
starts from a fixed radial-gap pose and exposes no saved-pose argument. Each
failed axis has five converged same-axis cases; usable donors converged in
**4–16 iterations**. The failure is numerical at these small loads; capacity
or contact-domain changes are not a recovery method.

| Target case | Axis | T, N | V, N | Selected frozen same-axis donor |
| --- | --- | ---: | ---: | --- |
| `a12-forward` | `rail_rear_bolt_right_1` | 25.321806 | 15.088685 | `a1-rear` |
| `a12-left` | `wj04_g7/.../upper_rail_1` | 0 | 1.975578 | `a12-forward` |
| `k12-right` | `bottom_center/clip_horizontal_bottom_left_2/rail_2` | 0.497099 | 4.923684 | `a12-forward` |
| `a1-rear` | `left_service/.../clip_horizontal_upper_left_2/upper_rail_1` | 4.795096 | 2.370525 | `k12-rear` |
| `a1-rear` | `rail_front_bolt_right_2` | 39.707373 | 16.599531 | `a12-forward` |

The minimum amendment is an initial-pose adapter to the pinned
`upper-right-combined-transfer.py:solve_state`. It compiles that function's
authenticated AST, replaces its cold pose with the donor's saved 36-DOF pose,
and adds diagnostic callbacks. No helper implementation is copied or edited.
AST shape/count guards bind the exact substitutions and preserve **150
Newton iterations / 50 Armijo backtracks**, all original force/moment,
PSD, descent and postprocessing guards, contacts, quadrature and constants.
The function retains the original Newton/Armijo algorithm; no new mechanics
method or test execution is introduced.

Donors must be solved, have the same axis, exact geometry/receiver order,
K20 and nonzero V, and satisfy the saved nodal residual tolerances. Choose
the smallest sum of squared T/V differences normalized by the larger load
in each pair, with case-order tie breaking. Zero-V nonunique donors are
excluded. Saved translations are not scaled; physical rotations are
multiplied by grip length to restore the helper's scaled coordinates.
The circular isolated model uses those scalar coordinates along the target's
own signed resultant drive/rotation basis. Only the seed is borrowed;
target forces, geometry, material diagnostics and all laws remain unchanged.

There is **one call per null, five calls maximum, no retry or longer budget**.
The unchanged full01 source/span proof supplies geometry; no normalization
is recalculated and no frame/native/CAD operation occurs. Converged outputs
must pass the same 80-field census, zero geometric-shortening convention,
nodal residual and independent host wrench checks. Their ten own-end rows
use the existing pressure recovery without another contact solve. Any
remaining numerical null retains its reason and prevents N10 completion.

`recovery-trace.json` records iteration residuals, energy, active bore sample
indices, tangent eigenvalue range/nullity, step size and accepted backtrack
fraction. One extra terminal residual evaluation per call records the final
pose whether or not the original convergence gate passes; it does not add
a Newton update or relax that gate. No failed-history cause is invented.

The combined worksheet retains original row positions. The 39,920 original
shaft-field lines are a byte-exact prefix, followed by at most 400 new field
lines. `reuse-manifest.json` records preserved-row stream hashes, counts and
the five replacement indices. The new receipt binds the original receipt,
all seven original outputs and the consumed f5 snapshot. Original accepted
end rows retain their f5 source joins; new rows identify the recovery producer
and original full01 receipt. **N09_complete remains false**, even if all
1,008 end sources are recovered: washer strength belongs to its consumer.

The consumed a007 producer and 7101 documentation remain byte-exact in
`rawlocal/bolt-reference-completion/preparation-n01-separated/`:
`a007b59e423985e598ddf350b870420dcd5733dc551519ca04e21f02ded5dd45` and
`7101b0b9d8e193cd91a85aa87c2158d49b2c0186b4b39ae8493fa89408c40256`.
N01's own `n01-attempt02/producer.py.snapshot` also binds the original a007
bytes. The parent preserved the same consumed sources under N02 attempt01's
`source-snapshots/bolt-reference-consumed-n01.*`. No old receipt, raw output,
helper, authority or criteria bytes are changed.

The failed d773 producer remains byte-exact in
`rawlocal/bolt-reference-completion/preparation-v2-end-sources/producer.py.snapshot`
with SHA-256 `d7737cbaf0fc52564735fd3f69afb64efa6c8b8c08bb034324d2ccb268c30c79`;
its documentation snapshot is
`2e6ba98063d0a92acc7032a36a9d62b74393b72aae6af830d85bfba9e7fc79a2`.
The failure preceded output-directory creation; `n01-attempt01/` was absent
on inspection. No attempt logs or frozen sources were written or removed.

The earlier `89d6ae1905177bc7339c18443ece20ca2f82965c85109f8fac4ab00a6a4c9930`
producer and its `4ca93105e40ad242870006d30098ddf5f77586da2fc002926ab8a759e9585ac8`
documentation remain byte-exact in
`rawlocal/bolt-reference-completion/preparation-89d6ae/producer.py.snapshot`
and `documentation.md.snapshot`. The corrected amendment separates the
calculation subset and records unsupported geometry; applicable full shaft
physics and all original source hashes remain unchanged.

## Bounded comparison

| Qualification item | Exact prepared coverage | Method and decision |
| --- | --- | --- |
| N01 | Twelve existing end-grain axes in six blocks × six nominal cases = **72 comparisons** | Reuse `lateral_reference.reference` and the recorded `end_grain_route.py` convention. The end-grain block is the main member, its bearing angle is 90°, and header bearing follows the same-state shear direction. Apply **Ceg = 0.67 once** to the six-mode 92 ksi reference. Record demand, each mode, governing reference and ratio. |
| N10 | Other 84 existing axes × six nominal cases = **504 steel records**: 72 quarter-inch candidate axes and twelve retained 3/8- or 1/2-inch axes | Reuse the saved extraction contract, the existing direct steel function and the complete shaft helper. Preserve simultaneous signed axial force and both lateral components. The bounded precision normalization permits all **504 prepared replay calls**, each with **80 beam samples**, totaling **40,320 samples** if every call completes. Geometry or replay outside the method retains a null shaft/combined index. Compare nominal thread tension separately from the simultaneous smooth-shaft axial/bending/shear envelope. |
| N09 source addition | The same 504 shaft states × two ends = **1,008 end/state rows** | Export each completed shaft's signed physical T/M, datum, basis, contact dimensions and independently integrated wood/hardware pressure wrenches. This supplies the ordinary washer worker's missing local M; it does not execute washer mechanics or establish N09 capacity. |

The sources are the **ce69 gravity / c3a8 comparison / 62bd response** proposal
packet. Loads stay **250 lb × 2 downward, signed 300 N horizontal, original
100 mm hold lever**, planning mass **225.19791414318078 kg** and dead-load
factor **1.1110134616260479**. Only `gap_scale = 1` is consumed. The reviewed
104-axis geometry supplies the unchanged axes and saved bore/grip quantities;
fresh forces belong to the unadopted 108-axis proposal. Historical forces,
passes and adjusted joint resistance are not transferred.

The saved extraction API is `knee-bridge-other-bolts.py:build(output)` and its
authenticated `attempt01/records.jsonl` receipt. That module has no separate
extraction callable. This producer consumes its saved records and reuses its
read/bind/authentication helpers; it never calls that old producer or writes
its output directory. Full mode rechecks all 504 T/V records against the
exact fresh NPZ rows and original row ownership; N01 mode rechecks only its
72 selected records. Both authenticate the complete original extraction
receipt/output closure. Selected rows retain their original 504-row indices.
Static geometry and row joins must agree across all six cases of each
selected axis. The 12 N01 bearing joins match the existing Ceg route's
quarter-inch, two-receiver, single-span, zero-interface-gap hypothesis.

## Shaft replay and applicability

These 84 saved records contain no shaft bending fields. The prepared replay
uses `upper-right-combined-transfer.py:beam_model/solve_state`, with the saved
physical head-to-nut bearing lengths and equal modeled bore radii. Retained
bore radii come from the pinned finished-face register. The saved lateral
plane must match the physical timber interface; axial ties must lie on the
shaft line. A multi-span receiver, unresolved bore, noncontiguous span pair,
unsupported interface offset or eccentric tie produces explicit per-state
N10 nulls. Receiver/schema conflicts or source-integrity failures still stop
preparation. The original geometry guards are retained; no contiguity is
invented. No lever-arm wrench is relabeled as recovered shaft bending.

### Exact cause of the first STOP

The first offending axis is
`left_service/left_service_mirrored_inner_outer_hypothesis/clip_horizontal_lower_left_1/lower_rail_1`.
Its head-to-nut receiver mapping is correct:

| Receiver | Original bearing span from the underhead axis datum, mm |
| --- | --- |
| `left_service_outer_lower_cleat` | `[2.031999999902837, 90.93200000090837]` |
| `base_rail_service_lower_left` | `[90.93200023044392, 129.0320002314495]` |

The signed endpoint mismatch is **2.295355443493463e-7 mm**. This exceeded
the a007 `math.isclose(..., abs_tol=1e-7)` guard, whose default relative
tolerance is `1e-9`. The read-only census then established that all 16 such
discrepancies are numerical geometry precision within the pinned 1e-6 mm
domain. The owner directed the bounded normalization after N02 consumed the
unchanged N01 result. Receiver identities require no schema correction.

Read-only interval joins found the same approximately 2.29e-7 mm mismatch
on these 16 axes:

| Frozen axis family | Exact suffix expansion | Axes |
| --- | --- | --- |
| `left_service/left_service_mirrored_inner_outer_hypothesis` | `clip_horizontal_lower_left_{1,2}/lower_rail_{1,2}` | 4 |
| Same family | `clip_horizontal_upper_left_{1,2}/upper_rail_{1,2}` | 4 |
| `wj04_g7/upper_g7_clearance_n86p9_reversed_rail_hypothesis` | `{lower,upper}_rail_{1,2}` | 4 |
| `wj06_outer_pair/right_outer_full_4x4_paired_rail_hypothesis` | `{lower,upper}_rail_{1,2}` | 4 |

### Bounded numerical normalization and face proof

The pinned `mini_moonboard/wood_joint_geometry.py` declares
`_GEOMETRY_TOLERANCE_MM = 1e-6`; its original hash is
`e437385d4894c7bcd4bbf4ee66aa9f96a53a8d3570efc6230fb225570abbb90e`.
The finished-face producer is bound by the saved register at
`a58e8f76b0d308352c734b6eab6bdea8c3adb75ab1c538e0905997d0232bab4f`.
Saved contact and finished-face linear matching use 1e-5 mm; the separate
1e-7 mm coordinate-roundtrip check verifies transforms rather than interface
adjacency. No force, moment, bore-clearance or solver tolerance is enlarged.

Normalization is restricted to the exact 16 axis IDs above and a unique
saved adjacent interface with the original receiver order. It requires the
saved demand point to equal the pinned common interface point, one matched
finished contact patch, both named planar source faces, and unique finished
bore end faces. Contact/individual-face distances, bore endpoint mismatch,
source projection and endpoint corrections must each remain within 1e-6 mm.
The recorded span mismatch also must remain **≤ 2.295365e-7 mm**.

Each adjacent endpoint is moved to the shaft-axis projection of that
authenticated common source/contact plane; outside span endpoints stay
fixed. The source plane agrees with the original span midpoint to at most
**1.0052357402952137e-9 mm**. The actual prepared bounds are:

| Saved geometry quantity | Maximum, mm |
| --- | ---: |
| Original adjacent bearing endpoint mismatch | **2.2953645384404808e-7** |
| Applied individual endpoint correction | **1.1577336067603028e-7** |
| Source point to its shaft-axis projection | **1.1368683772161603e-13** |
| Source plane to either matched finished source face | **1.1599104254855774e-7** |

Raw bearing lengths are checked against the extraction before normalization.
Afterward, the original positive-span, 1e-7 contiguity, equal-bore, diameter,
source-plane and bearing-length guards run. Bearing lengths include only the
recorded endpoint correction, so original lengths and corrections reproduce
every normalized value. Axial-tie collinearity remains separately required.

`geometry_applicability.numerical_precision_normalization` preserves original
and normalized spans, all endpoint/length corrections, the source station
and projection error, contact patch/source face indices, exact STEP bindings,
individual face distances and method/source hashes. It is carried by each
affected steel/end row and summarized for **16 axes / 96 states**. The former
96 geometry-null shaft states and 192 geometry-null end sources can now enter
the existing replay; full01 subsequently solved 499 of its 504 states.
True gaps beyond precision, unmatched interfaces and multi-span receivers
retain explicit per-state N10 nulls. N01 performs no N10 family preparation.

The replay retains the existing smooth circular shaft, 16 beam elements,
three bore quadrature points per element, compression-only bore/seat laws,
**E = 200,000 MPa, Kwood = 20 MPa/mm, Khead = 10,000 MPa/mm**, zero preload
and the conditional **92 ksi** steel property. Its in-memory beam wrapper
zeros geometric stiffness and shortening, matching `corner-first-order.py`.
The original helpers remain byte-identical. No coupon or old run entry point
is called. This is an isolated, first-order shaft hypothesis; it does not
establish compatible poses across all bolts in a joint or modify frame laws.

The quarter-inch head/nut contact land retains radius 5 mm. For retained
diameters, the declared circular land radius is half the catalog minimum nut
across-flats dimension, used hypothetically at both ends. These are explicit
contact hypotheses, not observed bolt-head or nut bearing profiles. Other
wood seats use the existing concentric catalog annulus hypothesis. For
`center_principal_right_2`, both ends credit only the documented 5 mm supported
patch; the partial-seat crescent and full washer annulus receive no credit.
Actual support masks and washer spreading remain unqualified.

The direct steel diagnostic reuses
`wood_joint_bolt_resistance.bolt_first_yield_reference` and the retained
producer's pure `steel_references` function. Nominal tensile stress areas are
**0.0318 / 0.0775 / 0.1419 in²** for 1/4 / 3/8 / 1/2 inch respectively.
The same-section average-shear diagnostic excludes bending and cannot close
N10 alone. The separate complete smooth-shaft envelope retains axial force,
bending and sectional shear from the same axis/case/sample. Thread-area
tension is never combined with smooth-section bending as one physical section.
The row's steel index is the maximum of its thread, direct same-section T/V
and complete shaft indices; a shaft result is required even when both direct
indices are finite. Beam and bore fields remain finite-element samples under
the retained contact hypothesis, not a continuum or actual-thread stress bound.

`SUPPORTED_COMPARISON` means a finite index ≤ 1 under that stated hypothesis;
`EXCEEDANCE` means > 1; `NULL_UNSUPPORTED` means no completed comparison.
A replay error preserves the exact error, null bend fields and null combined
steel index while retaining the direct T/V diagnostic. The output reports
`PARTIAL_NULL_SHAFT_STATES` whenever any of the 504 shaft comparisons is
missing. Maxima retain their own axis/case witnesses; independent maxima are
not assembled into a new load state.

## Own-end sources for the ordinary washer worker

Full mode writes `washer-ends.jsonl`, keyed by
`(case_id, axis_id, end_role, receiver_member)`. Every one of the 1,008 expected
end/state keys is present even when its shaft or pressure recovery is unsupported.
Unestablished receiver order remains null; no end datum or contact geometry
is fabricated for a family outside the method.
Successful mechanical replay means that the isolated shaft equilibrium and
beam field census closed; it does not mean steel or complete-joint acceptance.
An elastic-reference exceedance still exports its own end sources.

Let `n` be the shaft axis from head to nut, `d` its saved external-drive
direction, and `r = n × d`. The physical transverse basis has columns `[d,r]`.
The scalar helper supplies its signed contact moment `m`. At each nominal
outer-seat datum, physical moment on the receiver is **M = m r**, with physical
two-component representation **[0,m]** in that basis; moment on the beam is
its opposite. Force on the head receiver is **+T n**, and force on the nut
receiver is **−T n**. Accordingly `signed_T_n` is +T at the head and −T at the
nut; `normal_compression_T_n` and `fresh_signed_T_n` retain the positive axial
compression demand. All vectors use world XYZ. No moment transported from an
arbitrary lever is substituted for the own-end moment.

Each row records its seat datum, common interface datum, shaft axis, receiver,
physical transverse basis, signed force, signed M in world XYZ and the physical
two-component M. It carries its contact closures/tilts, ring radii, modeled
bore and shaft diameters, ordered grip lengths, K20/Khead stiffnesses, zero
preload, catalog washer ID/OD/thickness ranges and hypothetical head/nut land.
The central partial-seat route credits only its 5 mm patch. Actual support
masks, delivered profiles and washer spreading remain unqualified.

The retained pure `cleat-traction.py:wood_seat` function reconstructs pressure
from each saved closure and tilt on **256 quadrature points**. It independently
integrates force and physical moment about the end datum, once for the wood
annulus and once for the hardware bearing annulus. The scalar signed tilt is
represented by a directed slope and nonnegative pressure tilt, matching that
helper's two-plane interface. At T=0, the existing shaft `compression()` law
returns inactive zero-pressure contacts; recovery preserves that exact rule.
No contact equilibrium, washer flexure or additional shaft solve is called.

The exported recovery includes each pressure integral/centroid, its own-seat
force/moment wrench, signed source residuals and the balance between hardware
pressure and the opposing wood reaction on the washer. It also shifts the
recovered wood wrench to the named interface datum. Pressure actions remain
temporary arithmetic inputs; their half-million point dictionaries are not
duplicated into permanent outputs. The exporter retains the helper's nominal
first-order seat datum without a beam-end translation offset.

Source joins name the exact saved extraction row/hash, its receipt, the fresh
global-demand row ID/hash, component/tie rows, this output's steel row, the
comparison/NPZ hashes and the frozen producer/helper hashes. The full receipt
binds `washer-ends.jsonl`; the washer worker must authenticate that receipt
and its own support/state join before consumption.

Missing end fields or failed pressure recovery retain the exact null reason.
Known signed T/M remain available if a later pressure reconstruction fails;
unavailable moments remain null, never assumed zero. `N09_end_source_export`
reports finite and null rows separately. **`N09_complete` remains false** even
when all 1,008 sources recover; no washer metal stress, flexure or capacity is
calculated by this producer.

## Frozen source manifest

| Source | SHA-256 |
| --- | --- |
| `rawlocal/knee-bridge-gravity/attempt01/operator-assessment.json` | `ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95` |
| `rawlocal/knee-bridge-frame/attempt02/response/comparison.json` | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| Same directory, `response.npz` | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| `knee-bridge-other-bolts.py` | `7a03ecabeb89fd0415877152842fea3e7a80cfef4be6ebea3b52e602dce2585d` |
| `rawlocal/knee-bridge-other-bolts/attempt01/receipt.json` | `ee67b7e042a8fcf88d1c37eaaaaac8aebcb815e2cf73b8f1a22a61f44283da83` |
| Same directory, `records.jsonl` | `1050735cfa418fc13b27b48de0ba116adabe32683e1d1cf3524c07cca087dd95` |
| `../lateral_reference.py` | `845409d1daf0214bbd41484f0a0a58867cd266bbc7f19060d9eef9d342657e94` |
| `../end_grain_route.py` | `5b9faca5696d6c7add02e9ac6d5056363896bb2a7badb7ab7bb3fa8bfc9fe5d4` |
| `upper-right-combined-transfer.py` | `fba852724b82ee3cd28b0318bfdf156ac1786f85ac26257698d8d103c26c62b0` |
| `corner-first-order.py` | `6e3f899ac99d6eef629ac12570b6ea31ea5c3914467c1c7399b7bcdd8d320563` |
| `central-seat-transfer.py` | `b0ad536b3fad418dad1c07b56edd126ae78bace32eb8ecb150ba756880f7d7fa` |
| `knee-bridge-corner-references.py` (pure function loader) | `188b7626d989eb16fb09ee75b8218dd9968974c95c72830dcd83c33f856c4b83` |
| `cleat-traction.py` (pure pressure recovery functions) | `2834a9a9fd25083da16034b498b3356197a4a6b2b53ffb35663077c5f93f7764` |
| `mini_moonboard/wood_joint_bolt_resistance.py` | `488e58bbd58fbc2f22af5d4122e734732bae09de79dad71bbf2623eeca60b166` |
| Retained reference producer `produce.py` | `24b3cb82ed6a785ab5dc0cf910f22a0cce915438f8d4b04d527d82a245b1205b` |
| `/tmp/mini-moonboard-retained-frame-bolt-current-resistance-basis-2026-10-01.json` | `c3250f067c4590ee43f7ec7a5765d056d87e6ff5adb42837ed27710d9b4d4eb1` |
| Saved reduced `model-inputs.json` | `178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9` |
| Same packet, `contact-geometry.json` | `034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151` |
| Finished-face `surfaces.json` | `33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb` |
| Finished-face producer `surfaces.py` | `a58e8f76b0d308352c734b6eab6bdea8c3adb75ab1c538e0905997d0232bab4f` |
| Original tolerance source `mini_moonboard/wood_joint_geometry.py` | `e437385d4894c7bcd4bbf4ee66aa9f96a53a8d3570efc6230fb225570abbb90e` |
| Historical N01 `rawlocal/bolt-reference-completion/n01-attempt02/producer.py.snapshot` | `a007b59e423985e598ddf350b870420dcd5733dc551519ca04e21f02ded5dd45` |
| Full01 `rawlocal/bolt-reference-completion/full-attempt01/receipt.json` | `54125505dce1a499e964ef6b708f3148de7eac934e50f0c00e3bda28fd3ca274` |
| Same directory, consumed `producer.py.snapshot` | `f5a881203dcd21a446fb05c9e99aa997f7590542b59d55d0bcb5f929bb692d49` |
| `../assembly-package/hardware_engagement.py` | `d8e2a08e46fd9507a89d8e7ecb238ddf229490f4909345cbb641374ee8133295` |
| Same package, `rawlocal/hardware-axes.csv` | `2fb010f1b55757e614d90940bfa2a8400df6ee41ab0f950ffa56d30157150b01` |

The producer also pins `pyproject.toml` / `uv.lock` and requires NumPy
**2.5.2**; full mode additionally imports/requires SciPy **1.18.1**. Both
modes authenticate the original extraction source/output closure and reduced
geometry sources before/after consumption. N01 retains the receipt's original
historical provenance bindings without consuming N10-only method/geometry
contents. Only full mode expands the additional retained sources, finished
STEP bindings, catalog sources, original tolerance/face producers and the
historical a007 snapshot. The exact source maps contain **64** original
artifacts plus this producer for N01, **137** plus this producer for full;
`preparation-full-precision/source-manifest.json` records both maps.
Hashing STEP bytes performs no CAD operation. `sources.json` and `receipt.json`
will contain the exact expanded manifest and the selected mode's generated
output hashes. The receipt schema is `bolt_reference_completion_receipt/v2`.
The consumed five-state recovery closure contains **146 bindings**: the original 138, with its
f5 maintained-path entry authenticated at the consumed snapshot, plus the
new maintained producer, original full01 receipt and six other full01
outputs. The snapshot already accounts for the seventh original output.
`preparation-five-recovery/source-manifest.json` records the exact map and
the one historical source-path exception. No expected original hash changes.
The current two-state closure contains **159 bindings**: retain all original
146, resolve the maintained 509 entry to recovery01's snapshot, and add the
new maintained producer, bd468 receipt and its eight other outputs, common
conic method/oracle and consumed b69 documentation snapshot. It retains the
original f5 full01 receipt and every original output/source hash. The current
`preparation-two-convex-recovery/source-manifest.json` records that exact map.
The new receipt carries all a007/f5/509 snapshot identities for consumers;
no old receipt's producer entry is repinned to the new maintained source.

The full build does not consume or rewrite the completed cf866 N01 receipt;
it recomputes its 72 Ceg rows from the unchanged saved extraction. Its explicit
`historical_producer_snapshot_binding` authenticates a007 at
`n01-attempt02/producer.py.snapshot`. For a separate verifier consuming the old
N01 receipt, the only historical source-path exception is the old maintained
producer entry whose expected hash is exactly a007: check those bytes at that
bound snapshot, require its hash also equals the old receipt's producer hash
and `output_sha256["producer.py.snapshot"]`, and preserve every other original
source/output pin. The current maintained producer has its own new hash; no
old receipt pin is replaced with it. N02's preserved consumed copies provide
another byte-exact recovery source, not a new numerical acceptance basis.

## Consumed API and write boundary

Frozen recovery producer SHA-256:
`b0d45007a15e4de08f7c6a3d69194e7e434f43c96a221d02cf1382e1c17eb56f`.
AST parsing/compilation, pinned helper AST adaptation and Ruff passed without
calling a solver. All **159 source bindings** authenticated before and after
the saved-data preparation. No test or mechanics execution occurred.
The preparation manifest binds this producer, its documentation snapshot,
the original f5/ba19 and 509/b69 sources, historical exceptions and exact source map.
Parent completed this API at the final receipt recorded above. Execution in
this packet is closed with the single documented G7 numerical method limit.
The code and its historical source contracts remain frozen for authentication.

```python
# Preserved reproduction signature; no additional call is pending here.
receipt = producer.build(output)  # default mode="recover": only two targets, combined 504 / 1,008
# Equivalent: producer.recover(output) or build(output, mode="recover").
# Original build(output, mode="full"|"n01") APIs remain available as history.
```

The preserved API requires `output` to be a fresh immediate child of
`rawlocal/bolt-reference-completion/`. Its historical CLI is equivalent:

```bash
task_packet=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout
# Use the parent's existing pinned NumPy/SciPy/Clarabel environment.
python -B "$task_packet/bolt-reference-completion.py" \
  --mode recover \
  --output "$task_packet/rawlocal/bolt-reference-completion/recovery-attempt02"
```

The historical cheap N01 prerequisite used another fresh child and
`--mode n01`. It writes only `end-grain.jsonl`, `summary.json`, `sources.json`,
the producer snapshot and `receipt.json`. The receipt reports
`COMPLETE_N01_N10_PENDING`, **zero shaft calls**, `N10_pending: true`,
504 required/pending shaft states and no washer-end rows. N02 can consume that
N01 receipt without waiting for full steel replay. A later full call uses a
different fresh child; it does not rewrite the N01 result.

The API returns a receipt dictionary. Full output files are `end-grain.jsonl`,
`steel.jsonl`, `shaft-fields.jsonl`, `washer-ends.jsonl`, `summary.json`,
`sources.json`, the new producer's snapshot and `receipt.json`.
Recovery also writes `recovery-trace.json`, `reuse-manifest.json` and
`seed-known-answer.json`; its receipt
retains `mode="full"` for the combined worksheet and names
`execution_scope="RECOVER_TWO_NULL_STATES"`. Completion is based on all
504 finite shaft states, independently of all 1,008 end-source recoveries.
There are **ten bound outputs plus the receipt**. The build and CLI defaults
now select two-state recovery, so omitting a mode does not repeat all 504 calls.
Writes use fixed allowed names,
`O_EXCL | O_NOFOLLOW` and a descriptor opened on the owned output directory.
The output must have no symlink alias. Source iteration variables are never
write destinations. Existing outputs and consumed frozen files cannot be
overwritten by this API; it does not use a consumed helper's general dump API.

Only these two new maintained leaves and their ignored fresh snapshots are owned. No helper agent was used;
the parent owns heavy execution and staging. No frame/native/CAD execution,
tests, review loop, source geometry/hardware/law edit, staging or commit occurred.

## Preserved bounded execution estimate

The two-state preparation allowed **5–20 seconds**, with a **30-second slot
cap** before inspecting an overrun. The explicit QP caps total **12 seconds**
including the coupon; there are at most **300 original Newton iterations**,
two terminal residual evaluations and four end-pressure reconstructions.
Authentication, parsing and
writing the combined saved JSON dominate the fixed work. This is a planning
estimate from existing work, not a benchmark or promise of convergence.

The earlier full-mode preparation estimate is preserved below as history.
The identical shaft helper's saved 72-state `upper-right-combined-transfer`
attempt02 used the same NumPy/SciPy versions, median five and maximum thirteen
iterations. Its snapshot-to-checks file timestamp interval is **1.56 s**;
this is a timing proxy excluding startup and not a benchmark of this API.
Scaling to 504 calls gives roughly eleven seconds. The fresh census has
326 near-zero-V and 178 loaded states.

Allow **20–90 seconds for full mode**, including at most 516,096 saved-pressure
quadrature contributions across both annuli at applicable ends, authentication and
JSON output. Use a **120-second slot cap**, then inspect an overrun before
extending. For N01-only mode, allow **1–5 seconds**, with a **15-second cap**.
These are planning estimates; no new benchmark or engineering run was made.

## Explicit remaining scope

N01 supplies an end-grain lateral reference only. It does not establish axial
wood bearing, Cg/Cdelta applicability, splitting or complete-joint resistance.
N10 supplies all 504 nominal thread/direct T/V comparisons and 503 isolated
smooth-shaft stress envelopes in the final two-recovery result. G7's modeled
bending/combined index and its two end rows retain the documented numerical
method limit. This packet closes its execution at that finite assessment.
Actual delivered material,
root/shank area, transition/profile, nut/head engagement, washer strength and
spreading remain unqualified. A finite shaft result does not establish common
joint deformation or the actual changed-hole stiffness.

Sixteen corner axes, four continuous knee shafts and four new internal bridge
axes retain their separate producers. Frame stability/permanent loading,
common knee deformation and the splitting peer's work stay with their owners.
No Hillman/panel comparison or formal criterion is changed. These comparisons
carry no geometry, hardware, fabrication or climbing release.
