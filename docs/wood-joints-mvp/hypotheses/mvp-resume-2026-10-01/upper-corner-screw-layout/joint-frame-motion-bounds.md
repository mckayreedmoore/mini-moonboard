# Current coupled frame seating and stability implications

The active wider-profile assessment uses its **new** response and action
fields, explicitly applied four-row washer law and parent-run
[motion result](rawlocal/joint-frame-motion-bounds/profile-attempt01/summary.json).
The parent run completes in **9.626 s**: all twelve accepted states have
bounded 344-coordinate seating, seven nominal states have audited nonunique
body witnesses, and two zero-gap floor dispositions remain without accepted
fields. The unchanged ranks/nullities are computed afresh; no frame08 result
is transferred. Its twelve states retain 4,128 coordinate intervals, 600 body
records and 164 nontrivial support LPs. Every additional body rotation bound
is zero under the recorded tolerance.

The new [load-geometry result](rawlocal/joint-frame-motion-bounds/profile-load-geometry01/summary.json)
uses those exact accepted poses and nullspaces. It retains the actual physical
100 mm hold point, source CG allocations and four changed-stock height
intervals. Only saved-data products and independently checked body 3×3
spectra are evaluated; there is no new force-state, global eigenvalue, native
or project solve in this diagnostic.

| Maximum diagnostic | Preserved frame08 | New wider profile |
| --- | ---: | ---: |
| Additional body translation bound, mm | 1.149116 | 1.149112 |
| Saved plus seating centroid translation bound, mm | 7.807524 | 7.791242 |
| Saved plus seating rigid rotation bound, rad | 0.0345732 | 0.0335503 |
| Material-point rotation remainder bound, mm | 0.193397 | 0.191141 |
| Physical hold-point rotation remainder bound, mm | 0.017141 | 0.017064 |
| Conditional gravity CG rotation remainder bound, mm | 0.048435 | 0.045611 |
| Held no-slip tangent remainder, mm | 0.001295 | 0.001300 |

The governing bodies remain the gravity-only right knee inner frame block
for additional seating and the K12-right nominal top center left cleat,
top outer right cleat and top rail for the next three quantities. The new
physical hold-point remainder is **0.009443 mm**, with an absolute external
potential remainder bound of **38.295021 Nmm** and maximum finite load-moment
update of **2,467.299443 Nmm**. The new summed absolute gravity-potential
remainder bound is **4.381344 Nmm**. The external curvature projected onto
the translation-only seating nullspace stays below `4.264e-31 N/mm`.
These changed geometric diagnostics supply no bound for all internal,
contact and support stress stiffness. **Second-order stability remains
unestablished**, and all tangent-completion, numerical-goal and release
flags remain false.

## Preserved frame08 force basis

This preserved packet assesses nominal seating in the **344-coordinate**
frame08/action03 force basis. It changes no force, member, contact law,
clearance, screw stiffness, floor assumption or load lever. The reviewed
104 bolt axes and 66 Hillman screw axes remain the source geometry. Two
source floor-search dispositions have no accepted field and therefore no
pose envelope; their complete failed searches remain separate numerical
limits, not physical failure proofs.

The parent-run [runner](joint-frame-motion-bounds.py) completes all twelve
accepted states in **2.599 s** on one BLAS thread. **All 344 coordinates are
bounded in every accepted state.** All seven nominal-clearance states admit
an independently audited witness of nonunique timber seating; the five
accepted zero-gap states have unique fixed-force rigid coordinates under the
recorded numerical rank tolerance. No unbounded original-law recession is
found. The [summary](rawlocal/joint-frame-motion-bounds/attempt02/summary.json)
and [receipt](rawlocal/joint-frame-motion-bounds/attempt02/receipt.json) retain
all results and 115 frozen source bindings. The preceding 300-coordinate
certificate is preserved as history and is not transferred.

| Accepted nominal state | Nullity; body / metal-only projections | Maximum body translation increment bound, mm |
| --- | ---: | ---: |
| A12-rear | 10; 6 / 4 | 1.139522 |
| A12-forward | 10; 6 / 4 | 1.145469 |
| A12-left | 10; 6 / 4 | 1.108662 |
| K12-right | 10; 6 / 4 | 1.112669 |
| K12-rear | 10; 6 / 4 | 1.135919 |
| A1-rear | 16; 8 / 8 | 1.148023 |
| Gravity-only | 16; 8 / 8 | 1.149116 |

