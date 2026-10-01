# Joint completion and gravity-start report — October 1, 2026

Updated October 1, 2026 at 09:50 UTC (October 1 in Denver). The native export
assessment below was independently replayed; newer coordinator entries may
supersede this snapshot. Work remains exclusively on `master`.

Docker access is available. The actual frame's unloaded solid stiffness has
been exported and authenticated, and all fifty body numerical elastic gates
pass. The complete 50-body connector reduction now passes its numerical
gates; provenance replay confirms the source-bound attempt 04. Compatible
initial gravity equilibrium and a state-dependent gauge remain the next
support requirements. The first actual gravity-direction selector stopped
at its 45-second solver limit with no feasible solution found. That stop
does not prove the physical system infeasible. The reviewed native
mapping coupons are complete. They prescribe contact events; the full-frame driver
still needs to discover the coupled states and events. This investigation
reads the existing model and rank audit without altering either or launching
a native solve. The FEA coordinator retains implementation adoption, frozen
inputs, serialized execution and final mechanics validation.

The primary has now implemented and independently reviewed the right outer
knee's actual three-case bolt/receiver action join: 126 bolt states, 168
lateral planes and 294 receiver wrenches. This fills a missing right-side
input without reflecting left demands. The primary's subsequent full
right five-body boundary reconstruction covers all 338 modeled interfaces
and reproduces the 105 frozen body residual/radius records. The mechanics
owner has also checked an energy formulation that removes 1,192
ordinary-contact binaries while
retaining the 100 discrete floor episodes. Its algebraic fixture, numerical
factor preflight and final tiny selector replay pass. The actual reduced
selector also reached its search limit without a feasible state.
The 52-bolt source census covers 1,092 existing states: 42 transverse bolts
receive independently checked conditional lateral references. The new additive
end-grain method now computes the other ten bolts' 210 conditional references
while preserving the original scope exclusions. One bottom outer
bolt has a raw scenario ratio of 1.09451 and needs a supported disposition.
The primary's new bottom-joint join now reconstructs all four bolts, three
contact paths and the complete cleat balance in 21 states. Current geometry
already resolves the nominal contact areas an older diagnostic left null;
that stale dependency is removed. Fifteen corruption/applicability tests
pass; independent source review, numerical reconstruction and a full
byte-identical producer replay also pass.
**Three of six conditional frame cases remain usable; no complete joint or
formal criterion is accepted.**

## What prevents a simple startup

The [current rigid-body readiness audit](hypotheses/mvp-acceleration-2026-09-28/current-frame-gravity-rank-readiness-attempt01/README.md)
maps 50 bodies into 300 rigid coordinates. At its declared `1e-10` rank
cutoff, the bilateral-only, all-contact-open branch has nullity 80, including
six common rigid modes and 74 relative-body mechanisms. Six gauge constraints
cannot remove those relative mechanisms. Conversely, its optimistic branch
with every unilateral normal active has three remaining common modes. Neither
branch selects the actual gravity state: the normal laws have zero force at
zero extension and different one-sided tangents.

The [passing ten-stage native coupon](hypotheses/mvp-acceleration-2026-09-28/current-floor-staged-reference-native-attempt01/README.md)
validates the recorded capture/release/re-engagement mapping. Its prescribed
events do not locate frame events or prove compatibility of 100 floor cells.
The gravity-start audit also does not assemble the orientation-aware C3D20
elastic tangent. These are separate missing requirements; passing one does
not close the others.

## Parent's independent numerical cross-check

I reconstructed each rigid spring row directly from its source physical
receiver, application point and scalar direction. For outer-seat ties, the
two distinct seat points were retained. For fixed-floor receivers, the floor
displacement was zero. This reconstruction was compared to the existing
MPC-expanded rows after verifying the audit's 15 source/context pins. No
spring stiffness, coordinate, law, load or stored source result was changed.

The maximum row-coefficient difference was `3.8979930394589246e-13`.
The source model SHA-256 was
`61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8`;
the rank-audit script SHA-256 was
`8034554eaee03b9884bbc9cd9f6a6da51392beac2182d38339a787dfb30c2d90`.
Using the audit's same row/column normalization and cutoff sweep, the
physical-owner all-normal envelope retained rank 297/nullity 3 at all four
cutoffs (`1e-8`, `1e-10`, `1e-12`, `1e-14`). The source-MPC envelope instead
reported rank 300 at `1e-14`. Thus the tightest cutoff can count tiny mapping
residuals as restraints and erase the expected common null modes. It is not
evidence of a physically fully restrained open-tangent frame.

The independently reconstructed bilateral-only branch still has rank
220/nullity 80 at `1e-8` and `1e-10`. Its tighter-cutoff ranks also vary.
This confirms that the practical startup concern is not cured by changing a
numerical cutoff. This is an independent kinematic cross-check, not a new
elastic-rank certificate, gravity solution or accepted gauge.

I also checked the source mesh connectivity: all 50 body inventories are
connected through element adjacencies sharing at least three non-collinear
nodes. All 1,903 physical elements are C3D20. The source coordinates are not
uniformly affine bricks, however; the largest discrepancy from a corner-based
affine 20-node reconstruction is 16.7048 mm. Therefore a regular-cube check
cannot by itself certify every current element's geometry or elastic rank.
This screen does not establish positive Jacobians at integration points,
finished-CAD agreement or complete-frame stiffness.

## Source-backed elastic-operator route

