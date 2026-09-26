# Parent global wrench audit for contact states 39 and 40

**Status: bounded diagnostic consistency only.** These calculations do not
establish joint acceptance, stiffness, capacity, time accuracy, or a runtime
pass. The wood-joint candidate remains engineer-unreviewed and unreleased.

## Frozen states and method

The parent reconstructed accepted states 1:39 at 0.0195 s and 1:40 at
0.01975 s from the parent-stopped attempt03 trajectory. State 39 is the first
reported positive pressure/nonzero CFN state on the four monitored cleat
bores; state 40 is the following complete accepted state. The stop record
confirms this bounded observation goal, while the 0.025 s horizon remains
unverified. The state framing audit and its independent review are linked from
the [completion ledger](../../../completion-ledger.md).

The [monitor preflight](monitor-preflight.json) selects all eight finite
`PILOT_MONITOR` control vectors at each requested time. The
[state 39 report](state39.json) and [state 40 report](state40.json) each bind
the selected state to full physical-node ACC, matching FRD displacement,
the actual CLOAD/RAMP_N deck, 35 complete contact-pair wrenches, 24 authored
fit-MPC rows, and the pinned CalculiX 2.21 four-point consistent C3D10 mass
operator. Each state has 57,643 physical C3D10 elements, 15 positive-density
bodies and four zero-density nut carriers. The integrated positive-density
mass is 0.011775601009321 tonne in both states.

The parent serialized the two mass reconstructions using local image
`sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646`
(Gmsh 4.12.1, Python 3.12.3, NumPy 2.5.2). The repository was mounted
read-only, the output folder read/write, networking disabled, and the job was
limited to four CPUs and 10 GiB. The environment and artifact pins are in
[parent-run.json](parent-run.json). The host `.venv` does not include Gmsh;
the pinned FEA image supplied that integration dependency.

## Global-origin balance

The reported moment convention is
`M a - CLOAD - contact + C^T lambda`; the physical authored-MPC reaction is
`-C^T lambda`. Contact sums the slave and master force/moment records once per
pair and does not add the separately printed pair-offset couple again. All
315 contact records pass their emitted-vector identity checks at both states.

| State | Force residual (N) | Moment residual (N·mm) | Conditional moment output-token bound (N·mm) |
| --- | --- | --- | --- |
| 1:39, 0.0195 s | `(9.26e-12, -1.96e-10, -1.89e-10)` | `(-1.1174e-6, 1.2495e-7, 8.3922e-8)` | `(9.0983e-5, 2.0027e-5, 2.4094e-5)` |
| 1:40, 0.01975 s | `(5.78e-13, -3.76e-12, 3.05e-13)` | `(-8.4188e-7, -2.1131e-7, -1.5028e-7)` | `(6.7339e-5, 2.0861e-5, 6.4290e-5)` |

Each moment residual component is smaller than the report's conditional
output-token bound for that component. This is not a general equilibrium
pass: those bounds are conditional on reconstructed `M*a` and MPC multipliers
and exclude C3D10 integration/assembly error, residual multiplier uncertainty,
native operator uncertainty, and broader solver/model error. No force-residual
tolerance is established. The summed contact force is zero because the
complete master/slave actions cancel globally; local contact is present and
the contact moment resultants are nonzero.

## Limits and next work

These selected states establish interpretable output coverage and bounded
global wrench bookkeeping for this diagnostic. They do not provide accepted
local resistance or bolt/wood capacity. State 39 is the first *reported*
contact event, not a continuous-time onset. Physical thread engagement,
time-step sensitivity, broader mass/operator uncertainty, a defensible joint
response, and fresh full-frame demands remain unresolved. No geometry or axes
were changed.

## Independent result review

The [independent review](independent-review.md) recomputes the signed global
moment residual vectors from the serialized inertial, CLOAD, contact, and
authored-fit MPC terms. Differences from the stored residuals are at most
about `2.2e-17 N·mm`, consistent with JSON component serialization; the largest
component-to-bound ratio is 1.25%. The review also verifies the parent record's
execution, preflight, and result-file pins. This remains conditional output
consistency, not an equilibrium criterion or mechanical acceptance.

The reused state reports retain legacy `first_state` schema/status strings and
a nested `READY_FOR_PARENT_MASS_RECONSTRUCTION` status. Their `scope` fields
identify increments 39 and 40, while this directory's parent record binds the
completed mass reconstructions and diagnostic-only status. Read those current
bindings together; do not treat the legacy nested labels as a new result or as
an acceptance status.