These are conservative component-box norm bounds about each saved pose,
not claimed attainable maxima. Every body rotation increment is zero within
the recorded coefficient tolerance, so the maximum bound for an arbitrary
material point's seating increment is also **1.149116 mm**, on the gravity-only
right knee inner frame block. All remaining metal-coordinate bounds are finite;
metal-only tangent freedom does not imply unbounded washer/shaft motion.

The report covers **4,128 coordinate intervals** (344 × 12), **600 body
records** (528 timber and 72 panel), and **164 nontrivial support LPs**. Zero
observables and the five zero-nullity cases need no support solve. The
original-law timber witnesses have coordinate increment norms of
0.428364–1.042166 mm, fixed-motion changes at most `2.92e-16 mm`, no positive
inactive contact or disk excess, and external work magnitude at most
`3.67e-13 Nmm`. Every witness passes all unchanged physical-law and screw-law
audit gates.

## Method

For saved forces `f`, relative motions satisfy
`q = D a + e - H f`. Their elastic timber and shaft deformation is fixed;
the remaining pose changes have the form `delta_a = N z`, where the existing
bounded-seating helper supplies the nullspace `N` of active finite-law and
held-floor motion rows. All active spring deformation, original law
residuals and no-slip tangential motions remain unchanged. Inactive
unilateral rows retain `q + D delta_a <= 0`; unloaded circular pairs retain
their original radial disks.

The disk component boxes enclose those disks, so finite bounds on the outer
polyhedron are conservative admissible-pose bounds. A box endpoint is never
called an admissible state. Each component maximum has an explicit
nonnegative dual multiplier with `A.T y = c`, checked against the primal
value. An unbounded LP must furnish a recession direction whose free-disk
motion is zero, active-law motion is zero, and inactive contact motion is
nonpositive. Timber/body and metal-only recession directions are reported
separately. The existing numerical SVD, `1e-8 mm` motion tolerance and
`1e-9` LP feasibility tolerances are retained; SVD leakage below `1e-11` is
recorded and removed before the small LPs. These are numerical certificates
under stated tolerances, not exact arithmetic proofs.

This uses the source law/audit functions, receipt closure, accepted-state
inventory and bounded-seating nullspace routine. It uses HiGHS through the
already installed SciPy 1.18.1. The [official SciPy interface documentation](https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs.html)
specifies unrestricted variables when bounds use `None`, status 3 for
unboundedness, and the opposite sign convention of inequality marginals;
the runner explicitly supplies unrestricted coordinates, converts that sign,
and checks the resulting certificate instead of accepting status alone.

Finite extrema are shortened into the **actual disks** and checked again
with frame08's preserved `force_law_audit`. This supplies a concrete witness
of nonunique timber seating when one exists, while retaining every original
force, compatibility, floor, spring-domain and screw-law gate. Saved forces
already contain finite accepted law residuals; the witness preserves or
rechecks those residuals. It is not an exact inverse of approximate forces.

## What the motion bounds mean

The report gives centroid translation and rotation component intervals,
conservative Euclidean norm bounds, and a bound for the rigid increment of
**every material point** in each current body. The last bound uses the actual
source nodal radius about its rigid-coordinate origin. Because the elastic
field is unchanged at fixed force, those increments also bound the change
in total member motion between these fixed-force states.

Absolute elastic nodal deformation is not reconstructed by this runner.
The reported total rigid pose is the saved rigid pose plus its certified
seating interval; it is not a full member deflection envelope. No numerical
serviceability threshold is introduced.

The finite rotation remainder estimate `radius * theta_bound^2 / 2` bounds
the difference between rigid rotation and its linearized displacement. It
is a geometric diagnostic, not a recomputed force state. It cannot be used
to claim compatibility after the contact normals, load geometry or elastic
operators have changed.

