# Ordinary-joint solver practice review

Date: 2026-09-27. Scope: owner-reviewed WJ24 ordinary joint and its response
method. The initial review was read-only; six subsequent small native method
fixtures are linked below. No joint criterion is accepted.

## Findings from manuals and primary research

The software is appropriate for nonlinear contact, but the initial static
problem contains a known free internal motion. Abaqus documents this class of
difficulty: contact-dependent static restraint needs an engaged starting
state; friction needs normal pressure. Its dynamic formulation can traverse
temporarily free motion using inertia. This supports changing the procedure,
but does not prove the exact cause of this CalculiX stall.
[Contact difficulties](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEITNRefMap/simaitn-c-contacttrouble.htm),
[implicit dynamics](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEANLRefMap/simaanl-c-dynamic.htm).

The current quadratic tetrahedra use surface-to-surface penalty contact,
consistent with CalculiX's element/contact guidance. Its contact convergence
logic also checks changes in the active contact set; small residual forces
alone are insufficient. The manual's generic `RF` output has MPC limitations.
Its HHT default is alpha=-0.05; alpha=0 removes algorithmic dissipation.
[CalculiX 2.21 manual](https://dhondt.de/ccx_2.21.pdf), Golden rules, Contact
convergence, Output variables, and Direct integration dynamics (PDF page 300).

The planned alpha=0 transient is consequently stricter than a typical
quasi-static contact integration scheme. Algorithmic damping and a spring
anchoring the cleat have different mechanical effects. Any investigation of
nonzero HHT dissipation must preserve the cleat's freedom, record numerical
energy effects, and compare matched response under reduced dissipation and
smaller increments. This does not authorize using damping to qualify an
otherwise unsupported joint. It cannot explain the earlier static failure.
The Abaqus documentation explains the convergence tradeoff between transient
fidelity and dissipative quasi-static integration; its specific keywords are
not CalculiX controls.
[Implicit dynamics](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEANLRefMap/simaanl-c-dynamic.htm).

A dynamic result requires energy and loading-rate checks before a quasi-static
interpretation. The commonly cited small kinetic/internal-energy fraction is
a screening rule, not proof of equilibrium, contact correctness or capacity.
[Energy guidance](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEGSARefMap/simagsa-c-qsienergybal.htm).

Published timber-joint work demonstrates a component/beam-on-foundation model
validated against connection experiments and a 3D solid model. It predicts
global response and fastener sharing more cheaply; solid FE additionally
resolves local stresses. This supports a hierarchy of verified models rather
than treating increasing 3D detail as validation. Those published connection
laws do not automatically apply to this cleat.
[Basterrechea-Arévalo et al., 2023](https://doi.org/10.1016/j.engstruct.2023.116923).

## Local evidence and corrections

Attempt 09's full-cap force/motion maps agree after correction. Its frozen
static deck contains 35 face-to-face contact pairs, a linear penalty law, no
cleat boundary and no friction/preload. It timed out during its first 0.001 mm
increment; the contact spring count changed substantially. This is consistent
with a known free reference mode and unsettled contact activity. No accepted
pair-level output proves which interface caused the stall.

The source audit at `/tmp/ccx221-review-src/CalculiX/ccx_2.21/src` confirms that
`resultsforc.c` temporarily subtracts MPC forces and later restores them to
nodal `fn`; the generic linear-equation path differs from special control-node
handling for RIGID/MEANROT/PRETENSION. Reading only the restoration loop would
incorrectly suggest that our generic control-node RF gives a reaction.
`nonlingeo.c` and `worparll.c` also require scrutiny for imposed-motion work.
Preserve native energy output, but do not accept its printed external work or
control-node RF as the actuator work without a native known-answer check.
Section `SOF` is an independent wrench observation; its work pairing with the
flexible cap projection remains to be demonstrated.

The earlier clearance explanations are superseded by the source-frame audit
for the external-force pilot. The frozen port map defines N as
(0, −0.7660444431, +0.6427876097). Both the rail bolt direction
(0, −0.6427876097, −0.7660444431) and the principal bolt direction (−1,0,0)
are perpendicular to that N. The previous claim that N is nearly axial at
the rail bolts used an incompatible direction and cannot justify a 1.15 mm
external first-touch estimate. Neither that estimate nor the pilot's 1.3 mm
diagnostic travel bound proves contact; solved local gaps and actions are
required. This correction changes interpretation, not geometry or the frozen
dual load pattern. See the independent readiness audit in
`ordinary-external-force-transient-attempt02/`.

## Decision before further heavy execution

The [prescribed-motion known-answer checks](port-reaction-known-answer-attempt01/RESULTS.md)
are complete. Static generic-equation kinematics match, but the dynamic
average-MPC fixture fails symmetry and full dynamic equilibrium. Independently
omitting its imposed-acceleration inertia term reproduces the native history
to printed precision. The planned prescribed-MPC transient producer is now
disabled; it must not drive the expensive joint model.

The [balanced-force checks](force-port-known-answer-attempt01/RESULTS.md)
pass independent displacement, velocity, center-of-mass and energy comparisons
for both physical-node loading and a free homogeneous average controller.
Use directly applied dual nodal loads for the next bounded external-member
transient, with the whole assembly free and applied nodal work retained.
Freeze its local-contact output, time/load bounds, complete raw output and
numerical comparisons before execution. The method fixtures do not validate
the full patch's C3D10/contact/nut behavior or establish quasi-static response.

No additional static amplitude/time variants are justified by this review.
No artificial cleat support, physical friction/preload change, or historical
pass is introduced. The ordinary response, required sensitivities, reuse
domains and distinct families all remain required.