Section 7.63 of the [official CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf)
describes `*FREQUENCY,SOLVER=MATRIXSTORAGE,GLOBAL=YES`: it exports sparse
stiffness and mass triplets with a node/DOF map, then stops. The pinned local
manual's SHA-256 is
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`.
This is a possible way to obtain the solid elastic operator from the existing
solver, rather than implementing another C3D20 element kernel.

I inspected the installed image read-only. Its ID matches the existing
[2.23 build summary](hypotheses/evaluation-resume-2026-09-24/calculix-2.23-upgrade-attempt01/README.md).
The upstream `arpack.c` and `matrixstorage.c` hashes match that build's
manifest, and its recorded Makefile enables `MATRIXSTORAGE`. In the source's
global output branch, diagonals are written once and only one symmetric
off-diagonal triangle is emitted. A reader must reconstruct symmetry without
doubling diagonals and must use the emitted DOF map.

The independently prepared method packet contains one free, rotated
orthotropic C3D20 unit cube and an affine-energy oracle. Its proposed exit
gate is six rigid modes, positive non-rigid stiffness, correct DOF mapping
and agreement with the known affine strain energies and cross energies.
Preparing or passing synthetic reader tests is separate from observing native
behavior. The FEA coordinator owns adoption, exact freeze, serialized native
execution and final validation.

The [method packet](hypotheses/elastic-matrix-export-method-2026-09-30/README.md)
is now implemented and independently reviewed. Parent reproduced its tests:
15 invalid parser fixtures and three corrupted operators are rejected, while
the algebraic 60-DOF oracle passes all six affine modes. Independent tensor
rotation agrees within `2.3e-13`. Review corrected a native connectivity-line
error and documentation provenance; the generator now preserves the required
16-plus-5 entry split. These are code and proposal checks; this particular
free orthotropic deck has not been run.

The coordinator subsequently ran a separately frozen **free isotropic cube**.
Its [native assessment](hypotheses/mvp-acceleration-2026-09-28/current-free-c3d20-matrix-export-native-attempt01/README.md)
passes: 60 equations, six rigid modes, no significant negative stiffness
eigenvalues, normalized rigid residual `3.45e-15`, analytical shear energy and
translation mass. Assessment SHA-256 is
`fea5d33bb8874b3abfa34acfbd15ceca3d8f6dd45d346ecf638cf45ffc0b85f4`.
I independently replayed its source/output authentication on October 1 UTC;
the replay returned `PASS_REPLAY_NATIVE_FREE_C3D20_EXPORT_ASSESSMENT`.
This establishes the built-in export route on that coupon. It does not
establish rotated wood, constrained equation mapping or current-frame rank.
There is no reason to repeat the free isotropic export merely to confirm it.

The coordinator then ran the [constrained export](hypotheses/mvp-acceleration-2026-09-28/current-constrained-matrix-export-native-attempt01/README.md),
reusing the orthotropic packet with an SPC, interpolation MPC and SPRING2.
The native operator has the expected 58 active translations and five allowed
rigid modes. All 36 rotated-material/projected-spring affine cross energies
agree with the independent oracle; maximum discrepancy is
`1.21645e-11 N/mm`. Assessment SHA-256 is
`49805f1f32857ef85ac9650e26e3ed3c1dfcadf0607fe322a3bf833932ff03b7`.
I independently replayed source/output authentication, returning
`PASS_REPLAY_NATIVE_CONSTRAINED_EXPORT_ASSESSMENT`. This verifies the tiny
`K_export = B^T K_physical B` mapping, rather than deletion of dependent rows.
Nonzero reference offsets and applied loads remain separate from the
frequency export; their work identity is an analytical check, not native
capture evidence. The constrained mass matrix was not evaluated.

The [physical connector projection contract](hypotheses/mvp-acceleration-2026-09-28/current-frame-physical-connector-projection-contract-attempt01/README.md)
now supplies 348 bilateral, 1,292 unilateral and 200 separate floor-tangent
rows over 37,647 physical translations, preserving the source ground
projections. It is an input-only rejoin interface for
the exported frame operator, not a gravity solution. Actual operator reduction, body
equilibrium, state selection and continuation still need validation. Do not
infer a unilateral tangent at zero extension from a
frequency export of nonlinear springs, or substitute an auxiliary export
mass matrix for the authenticated gravity loads.

The coordinator's [actual pure-solid frame export](hypotheses/mvp-acceleration-2026-09-28/current-frame-pure-solid-matrix-export-native-attempt01/README.md)
has subsequently completed in 2.342314 seconds with native exit zero. Its
assessment authenticates 37,647 physical translations, 2,320,506 unique
upper-triangle entries, finite positive diagonals, exact reconstructed
symmetry, no nonzero cross-body stiffness, and all 300 physical rigid fields.
Maximum normalized rigid residual is `2.6186013240290654e-13`; assessment
SHA-256 is `ba41b9c75815f7daf27b3517ac01afff109d5f3e3611aa985811e92c269e69ec`.
Primary replay returned `PASS_REPLAY_AUTHENTICATED_PURE_SOLID_EXPORT`. This
settles obtaining the source solid operator, not its complete elastic rank or
a frame response. A checked reaction-free per-body reduction must preserve
the six physical force/moment balances of every body before gravity/state
selection can use that operator.

The coordinator has now completed the [actual 50-body numerical elastic audit](hypotheses/mvp-acceleration-2026-09-28/current-frame-body-elastic-positivity-audit-attempt01/README.md).
Every isolated body passed rigid-lift Cholesky and reciprocal-condition checks;
the minimum estimated reciprocal condition was `9.93942622e-11`, above the
declared `1e-12` floor. The source stiffness was unchanged. Primary authenticated
the recorded audit against its source pins without repeating its heavy run;
assessment SHA-256 is
`2ad8c74b4a061ee9335c3b9f3549f325929be9148d1753f370998ec5e681c563`.
This clears the recorded numerical elastic gate for reduction. It supplies
no physical restraint, gravity state or new response. Compliance construction
must keep every raw body wrench in the explicit 300 force/moment equations;
projecting an intermediate elastic right-hand side cannot silently remove
an unbalanced physical load.

The first [actual connector-compliance reduction](hypotheses/mvp-acceleration-2026-09-28/current-frame-connector-compliance-attempt01/README.md)
has since stopped on one numerical gate: the largest panel's projected basis
columns 16–32 had relative residual `7.23261944e-10`, exceeding the fixed
`1e-10` threshold. Gauge and multiplier checks passed separately. Extended-
precision evaluation of the same solution still gives `3.00920477e-10`, so
changing evaluation precision alone does not resolve it. No compliance
operator, force or contact state was accepted. Primary authenticated the
recorded stop without rerunning the reduction. This is a numerical stop,
not a demonstrated panel or joint failure. The coordinator owns a bounded
iterative-refinement check on the exact rejected chunk, with unchanged source
stiffness and gates, at most five corrections, and explicit stagnation stops.
That bounded check subsequently cleared the panel chunk in one correction:
extended force residual fell from `3.0092e-10` to `3.8855e-11`.

Connector-compliance attempt 02 then completed all four panels and stopped
at `kicker_left`, interface columns 16–31. Its force residual and displacement
gauge pass, but the multiplier stabilizes at `1.6435e-9 N`, above the
unchanged `2e-10 N` limit. Primary authenticated this attempt's record without
rerunning the reduction. It still accepts no complete compliance operator,
force, state or fourth usable case.

The coordinator's exact stopped-iterate diagnostic attributes that multiplier
to the frozen operator's nonzero rigid-mode coupling: predicted
`1.6435145875e-9 N`, observed `1.6435112275e-9 N`, with component discrepancy
at most `7.7259e-15 N`. Primary replay returned
`PASS_REPLAY_KICKER_RIGID_LEAKAGE_EQUATION_DIAGNOSTIC`. This is a causal
numerical diagnosis, not joint failure. The pinned writer's 14-significant-digit
serialization is a possible contributor, not a proved sole cause. A distinct
elastic quotient/projection method needs a known-answer check and an explicit
original-operator error disposition before another full reduction. Repeating
the same refinement or relaxing the old limit does not resolve this stop.

The coordinator's subsequent read-only screen found all fifty original body
operators within its proposed rigid-leakage limit. The new quotient-method
review required bounded refinement with extended-precision audits, physical
gauge-wrench reporting as `(R^T R) lambda`, and actual rigid-equation closure.
Those method concerns precede the later reduction and do not erase either
preserved stopped attempt.

The coordinator's attempt 04 (local packet
`hypotheses/mvp-acceleration-2026-09-28/current-frame-connector-compliance-attempt04/`,
pending that owner's publication)
subsequently cleared all fifty bodies in 34.382 seconds. Its aggregate gate
propagates the unchanged nodal residual budget through the rigid-mode map
and separately gates measured arithmetic-order error. The original exported
stiffness and the recorded nonzero multipliers remain preserved. Maximum
chunk nodal relative residual is `9.2617201e-11`; full `H` reciprocity error is
`9.3832183e-11` against the `1e-8` gate, with symmetric-part minimum eigenvalue
`+2.3942328e-10 mm/N`. Primary independently replayed provenance, returning
`PASS_COMPLIANCE_RECORD_PROVENANCE PASS_SOURCE_BOUND_FRAME_CONNECTOR_COMPLIANCE`.

This clears the elastic reduction gate: `H` is 1840×1840, `D` is 1840×300,
`e` is 1840×12 and `W` is 300×12. The twelve load columns preserve separate
gravity/climber pairs for the six cases. Physical solutions still require
`D^T f = W` and `q = D a + e − H f`, compatible source laws and captured floor
history. The retained original force/moment residuals in intermediate basis
columns are not accepted physical-response residuals. No gravity-settled
state, fourth usable case or joint strength follows from this numerical gate.

Primary also replayed the [six-case source identity contract](hypotheses/mvp-acceleration-2026-09-28/current-six-case-operator-reuse-contract-attempt01/README.md)
and [free-body condensation fixture](hypotheses/mvp-acceleration-2026-09-28/current-free-body-elastic-condensation-fixture-attempt01/README.md).
The former verifies twelve source equality groups and six distinct load maps;
it avoids five redundant elastic exports without transferring any state,
force or pass. The latter checks independent constant-stress surface traction
loads on the authenticated free cube and rejects an unbalanced point load
before using the elastic inverse. It is a small method check, not the actual
50-body reduction. Both results advance named dependencies in the gravity
implementation; neither adds a fourth usable case.

The coordinator subsequently found a load-map labeling error. The projection
packet's preserved `source-gravity-nodal-map.json` contains combined A12
gravity and climber loads, not gravity alone. The [separated-load audit](hypotheses/mvp-acceleration-2026-09-28/current-physical-load-map-audit-attempt01/README.md)
verifies every source node in all six cases. A12 combined force is approximately
`(0,+300,-4424.926817) N`; its gravity is `(0,0,-2200.816010) N` and climber
force `(0,+300,-2224.110808) N`. Primary replay returned
`PASS_SIX_CASE_SEPARATED_LOAD_RECOMPOSITION_WITH_EXPLICIT_LABEL_ERRATUM`.
Gravity settling must use the pure-solid preflight packet's separated
`gravity_nodal_map`, then add its case-specific `climber_nodal_map` during
the ramp. No response was calculated from the mislabeled map; the unloaded
stiffness and connector rows are unaffected. Earlier gravity-only wording
for that preserved projection file is superseded.

The pinned parser also explains the native warning on explicit `GLOBAL=YES`:
it defaults to global output and recognizes only `GLOBAL=NO` as an override.
The ignored redundant YES leaves the observed global node/DOF map unchanged;
the numerical export oracles still pass. Future new decks should omit that
token. This specific source/log reconciliation does not waive other warnings
or require a rerun merely to remove the redundant token.

## Concrete implementation consequence

The next support implementation must resolve the gravity branch and its
normal signs together, then demonstrate the nullspace and reaction-free
gauge of that actual state. It must preserve the existing gravity nodal
forces and first moments, the source unilateral laws and all-body/global
balance checks. Any relative mechanism in the actual branch stops readiness;
it cannot be removed as a common-coordinate gauge.

Once the gravity branch is established, the driver must localize opening
and re-engagement events, release tangents at opening, and capture their
measured reference coordinates at bearing events. No-state, incompatible
multiple-state, cycle and exhausted-budget outcomes remain explicit stops.
The [mapping preflight](hypotheses/mvp-acceleration-2026-09-28/current-staged-floor-native-mapping-preflight-attempt01/README.md)
already records these requirements; another prescribed-event coupon would
not by itself implement them.

The coordinator has also verified a borrowed SCIP/PySCIPOpt
[indicator selector](hypotheses/mvp-acceleration-2026-09-28/current-coupled-indicator-selector-fixture-attempt01/README.md)
on eight tiny, source-pinned fixtures, including ambiguous, infeasible and
multiple-state cases. It uses signed unbounded unknowns without a supplied
finite big-M, and exhaustion of its budget stops without a completeness claim.
This supplies a tested small-state selection method. It does not establish
100-floor-cell scalability, discover events or provide the frame's gravity
state. Neither this fixture nor the matrix coupon adds a usable frame case.

The coordinator then froze and ran the actual A12 gravity-direction selector
(local `current-a12-gravity-direction-selector-attempt01/` packet, pending
that owner's publication). It retained all 1,840 force/extension coordinates,
300 raw body coordinates and 100 coupled floor cells. SCIP stopped at its
45-second limit, with zero feasible solutions and 46.823 seconds total
elapsed. Parent independently authenticated its thirteen source pins, input
record and output pin. No finite gravity state, branch-rank result, uniqueness
or infeasibility proof follows, and three rear cases remain usable. No
automatic larger-budget or guessed-mask retry is queued.

Parent also personally inspected the stopped formulation. A separate
[read-only relaxation review](hypotheses/gravity-selector-relaxation-review-2026-10-01/README.md)
proves that unconditional `f >= 0` and `f >= k*q` are implied by every one
of its 1,292 positive-stiffness unilateral row laws. Adding them preserves
the integral source-law states and may strengthen the elementary indicator
relaxation. It does not replace complementarity or apply to signed bilateral
or floor-tangent forces. Independent review confirms the proof and source
binding. Whether SCIP already derives equivalent bounds during processing,
and whether an explicit addition improves runtime, remain unmeasured.
This is a bounded formulation recommendation for the mechanics owner, with
no changed solver method, new fixture campaign or actual-frame retry.

The mechanics owner subsequently pursued a more substantial formulation
change. Its local `current-primal-energy-condensation-fixture-attempt01/`
known-answer packet establishes, for symmetric positive-definite compliance,
ordinary unilateral spring forces through convex hinge energy rather than
binary indicators. It retains all 100 coupled floor episodes and their
original sign/reference laws. A constrained energy minimum can carry an
extra floor-normal bound reaction: the fixture detects and rejects a
0.5 N example rather than accepting the optimizer's label. Zero-force
ambiguity and distinct admissible masks also remain explicit outcomes.

The owner's single `current-frame-convex-energy-factor-preflight-attempt01/`
factorization of the declared symmetric part of the actual 1,840-row
compliance passes in 2.149 seconds: reciprocal-condition estimate
`2.4413446e-11`, reconstruction residual `3.58e-16`. Raw compliance is
preserved. A separate existing-A12 diagnostic bounds the observed action of
the symmetrization at `7.174e-10 mm` across seven increments and keeps the
original response checks unchanged. These are numerical method results,
not an accepted gravity solution or a new frame case.

The final tiny `current-floor-binary-convex-energy-adapter-attempt01/`
adds prescribed-mask OSQP recovery and original-law audits after its first
SCIP optimizer candidate failed force-recovery precision. The mechanics
owner's final stable replay passes all 24 masks in eight analytical cases,
the raw-wrench oracle and a nonzero raw-operator skew audit, without widening
any tolerance.

The owner then froze and ran one actual reduced
`current-a12-gravity-direction-convex-selector-attempt01/` application.
Construction took 1.102 seconds and presolve 1.15 seconds. The 45-second
search limit expired at one processed root node with zero feasible solutions
and no candidate force vector; total elapsed time was 47.092 seconds. The
presolved problem still has 100 binaries, 5,873 continuous variables, 3,732
linear constraints, one nonlinear energy constraint and 600 indicators.
Recorded provenance passes. The solver log does not identify which root-node
subroutine consumed the remaining time. The owner's subsequent local
`current-a12-root-relaxation-diagnosis-attempt01/` source audit identifies
a specific risk: the energy formulation has unbounded body coordinates and
a linear gravity-work term. An exact compatibility-null direction with
nonzero gravity work would make a branch's objective unbounded; zero work
would leave a flat coordinate. The existing cutoff-sensitive rank screen
does not prove such an exact direction or evaluate gravity work on all 74
additional all-open relative mechanisms. The log therefore remains a timeout,
not an unboundedness or physical-infeasibility certificate.

The proposed bounded check adds the original equilibrium equality
`D.T*g = W_g` to the existing tiny fixtures and includes balanced and
deliberately perturbed gauge/load examples. Every exact physical branch
already obeys that equality; its effect on the relaxation is unmeasured.
It cannot remove a true compatibility-null recession or replace independent
law, gauge and original-operator checks. The mechanics owner retains this
method work; no duplicate fixture, arbitrary anchor, load projection,
larger-budget or guessed-mask frame retry is queued by the primary.

This second stop proves neither physical infeasibility nor failure of a
joint. A new bounded search method must settle the identified frame-scale
limitation while retaining original-operator, body, law, sign and history
checks. Rejecting one energy minimizer cannot exclude other floor branches.
The primary has not rerun these owned solves, adopted the approximation, or
widened any physical response gate.

The mechanics owner's newer fixed-episode reproduction work is separate from
discovering gravity. Its adaptive-rho QP returned `solved` in 0.652 seconds
and 1,250 iterations, but failed 69 original force-token and 30 projected-q
interval comparisons, plus one small negative unilateral-force gate. All
300 rigid-coordinate interval comparisons pass. The candidate remains
rejected, rather than gaining acceptance from the optimizer status.
Primary authenticated this local attempt-02 record's 39 source pins,
assessment/output join, freeze and diagnostic-candidate hashes without
rerunning it. The assessment SHA-256 is
`ca52e94df2937fee7a2cf7a310c77f5251a3a6087a2ea930e855aee5c01205a0`.

The next bounded precision method and direct fixed-active-set KKT preflight
are still owner-held local preparations at this snapshot. The latter
estimates 734 nonfloor zero-force rows from the existing candidate, retaining
all floor normals separately, and requires strict source/sign checks after
an unregularized solve. Neither preparation is an executed result, a new
selected floor state, a gravity settlement or a fourth usable frame case.
This identifies the current numerical issue more precisely than saying that
Docker or stiffness export is blocked: reproduction accuracy and gravity-state
discovery remain distinct unresolved steps.

## Right-corner load-path input

The primary personally implemented the
[right outer-knee source join](hypotheses/right-corner-signed-load-path-2026-10-01/README.md)
using the pinned A1/A12/K12 responses. It checks six modeled right bolt axes,
eight lateral planes and the separate outer-seat ties, including both planes
of each three-receiver side bolt. Saved local RF components, global force
bases, signs, source rows and rounding radii agree. The join covers 126 bolt
states, 168 plane states and 294 receiver wrenches; internal force/couple
bookkeeping and five corrupted-record rejection checks pass. An independent
Luna/max replay reconstructed every receiver force, transported couple and
component radius exactly from the pinned response records.

All eight lateral-plane peaks occur at K12 full load. The largest selected
per-bolt receiver force is 525.919473 N on `base_side_right`, `side_1`,
with simultaneous transported-couple magnitude 24,873.090030 Nmm about that
bolt's modeled head-seat point. This couple is force transport to a common
datum, not internal bolt bending. Finished sections, resistance and
combined behavior remain open. No left-corner
force, capacity or pass was transferred, no native response was produced,
and the reviewed geometry was preserved.

The subsequent
[full right five-body boundary](hypotheses/right-corner-whole-boundary-2026-10-01/README.md)
includes the entire shared header and every source connection touching those
five bodies. Each case contains 392 scalar carriers grouped into 338 physical
interfaces, with 42 internal and 296 boundary interfaces forming 62 boundary
port groups. The adapter retains all selected/released floor tangents rather
than guessing zero actions, along with panel/screw, retained-frame and
neighboring-member transfers. Source nodal loads, descriptor reporting datums,
all five body residuals and their force/moment rounding bounds reproduce the
existing all-body audits at every one of the 21 states. Independent Luna/max
source-endpoint replay also reproduces all 105 body checks and 21 assembly
sums. The body limits stay 0.1 N and 2 Nmm. Assembly cancellation is a bookkeeping check; the net
boundary resultant cannot stand in for the individual joint/section actions
that cancel within it. This adds no strength result or new frame case.

## Continuous-bolt method dependency

The mechanics owner's local
`current-bg003-anisotropic-clearance-point-law-fixture-attempt01/` now passes
its seven known-answer gates, including a mixed-direction force oracle,
isotropic and zero-clearance limits, rotation and independent energy/tangent
differences. Its point law minimizes an anisotropic quadratic over a circular
free-clearance disk and keeps the coupled Y/Z response. Parent replay passed.
This is a constitutive hypothesis, not calibrated timber bearing or joint
resistance. The mechanics owner has subsequently completed the declared
eight A12 bolt-1 density/mesh/clearance proxies in 23.58 seconds, under one
parent-held lock and the frozen 180-second/6-GiB caps. No native solve was
launched. Its local `current-bg003-anisotropic-clearance-finite-adapter-attempt01/parent-results.md`
records `PASS_BOUNDED_PROXY_ONLY`, with no joint acceptance. Primary
authenticated all 22 frozen source pins, the input/assessment join and result
SHA-256 `ad3f95de06884b2a1f63d982fa67dfee8128a2fed0c77a20cedc0624fc1de3c5`
without rerunning the owned finite suite.

All eight proxy states pass the declared free-degree equilibrium, receiver
force/first-moment closure, gauge and free-end gates. Signed middle actions
and sampled peak couple change by less than 0.276% between 16 and 32
divisions. Sampled pressures instead change by up to 4.27% in the reported
clearance comparisons; no 1% pressure-refinement pass is claimed. The
pressure proxy is not a washer pressure or an applicable Fc-perpendicular
check. Clearance lowers sampled peak bending but raises sampled bearing
pressure, so neither scenario establishes a general upper bound. The result
covers only A12 bolt 1 and its hypothetical law/densities. Applicable bearing
and combined-joint methods, shared two-bolt receiver behavior, splitting and
axial/thread/washer/steel interaction remain unresolved. The owner has stopped
this bounded suite rather than enlarging its parameter/mesh campaign.

## Remaining two-receiver bolt references

The new [52-bolt packet](hypotheses/remaining-single-shear-reference-2026-10-01/README.md)
extends source-bound lateral arithmetic beyond the primary corner and upper
owner's cohorts. It includes four simple right post/header bolts and excludes
the two right continuous three-receiver bolts. All 1,092 source states join
their actual lateral-plane forces, separate outer ties, receiver intervals
and conditional grain maps. Forty-two transverse-to-grain bolts supply 882
reference rows; ten end-grain-axis bolts retain 210 explicit null-reference
and null-ratio rows under the reused method's scope boundary. The existence
of NDS end-grain provisions is acknowledged; this original packet does not
apply them. The later additive packet below does, with its own method boundary.

Parent's complete replay and independent six-mode NDS closed-form calculation
agree on 10,584 eligible comparisons within `9.70e-16` relative difference.
Both main/side assignments agree after mapping the role-labelled modes.
The largest raw comparison is
`bottom_outer/clip_horizontal_bottom_left_1/side_1`, A1 rear full load:
661.948743 N / 604.790663 N = **1.094508867**, Mode IV. This uses an unadopted
45,000-psi Fyb and nominal smooth-body quarter-inch scenario. It is a named
strength-disposition dependency, not an adopted joint failure; ratios below
one are likewise not passes. Applicable properties, adjustments, group,
geometry, splitting and combined behavior remain open. The reviewed model
was not changed. Published code, summaries and independent review leave the
raw record local.

The primary has now implemented the separate
[ten-bolt end-grain packet](hypotheses/end-grain-single-shear-method-2026-10-01/README.md).
An independent source review supports a conditional main-member assignment
to each axis-parallel cleat/block, independent of modeled head/nut convention;
the transverse side member is `base_header` on all ten axes. Extending AWC's
explanatory bolted-role guidance to the NDS main-member end-grain clauses is
recorded as engineering interpretation, not explicit normative wording.
The source-authenticated census preserves all 210 original state rows. The
new calculation uses main `Fe⊥ = 4,450 psi`, the header's actual load/grain
angle, `Kθ = 1.25`, and `Ceg = 0.67` once on the six-mode reference `Z`.
Simultaneous axial ties stay separate.

Independent closed-form verification and parent replay pass all 1,260
unadjusted and 1,260 once-adjusted mode comparisons; maximum relative mode
differences remain below `8.1e-16`. Ten focused tests and Ruff pass. The
separate calculation review retains source rows, geometry/grain identities,
the five/five modeled seat split and the explicit claim limits.

The largest new `Ceg`-only scenario ratio is **0.302778140**, on
`center_principal_header_left_2` at K12 rear full load:
120.091599 N / 396.632330 N, Mode IV. All ten axes have 21 rows. These
are conditional lateral references, not complete-joint acceptance or fully
adjusted design ratios. The earlier producer/output and its null fields are
unchanged. Both packets explicitly distinguish the unadopted quarter-inch
45,000-psi bending-yield hypothesis from material qualification: Table 12A's
displayed diameters begin at 1/2 inch, and Table I1 / the TR-12 example's
`D ≥ 3/8 in` basis also does not qualify a quarter-inch bolt. No favorable
material or adjustment has been adopted to turn an exception into a pass.

## Parallel washer input result

The new [primary-corner support checker](hypotheses/corner-washer-support-2026-10-01/README.md)
uses the four authenticated current-finished STEP members and the saved seat
map. All twelve outer seats on six BG001/BG003/BG045 bolts support the full
modeled CAD annulus and both catalog dimensional extremes. Inward support
fractions are 1.0 and outward overlap is 0.0 at 0.01, 0.05 and 0.1 mm probe
depths; the maximum matching face-plane offset is `2.274e-13 mm`. BG003 keeps
its middle receiver without adding a middle washer. This settles the
geometry-only annulus support input for these saved solids. It does not prove
physical flatness, pressure distribution or washer resistance, and it does
not cover the other 86 candidate bolts. The check is coaxial at the nominal
saved seat poses. A subsequent [eccentric washer screen](hypotheses/corner-washer-eccentric-support-2026-10-01/README.md)
now covers washer play and separately combined bolt/bore clearance for the
declared 6.35-mm nominal smooth-body scenario and 7.5-mm wood bore. All twelve
finished seats contain the full swept radial region from 3.75 to 11.0652 mm,
with outward overlap zero at the three probe depths. This checks every
in-plane direction within the frozen solids and kernel tolerance; discrete
direction samples also agree with the circle-overlap formula within
`9.7e-10 mm²`. For the plain catalog washer's minimum OD and maximum ID,
the combined scenario leaves `206.013152 mm²` supported area. The bore causes
a small unsupported crescent that the earlier coaxial result did not describe.
These are conditional geometry inputs, not wood pressure or washer strength.
The nominal body is not a delivered-shank lower bound; bolt tilt, seat drift
and fabrication tolerance remain outside this check.

Primary review corrected the checker repository path, required actual
rejection tests for clipping and embedded/reversed seats, and added an
outward protrusion fixture so full support cannot hide an obstructed washer
face. Review of the eccentric extension also found and corrected a success-exit
path that could report failed envelopes: its check now rejects failed support,
outward obstruction and failed/nonfinite direct area comparisons. Parent
replayed the geometry and rejection fixtures; an independent reviewer replayed
the same frozen bytes. The [method note](hypotheses/corner-washer-method-investigation-2026-10-01/source-note.md)
identifies a conditional contact-resolved elastic metal-demand calculation:
it can report required minimum yield after the footprint, coupled actions
and contact model are bound. Missing catalog yield need not stop that demand
calculation. The existing clamped thin-annulus benchmark cannot be treated as
the current washer model. Direct Grade 5 tensile yield also remains distinct
from the NDS dowel-bending input. The subsequent
[specification-source disposition](hypotheses/fyb-specification-basis-2026-10-01/README.md)
confirms the NDS tensile-yield route and corrects the Appendix attribution.
A delivered-bolt test need not block conditional sensitivity arithmetic;
106 ksi remains an empirical estimate, with no demonstrated guaranteed
minimum or adopted product-specific F606-derived basis.

The new [bearing-footprint input review](hypotheses/washer-bearing-footprint-inputs-2026-10-01/parent-review.md)
also separates the head's offset-plane gauge circle from its unknown actual
bearing-plane profile. Nut chamfer/countersink limits support a declared
concentric flat-face scenario, with source alignment/runout bounds retained;
they do not supply a guaranteed contact area or uniform pressure. Parent
took over the full-clause inspection after the worker's delayed source trace.
This supplies a concrete contact-model input handoff, with no native launch
or resistance adoption. The subsequent
[catalog material-option review](hypotheses/catalog-washer-yield-basis-2026-10-01/parent-review.md)
also corrects an overly restrictive prerequisite: source-covered Unistrut
P1062 and Eaton B200 steel fitting defaults support conditional 33,000-psi
yield floors without a new delivered-lot certificate or physical test for
option comparison. Their oversized square geometry and larger bores remain
unverified replacements. Those properties cannot be transferred to the
current `25NWUS` washer, and no washer capacity or replacement is adopted.

Direct parent inspection of the pinned standard and an independent review
also corrected the [thread-gage source interpretation](hypotheses/thread-gage-functional-fit-2026-10-01/source-note.md).
`LG` is the stopped special-ring face coordinate, `LB` ends at the last thread
scratch, and nominal `LT` is a calculation reference. A nut envelope lying
between `LG,max` and the minimum tip does not establish full-form thread
coverage or matched nut travel. BG001's current four-inch scenario is not
shown unfit. A 3.75-inch standards scenario clears the recorded dimensional
comparators, but is not a selected product or approved model change. The
remaining conditional inputs are explicit male first/last complete-thread
coordinates and matched nut active-thread/chamfer bounds. No received-piece
inspection is required to calculate a declared profile; these standard
coordinates alone do not supply that profile or engagement resistance.

The [direct retained-wrench CAD investigation](hypotheses/retained-wrench-cad-lead-investigation-2026-10-01/source-note.md)
also resolves one stale source lead: the Olander page is reachable, but its
live anonymous CAD availability response rejects Wera `05073287001` as an
invalid product key and leaves its model button disabled. A visible CAD label
does not supply tool geometry. A separate manufacturer lookup recovered the
exact Wera 3/4-inch family's length, mouth width/thickness and ratchet
width/maximum height; parent checked its rendered table. Those dimensions
narrow an envelope proposal but do not supply a complete contour or engagement
datum. The four 3/4-inch retained leg-bolt tool checks
remain a specific source gap; repeating that public lead will not establish
access. Conditional source-supported tool models can be evaluated before
physical receiving.

Disposition: the investigation identifies a startup and rank-interpretation
issue. It authorizes no extra floor restraint, revised geometry or native
launch, and adds no blanket external sign-off or physical floor test. Usable
conditional responses remain the three rear cases; complete joint acceptance
and the full six-case requirement remain open.

## Remaining 54 bolts' washer seats

The primary took over a stalled implementation and completed the
[remaining-seat checker](hypotheses/remaining-candidate-washer-seats-2026-10-01/README.md):
54 candidate bolts, 108 outer seats and 26 actual finished STEP members.
The partition excludes the six reviewed corner bolts and the parallel upper
owner's 32 axes, without overlap. All 108 seats are covered; 107 meet the
declared centered and continuous eccentric geometry gates. The full check
correctly exits 1 for its one explicit exception.

On `center_principal_right_2`, the nut washer's receiver is
`base_principal_center_right`. The retained 38.1 mm F1–G1 service passage cuts
21.1486664 mm² from the nominal washer footprint: 90.5046352% of the centered
CAD annulus is supported. Independent source/STEP and circle-intersection
checks agree at all three probe depths. The swept enclosure also fails at
this seat, so the checker marks its hole-only-area approximation inapplicable.
This requires a supported partial-contact/washer-metal/wood method or a
reported and reviewed design option. No geometry was altered and no adopted
strength failure or joint pass follows from the finding.

The plain catalog washer and 6.35 mm bolt body remain conditional envelopes;
they are not delivered dimensions. Tilt, drift, real-seat tolerance, pressure
distribution and washer strength remain outside the geometric screen. A
new [signed-action join](hypotheses/remaining-candidate-washer-demands-2026-10-01/README.md)
now reconciles these 54 axes with the three existing accepted response
families: 1,134 unique ties and 2,268 head/nut seat actions. It retains 1,106
positive tensile actions and 28 display zeros, with no negative tie forces.
The largest recorded action is 231.1119 N in A1 rear on the bottom-left outer
`side_2` bolt. The partial-support nut seat carries 3.736414, 41.45025 and
64.40226 N at A1, A12 and K12 full load, respectively. Its exception is retained
at all 21 states. This supplies source-bound demand inputs, not a new native
response, partial-contact resistance or six-case completion.
Independent replay found no material source-join or sign defect. Parent also
rejected six deliberately corrupted source records; these checks verify the
join's guards, not the physical capacity of a joint.

Parent has now implemented and independently reviewed a
[nut-projection check at that partial seat](hypotheses/partial-seat-nut-footprint-2026-10-01/README.md).
It binds the passage record to the actual STEP cylinder, including its
50.95–89.05 mm axial extent. The nearest passage edge is 6.559876 mm from
the bolt axis. Under the declared nominal body/bore play and nut-axis offset,
a circular end-face enclosure of radius 6.260104 mm leaves 0.299772 mm
clearance; an enclosure covering the full hex silhouette has radius
7.111004 mm and reaches the passage by 0.551128 mm. Both are explicitly
geometric scenarios. A chamfer-circle limit is not a guaranteed pressure
patch, and failure of an enclosing disk is not proof of actual nut failure.
The washer annulus remains partial; contact, bending and wood resistance
remain open. The checker correctly returns the geometric exception rather
than silently substituting the smaller face for the complete hex.

The parallel [upper-block packet](hypotheses/upper-block-strength-2026-10-01/README.md)
is now published. Parent replay confirmed its 64 nominal seats and 1,344
seat states. Combining its seats with the twelve primary-corner seats and
the 108-seat extension covers **all 184 candidate outer seats nominally**:
183 satisfy their declared nominal support screens and one is partial.
The primary's subsequent [upper eccentric extension](hypotheses/upper-washer-eccentric-support-2026-10-01/README.md)
covers those 64 seats under the same declared nominal-body and catalog
clearance method. All 64 meet the swept support and near-face clearance
gates; 768 direct area comparisons agree within `3.2869e-6 mm²`.
Across the three cohorts, all 184 seats now have conditional eccentric
screens, with 183 meeting their declared geometry gates and the same one
partial-support exception. Real shank/bore/seat tolerances, tilt and contact
pressure remain outside that geometry result.
It also records top-outer lateral demand/reference ratios 1.1631 left and
1.3667 right under an unadopted 106 ksi bending-yield estimate. Those are
conditional component comparisons requiring an applicability/material/
adjustment disposition, not adopted joint failures or passes. Exact sampled
block sections, signed actions and nominal washer evidence are useful inputs;
splitting, metal bending, combined behavior and all six cases remain open.

The parallel owner's subsequent
[upper outer load-path implementation](hypotheses/upper-outer-load-path-2026-10-01/README.md)
is now published in commits `d63bd7c9` and `1aaac459`. It covers 42 block
states, 672 native connection transfers and 84 host-interface states with
same-state force/couple and splitting-input records. Its tests and three
replays pass under independent review. The modeled gross block elements
omit the finished bores; neither point-cut nor selected-node-cut actions
are accepted as tractions in the finished ligaments. The packet therefore
advances load-transfer inputs without resolving the two lateral comparisons,
cleat splitting or complete-joint interaction.

The upper owner's [stock reconciliation](hypotheses/current-stock-envelope-reconciliation-2026-10-01/README.md)
is now published in `e853af55` and `5b10b4e0`, following 68 tests, two exact
replays and three independent reviews. All 44 proposed starting boxes and
the four prepared sections contain their bound finished solids. Fifteen
declared stock-length/trim scenarios preserve each remnant's original
section. All eight-foot-only scenarios leave five blanks unplaced: header,
two center principals and two sides. The principals and sides exceed that
nominal length; the header misses the declared full trailing-kerf convention
by 0.025 mm even with zero trim. The longer-option scenarios place all 44.
These are bounded heuristic geometry/length results, not optimized purchase
quantities, delivered-board findings, post-rip grade or a cost/yield guarantee.

## Bottom outer left joint disposition

The primary personally implemented the
[bottom joint source join](hypotheses/bottom-outer-joint-disposition-2026-10-01/README.md)
after tracing the 1.0945 flag to the simultaneous source actions. The exact
current graph and face atlas already establish two 10,552.972706618 mm²
cleat mating regions and a separate 5,322.57 mm² direct rail/side region.
The older WJ24 gross/null-area field is superseded for nominal geometry;
another geometry study is unnecessary for that dependency.

The additive producer covers four bolts' 84 unchanged reference rows, 252
contact-cell states, 63 pair states and 21 complete cleat free bodies. The
cleat boundary has exactly four lateral planes, four separate outer-seat
ties and eight cleat contact cells, plus its original source nodal body loads.
All balances reproduce the original audits under `0.1 N / 2 Nmm` gates.
The largest component residuals are `8.5072e-5 N` and `0.00354334 Nmm`.
The host-to-host contact is recorded separately because it does not touch
the cleat. Full host boundaries and finished-section strength remain open.

There are 112 resolved compressive and 140 resolved open cell states. Peak
modeled cell averages are 0.0469223 MPa on rail/cleat, 0.2345213 MPa on
side/cleat and 0.3118800 MPa on direct rail/side, all at A1 full load.
The conditional 625-psi perpendicular-grain context applies only to resolved
compression on appropriately oriented receivers. Open/ambiguous ratios are
null; the direct rail receiver is parallel to proposed grain and explicitly
excluded. These averages are not physical pressure peaks or accepted bearing
utilizations.

Source/code review found and resolved the open-cell comparison and force-radius
attribution gaps. Fifteen meaningful source-guard tests and Ruff pass.
Independent numerical reconstruction checks all 504 native scalar force
components and all 21 balances; a full producer replay is byte-identical.
Parent also ran that verifier successfully, with zero force/moment interval
excess. The
NDS method review also confirms that exactly quarter-inch bolts do not receive
the smaller-diameter exemptions for group and geometry adjustments. Group
row/load applicability must still be established. The actual paired stations
are 33 mm apart, along different
receiver grain directions; applicable group/local-stress and adjustment
inputs are recorded in the
[adjustment note](hypotheses/bottom-outer-joint-disposition-2026-10-01/adjustment-applicability.md).
A rail-cleat parallel-tension end-distance sensitivity is 0.975253; its
classification is conditional and it does not transfer automatically to the
flagged side bolt. Nonzero axial ties also require applicable angled-to-fastener
and axial bearing checks under NDS §12.3.9 and any applicable equivalent
shear-area check under §12.5.1.2(b). The source-plane reference does not
complete those checks.

The `side_1` bolt's 661.9487434 N lateral action and separate 197.1248 N tie
remain unchanged. Its 604.7906633 N Mode IV reference uses an unadopted
45-ksi quarter-inch scenario. Contact compression does not reduce that
actual bolt action or resolve the raw ratio. A supported hardware/material,
adjusted group, local finished-section and combined-joint disposition is
still required. No reviewed geometry or native response was changed.

## Work remaining for the complete conditional package

The persistent goal is the complete conditional MVP-E package for
`compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. Completing a method coupon or the
left corner alone does not complete that goal. The
[completion handoff](luna-max-completion-handoff.md) defines the endpoint;
[criteria.json](criteria.json) retains 36 migrated safety questions and eleven candidate
obligations, with no formal passing dispositions yet. That register is not a
measure of zero engineering progress: several source, demand and method
dependencies now have useful evidence. Final closure requires integration of
applicable evidence, not a reinterpretation of pending entries as passes.