Across these rigid-pose envelopes, the largest centroid translation norm
is **7.807524 mm** at the K12-right nominal top center left cleat. The largest
rigid rotation is **0.0345732 rad** at its top outer right cleat. The largest
linearized-rotation remainder bound is **0.193397 mm**, at the same state's
top rail; gravity-only nominal has a largest remainder of **0.007647 mm**.
These include the saved rigid pose, so they are distinct from the much smaller
additional seating bounds above. The source equations do not establish how
those geometric remainders change contact or stability; no acceptance threshold
or updated-contact pass is inferred from their magnitude.

## Stability disposition

Active-map rank is used to identify candidate zero-energy directions, then
the unilateral and disk laws determine whether those directions have bounded
extent. Bounded clearance seating can contain a finite continuum with no
local restoring stiffness. An admissible witness preserves active spring
deformation and the elastic body/shaft field, while its external work is
explicitly recorded. This is more specific than treating rank loss as frame
failure or positive strain energy as a stability proof.

Local reactions are identical within the stated fixed-force first-order
pose set. That result does not envelope a changed coupled force branch.
Where timber participation is absent, the report identifies the conditional
first-order body restraint result separately from remaining metal freedom.
It does not promote that result to second-order or dynamic stability.

For all seven nominal states, the original-law witnesses demonstrate actual
finite first-order flat timber directions, rather than an unconstrained rank
guess. Clearance and unilateral seating bound their extent without making
the tangent strictly restoring. The five accepted zero-gap states have no
rigid tangent freedom inside this first-order source model. Thus the packet
closes the current **fixed-force seating and finite stability-implication
assessment**, while leaving geometric/buckling and dynamic behavior outside
what these source equations establish. It supplies no overall frame stability
or structural release claim.

The summary's `first_order_*_restoring_stiffness_strict` fields describe the
absence of a fixed-motion nullspace within the conditional positive linear
elastic/contact source model. They are not an independently computed tangent
eigenvalue or prestress stability result. This packet never substitutes those
fields for the explicit second-order stability limit.

The source model has no geometric stiffness, inertia, buckling eigenproblem
or dynamic history. The report therefore supplies a finite assessment of
the governing first-order mechanism and rotation implications, with those
omitted behaviors explicit. New coupled branches must be assessed with
their own forces and active laws; none can inherit frame08's motion bounds.
No blanket external review, physical test, floor-friction test or fabrication
gate is added by this assessment.

## Saved load geometry and the second-order boundary

The separate source-only [load-geometry diagnostic](rawlocal/joint-frame-motion-bounds/geometric-load-diagnostic-attempt02/summary.json)
evaluates all twelve saved poses in **2.600 s**, without changing the frozen
motion producer or solving another force state. For a rigid arm `r`, its
finite point position is `t + exp([theta]) r`. The omitted displacement is
`(exp([theta]) - I - [theta]) r`, bounded by
`||r|| ||theta||^2 / 2`. The diagnostic checks this formula and the sign of
the external load curvature against an analytic rotating-point coupon.

The recorded physical hold point remains **100 mm** from the reference
patch center. Its first-order body wrench matches the equivalent face-node
load, but those two distributions need not have the same second-order work.
Using the physical point, the largest saved rigid remainder is **0.009469 mm**
and its conservative bound is **0.017141 mm**, both at A12-rear nominal. The
associated external-potential remainder has an absolute bound of
**38.468 Nmm**. The largest finite change of its body-origin load moment is
**2,469.174 Nmm**, at A12-forward nominal. These are load-location arithmetic
results, not equilibrated second-order reactions or a permitted deflection.

Physical gravity locations are partly available. The frozen mass inventory
and load adapter retain all 50 stock centroids, 760 positive hardware mass
shares from 586 source components, and 142 T-nut centroids. Their force-plus-
transfer-couple decomposition reproduces every current body gravity wrench
within `8e-10 Nmm`. Forty-six stock heights retain their exact source values.
For the four changed timber masses, the current wrench fixes transverse CG;
the saved current node/stock envelope supplies an outer height interval.
No old or newly computed uniform centroid is silently assigned to them.
The endpoints bound possible source-gravity terms and are not claimed
admissible physical CG witnesses. The existing proportional 25 kg allowance
scales these source allocations; it establishes no actual accessory location.

