# Ordinary-joint external force-history review, attempt 01

Date: 2026-09-27  
Scope: read-only decision review for the reviewed bottom-center-right ordinary
joint. No input, runner, geometry, plan, or ledger was changed. No solver or
test was run. Mechanical and joint acceptance remain false.

## Decision

The proposed post-clearance question is:

> Under a source-bound simultaneous wrench history at the rail and principal
> ports, does the free cleat enter bolt-to-wood bearing and retain a stable
> response for at least two accepted states after first bearing? What are the
> port motion, cleat motion, four bore actions, three wood-face actions, and
> energy/momentum balance over that event?

**No changed physical force-time law can be frozen from the available
evidence.** Do not run another transient on a guessed amplitude or duration.
The only supportable proposal is conditional: use the raw, source-bound
simultaneous six-component rail and principal port-action histories from a
current full-frame demand solution or a directly measured test. Apply those
sampled histories through the existing force-dual maps, with piecewise-linear
interpolation between recorded samples and without arbitrary rescaling,
smoothing, dwell, or unload. Preserve a recorded dwell/unload only if the
source history contains it. This changes the present artificial unit pulse
into a demand-bound history, but it is not executable until its force vectors
and time coordinates exist.

The missing input is the **signed six-component action versus time at both
source-bound local ports for one named current-revision case**, including the
action datums and time basis. A static case additionally needs an explicit
engineering decision that the desired question is quasi-static and an
evidence-based application-time/rate basis. The reviewed
[full-frame manifest](../current-full-frame-input-manifest-attempt02/README.md)
does not yet supply current-frame reactions or member/joint demands. The six
[current load records](../current-load-cases.json) are applied loads at hold
  patches, not the two local port actions. They cannot be copied or transformed
  into local joint demand without the absent full-frame transfer solution.
  The [WJ-09 completion-ledger row](../../../completion-ledger.md) records
  the same missing current-revision demands and no accepted external response.

## Evidence check

- Attempts [02](../ordinary-external-force-transient-attempt02/force-freeze.json)
  and [03](../ordinary-external-force-transient-attempt03/force-freeze.json)
  freeze the same n_plus unit wrench: a 1 N reference scale with a quintic
  smoothstep amplitude over 0.1 s and a 0.025 s hold. Attempt 03 changes
  output instrumentation only. Its one accepted state at 0.001 s has amplitude
  9.8506e-6; its applied field is below the recorded force floor. At that
  single state, `pilot.stdout` prints external work `1.223180e-12 N mm`,
  elastic contact energy `8.583830e-18 N mm`, total energy
  `1.223338e-12 N mm`, and a `0.012881%` native relative balance residual.
  These sub-floor printed values do not constitute an independent accounting
  audit or establish bearing/post-bearing response. The run stops before a
  meaningful post-clearance response. Repeating or altering that numerical
  pulse does not supply a physical force history.
- The current [six-case input contract](../current-load-cases.json) records
  250 lb × 2 loads at A12/K12/A1, explicit hold and panel datums, and derived
  standoff moments. Its own scope is applied inputs. The current full-frame
  manifest says support, reactions, member/joint demand, and stability outputs
  are not present. The earlier
  [response decision review](../ordinary-external-response-decision-review-attempt01/README.md)
  likewise requires fresh current-revision six-case demands.
- A suitable work-conjugate geometric port map is available. The external
  port record binds each full cap and its force-dual distribution. Attempt 09
  independently reconstructs the same 43-node-per-port displacement
  projection, reports zero map mismatch, and gives random virtual-work
  relative error 3.87e-16. This freezes the map, not a response or demand.
- Attempt 03 already requests all-physical-node U,V, both port SOF
  sections, and per-pair output for the 35 contact pairs. Its accepted state
  history does not reach engagement; its single printed sub-floor balance
  cannot assess the event or post-contact energy gates. Its nonconverged
  last-iteration frames are not accepted response states. It also omits
  reaction output at the three artificial global-gauge nodes. Attempt 09
  specifies all 9,369 cleat-node displacements, but its static run accepted no
  state. Do not merge those input-only/output-only records into a response
  result.

