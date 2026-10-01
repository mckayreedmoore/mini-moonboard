# Ordinary-joint actuation/map-binding handoff — attempt03

Date: 2026-09-28  
Candidate revision: `led-clearance-2x6-runner-seated-blocks-v1`  
Status: **NOT_FREEZE_READY**

This append-only successor resolves attempt02's remaining handoff ambiguity by
separating the ordinary-case freeze from the independent T02/T03 method-coupon
lane. It does not select a history, authorize execution, change geometry, or
establish mechanics acceptance. The machine-readable dependencies are in
[`dependency-lanes.json`](dependency-lanes.json); the packet and upstream
sources are bound in [`source-pins.json`](source-pins.json).

Verify packet files with `sha256sum -c SHA256SUMS` from this directory. Verify
upstream files with `sha256sum -c SOURCE-SHA256SUMS` from the repository root.

## Two lanes that converge before the ordinary-joint run

The case-freeze lane is ordered and remains open:

1. Classify the question as local component characterization or physical/service
   transient. The reviewed sources do not provide simultaneous source-bound
   six-component rail and principal histories with a physical time basis. A
   characterization result must remain a bounded diagnostic and cannot be
   called service demand.
2. Bind the exact history, signs, frames, datums, units, solver procedure and
   version, time basis, ramp, duration, event rule, timestep range and resource
   cap. The prior `*STATIC` deck's unit step time is not physical time.
3. Reparse the immutable final deck to identify every active map, carrier,
   control, support, pivot and dependent equation row. Attempt01's N+ deck has
   A00–A03; do not prune an instantiated map based on response magnitude.
4. Under that selected history, prove exact transformed map equivalence or
   qualify every distinct active map with matched direct, map-only and
   map-plus-carrier comparisons. A00's prior small global-Y body-force fixture
   does not qualify A01–A03 or external-port motion.
5. Freeze the applicable observations, resolved-bearing rule, signed bore
   thresholds, balance/work/energy/momentum/rate/timestep limits, required
   accepted post-onset states and fail-closed stop/resource rules. Each value
   needs a source/method basis and units.

The method-coupon lane is independent of case-freeze decisions 1–5. T02 and
T03 may be prepared, reviewed, and—if their own gates are satisfied—run while
the case-freeze lane is still unresolved. This does **not** permit the ordinary
joint run early. Each coupon requires pinned CalculiX 2.23 runtime access,
fresh parent readiness, its required authorization and a durable parent-owned
run-once record. Native jobs use one serialized slot; run one coupon at a time
and preserve its complete result and parent audit. T02 qualifies capture
instrumentation only. T03 `shared_slave_penalty` qualifies its small coupon
topology only. Neither establishes ordinary-joint mechanics.

The lanes converge at the immutable ordinary-joint freeze. That run requires
all case-freeze decisions 1–5, both applicable coupon gates, active-map
qualification, complete input/output hashes, fresh readiness/authorization,
and a distinct parent-owned run-once record. A failure or frozen stop leaves
the response unresolved and must preserve all evidence. Only an audited
response can proceed to numerical/model sensitivity and family applicability;
it remains separate from six fresh frame cases and the 47 structural criteria.

## Current stop boundary

Both packet checksum manifests and the 58 bound source hashes passed parent
validation. Attempt02's correctness review confirmed that the static step-time
clarification is accurate and that no unqualified map/result was promoted.
Its architecture review found only the ambiguity corrected here. This packet
is still a planning handoff: the runtime is inaccessible, T02/T03 native
coupons have not run, the case classification/history and acceptance contract
remain open, and no ordinary-joint response is accepted. Preserve the reviewed
geometry, exact source decks and historical failed runs.

No capacity, criterion pass, fresh frame result, fabrication authorization,
candidate selection, floor qualification or climbing release follows from
this packet.
