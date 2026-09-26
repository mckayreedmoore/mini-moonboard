# Parent readiness: aligned K=10000 numerical sensitivity

Decision September 25, 2026: GO for a bounded numerical diagnostic only,
after the original K=100000 baseline has terminated and its outputs have
been hash-checked. The baseline's early-stop record explains the scheduling
decision; the child does not replace that branch's evidence.

The [parent input review](parent-input-review.md) verifies the one native
scalar change from 100000 to 10000 N/mm³. All 35 contact pairs, 70 surfaces,
timber/steel geometry and materials, zero preload, frictionless contact,
assumed stiff nut coupling, applied force pattern, ramp, time points and
motion-stop limits are unchanged. The child freeze is
`4f5d892d6f6270ae2d645463255a048b8b719331a0906412c4c4b85fd304f367`;
the pilot remains
`48649259ba8441429a5dd094ae08487e3713d6b5b860ac39ca1acf71b837d963`.

Use the same pinned native image/binary, four CPU cores/threads and 10 GiB
memory allowance. The maximum runtime is 2400 seconds. Retain the launcher
limits of 3 mm absolute q, 5 mm maximum loaded-node motion and 0.01 rad
controller rotation at requested output points. Those sampled stops do not
bound unsampled overshoot. This shorter diagnostic prioritizes comparison
at the first common output knot; neither a second knot nor seating is
promised within the budget.

The [comparison contract](../penalty-comparison-contract.md) governs numerical
triage before response interpretation. Faster convergence is not acceptance
of contact compliance. Missing pair reports, substep displacements, contact
penetration or momentum evidence remain unavailable rather than assumed zero.
The first coarse increment still has a known free-body displacement
integration error even when its forcing impulse is exact.

This authorizes no reviewed-geometry change, physical hardware selection,
fabrication or criterion pass. It is not a justified finite engagement law,
joint capacity test or full-frame load case.