| Workstream | Evidence available now | Remaining engineering result |
| --- | --- | --- |
| Current-frame gravity and six cases | Three authenticated conditional rear cases, A12/A1/K12, each with seven accepted states. All six source loads pass the necessary normal-resultant footprint screen. The actual pure-solid operator is exported; source/map/rigid-field checks, all fifty body numerical elastic gates and complete connector reduction now pass. Both the first actual selector and the subsequent reduced energy selector exhausted their 45-second search limits with zero feasible solutions, no candidate and no infeasibility proof. The mechanics owner's energy fixture, symmetric-compliance factor and final 24-mask tiny adapter replay pass; actual-frame root-node runtime diagnosis is ongoing. | Establish compatible gravity, actual branch nullspace and reaction-free gauge from the source-bound reduction and all 300 body balances; discover capture/release events; validate one currently unusable forward/left/right case, then finish all six cases and applicable sensitivities under unchanged response gates. Necessary statics, tiny fixtures, solver time limits and convergence alone cannot supply these results. |
| Complete joint resistance | Audited left-corner exports retain 168 signed lateral-plane states, simultaneous physical ties, section actions and onward transfers. The [whole-assembly transfer summary](hypotheses/mvp-acceleration-2026-09-28/current-corner-whole-assembly-transfer-attempt01/README.md) records the connected left boundary coverage. The right-corner join adds 168 right-plane states and 294 same-state receiver wrenches; its full five-body extension reconstructs 338 interfaces and 105 body states. The published upper packets supply eight blocks/32 bolts and the top-outer load-transfer/host inputs. The remaining 52-bolt census joins 1,092 states: 882 transverse conditional reference rows, plus the separate end-grain packet's 210 conditional Ceg-only rows with unchanged original exclusions. The bottom-left joint now joins its four bolts, three contact paths and complete cleat balance in all 21 states. | Resolve actual continuous three-receiver BG003 bearing/steel behavior, mixed grain and actions, adjustment/group effects, axial/lateral/bending interaction, splitting, tear-out and local finished-section resistance. Resolve BG045 loaded-edge applicability, including the conditional 20-versus-25.4 mm exception. Dispose the two upper outer and one bottom outer raw ratios above one under their distinct unadopted bases. The ten simple end-grain bolts now have a reviewed conditional route; resolve their source-supported material, geometry/adjustment and complete-joint inputs, then extend supported methods to all 24 duties and missing cases. No historical corner or selected-baseline pass transfers. |
| Hardware and washer seats | The [hardware/material packet](hypotheses/hardware-material-specification-2026-09-30/README.md) supplies per-receiver smooth-body and nut-thread profile requirements for all 92 new axes, conditional Grade 5 properties, declared timber cases and catalog leads. All 184 candidate outer seats now have nominal and conditional eccentric geometry coverage, with one partial-support seat. The 54-axis demand join adds 1,134 ties and 2,268 seat actions. The reviewed Fyb source disposition permits conditional empirical sensitivity work without a blanket delivered-test prerequisite. | Bind a compatible conditional stack/profile and its functional engagement; resolve the long BG003 product specification, adopted quarter-inch dowel-bending basis, head/nut load footprints, shank/bore/seat tolerances and tilt, the partial-support seat and a supported washer metal/contact method. Keep conditional arithmetic separate from received-piece observations. Uniform annulus pressure and hardness are not metal resistance. |
| Members, contact and panels | Both complete five-body corner source boundaries and the left BG045 header section inventories have been reconstructed. Conditional DF-L No. 2 inputs and per-member grain proposals are published. The reviewed 66 Hillman axes and eight recorded moves are preserved. | Apply applicable strengths and adjustments to simultaneous member/section/contact demands, include cut/boring and stability effects, and prove the changed panel/screw receiver and kerf-right kicker-edge transfers. Reuse unchanged LEG/runner resistance; reopen only changed demands, geometry, receivers or hardware. Do not start a blanket panel or retained-member qualification campaign. |
| Installed fit, assembly and transport | Candidate and retained access producers, critical envelopes and a forward/reverse sequence hypothesis exist. Counts reconcile to 24 blocks, 92 new axes, twelve retained frame stacks and 66 separate panel/kicker screws. | Resolve named nut/washer slide and wire dependencies with compatible thread geometry, tools, counterhold and capture. Verify tolerances, hold/LED/wire access, reversible supported operations and individual-member removal paths. Screen permanent ordinary-N envelopes from named datums; document any exception before implementing a change. Proxy overlap is not proof that a real tool is blocked. |
| Build documents, stock, counts and cost | Published stock reconciliation covers all 20 frame timbers/24 blocks, exact containment, four prepared sections and 15 length/trim scenarios. Longer options place all 44 blanks; all eight-foot-only scenarios retain five unplaced blanks under their stated kerf convention. The published 44-piece stock-frame feature register binds 648 faces, all 170 axes/278 receiver matches and 32 preserved LED/service passage correspondences. The source-price package for the twelve scenarios that place all blanks is in final review. | Integrate supported joint/fit decisions and the reviewed dimensional scenarios into one revision-bound BOM, sourced package quantities and cost, finished-feature/drawing register, assembly/removal instructions and receiving checklist. Keep Actual/Disposition blank. Stock placement is not an optimized order or grade qualification; do not inherit original-board grade for a hypothetical ripped section. |
| Final acceptance and independent review | The exact 47-question scope and fail-closed coverage/criteria producers exist, with source-bound method and demand packets. | Bind every applicable criterion to current method, input, case/identity coverage, numerical result and supported disposition. Independently review the complete package and resolve material findings. All applicable requirements must pass before the conditional engineering endpoint can be called complete. |

