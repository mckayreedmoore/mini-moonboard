# Assumption audit and owner clarification

The subsequent owner instruction limits current verification to the single
2×6 rear support legs and their attachment assumptions. Panel construction is
accepted as the design basis; another frame comparison is explicitly outside
scope. See [the leg-only assessment](leg-only-assessment.md) for the current
calculation and finite remaining checks. The discussion below audits the older
model; it does not reinstate a whole-frame assessment requirement.

The owner clarified on 2026-09-12 that floor friction is outside the requested
assessment. For subsequent member/connection calculations, explicitly assume
that the feet do not slide. Do not require friction measurement or use the
previous μ=0.40 comparison as a release prerequisite. This is a structural
boundary assumption, not a verified floor property or a newly modeled anchor.

## What the existing calculations do and do not establish

All twelve attachments on each of the four main panels were included. The
reinforced candidate also has nine screws per kicker, for 66 panel/kicker
screws total, plus 132 SDS screws and 24 structural bolts.

The native F10 cases represent a 250 lb body weight multiplied by two:
500 lbf downward, plus a separately fixed 300 N (67.4 lbf) horizontal force,
at a 100 mm (3.94 inch) outward hold projection. All of that resultant is
applied at one hold. This is a severe comparison scenario, not a 250 lb static
hang and not a verified impact spectrum or universal worst case.

Product/NDS/APA reference values have sources and explicit adjustment
conditions. The response model is less established: it assigns the same
isotropic spring stiffness to different screw and bolt types, tries two
arbitrary stiffness levels, uses homogeneous isotropic plywood and timber,
and applies a mathematical force/couple over a 20 mm patch rather than solving
actual hold contact. Neither stiffness case has been established as a bound on
the real assembly. Software tests verify calculations and force recovery; they
do not validate those physical assumptions.

Consequently, the earlier release report's imperative statements that the top
rail, panel attachment count and leg connection must be redesigned are stronger
than these diagnostics support. Treat those results as concerns to investigate,
not demonstrated physical inadequacy or settled redesign requirements. Separate
source-based detailing findings, such as the declared cross-grain bolt-row
criterion, remain distinct from this response-model uncertainty.

A simple comparison explains why twelve screws can seem adequate: 250 lbf
shared equally among twelve attachments is 20.8 lbf each, before panel dead
load, dynamics and moments. That is arithmetic illustrating the intuition,
not an established sharing model or a panel capacity rating. Actual forces
include shear and withdrawal and need not be equal.

## No established failure weight

No defensible climber weight for physical failure follows from the existing
runs. Dividing 250 lb by a reported utilization is invalid: panel/frame dead
load and the fixed horizontal force do not scale with climber weight; active
contacts can change; and the assumed connection stiffnesses are uncalibrated.
Moreover, the denominators are allowable/reference criteria, not measured
ultimate breaking strengths. Exceeding one does not predict collapse.

A useful next capacity study must state a no-slip support assumption, distinguish
static hanging from a chosen dynamic load case, justify panel and connection
load sharing, and vary climber weight with all other terms treated explicitly.
Its initial output would be a conditional design-reference crossing, not an
ultimate failure weight. Do not publish a numerical weight limit by extrapolating
the exploratory results.
