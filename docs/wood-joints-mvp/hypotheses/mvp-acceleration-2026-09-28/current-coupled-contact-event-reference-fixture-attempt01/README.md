# Exact coupled contact-event reference fixture

This fixture tests the event-reference dependency identified in the
[support/corner review](../../support-corner-review-2026-09-30/README.md).
It uses that review's synthetic structural matrix `[[2,1],[1,2]] N/mm`
and normal law `N=2 max(q,0)`, with positive `q` denoting compression.
It performs no native or frame calculation.

The **synthetic** settling force is `(-4,-3) N`. Its open equilibrium is
`t=-5/3 mm, q=-2/3 mm`. Then ramp the external force as
`F=(-4,-3+2α) N`. Before contact the exact open branch is

```text
t=(-5-2α)/3 mm
q=(-2+4α)/3 mm
```

Contact starts at `α=1/2`, with `q=0`, `t=-2 mm` and zero normal/tangent
reaction. Capture `t_ref=-2 mm` there. Afterwards the held branch is
`q=(2α-1)/4 mm, N=2q, T=-q`. At full load it reaches the review's
`F=(-4,-1) N` example with `q=1/4 mm, N=1/2 N, T=-1/4 N`.
Thus this particular synthetic path reaches an admissible final state where
the fixed-zero reference has no admissible branch. This does not show that
the actual frame's gravity/climber path can do so.

Unloading releases the tangential constraint when compression reaches zero.
The fixture changes lateral force while open and then re-engages at
`t_ref=-1 mm`, demonstrating that retaining the previous `-2 mm` reference
would describe a different history. Every stored state checks exact force
balance, the normal law and zero open tangential reaction.

Event bracketing is tested at odd step counts 3, 7, 15, 31 and 63, so contact
always occurs between sampled steps. Exact linear interpolation recovers the
same event/reference at every resolution. A last-open reference instead has
errors `1/(3n) mm` for the first ramp and `2/(3n) mm` for re-engagement.
Those finite-step errors are recorded, not hidden by a force tolerance.
For a nonlinear frame, this linear event oracle is only a validation target;
its locator/refinement and coupled branch selection still need proof.

The SPD synthetic operator needs no coordinate gauge. This fixture does not
validate a reaction-free full-frame gauge, count internal zero modes, select
states for 100 contacts, or establish frame uniqueness, capacity or acceptance.
The settling load is not a decomposition of actual frame gravity.

Read-only replay:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-coupled-contact-event-reference-fixture-attempt01/verify.py --verify
```
