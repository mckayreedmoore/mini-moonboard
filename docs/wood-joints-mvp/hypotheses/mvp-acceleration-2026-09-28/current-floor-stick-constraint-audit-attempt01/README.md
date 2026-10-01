# Exact-stick floor constraint expressibility audit

The pinned source has 100 floor cells and two scalar tangent components per
cell. Existing finite tangent springs are not, by themselves, exact no-slip
constraints. This input-only audit checks whether the same frozen floor
interpolation points can express exact tangential zero motion on a conditional
all-bearing branch without changing geometry or prescribing an already
dependent auxiliary degree of freedom. It does not generate a native deck.

The [pinned 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf), section 7.56,
permits homogeneous linear equations but each degree of freedom can be
dependent in only one equation or SPC. Directly fixing the existing
projection ghost would violate that rule. The audit recursively expands
the existing floor projection equations to unconstrained physical solid
masters, then uses row/column pivoting to express the same homogeneous
constraint space with distinct new physical pivots. The nonpivot masters
remain independent, so the added equations need no mutual dependency cycle.

Result: the 200 rows have rank 200 over 800 physical master DOFs. No selected
pivot is already dependent or fixed. Original-row reconstruction residual
is 1.95e-16 at coefficient scale; an admissible trial motion closes all
original tangent equations within 2.92e-16. No floor force or displacement
response is solved. `constraint-matrices.npz` stores original/reduced matrices,
pivots and singular values; `audit.json` retains physical DOF and cell owners.

Reproduce from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-floor-stick-constraint-audit-attempt01/produce.py
```

This unlocks an exact source-bound constraint representation. It does not
verify native constraint-force output, actual positive normal bearing or
release/recontact/reference capture. Ground-reference reaction mapping still
needs known-answer evidence before any full-frame use. Any cell opening
invalidates the all-bearing stick hypothesis. The previous aggregate wrench
witnesses do not establish compatible bearing. No frame readiness, floor
capacity, hardware capacity or complete-corner acceptance follows.
