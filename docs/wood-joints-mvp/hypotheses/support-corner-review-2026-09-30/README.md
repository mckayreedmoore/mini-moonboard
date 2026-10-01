# Independent support and corner review, September 30, 2026

This packet responds to the owner's request to investigate the working
agent's blockers and queue concrete approaches. It adds independent small
mathematical checks. It changes no reviewed geometry, source evidence,
candidate authority, hardware policy or strength criterion, and runs no
native solver. Its output is not a corner pass or a construction release.

The current development revision remains
`led-clearance-2x6-runner-seated-blocks-v1`. Three conditional cases have
authenticated corner exports: A12-rear, A1-rear and K12-rear. The latest
[six-case register](../mvp-acceleration-2026-09-28/current-six-case-corner-response-register-attempt04/register.json)
keeps forward, left and right responses unresolved. The 92 new block axes
remain separate from the twelve original leg/runner arrangements and the
66 Hillman panel/kicker axes.

## Floor support: resolve the reference and loading scenario first

The latest forward input has one static step, one CLOAD block and the
explicit branch `monotone_zero_gap_first_bearing_reference_zero`. It scales
the combined loads in that step and requires selected cells to remain
strictly bearing with their tangential coordinates restrained to zero.
Forward attempt05 still fails its strict support check at SPR1026.
This is a rejected response, not proof of frame failure or proof that every
possible support state fails.

The earlier [feasibility plan](../mvp-acceleration-2026-09-28/next-gate-feasibility-plan-2026-09-29.md)
instead describes recording the current relative tangent position at first
bearing and resetting it after opening and re-engagement. Those history
rules are not implemented by a fixed zero-reference, one-step mask. This
is a distinction between scenarios, not a reason to relabel any existing
forces.

The independent exact-arithmetic check reproduces the source coupled toy:

- With its tangent restrained to zero, the normal coordinate is
  `q = -1/2 mm`, so the cell is open and the tangent restraint is inadmissible.
- With the tangent released, `t = -15/7 mm`, `q = 2/7 mm` and
  `N = 4/7 N`, so the cell bears and violates the released-tangent branch.
- A different held reference, `t_ref = -2 mm`, admits
  `q = 1/4 mm`, `N = 1/2 N`, and tangent reaction `-1/4 N`.
  This example shows that the reference matters. It does not demonstrate a
  reachable loading history, a unique response, or a full-frame solution.

The positive normal stiffness is unchanged at `2 N/mm` throughout. A
separate finite-tangent-stiffness calculation gives
`q = (2 - k_t)/(7 + 4 k_t)` on its assumed closed branch. For
`k_t >= 2 N/mm`, that branch is not strictly compressed. Making the
tangent spring arbitrarily stiff is therefore not a general remedy for
this gate. The source
[rigid-normal-limit check](../mvp-acceleration-2026-09-28/current-ideal-stick-rigid-normal-limit-screen-attempt01/README.md)
also shows that normal stiffening alone does not fix the toy.

The next useful floor deliverable is a separately named scenario with
gravity settling before the climber load:

```text
settling:       F(beta)  = beta * F_gravity
climber ramp:  F(alpha) = F_gravity + alpha * F_climber
```

Freeze the decomposition of all member, panel and mapped hardware gravity,
not only a convenient subset. Declare initial contact/reference states and
the event rule for opening and re-engagement. Solve normal and tangent
states together; an equilibrium whose contact state contradicts its
constraints is not usable. At a new contact episode, capture the contact
event's relative tangent coordinate rather than choosing an offset after
seeing the desired final result. A finite-step last-open coordinate needs
an event or step-refinement justification.

Before a frame run, replay the existing
[two-cell contact/reset fixture](../mvp-acceleration-2026-09-28/conditional-floor-two-cell-coupled-stick-fixture-attempt01/README.md)
and the coupled no-state/multiple-state fixtures. A bounded selector must
report unresolved when it cycles, finds multiple admissible branches without
a justified history selection, or exhausts its budget. The zero-load start
also needs a reaction-free coordinate gauge or nullspace treatment; it must
not acquire a floor anchor. Gravity staging and reference reset are a
method/scenario proposal, with no guarantee that all frame cases will have
admissible responses.

Retain the existing strict normal, source-law, MPC, open-tangent and
individual-body/global checks. Do not accept earlier rejected DATs,
introduce a guessed friction coefficient, retain tangential reactions at
open cells, widen precision tolerances to hide signed mismatches, or resume
automatic contact-mask retries. Parent remains responsible for freezing,
readiness, serialized native execution and final validation.

The pinned [CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf) and its
locally recorded source review support the distinction between exact
conditional stick and the program's finite friction/tied-contact options.
Changing solver brands does not supply the missing history definition.

## BG003: replace an arbitrary bearing diagram with a compatible diagnostic

The existing
[piecewise bearing construction](../mvp-acceleration-2026-09-28/current-bg003-piecewise-bearing-profile-feasibility-attempt01/README.md)
preserves source forces and moments while choosing zero lateral shear and
moment at the middle cut. That is a valid statement about statics. The
chosen reactions jump at sign switches and at the artificial split inside
the middle receiver; a uniform continuous elastic foundation does not
produce that field. Neither statics nor the split by itself establishes
physical bearing, a safe strength bound, or two independent lap joints.

The new [diagnostic producer](diagnose.py) solves one continuous
Euler–Bernoulli beam through the full `38.1 / 88.9 / 88.9 mm` stack. Each
physical wood receiver has its own transverse translation and rotation in
both planes. The middle receiver is one body and one continuous foundation;
there is no hinge or change in its law at the middle cut. Equal isotropic
zero-gap opposing-flank linear foundations are an explicitly mathematical
scenario. Their potential is

