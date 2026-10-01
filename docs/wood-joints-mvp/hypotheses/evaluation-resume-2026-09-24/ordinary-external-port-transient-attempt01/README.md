# Ordinary external-port transient, attempt 01

Date: 2026-09-27. Candidate: `led-clearance-2x6-runner-seated-blocks-v1`.

## Disposition after known-answer check

**Do not execute this prescribed-MPC plan.** No deck was frozen or native job
run for this directory. The [small native fixtures](../port-reaction-known-answer-attempt01/RESULTS.md)
failed the prescribed-MPC dynamic method gate, and its producer is disabled.
The [balanced-force alternative](../force-port-known-answer-attempt01/RESULTS.md)
passed its limited method checks and needs a separately frozen full-patch
transient. The original pre-run plan follows as history.

## Decision, observation, next step

**Decision:** Traverse the initial open-clearance configuration by implicit
dynamics with the existing density scenario, loading only the two external
member coordinates and leaving the cleat free. This changes the equation of
motion from the unsuccessful static attempt 09; it does not change physical
geometry, contact, material, engagement, friction or preload.

**Observation:** Attempt 09's independently checked full-cap projection and
dual load map agree, but its static run accepted no increment before its
900-second timeout. Its first 0.001 mm increment remained far inside nominal
bore clearance, with changing contact activity. A free cleat translation
exists in the reference tangent. The previous goal turn made progress by
correcting the pilot's one-sided clearance arithmetic, but did not obtain a
response. The current shaft-to-receiver and shaft-to-cleat contact graph must
also be included before selecting the new endpoint; the previously proposed
1.3 mm is not a verified closure bound.

**Next step:** Freeze a derived transient deck and independently audit its
differences from attempt 09. Preserve the source inputs and their independent
algebra audit. Retain all physical-node displacement and velocity, cap
section forces/moments, all contact-pair actions and contact fields, strain
and kinetic energy, and native external-work output where supported. Use a
sampled smooth displacement ramp and a short hold. Record numeric ramp,
increment, resource, observation and comparison bounds in `transient-plan.json`
before parent-owned serialized execution. Terminate the named container before
hashing terminal outputs. Keep accepted raw output even if the run times out.

This is a displacement-controlled external response diagnostic. Force and
moment accounting must include inertia; external work must include changes
in kinetic, elastic and contact energy. A converged transient alone is not a
quasi-static response or joint acceptance. A slower ramp and smaller increment
must support that interpretation before further numerical and physical
sensitivities or family reuse. The selected baseline and all reviewed axes
are preserved.

## Source and practice review before execution

The [solver practice review](../ordinary-solver-practice-review-2026-09-27.md)
identifies a required known-answer check of generic MPC reaction and imposed
work extraction before expensive execution. Native printed external work is
not yet verified for this displacement-driven case. The producer's alpha=0
choice removes algorithmic dissipation; review that choice explicitly against
the documented default and response sensitivity rather than equating every
numerical damping mechanism with an artificial cleat support. No transient
plan or deck has been frozen or executed yet.
