# Ordinary-joint actuation/map-binding handoff — attempt02

Date: 2026-09-28  
Candidate revision: `led-clearance-2x6-runner-seated-blocks-v1`  
Status: **NOT_FREEZE_READY**

This append-only successor orders the decisions left open in attempt01 and
corrects one timing phrase identified by independent review. It does not
select a new case or history, authorize a native run, change geometry, or
establish mechanics acceptance. The machine-readable sequence is in
[`decision-sequence.json`](decision-sequence.json). Attempt01 and both
independent reviews are pinned in [`source-pins.json`](source-pins.json).

Verify packet files with `sha256sum -c SHA256SUMS` from this directory. Verify
the upstream source files with `sha256sum -c SOURCE-SHA256SUMS` from the
repository root.

## Corrected interpretation of attempt01

Attempt01 says the `NLGEOM *STATIC` deck ramps to 1.0 mm “over one second.”
That is a unit static step-time interval in the static amplitude; it is not a
physical second or a transient duration. The deck failed before accepting its
first increment and produced no response. Its step time and amplitude cannot
be reused as the next transient’s physical time basis.

## Coordinator order

Resolve these items in order. A downstream choice is not ready while its
upstream basis is open.

1. **Classify the question.** State whether the target is local component
   characterization or a physical/service transient. The current records do
   not provide source-bound simultaneous six-component rail and principal
   histories with a physical time basis. Without those histories, no run or
   result may be described as service demand. Characterization remains a
   separate diagnostic question and still needs an applicable, known-answer
   method.
2. **Bind the exact input history and method.** Once the purpose is declared,
   identify the source case, controlled coordinates or sampled force/moment
   histories, signs, frames, datums, units, solver procedure/version, time
   basis, ramp, duration, event/endpoint rule, timestep bounds and resource
   cap. For a physical case, source curves and their provenance are mandatory.
   For characterization, state the limited diagnostic question and do not
   imply a service load. Do not infer a physical second from a static step.
3. **Derive the active map set from that exact deck.** Reparse the immutable
   deck and bind every instantiated nut-fit map, carrier, control, support,
   pivot and dependent equation row. The attempt01 `n_plus` deck instantiates
   A00–A03, so all four remain in preflight. Another case may use fewer only
   when its exact deck proves that; response magnitude is not grounds to prune
   an instantiated map.
4. **Resolve map applicability under the selected history.** For every
   distinct active map, either demonstrate exact transformed equation,
   support, pivot, dependent-row, RHS, carrier-kinematic and work-dual
   equivalence to a qualified map, or qualify it through matched direct,
   map-only and map-plus-carrier comparisons under the applicable frozen
   method/history. A00’s known-answer result covers A00/M03 under its small
   global-Y body-force history only; it does not qualify A01–A03 or attempt01’s
   external-port motion.
5. **Freeze the observation and acceptance contract against that method.**
   Bind the exact outputs, accepted-state/generation/face joins, signed bore
   observations, first *resolved* bearing rule, required post-onset states,
   force/moment closure, work/energy/momentum measures, rate and timestep
   comparisons, numerical thresholds, failure limits and resource stops.
   Thresholds require a stated source/method basis and units. Do not copy the
   failed static deck’s gates or call capture instrumentation a mechanics
   oracle. Missing observations are unavailable, never zero.
6. **Pass prerequisite method coupons.** Their preparation can proceed while
   the case freeze is being resolved, but native jobs remain serialized. With
   pinned CalculiX 2.23 access, fresh parent readiness, required authorization
   and a durable parent-owned run-once ledger, build and run the bounded T02
   contact-capture coupon and T03 `shared_slave_penalty` coupon, one job at a
   time. Preserve each full result and parent audit. T02 qualifies capture
   instrumentation only; T03 qualifies its small topology only. Neither
   accepts the ordinary joint. Do not synthesize an authorization receipt.
7. **Create an immutable ordinary-joint freeze.** Only after steps 1–6 are
   closed, bind the complete input/output hashes, exact active maps, accepted
   method, thresholds, stops, runtime envelope, readiness/authorization, and
   unique run-once record. Parent schedules this native run serially. Any
   source, capture, solver, minimum-step, or resource failure leaves the
   response unresolved; preserve the failed evidence and do not tune the
   reviewed physical model to force continuation.
8. **Audit response before expanding scope.** Reconcile accepted-state
   outputs, signed transfer, contact/bearing, kinematics, equilibrium, work
   and energy under the declared method. Only an auditable response proceeds
   to matched mesh, timestep/contact, clearance, grain-frame and engagement
   sensitivities, then complete family applicability. It remains separate
   from fresh six-case frame demands and the 47 structural criteria.

## Current state and stop boundary

Attempt01 is a bounded map/history draft, not a run freeze. Its source pins
and packet checksums pass; correctness review matched all four map summaries
and all 24 emitted equation cards to the pinned source inventory. Architecture
review found the dependency-order gap now addressed here. Correctness review
also found the static-step wording gap corrected above. These reviews validate
the handoff and source binding only; they do not establish a physical response.

Current environment and readiness remain fail-closed: the pinned Docker
runtime is inaccessible to this process; no local CalculiX executable or
alternate runtime is available; T02/T03 native coupons have not run; and the
attempt01 transient history, map qualification route, acceptance thresholds,
and freeze remain unresolved. Preserve the owner-reviewed geometry and all
source decks. Do not run a native solve until every applicable gate above is
source-bound and parent readiness is fresh.

The reviewed candidate, direct contact model, free cleat, current port maps,
66 Hillman axes, 92 candidate bolt axes, and twelve starting frame-bolt
arrangements remain unchanged. No capacity, criterion pass, full-frame result,
fabrication authorization, candidate selection, floor qualification, or
climbing release follows from this packet.
