# Straight-line SPRINGA known-answer method check

This separate, single-launch coupon tests a built-in workaround for the
failed nonlinear SPRING2 reversal. It changes the numerical carrier type,
not the opposing force laws, applied loads, hand answers or pinned binary.
It produces no current-frame or corner demands.

The inspected CalculiX 2.23 source assigns current elongation in the SPRINGA
tangent branch; its SPRING1/SPRING2 tangent branches use an unassigned
`val` when selecting a nonlinear interval. See the previous packet's
[bounded diagnosis](../nonlinear-spring2-known-answer-attempt01/diagnosis.md).
This is a strong source-based explanation, not binary-level causation proof.
The [official source](https://github.com/Dhondtguido/CalculiX/blob/master/src/springstiff_n2f.f)
also shows the missing assignment in the inspected online version; that
mutable upstream view is not used as the runtime pin.

The pinned [2.23 manual](https://www.dhondt.de/ccx_2.23.pdf), sections 6.2.42
and 7.122, documents nonlinear SPRINGA and warns about reversal, unused
directions and constant table extrapolation. Each auxiliary spring has an
initial 100 mm X span, all Y/Z motion is fixed, and its free-end X motion is
tied to the single physical coordinate. For expected movements ±0.1 mm,
`length - initial_length = delta` exactly, its direction stays fixed, and
its ±10 mm force table is not extrapolated. The 100 mm auxiliary span is
numerical, not a physical member or bolt dimension.

| Step end time | Applied force N | Displacement mm | Positive / negative internal force N |
| --- | ---: | ---: | --- |
| 1 | 10 | 0.1 | 10 / 0 |
| 2 | -20 | -0.1 | 0 / -20 |
| 3 | 10 | 0.1 | 10 / 0 |

Freeze SHA: `c782f4c39c764691b6de0ed608798d43bd3b7310badf769eee3b8aa13ca230ba`.
`prepare.py` and `assess.py` are frozen sources; do not edit them after review.
The assessor checks all three answers, MPC and fixed-direction constraints,
intended table forces, endpoint RF signs/action-reaction and physical/ground
equilibrium. Mere convergence is insufficient.

Parent readiness, focused independent preflight and the existing serialized
native runner govern the one 60-second launch. This packet authorizes no
frame solve, floor stick/reference method, hardware resistance or complete
corner acceptance. The old SPRING2 result remains a failed method check.


## Observed result

The single scoped serialized native launch returned 0 and is terminal.
`assess.py` reports `PASS_NATIVE_STRAIGHT_SPRINGA_LAW_AND_ENDPOINT_FORCE_FIXTURE`.
All three hand answers match exactly at printed precision: +0.1, -0.1,
+0.1 mm; the signed endpoint force pairs and physical/ground balance pass.
Parent additionally inspected all 18 converged printed increments: maximum
table-law residual 1.78e-15 N and ground-balance residual 7.11e-15 N.
See `assessment.json` and `parent-all-increment-check.json`.

This establishes the bounded straight-line scalar constitutive and endpoint
output method. It does not yet verify a relative-coordinate MPC between
two moving bodies, ideal floor stick/recontact, frame cases, product
capacities or complete-joint acceptance. A bounded two-moving-body coupling
check is the remaining method bridge, not a redesign of reviewed geometry.