Conditionally letting each recorded mass share follow its receiver's rigid
pose, the largest gravity CG rotation-remainder bound is **0.048435 mm**,
at K12-right nominal. The largest summed absolute gravity-potential remainder
bound is **4.403780 Nmm**, at K12-rear nominal. Hardware allocation preserves
source mass accounting and first moments; it does not establish actual
hardware kinematic attachment. The equivalent native gravity nodal map also
contains self-equilibrated horizontal correction forces, so its separately
reported curvature is not promoted to physical gravity curvature.

For a fixed global-direction force `F`, let `s = exp([theta]) r`. Its potential
is `-F . (t + s)`. The Hessian with respect to an incremental rigid rotation
about the saved orientation is
`K_load = (F . s) I - (F s.T + s F.T)/2`, in `Nmm/rad^2`. It is affine in each
unknown gravity CG height, so endpoint matrices provide entrywise intervals
and conservative eigenvalue bounds without another equilibrium solve. All
certified seating directions have zero body rotations; the largest numerical
projection of the conditional physical external curvature onto those
directions is below `2.86e-31 N/mm` in the source's scaled coordinates. Thus
this external term neither removes the nominal neutral seating nor supplies
a restoring-stiffness proof for other deformation modes.

The saved bearing masks retain the original no-slip assumption. Replacing
each footprint's linearized rigid displacement by its finite rotation gives
a maximum held tangential-constraint remainder of **0.001295 mm**, at
K12-rear nominal. The diagnostic reports the normal remainder as well. It
does not correct the elastic field or reimpose finite contact/support
compatibility; these remainders are an explicit measure of omitted geometry.