## Conditional force and motion definition

Once the missing current local actions are supplied, define the applied
nodal CLOADs from the existing cap maps. For each port, let B be the
source-bound full-cap motion projection and W(t) its six-component
generalized wrench. Record separate sampled time series for all six wrench
components at each port; interpolate each component independently and do not
rescale a fixed six-component pattern with one shared scalar curve. Apply
f(t) = B-transpose W(t) and recover q(t) = B u(t)
from the same 43 cap nodes. Then the discrete port pair is exactly
work-conjugate: f dot du = W dot dq. Report the rail and principal port
coordinates separately and their relative six-DOF motion at the recorded
common datum. Freeze wrench axes, signs, time units, and whether each
component stays global or follows a moving frame. Do not infer a port reaction
from controller-node RF; report native SOF section resultants independently,
orient them, and shift moments to the common datum. Reconcile section
resultants with the applied port wrench and port/cap momentum before
interpreting a difference.

The centered CAD bore scenario has 0.575 mm radial travel at each side; its
approximately 1.15 mm symmetric relative-N travel is only a geometry cue.
The event gate must use the frozen local bore contact output, not a commanded
1.15 mm displacement. Keep the cleat free, preserve openable frictionless
contact, and keep the named material, density, clearance, and stiff nut
engagement assumptions explicit. The external load history must cover the
actual first-bearing event plus the two accepted post-bearing states; a static
load contract does not establish a transient duration.

## Accepted-state accounting to freeze before any native run

Persist one row per accepted increment, bound to exact source/input hashes
and solver identity. At minimum, retain:

1. **Input and port work:** source sample, time, interpolated rail/principal
   wrench, nodal CLOAD field, full-cap q for both ports, and relative motion.
   Independently integrate the nodal force-displacement work and compare with
   the generalized wrench-motion work and native accumulated external work.
   Preserve signs and all moments at the shared datum.
2. **Port transfer and free cleat:** both SOF section force/moment vectors,
   shifted to the shared datum; all 9,369 cleat-node displacements reduced to
   six-DOF pose plus deformation residual; every one of the 35 contact-pair
   gaps/state/actions, including all four bore pairs and three wood faces.
   Orient contact actions by the frozen master/slave ownership.
3. **Whole-model dynamics:** accepted U,V over all physical nodes, frozen
   densities/mass distribution, applied external loads, and reactions at all
   three gauge nodes. Compute linear and angular momentum at each accepted
   state. Compare momentum changes with time-integrated external force and
   moment impulses, including gauge reactions and any applied body forces.
   The existing force deck does not print gauge RF; add and verify the needed
   reaction channel for the pinned solver, constraints, and dynamic terms.
   The official 2.23 manual defines RF as reaction plus CLOAD at the node and
   DLOAD on any element containing that node, but only as static-force output;
   it excludes dynamic forces such as dashpots. Subtract included load terms
   before treating RF as a constraint reaction or adding it to the impulse
   balance, to avoid double-counting. Current upstream keyword pages also say
   MPC forces are omitted; treat those pages as corroboration, not proof of
   2.23 behavior. Do not interpret loaded-node RF as a pure reaction or assume
   RF alone closes dynamic momentum.
4. **Energy:** independently compare native work change against whole-model
   elastic/strain energy, kinetic energy, and verified contact energy at every
   accepted state, with any modeled dissipation named separately. Retain the
   element energy totals as a second check and close the frozen relative and
   absolute residual gates. A topology count or unqualified global contact
   energy is not a contact-energy audit.
