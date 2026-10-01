# Solver-switch investigation

Research checkpoint: September 27, 2026. This resumes the owner's interrupted
request to explain the CalculiX difficulties, examine comparable work, and
assess whether another FEA tool would help. Scope is the reviewed wood-joint
development candidate. This review changes no model or acceptance status and
runs no solver.

Switching methods could remove a specific numerical obstacle. The evidence
does not yet establish that switching software would produce an accurate
current-joint response. A small comparison with an independent implementation
would be more informative than migrating the complete frame immediately.

## What is actually going wrong

The [attempt04 replay](hypotheses/evaluation-resume-2026-09-24/ordinary-external-force-transient-attempt04-diagnostic/replay-attempt01/RESULTS.md)
isolates the logged blocker: increment 2, iterations 2–26 fail the contact-count
stability gate while the logged residual, displacement and viscoelastic checks
pass. Only the tiny startup state at 0.001 s is accepted. This is not a
demonstrated strength failure or an accepted response at the diagnostic load.

The [pinned source interpretation](hypotheses/evaluation-resume-2026-09-24/ordinary-external-force-transient-attempt04-diagnostic/contact-count-interpretation.md)
identifies the count as generated face-to-face penalty springs. Signed
clearance can enable or suppress those springs within an increment. Their
changing count does not measure changing force. Existing rejected-iteration
outputs cannot distinguish negligible near-zero gap changes from mechanically
significant changes. Floating-point chatter remains a hypothesis.

This gate agrees with the [CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf),
sections 6.10.2 and `*CONTROLS`: the default relative count threshold is 0.001.
The local official HTML manual was inspected at `node203.html`, `node251.html`
and `node206.html` under `/tmp/ccx223-html/CalculiX/ccx_2.23/doc/ccx/`.
The last entry also states that mortar contact is limited to static procedures.
It cannot simply replace contact in the existing implicit dynamic deck.

The earlier static problem also has a free cleat motion before sufficient
contact engages. That problem is broader than CalculiX: the
[Abaqus contact troubleshooting guide](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEITNRefMap/simaitn-c-contacttrouble.htm)
describes unconstrained static motion and contact chattering. Its suggested
stabilization and initialization changes require a separate applicability
decision; they are not permission to add support or alter this joint's gaps.

## What a different method could change

| Approach | Potential benefit | Remaining limitation |
| --- | --- | --- |
| Another implicit contact implementation | Different enforcement, convergence tests and diagnostics may avoid this particular spring-count stall. | Free static motion and contact switching can still cause difficulty. Success on this joint is untested. |
| An explicit dynamic procedure | Its time integration avoids the current implicit equilibrium iteration and its particular count gate. | Small stable timesteps, inertia, contact accuracy and loading-rate sensitivity still need evidence. Constraint correction can introduce additional solves. |
| CalculiX mortar contact | Provides a materially different contact formulation without a complete software migration. | Static only in pinned 2.23; current shared boundaries, cross-role nodes and output mapping remain unresolved. |

The explicit-method description follows the
[Abaqus documentation](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEANLRefMap/simaanl-c-expdynamic.htm).
An explicit result would still need equilibrium, energy and rate checks before
a quasi-static interpretation; the
[energy guidance](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEGSARefMap/simagsa-c-qsienergybal.htm)
does not make a small kinetic-energy fraction sufficient proof of accuracy.
These are method comparisons, not a selected product or a migration decision.

## Comparable research and newer local evidence

Zambrano-Jaramillo and Fischer's
[timber-model benchmark](https://www.proceedings.com/content/080/080513-0049open.pdf)
compares specific Abaqus Standard and Explicit material implementations.
Their explicit embedment model exhibited premature failure and did not reliably
reproduce the standard result. This is not a general verdict against explicit
analysis; it shows why a different solver and apparent numerical progress do
not establish equivalent material behavior.

Shi and colleagues' [bolted LVL/glubam study](https://research.manchester.ac.uk/en/publications/bolted-steel-to-laminated-timber-and-glubam-connections-axial-beh-2/)
compared its detailed model with 48 connection tests, load–displacement curves
and measured strain fields. Its materials and steel-to-wood connections differ
from this candidate. The relevant lesson is to distinguish numerical execution
from evidence for connection behavior; its capacities cannot be transferred.

Locally, the [monotonic fixture](hypotheses/evaluation-resume-2026-09-24/contact-mortar-c3d10-monotonic-attempt01/RESULTS.md)
failed intermediate analytical checks for both penalty and mortar contact.
The [full-step fixture](hypotheses/evaluation-resume-2026-09-24/contact-mortar-c3d10-fullstep-attempt01/RESULTS.md)
subsequently passed opening, compression and reopening endpoints for both.
That pass applies to its fixed endpoint schedule, not the omitted intermediate
states. The shared-edge fixture currently has a preparation/readiness record,
not an accepted result. These newer records supersede any impression that a
single successful mortar coupon has qualified the full joint.

## Recommended continuation

Complete the bounded shared-edge and cross-role method checks already being
prepared. If those leave CalculiX unsuitable, compare the existing analytical
fixtures in a second implementation before porting a representative joint.
Preserve intended contact compliance, openings, materials, free motion and
load resultants; document necessary element and output differences. Require
correct intermediate and endpoint response, then comparable joint reactions,
gaps and energy under appropriate refinement. Do not choose by convergence or
runtime alone.

No new full-frame run, solver installation, altered geometry, relaxed `delcon`,
physical friction/preload assumption or joint acceptance follows from this
review. Existing candidate-specific resistance and six-case demand work remains
necessary regardless of solver.