The full prestressed tangent requires more than these external terms. The
fixed `H` and `D` do not update member/shaft stress stiffness and axial-force
shortening, contact/seat normals and lever arms, or no-slip constraint
geometry. In a total-potential formulation the missing terms include the
internal initial-stress second variation, schematically
`integral sigma_ij v_k,i v_k,j dV`, the spring/contact terms
`sum f_j delta^2 g_j`, and the support reaction terms from second derivatives
of held constraints. The radial spring law is already nonlinear in its
reference coordinates; that does not supply all of these evolving-geometry
terms. The pinned [CalculiX 2.23 nonlinear-static description](https://www.dhondt.de/ccx_2.23.pdf#page=293)
distinguishes initial-displacement and initial-stress stiffness, and its
[buckling description](https://www.dhondt.de/ccx_2.23.pdf#page=301) uses the
initial-stress matrix in the tangent stability calculation.

A conditional sufficient comparison would require a lower bound `m` on
the material/contact tangent over the admissible support/contact critical
cone and a bound `G` on all remaining geometric terms, then demonstrate
`m > G`. The saved fields evaluate the external-load part of `G` and show its
vanishing projection on the seating nullspace. They supply neither the full
geometric bound nor a positive tangent margin over all elastic member,
shaft and support modes. **Second-order stability remains unestablished**;
this arithmetic does not complete a tangent, P-delta or buckling assessment.

## Reproduction and retention

The analytic disk, disk-witness, metal-only recession and unilateral
recession coupons pass in **0.27 s**. Source-only preparation took **0.47 s**.
The frozen [request](rawlocal/joint-frame-motion-bounds/prepare-attempt02/request.json)
has SHA-256 `db5fc9893f98121a4f4f881a6f19d1b4000f30ce098cb30d52a4c1d159cad553`;
the summary is `807a4a1ec3847bc86378b8a2700cf903b95a27afcaa8991f0d6e1b297e51ef0c`,
and the completed receipt is
`2a4aa36755825e95c4e7837f5427674283f654aaa7f113950c0e728a3f19d7ac`.

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/joint-frame-motion-bounds.py \
  --stage build \
  --request docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-motion-bounds/prepare-attempt02/request.json \
  --expected-sha256 db5fc9893f98121a4f4f881a6f19d1b4000f30ce098cb30d52a4c1d159cad553 \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-motion-bounds/attempt02
```

The fresh ignored output retains request, producer snapshot, analytic
coupons, dual multipliers, extrema, recession directions, original-law
witnesses, summary and source/output receipt. The source frame, wood-port
reduction and action packets remain active dependencies. No source or raw
run is removed or archived by this packet.

Attempt01 remains an immutable earlier result. Attempt02 is the active
reporting contract: it adds explicit prior-300/no-transfer guards, current
344-coordinate layout, typed fixed-force reference bounds, dual-multiplier
row identities and the fixed/inactive/free-pair constraint joins. Its cheap
postprocessing replay gives the same numerical results; it repeats no native
or frame solve. Both attempts are recoverable.

For a changed force basis, receipt selection alone is insufficient when a
separate law-update packet changes the original preparation's `k` array.
Any follow-up must apply and authenticate that explicit update before the
motion and source-law audit; the old `assemble()` loads the preparation's
original laws. Reuse the source binding, nullspace, component-bound and
witness functions through a frozen ignored adapter, preserving this producer
and its results. Changed timber compliance similarly requires its own H/e
replacement rather than relabeling these fixed-force bounds.

The ignored [profile-update adapter](rawlocal/joint-frame-motion-bounds/profile-update-adapter.py)
consumes the separate wider-profile frame's actual accepted fields. It
requires the new `inputs.json` to embed `washer_joint_update`, exactly equal
to the frozen four-row `joint_frame_scalar_seat_update/v1` contract derived
by the existing member-replacement API. It authenticates that profile packet,
checks exactly four changed `k` rows and unchanged other joint arrays, then
uses the original pose and witness functions with the **new** laws and fields.
Unchanged law/audit definitions may be reused from their pinned method
snapshot; no old force, pose, rank or bound is transferred. Its source hash is
`b62ca4279e52c7ee7ffde978380405925d2d0f4f2c71084473f1fc14b9a3283c`.
It reuses the profile API's source serializer to preserve the three explicit
absolute temporary-source bindings alongside repository-relative bindings.
The adapter has passed syntax and Ruff checks; the completed changed-frame
motion assessment above is parent-run.

The load-geometry diagnostic retains its ignored helper snapshot, analytic
coupon, 120 source pins and output [receipt](rawlocal/joint-frame-motion-bounds/geometric-load-diagnostic-attempt02/receipt.json),
SHA-256 `70fa5b3980ecbc057ee6f5b85e8b060695a0493e828dc49b0cee211a573e56f9`.
Its summary SHA-256 is
`9fa01b43fcf3fd8d5dcd4407c19798b408f9fc3a576320e9d2a72a94e8e1d651`.
The failed single-direction gravity-collapse assumption is separately
preserved under `rawlocal/joint-frame-motion-bounds/geometric-load-diagnostic-failed-gravity-collapse`;
it is a representation-method stop, not a frame or physical failure.
The diagnostic outputs remain active arithmetic evidence, with all
second-order stability and structural-release flags false; nothing is
removed or archived.

The ignored [profile load-geometry adapter](rawlocal/joint-frame-motion-bounds/profile-load-geometry-adapter.py)
reuses the frozen diagnostic arithmetic for fresh wider-profile accepted
fields. Its `prepare` stage requires explicit new motion, action and response
paths with their receipt hashes. It authenticates the applied four-row washer
update, unchanged external load/geometry freeze, accepted-state inventory,
saved rigid poses and actual 344-coordinate nullspaces. Its `build` stage
requires that fresh request and hash; the result binds all three new packets
and carries no old force, pose, rank, nullspace or bound forward. Absolute
profile-source identities remain intact.

The existing curvature arithmetic has a translation-only seating domain.
Preparation stops explicitly if the new certificate has body rotational
participation or lacks the accepted gravity-only zero field needed for the
source gravity-map join. It does not convert such a stop into frame failure
or diagnostic completion. The adapter's analytic rotation/Hessian coupon,
absolute-source, zero-nullity and old-force-relabel guards pass, as does Ruff.
Its source SHA-256 is
`19565e6458f301aa33fc374cdad9ff401979d06ceb476dd8ebc33a9b4c4a9ee4`.
Changed-profile load geometry consumes the actual new motion receipt as
recorded below; the earlier diagnostic remains immutable.

The parent supplied the new wider-profile
[response](rawlocal/joint-frame-profile-followup/profile-enriched01/receipt.json)
and [action export](rawlocal/joint-frame-action-reconciliation/profile-attempt01/receipt.json),
receipt SHA-256 values
`317f8800d0f1ad947778d4f553a46403b50fbb9d921d0b70f8854928f9994455`
and `ae201061f06ce1d4f8610903279d224c0a3830820d2b2629ef0b579b8fed891a`.
Their complete source/output closures authenticate. Source-only motion
preparation completes in **6.016 s** with **688 source pins**, including the
three explicit absolute identities. Its
[request](rawlocal/joint-frame-motion-bounds/profile-prepare01/request.json)
SHA-256 is
`d40251b033d66c884f1ad88a84f4b51621091f1b3d063e727f4d23a546292e85`;
the preparation [receipt](rawlocal/joint-frame-motion-bounds/profile-prepare01/receipt.json)
is `9b69a1d3ec1ab99f3601be9a2c5c3f49cc333740f784fa439356b3ed90748d39`.
It binds twelve accepted states and fourteen dispositions, with the two
unavailable zero-gap floor branches explicit. Exactly port rows 1530, 1531,
1566 and 1567 change from **3,751.291479** to **5,108.952205 N/mm**. Original
law/audit definitions are reused as definitions only; the new forces, poses,
bearing masks and applied scalar laws supply the actual motion basis.
Preparation executes no LP or project solve and establishes no changed-frame
motion bound or stability result.

The parent subsequently executes that exact request into
[profile-attempt01](rawlocal/joint-frame-motion-bounds/profile-attempt01/receipt.json),
receipt SHA-256
`05ba140821e412da12e4f4b123649f771135d53dfeb197af80186139d691208d`,
summary `07820536d615a6abaec0a19dc20113ad455290c3fc2322eb6af4160e36fe367c`
and certificate arrays
`e2586f90b40e8e196fa5b09bb9b6d460b2d434bad0f6eebdcd52d9efd9a2148b`.
The new motion/source/output hashes authenticate independently. All new
accepted state pointers, body poses, coordinate bounds and nullspaces join
the supplied response and action records exactly.

Source-only load-geometry preparation completes in **9.613 s**. Its
[request](rawlocal/joint-frame-motion-bounds/profile-load-geometry-prepare01/request.json)
SHA-256 is
`19c860afff7a80d469ba64d702f87eb72d4e8498a8cf11ba4c213f0fcda8d93c`.
The resulting [receipt](rawlocal/joint-frame-motion-bounds/profile-load-geometry01/receipt.json)
is `2c2d0f74896a3992c355e1379876e6d9b11c17f2b01ca2280f9eda3171b0bea2`,
and the summary is
`6c6ba499f212755b3313a248888ce50cdf435d2e0ffa8e360a9c84fcba221236`.
It binds **703 source pins**, all twelve fresh accepted states and the full
fourteen-disposition inventory. The unaccepted states acquire no pose or
load-geometry result. The frozen `19565e…` adapter and `04c3d3…` arithmetic
remain unchanged.

The ignored [3×3 launcher](rawlocal/joint-frame-motion-bounds/profile-load-geometry-3x3.py),
SHA-256 `705735e3821a6985ef04e2200b3478e57abc7d3dbff99a7cc42b7734f6f6ac04`,
is pinned by the fresh request. It checks that every external curvature
matrix consists exactly of fifty independent rotational 3×3 body blocks
and 194 zero scaled coordinates, then evaluates its spectrum through those
blocks. Its analytic spectrum coupon passes; the result explicitly records
maximum eigenproblem dimension three and no global eigenproblem. The
launcher adds no tangent or buckling calculation. Source/output hashes of
both completed profile packets and both preserved frame08 packets pass.

```sh
PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-motion-bounds/profile-load-geometry-3x3.py \
  --stage build \
  --request docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-motion-bounds/profile-load-geometry-prepare01/request.json \
  --expected-sha256 19c860afff7a80d469ba64d702f87eb72d4e8498a8cf11ba4c213f0fcda8d93c \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/joint-frame-motion-bounds/profile-load-geometry01
```

The wider-profile motion and load-geometry packets are active downstream
evidence; frame08 and its original geometry diagnostic remain preserved
comparison evidence. All are recoverable and remain source-bound. No raw
packet is removed or archived here.