5. **Interpretation gates:** count first positive bearing separately for
   each bore pair, require two complete accepted states afterward, and report
   section closure, force/moment/momentum residuals, work/energy residuals,
   and stop reason. Call the branch quasi-static only after the already
   recorded kinetic-to-strain-plus-contact and matched-rate/timestep gates
   pass. Otherwise report a dynamic-only diagnostic.

Keep the existing 5% and floor gates labeled numerical diagnostic thresholds,
not engineering acceptance tolerances. No per-body equilibrium claim is
available from the compact wrench report unless continuum internal transfer
and solver-generated nut-carrier constraint actions are included. The frozen
force gates use a 1% inertial-force relative tolerance, a 0.01 N force floor,
and a 10 N mm moment floor. The moment floor is torque, not angular-momentum
impulse in N mm s. Define dimensionally consistent linear/angular impulse
normalizations and absolute floors from the source time basis before any future
run; do not reuse the torque floor for impulse closure.

## Solver-specific notes

The force attempts pin the separately built ccx-upstream-2.23 executable and
the official 2.23 manual hash in their freeze records. In that manual,
AMPLITUDE is a time/value table that linearly interpolates the amplitude and
multiplies the reference load; DYNAMIC loads otherwise start at full strength.
The current smoothstep is therefore an analyst-specified numeric history, not
evidence of a physical ramp. See the
[official 2.23 manual PDF](https://www.dhondt.de/ccx_2.23.pdf) and its
[HTML archive](https://www.dhondt.de/ccx_2.23.htm.tar.bz2). The archive
verified online has SHA-256
ed14b31b51972d5492209a42fcd52a062e36cbc7843bcd358617cb3aee0da736.
The pinned manual defines RF as reaction plus CLOAD at the node and DLOAD on
any element containing it. It limits RF to static-force output; dynamic
forces such as dashpot forces are excluded. Remove applicable CLOAD/DLOAD
contributions before treating RF as a constraint reaction or including it in
the impulse balance. Current upstream [NODE PRINT][ccx-node-print] and
[NODE FILE][ccx-node-file] pages also say MPC forces are not calculated; treat
that as corroboration, not proof for the pinned 2.23 executable. Loaded-node RF
is not a clean port resultant, and gauge RF cannot be assumed to close dynamic
momentum. Use source-bound SOF output and the audited CLOAD map for port
resultants. The manual distinguishes `CF/CFN/CFS` surface-force summaries,
`CELS` contact-spring energy at active slave nodes, and generated contact
topology written to `.cel` by `CONTACT ELEMENTS`; topology is not force or
energy evidence. LAST ITERATIONS stores nonconverged displacements, not
accepted response. The input-only
[attempt 09 map audit](../ordinary-port-motion-attempt09-common-map/port-motion_n_plus-audit.json)
supports the motion/load dual, not a force reaction result.

Online verification surfaced a version detail worth preserving: the official
CalculiX discussion reports .frd acceleration output (A) was implemented
after the manual by commits a151767 and fe0b25e in April 2026
([upstream discussion][ccx-acceleration-output]).
The pinned build manifest hashes an official 2.23 source archive, but the
current artifacts do not establish that this particular archive contains
those later changes. This proposal therefore uses all-node V output and
accepted-state momentum differences; do not assume A is available from the
version label alone.

[ccx-acceleration-output]:
  https://calculix.discourse.group/t/acceleration-output-for-dynamic-calculations/2846

[ccx-node-print]:
  https://github.com/calculix/cae/blob/master/doc/NODE_PRINT.html
[ccx-node-file]:
  https://github.com/calculix/cae/blob/master/doc/NODE_FILE.html

## Disposition

The port map and geometric motion observable can be frozen now. A changed
physical force-time law, response values, and complete force/moment/momentum
closure cannot. Obtain the two local port-action histories and time basis from
the same current-revision full-frame case (or a measured test), then freeze
the history and audit the missing gauge/energy observations before deciding
whether another bounded native run can answer the question. Until then, no
law is selected and all model/mechanical acceptance claims remain false.
