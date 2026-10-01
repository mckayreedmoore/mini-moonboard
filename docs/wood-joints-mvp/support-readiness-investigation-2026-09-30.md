# Gravity-start readiness investigation — September 30, 2026

Updated October 1, 2026 UTC (September 30 in Denver). The native export
assessment below was independently replayed; newer coordinator entries may
supersede this snapshot. Work remains exclusively on `master`.

Docker access is available. The actual frame's unloaded solid stiffness has
now been exported and authenticated. The present support blocker is compatible
initial gravity equilibrium and a state-dependent gauge. The reviewed native
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
the exported frame operator, not a gravity solution. Full elastic rank, body
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
saved seat poses; washer eccentricity and seat-location tolerances remain
separate fit/contact inputs.

Primary review corrected the checker repository path, required actual
rejection tests for clipping and embedded/reversed seats, and added an
outward protrusion fixture so full support cannot hide an obstructed washer
face. The [method note](hypotheses/corner-washer-method-investigation-2026-10-01/source-note.md)
identifies a conditional contact-resolved elastic metal-demand calculation:
it can report required minimum yield after the footprint, coupled actions
and contact model are bound. Missing catalog yield need not stop that demand
calculation. The existing clamped thin-annulus benchmark cannot be treated as
the current washer model. Direct Grade 5 tensile yield also remains distinct
from the NDS dowel-bending input.

The [direct retained-wrench CAD investigation](hypotheses/retained-wrench-cad-lead-investigation-2026-10-01/source-note.md)
also resolves one stale source lead: the Olander page is reachable, but its
live anonymous CAD availability response rejects Wera `05073287001` as an
invalid product key and leaves its model button disabled. A visible CAD label
does not supply tool geometry. The four 3/4-inch retained leg-bolt tool checks
remain a specific source gap; repeating that public lead will not establish
access. Conditional source-supported tool models can be evaluated before
physical receiving.

Disposition: the investigation identifies a startup and rank-interpretation
issue. It authorizes no extra floor restraint, revised geometry or native
launch, and adds no blanket external sign-off or physical floor test. Usable
conditional responses remain the three rear cases; complete joint acceptance
and the full six-case requirement remain open.

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
| Current-frame gravity and six cases | Three authenticated conditional rear cases, A12/A1/K12, each with seven accepted states. All six source loads pass the necessary normal-resultant footprint screen. The actual pure-solid operator is exported and source/map/rigid-field checks pass. Free/constrained export coupons, a free-cube condensation fixture, tiny indicator fixtures, physical connector projections and a six-case operator-reuse contract are available. | Validate actual-body elastic rank and reaction-free reduction, then rejoin body/load/connector maps; establish compatible gravity, actual branch nullspace and reaction-free gauge; discover capture/release events; validate one currently unusable forward/left/right case, then finish all six cases and applicable sensitivities under unchanged response gates. Necessary statics, tiny fixtures and convergence alone cannot supply these results. |
| Complete joint resistance | Audited corner exports retain 168 signed lateral-plane states, simultaneous physical ties, section actions and onward transfers. The [whole-assembly transfer summary](hypotheses/mvp-acceleration-2026-09-28/current-corner-whole-assembly-transfer-attempt01/README.md) records the connected boundary coverage. Individual-bolt component helpers exist. | Resolve actual continuous three-receiver BG003 bearing/steel behavior, mixed grain and actions, adjustment/group effects, axial/lateral/bending interaction, splitting, tear-out and local finished-section resistance. Resolve BG045 loaded-edge applicability, including the conditional 20-versus-25.4 mm exception. Extend supported methods to the other affected joint families and all 24 duties; no historical corner or selected-baseline pass transfers. |
| Hardware and washer seats | The [hardware/material packet](hypotheses/hardware-material-specification-2026-09-30/README.md) supplies per-receiver smooth-body and nut-thread profile requirements for all 92 new axes, conditional Grade 5 properties, declared timber cases and catalog leads. All 126 corner tie states and 252 seat states are available. The twelve primary-corner annuli now have geometry-only support evidence on the exact saved wood faces. | Bind a compatible conditional stack/profile and its functional engagement; resolve the long BG003 product specification, quarter-inch dowel-bending basis, head/nut load footprints, remaining washer-seat coverage and a supported washer metal/contact method. Keep conditional arithmetic separate from received-piece observations. Uniform annulus pressure and hardness are not metal resistance. |
| Members, contact and panels | Complete five-body corner boundary and BG045 header section inventories have been reconstructed. Conditional DF-L No. 2 inputs and per-member grain proposals are published. The reviewed 66 Hillman axes and eight recorded moves are preserved. | Apply applicable strengths and adjustments to simultaneous member/section/contact demands, include cut/boring and stability effects, and prove the changed panel/screw receiver and kerf-right kicker-edge transfers. Reuse unchanged LEG/runner resistance; reopen only changed demands, geometry, receivers or hardware. Do not start a blanket panel or retained-member qualification campaign. |
| Installed fit, assembly and transport | Candidate and retained access producers, critical envelopes and a forward/reverse sequence hypothesis exist. Counts reconcile to 24 blocks, 92 new axes, twelve retained frame stacks and 66 separate panel/kicker screws. | Resolve named nut/washer slide and wire dependencies with compatible thread geometry, tools, counterhold and capture. Verify tolerances, hold/LED/wire access, reversible supported operations and individual-member removal paths. Screen permanent ordinary-N envelopes from named datums; document any exception before implementing a change. Proxy overlap is not proof that a real tool is blocked. |
| Build documents, stock, counts and cost | Source geometry, stock proposals, hardware counts and builder-document organization exist. Conditional material cases include separate treatment of the four ripped blocks. | Reconcile the supported joint/fit decisions into one revision-bound BOM, stock cut/yield basis, sourced package quantities and cost, drawings, assembly/removal instructions and receiving checklist. Keep Actual/Disposition blank. Do not present a hypothetical ripped-block grade as inherited from the original board. |
| Final acceptance and independent review | The exact 47-question scope and fail-closed coverage/criteria producers exist, with source-bound method and demand packets. | Bind every applicable criterion to current method, input, case/identity coverage, numerical result and supported disposition. Independently review the complete package and resolve material findings. All applicable requirements must pass before the conditional engineering endpoint can be called complete. |

The immediate order is actual-body elastic reduction/body-equilibrium rejoin →
compatible gravity → one missing usable frame case, in parallel with the connected corner resistance
rows. Washer support/footprint and hardware/material input work can proceed
without native runs or received-piece inspection. A new native method study
must settle a named dependency in that sequence. The mechanics coordinator
retains readiness, freezes, serialized native execution and final validation;
Luna/max workers receive bounded author/reviewer tasks with separate paths,
and the primary investigates stalled work directly.

No defensible completion percentage follows from the case count. Three of six
usable conditional cases is the response milestone; complete joint resistance
and the integrated 47-criterion endpoint remain open. Finishing this goal
would produce conditional engineering documentation under the recorded
no-slip assumption, not inspected hardware, fabrication authority or a
climbing release.