The immediate order is diagnosis of the reduced selector's root-node stop →
a checked bounded remedy → compatible gravity with checks against the
original operator and body equilibrium → one missing usable
frame case, in parallel with the connected corner resistance
rows. Washer support/footprint and hardware/material input work can proceed
without native runs or received-piece inspection. A new native method study
must settle a named dependency in that sequence. The mechanics coordinator
retains readiness, freezes, serialized native execution and final validation;
Luna/max workers receive bounded author/reviewer tasks with separate paths,
and the primary investigates stalled work directly.

The next bounded joint tasks are now explicit. The primary has implemented
the ten-axis conditional end-grain route, with separate source-role and
calculation review; the remaining dependency is supported material,
geometry/adjustment and complete-joint disposition. The bottom outer left
`side_1` comparison now has the simultaneous four-bolt/contact and complete
cleat inputs; it needs its conditional material, applicable-adjustment/group,
finished-section and combined-joint disposition. This is a
named issue, not permission to change bolt size or choose a favorable factor.
The mechanics owner continues BG003 bearing/combined-joint applicability and BG045
edge/finished-section applicability. The upper owner's stock and finished-feature
packets are now published; it also owns the source-priced compatible
lumber/plywood package. Each author freezes its inputs and code;
a separate Luna/max reviewer checks source applicability, reconstructs the
calculation and reviews claims. Parent resolves findings and integrates
current evidence without transferring a three-case component result into
complete-joint or six-case acceptance.

