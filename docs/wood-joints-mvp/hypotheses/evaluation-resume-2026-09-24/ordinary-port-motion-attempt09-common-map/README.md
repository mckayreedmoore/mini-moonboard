# Ordinary external-port common-map control, attempt 09

Date: 2026-09-27
Scope: input-method correction for the reviewed bottom-center-right ordinary
WJ24 patch. This directory begins as a decision record; it is not a solver
result or joint acceptance.

## Decision, observation, next step

**Decision:** Make the controlled external-port coordinate exactly the same
full-cap linear projection used by the source-bound force dual. Keep all 43
source cap nodes in the coordinate, while choosing the six MPC dependent
physical DOFs only from cap nodes outside contact surfaces and nut-equation
dependencies. Contact nodes may appear as independent terms in the equations;
they remain free DOFs and are not selected as dependent variables.

**Observation:** Attempt 08 controls a renormalized 25-node subset, excluding
18 nodes that belong to contact surfaces. The force dual is defined over all
43 cap nodes. Both maps reproduce a rigid section, but are different linear
functionals for flexible-cap motion; their omitted original area weight is
0.3563359017 on each port. This is enough to reject direct force-versus-motion
comparison.

**Next step:** Rebuild the motion equations from the full-cap map, independently
reconstruct the map from the frozen section nodes and weights, prove exact
discrete virtual-work duality against the force map, and audit that no contact
or nut dependent DOF is reused. Retain all source-bound cleat nodes for free
pose extraction and add native `SOF` section output on both source-bound port
caps. If those input checks pass, freeze one diagnostic case and predeclare
response, equilibrium, output and stop bounds before any native run. The cleat
remains free; no contact gap, friction, preload or stabilization is changed.

## Limits

This corrects the port-coordinate definition only. It does not establish a
converged solution, contact engagement, cleat equilibrium, member response,
material or hardware adequacy, sensitivity, family reuse, or capacity. The
nominal bore/shaft clearances must be taken from the frozen source-bound
geometry report and must not be replaced by a generic nominal-hole assumption.

## Pilot criteria frozen before native execution

The first diagnostic is the static, displacement-controlled `n_plus` path to
1.0 mm relative external-port motion. The centered CAD wood-bore radial gap is
0.575 mm; 1.0 mm is selected to pass that geometric travel and observe the
contact-supported branch. This is an analysis scenario, not an as-built hole
measurement, service demand, or conservative physical bound. The cleat has no
boundary condition, spring, friction, preload, gap correction, or stabilizing
restraint.

The pilot records the full-cap six-component port motion, both `SOF` port
wrenches, all 9,369 cleat-node displacements, all 35 contact-pair outputs,
contact state, element strain energy and the accepted increment history. Count
the contact event from source-bound bolt-to-wood bore pairs. The pilot is
usable only if it reaches 1.0 mm with at least two accepted equilibrium states
after first positive bolt-to-wood bearing, and closes equal-and-opposite
external section resultants at the common joint datum. If the free cleat does
not settle, the solver fails to converge at its minimum increment, or required
outputs are absent, stop this branch and record it unresolved. Do not add a
constraint or tune a physical input to force continuation.

For this numerical diagnostic, select force closure as
`||F_rail + F_principal|| <= max(0.01 N, 0.01 * max(||F_rail||, ||F_principal||))`.
Select moment closure at the joint datum as 1% of the larger port moment or
force-times-port-arm scale, with a 10 N·mm absolute floor. The absolute floors
are 1% of the frozen 1 N / 1,000 N·mm diagnostic wrench scale; they are not
capacity or service tolerances. Before work comparison, orient the `SOF`
section signs with the independently checked area-vector convention. Compare
external incremental work `Σ 0.5*(Q_i + Q_{i+1})·(q_{i+1}-q_i)` with the change
in reported elastic plus frictionless contact energy, allowing 5% relative
difference and an absolute floor from the same unit-wrench scale. These are
analyst-selected diagnostic gates; no response becomes design-accepted from
meeting them.

If the baseline branch meets those gates, the predeclared numerical comparison
gate is 5% in the six-component wrench and secant compliance at matched full-cap
motion, with first-bearing motion compared within 5% of the 0.575 mm CAD travel.
Run matched static-increment, local mesh, contact-penalty, grain-frame,
clearance, and axial-engagement scenarios. Any sensitivity above 5% means the
response remains scenario-dependent and must be reported as such. This 5% is a
numerical stability threshold, not an engineering allowable. Later family
reuse still requires complete-patch transform, contact, bolt-axis, boundary
path, and signed-demand equivalence.

## Execution result

The pinned CalculiX 2.21 run parsed the deck and assembled 334,902 equations.
Under the 0.001 mm first increment, it reached 33 Newton iterations without
accepting the increment. The reported force residuals and displacement
corrections were small, while the contact spring count changed from 188,068 to
34,972. The 900-second parent timeout then sent signal 9 (exit 137); Docker
events confirm this was the declared timeout, not an OOM termination. The
input hashes remained unchanged. `.dat` and `.sta` are empty and `.frd` has
only its 80-byte header, so no motion, wrench, contact result, or response
state was accepted. The case never reached the 0.575 mm radial wood-bore
clearance.

This directly tests and rejects the static `n_plus` path as an executable
response method under this contact setup. It does not show a physical joint
failure. The port-map correction is successful; the free-cleat static contact
branch remains unsolved. Do not repeat this case with arbitrary smaller
increments or another endpoint. The next bounded method decision is whether a
source-bound transient driven only through the two external ports can resolve
the free cleat through contact while keeping kinetic energy small relative to
elastic/contact energy. If inertia is material, retain a dynamic-only result
and leave quasi-static response unresolved.

## Post-run correction and bounded next observation

The pre-run 1.0 mm clearance rationale was incomplete for this symmetric
two-port path. The ports each move 0.5 mm at that endpoint. With the cleat free
and centered, it can translate between them, so the idealized two-sided bore
travel is about `2 * 0.575 = 1.15 mm` before both bolt rows are forced into
bearing; face contact or member flexibility may change the actual onset. The
attempt did not accept even its first 0.001 mm increment, so it provides no
observation of this clearance event. Preserve the original pilot criteria as
history; they do not govern a follow-on run.

The next bounded observation is one source-frozen, physical-mass transient
driven smoothly through the corrected full-cap external-port coordinates. Use
approximately 1.3 mm relative N travel only as a nominal geometry target, and
stop on the observed local bore/face contact state plus a short accepted
post-onset sequence. It is not a service demand or conservative clearance
bound. Keep the cleat free and do not add stabilization, friction, preload,
gap adjustment or local springs. Record port motion and both `SOF` wrenches,
cleat pose and velocity, each bore/face action and gap, accepted-state energies,
and input/output hashes. In transient balance, include inertia and momentum;
compare external work with changes in elastic, contact and kinetic energy.
Compare a slower ramp and smaller time step at matched contact and motion
states. Label the branch quasi-static only if the energy, balance and rate
checks meet predeclared numerical gates. Otherwise retain a dynamic-only
diagnostic and leave the quasi-static external response unresolved. Do not run
another static amplitude or increment variant.
