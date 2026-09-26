# Prepared 100 N reference-amplitude seating diagnostic

Status: frozen, not executed. This is a separate child of pilot04's immutable
input record. Pilot04's ongoing response is not an input or an accepted basis
for this case. Heavy execution remains serialized, and this child must not run
until the parent disposes the current run and checks readiness.

Exactly 662 existing serialized CLOAD components are multiplied by 100. All
other input cards, including the amplitude table, mesh, materials, contacts,
nut coupling, time settings and output requests, are unchanged. The ramp's
full reference amplitude is 100 N at 0.1 s; this 0.025 s pilot reaches only
15.625 N on each opposed side. It is not a 100 N service-load case.

The original unit-load weights still define q and its 3 mm sampled stop.
Actual scaled CLOAD vectors are recorded separately for work and momentum
accounting. Loaded-node and nut-controller stops remain 5 mm and 0.01 rad.
These limits act at complete reported samples, not exact crossing events.

A free-motion extrapolation suggests that this larger drive might reach the
modeled bore clearances within the pilot window. That extrapolation is not a
prediction of the joint: COM motion differs from the actuator observation,
rotation affects the local bore gap, and contact invalidates linear scaling.
Required outputs include per-bore approach/contact onset and normal transfer,
both sides of complete wood/metal interfaces, bolt/nut engagement actions,
actual applied-load work, momentum and energy balance.

The inherited 0.0025 s first increment crosses amplitude knots and retains
the known coarse-ramp impulse error. This preparation can support an
exploratory contact-onset diagnostic only. Quantifying the seated response
requires a time-refined companion and transfer/engagement checks; the
[time-point source review](../native-ramp-time-points-review.md) explains a
way to align integration endpoints with the ramp knots. No support, preload,
friction, artificial gap closure, physical thread qualification, stiffness or
capacity acceptance is added.

The producer is [`wood_joint_current_scaled_transient.py`](../../../../../fea/wood_joint_current_scaled_transient.py).
`parent-input-freeze.json` binds the source and `input-freeze.json` binds this
derivative. The force scaling is exact in decimal serialized terms; unit
observation weights and every non-CLOAD input line remain unchanged.