The [parallel-owner handoff](parallel-owner-handoff-2026-10-01.md) now records
the owner's selection of upper-block strength for the separate hardware/material
thread: eight upper blocks and 32 axes, beginning with the top outer pair and
reusing existing source demands. That owner owns its published packet and
its 64 nominal washer seats. Its first bounded packet goal is complete; it
has now claimed `hypotheses/upper-outer-load-path-2026-10-01/` under a new
ongoing owner-directed goal. That lane covers the two top outer joints'
same-state force/couple, finished-section actions, applicable splitting/
tear-out and combined checks using existing sources, with no native run or
geometry change. The complete-joint and full MVP-E goals remain open.
The primary's reviewed
54-bolt/108-seat geometry extension is complete as a screen, with the explicit
partial-support exception; its three-case demand join now passes its source
checks. The primary also owns the isolated 64-seat upper eccentric extension;
it reuses the upper source cohort without editing the upper owner's packet.
This allocation avoids
duplicating the mechanics
coordinator's elastic/gravity, BG003 and BG045 work or the primary's six-corner
washer and source investigations.

The primary's right-corner action packet is complete as an independently
reviewed input join. Its subsequent right whole-body source boundary is
reconstructed; finished-section and resistance closure remain separate work.
The upper owner's newest load-path and stock packets are published as
conditional input evidence. The primary did not duplicate their producers.
The 44-piece dimensional reconciliation does not by itself establish
post-rip grade, purchased quantities, cost or joint acceptance. The separate
feature and source-price lanes remain recorded in the shared handoff.
The feature owner has published `03b0d54e` and `6ade76c0`, with 18 tests
plus two subtests, two exact replays, all 278 receiver matches and 32 traced
LED/service passages, followed by final independent review.
Its [feature packet](hypotheses/current-finished-feature-register-2026-10-01/README.md)
contains code and summaries on master. The source-price packet's separate
final review is pending. The primary has
proposed the current 66-screw demand/receiver-transfer join as that owner's
next disjoint joint-completion lane, reusing the already complete geometry
receiver screen and preserving the Hillman policy.

No defensible completion percentage follows from the case count. Three of six
usable conditional cases is the response milestone; complete joint resistance
and the integrated 47-criterion endpoint remain open. Finishing this goal
would produce conditional engineering documentation under the recorded
no-slip assumption, not inspected hardware, fabrication authority or a
climbing release.
