# Two-cell rotational support fixture — attempt02

## Engineering result and stop condition

This bounded fixture tests whether a load-driven compression-only contact
selector can uniquely choose among four states—both supports open, both
bearing, left only, and right only—when the supported body can translate and
rotate. Its useful result is limited to the normal active-set method with two
contacts and two rigid-body degrees of freedom. Stop this method check if any
stage has no admissible state, more than one admissible state, or a force or
moment residual outside the recorded tolerance. A pass does not close the
whole-frame floor-support gate.

## Result

The standard-library verifier enumerates all four subsets at every stage and
returns **PASS_TWO_CELL_NORMAL_ACTIVE_SET_FIXTURE** for five load states.
Exactly one state is admissible at each stage. It finds normal reactions of
5 N and 15 N for the deliberately eccentric both-bearing case, 5 N at the
left-only case, and 5 N at the mirrored right-only case. Maximum generalized
force or moment residual is below the recorded 1e-9 tolerance. The complete
inputs are in [fixture.json](fixture.json); deterministic results are in
[observed.json](observed.json).

Reproduce from the repository root with:

    python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/conditional-floor-two-cell-rotation-fixture-attempt02/verify_fixture.py

## Method and limits

The body has vertical translation z and right-hand-rule rotation theta_y.
At a contact station x_i, the gap is
g_i = g0_i + z - theta_y*x_i and the upward normal force is
N_i = 100*max(0, -g_i) N. The analytic restoring carrier has a diagonal
100 N/mm and 1,000,000 N*mm/rad stiffness matrix. This makes the equations
hand-checkable while allowing the contact reactions to change with rotation.
The carrier is a mathematical device, not a measured floor or candidate
frame property.

For each proposed active subset S, the verifier solves
(K + k_n A_S^T A_S)q = f - k_n A_S^T g0_S,
where q = [z, theta_y], each row of A is [1, -x_i], and
f = [-P, M_y]. It then checks compression and gap signs on bearing and open
contacts, respectively, and sums carrier, applied, and contact generalized
forces to verify both vertical force and moment equilibrium. This is exhaustive
enumeration of four states, not a production algorithm for the 1,122-cell
reduced model.

This fixture addresses the specific limitation identified by the prior
one-cell fixture review: it adds rotational coupling and two-contact load
sharing to a known-answer analytical test. It does not include the
bearing-conditional tangent law exercised by attempt01; coupled tangential
constraints could further change normal states and remain unresolved. It also
does not model elastic frame deformation, real floor compliance, history
dependent friction, or native solver behavior. No mesh or native solve was
run. The full floor gate stays **BLOCKED**, and no attempt01 or c11 response
force transfers to this result.

## Source pins

| Source | SHA-256 |
|---|---|
| [AGENTS.md](../../../../../AGENTS.md) | `672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536` |
| [Option A/B selection](../option-ab-method-selection-2026-09-29.md) | `d73dc9b2583c88b64fab4a8e61b1910dfbdb2881cc6dde629b30911a5425c76a` |
| [attempt01 fixture](../conditional-floor-stick-coupled-load-fixture-attempt01/fixture.json) | `da7961d07502df2fbb0d17de26db0490fc0c868f152dc108b9eae36b01b41a27` |
| [attempt01 observed result](../conditional-floor-stick-coupled-load-fixture-attempt01/observed.json) | `3463cb223c915b4da4b025b9f96e1729e23b9f9ec38f74d82548e4b3a4324954` |

The artifact files are integrity-pinned in [SHA256SUMS](SHA256SUMS).
