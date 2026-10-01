# Native nonlinear scalar spring method check

Parent scopes one native launch of this disconnected five-node known-answer
fixture, with a 60-second limit, on the pinned stock CalculiX 2.23 image. The
current reviewed candidate geometry is not changed or represented here. This
is a new method coupon, not C11/C12 or a six-case frame restart. Root owns the
exact freeze, readiness, serialized slot and final verification.

The specific engineering question is whether native nonlinear `SPRING2`
force-displacement laws preserve the existing isolated scalar endpoint and
linear MPC arrangement. If verified, native opening/bearing can be evaluated
without another sequence of manually selected linear normal/tie branches.
An all-bearing floor hypothesis would still require compatible positive
normal reactions and the complete frame input gates; this coupon does not
implement conditional tangent engagement or choose contact history.

## Frozen method and hand answers

One physical X coordinate is copied by linear equations to two separate
scalar spring endpoints. Each spring has its own fixed endpoint. All unused
translations are fixed. The positive spring has internal component force
`100 max(delta,0)` N, the negative spring `200 min(delta,0)` N, where
`delta=u_first-u_second` mm. The scalar physical balance is
`F_external - f_positive - f_negative = 0`.

| Step end time | Applied force (N) | Physical X displacement (mm) | Positive/negative internal forces (N) |
| --- | ---: | ---: | --- |
| 1 | +10 | +0.1 | +10 / 0 |
| 2 | -20 | -0.1 | 0 / -20 |
| 3 | +10 | +0.1 | +10 / 0 |

Opposing one-sided laws keep this one coordinate supported in both load
directions. This does not establish that a frame with open carriers has no
mechanism. Tables span -10 to +10 mm; all hand answers are well inside that
range. No small artificial stiffness, preload, wrong-sign regularization or
native solver modification is introduced.

The pinned [CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf),
SHA-256 `a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`,
section 6.2.41 (pp.128–129) permits a piecewise linear nonlinear spring
relationship; section 7.122 (pp.598–599) specifies the component DOF line,
force/elongation ordering, decimal real fields and ascending elongations.
It warns that extrapolation keeps force constant and may create zero tangent
stiffness. That warning is handled by the declared limited range, not by
assuming extrapolation is linear.

The exact freeze and source snapshots are under [native/](native/).
An independent preflight must bind to that freeze before the parent runner
can launch. Existing `fea/wood_joint_reduced_native.py` owns the lock, profile
and binary checks, immutable authorization and consumed-run ledger record.
The old linear `K*deltaU` force verifier cannot be reused unchanged for these
nonlinear laws. Native displacements and isolated endpoint RF forces must be
checked against the hand laws, action/reaction and physical equilibrium.

Status: input prepared; preflight and execution results are recorded separately.
No physical joint acceptance or frame demands follow from this preparation.


## Observed native result

The single scoped launch is consumed and terminal. CalculiX returned 201:
`*ERROR: increment size smaller than minimum`, during step 2 near total
time 1.333333, where the ramp changes sign. The assessor records
`FAILED_METHOD_CHECK`; no method or frame acceptance follows.

Step 1 matches +10 N / +0.1 mm with the intended +10 N positive spring,
zero negative spring and -10 N ground reaction. All 17 printed converged
increments before failure match the table law within 8.9e-16 N at printed
precision. [partial-observations.json](partial-observations.json) records
these partial results. It does not verify the negative branch or completed
reversal. A bounded diagnosis can identify a proposed method correction;
this packet grants no second launch or frame-run authority.