```text
U = 1/2 integral(EI * |w''|^2 ds)
  + 1/2 sum_j integral(k * |w - a_j - b_j*(s-s_j)|^2 ds).
```

The source's interface actions are applied once, as the balancing external
wood force and first moment. They are not also applied to the beam. A
reaction-free translation/rotation gauge removes only global rigid modes;
the physical beam ends are free. Integrated foundation actions recover
each receiver's lateral source force and first moment. Bolt internal moments are recovered from the
distributed bearing, rather than copied from whole-member datum moments.

The dimensionless parameter is `beta = k * L^4 / EI`, with
`L = 215.9 mm` and line-foundation `k` in `N/mm²`. The producer normalizes
`EI/L³` for the solve, so its displacements are not predictions of physical
slip. It tests beta values `1`, `100` and `10,000`, not calibrated wood
stiffnesses or proven weak/stiff asymptotic bounds.

For A12-rear bolt 1 the computed middle-cut magnitudes are:

| Dimensionless beta | Transverse shear | Bending moment |
| ---: | ---: | ---: |
| 1 | 108.471 N | 5,971.907 Nmm |
| 100 | 108.356 N | 5,933.768 Nmm |
| 10,000 | 97.720 N | 3,518.043 Nmm |

These are compatible responses under the declared ideal foundation. They
demonstrate that zero middle-cut shear/moment is not imposed by the source
wrench equilibrium. They do not prove that every compatible field has
nonzero cut actions, nor bound the real bolt's demand or strength.

The packet checks both BG003 bolts in each of the three accepted full-load
cases at all three beta points: 18 scenarios. It verifies known-answer
cantilever force/couple deflection and rotation, sign reversal, paired
unilateral flank signs, a separate gap fixture, symmetric transfer,
rigid-motion invariance, 90-degree transverse rotation, reaction-free gauges,
receiver wrench closure and free-end closure. Meshes use 16 and 32 elements
per receiver; sampled peak, middle-cut magnitudes and signed middle-cut
vectors must agree within 1%.
The JSON reports actual errors for every scenario. This is a reduced
compatibility diagnostic, not a validated nonlinear bearing or strength model.

Use this as the small method check envisaged by the existing
[continuous-dowel proposal](../mvp-acceleration-2026-09-28/current-bg003-continuous-dowel-method-candidate-attempt01/README.md).
Before applying its results as candidate mechanics, address the modeled
`0.575 mm` radial clearance, grain-dependent bearing law, foundation
stiffness sensitivity and continuous steel behavior. NDS `Fe` is a
strength reference, not a stiffness or a load-slip curve. Keep the axial
tie, thread/runout, washer seats, splitting and two-bolt group checks
separate and then assess their applicable interactions. Do not sum
independent plane capacities or turn this elastic diagnostic into a
complete-joint pass.

## BG045: keep the conditional detailing deficit concrete

The prior
[two-case screen](../mvp-acceleration-2026-09-28/current-corner-bg045-two-case-wood-mode-screen-attempt01/README.md)
records the proposed block grain, smooth quarter-inch bolt and rectangular
envelope scenario. For A1 axis 2, the block force points toward the minus-Y
face that is 20 mm away. Against the named `4D = 25.4 mm` loaded-edge
comparison, the deficit is 5.4 mm. This calculation does not need delivered
stock inspection. It should remain a conditional detailing exception under
the explicitly stated edge interpretation, rather than disappearing among
generic missing-inspection notes.

For a conservative rectangular envelope screen requiring 25.4 mm clearance
to both Y faces of the 133.35 mm block, the allowed axis band would be
`25.4–107.95 mm` from one face; the current positions are `20–113.35 mm`.
That is an arithmetic target for a proposed geometry study, not an approved
axis move. The 5.4 mm is not a sufficient change specification: finished
profile, other bores, washer access, receiving header, supported screw axes
and onward load transfer still have to be checked. Report required changes
before altering the reviewed model.

The local [AWC NDS source review](../mvp-acceleration-2026-09-28/current-bg045-edge-applicability-dependency-attempt01/README.md)
supports retaining edge detailing separately from the end-grain lateral
factor. It does not supply a universal ray-selection rule for every oblique
force. Neither favorable individual-bolt ratios nor this envelope screen
settles splitting or complete mixed-action resistance.

## Handoff and reproduction

The [handoff message](message-to-worker.txt) was queued to the working
`Review mini moonboard FEA` task through tmux pane `%24` on September 30.
The terminal confirmed that it would be submitted after the next tool call.
Queueing guidance does not establish its adoption or close any analysis gate.

Finish the signed wood-section calculation from the three authenticated
corner exports and retain their exact source guards. Give BG003 compatible
bearing and the BG045 detailing exception priority. Continue to reuse the
twelve original leg/runner arrangements' resistance evidence, reopening
only specifically changed actions or receiver details. Bound panel work to
an identified corner load-transfer dependency.

Reproduce from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/support-corner-review-2026-09-30/diagnose.py
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/support-corner-review-2026-09-30/diagnose.py --verify
```

The first command writes only this packet's [diagnostics.json](diagnostics.json).
The second verifies byte-identical reproduction without writing. The
producer authenticates the three exported force-report hashes and their
full-load/corner-balance guards, the original toy and profile sources, and
the rejected forward input hashes. The JSON includes its producer hash. An
independent Luna Max review checked the mechanics, normalization and cut
signs and reproduced the initial packet. Its suggestions were incorporated
as explicit mask/sector enumeration, signed-vector refinement and separate
cut-origin names; the strengthened packet again reproduces byte-identically. No
native solve, capacity, complete floor response, geometry change or joint
acceptance results from either command.
