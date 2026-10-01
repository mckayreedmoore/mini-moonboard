# Joint completion and gravity-start report — September 30, 2026

Updated October 1, 2026 at 06:30 UTC (October 1 in Denver). The native export
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
| Current-frame gravity and six cases | Three authenticated conditional rear cases, A12/A1/K12, each with seven accepted states. All six source loads pass the necessary normal-resultant footprint screen. The actual pure-solid operator is exported; source/map/rigid-field checks, all fifty body numerical elastic gates and complete connector reduction now pass. Free/constrained export coupons, a free-cube condensation fixture, tiny indicator fixtures, physical connector projections and a six-case operator-reuse contract are available. The actual gravity-direction selection stopped at its solver budget without a feasible solution or infeasibility proof; parent has supplied a reviewed formulation-strengthening hypothesis. | Establish compatible gravity, actual branch nullspace and reaction-free gauge from the source-bound reduction and all 300 body balances; discover capture/release events; validate one currently unusable forward/left/right case, then finish all six cases and applicable sensitivities under unchanged response gates. Necessary statics, tiny fixtures, solver time limits and convergence alone cannot supply these results. |
| Complete joint resistance | Audited corner exports retain 168 signed lateral-plane states, simultaneous physical ties, section actions and onward transfers. The [whole-assembly transfer summary](hypotheses/mvp-acceleration-2026-09-28/current-corner-whole-assembly-transfer-attempt01/README.md) records the connected boundary coverage. Individual-bolt component helpers exist. The published upper packet adds eight blocks/32 bolts with sampled sections and signed three-case comparisons. | Resolve actual continuous three-receiver BG003 bearing/steel behavior, mixed grain and actions, adjustment/group effects, axial/lateral/bending interaction, splitting, tear-out and local finished-section resistance. Resolve BG045 loaded-edge applicability, including the conditional 20-versus-25.4 mm exception. Resolve the two upper outer ratios above one under their unadopted method; extend supported methods to the other affected joint families and all 24 duties. No historical corner or selected-baseline pass transfers. |
| Hardware and washer seats | The [hardware/material packet](hypotheses/hardware-material-specification-2026-09-30/README.md) supplies per-receiver smooth-body and nut-thread profile requirements for all 92 new axes, conditional Grade 5 properties, declared timber cases and catalog leads. All 184 candidate outer seats now have nominal and conditional eccentric geometry coverage, with one partial-support seat. The 54-axis demand join adds 1,134 ties and 2,268 seat actions. The reviewed Fyb source disposition permits conditional empirical sensitivity work without a blanket delivered-test prerequisite. | Bind a compatible conditional stack/profile and its functional engagement; resolve the long BG003 product specification, adopted quarter-inch dowel-bending basis, head/nut load footprints, shank/bore/seat tolerances and tilt, the partial-support seat and a supported washer metal/contact method. Keep conditional arithmetic separate from received-piece observations. Uniform annulus pressure and hardness are not metal resistance. |
| Members, contact and panels | Complete five-body corner boundary and BG045 header section inventories have been reconstructed. Conditional DF-L No. 2 inputs and per-member grain proposals are published. The reviewed 66 Hillman axes and eight recorded moves are preserved. | Apply applicable strengths and adjustments to simultaneous member/section/contact demands, include cut/boring and stability effects, and prove the changed panel/screw receiver and kerf-right kicker-edge transfers. Reuse unchanged LEG/runner resistance; reopen only changed demands, geometry, receivers or hardware. Do not start a blanket panel or retained-member qualification campaign. |
| Installed fit, assembly and transport | Candidate and retained access producers, critical envelopes and a forward/reverse sequence hypothesis exist. Counts reconcile to 24 blocks, 92 new axes, twelve retained frame stacks and 66 separate panel/kicker screws. | Resolve named nut/washer slide and wire dependencies with compatible thread geometry, tools, counterhold and capture. Verify tolerances, hold/LED/wire access, reversible supported operations and individual-member removal paths. Screen permanent ordinary-N envelopes from named datums; document any exception before implementing a change. Proxy overlap is not proof that a real tool is blocked. |
| Build documents, stock, counts and cost | Source geometry, stock proposals, hardware counts and builder-document organization exist. Conditional material cases include separate treatment of the four ripped blocks. | Reconcile the supported joint/fit decisions into one revision-bound BOM, stock cut/yield basis, sourced package quantities and cost, drawings, assembly/removal instructions and receiving checklist. Keep Actual/Disposition blank. Do not present a hypothetical ripped-block grade as inherited from the original board. |
| Final acceptance and independent review | The exact 47-question scope and fail-closed coverage/criteria producers exist, with source-bound method and demand packets. | Bind every applicable criterion to current method, input, case/identity coverage, numerical result and supported disposition. Independently review the complete package and resolve material findings. All applicable requirements must pass before the conditional engineering endpoint can be called complete. |

The immediate order is accepted elastic operator/body-equilibrium rejoin →
compatible gravity → one missing usable frame case, in parallel with the connected corner resistance
rows. Washer support/footprint and hardware/material input work can proceed
without native runs or received-piece inspection. A new native method study
must settle a named dependency in that sequence. The mechanics coordinator
retains readiness, freezes, serialized native execution and final validation;
Luna/max workers receive bounded author/reviewer tasks with separate paths,
and the primary investigates stalled work directly.

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

No defensible completion percentage follows from the case count. Three of six
usable conditional cases is the response milestone; complete joint resistance
and the integrated 47-criterion endpoint remain open. Finishing this goal
would produce conditional engineering documentation under the recorded
no-slip assumption, not inspected hardware, fabrication authority or a
climbing release.
