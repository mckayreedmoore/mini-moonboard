# Attempt04 elastic operator identity review

This read-only check verifies attempt04's source/output pins, replays the
attempt02 quotient and rigid-wrench scaling fixtures, and reconstructs the
kinematic `D` and raw wrench `W` maps from the frozen connector rows, body
coordinates, and six separated gravity/climber load maps. It performs no body
stiffness factorization, `H` recomputation, physical equilibrium solve, or
native run.

From the repository root, run
`.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-connector-compliance-attempt04-operator-review-attempt01/verify_review.py`
to write [assessment.json](assessment.json); append `--verify` to replay it.
The review exactly reproduces `B`, `D`, and `W` from their source identities;
all 1840 source rows retain positional identity, with duplicate text IDs
preserved. The stored operators have shapes `H: 1840x1840`, `D: 1840x300`,
`e: 1840x12`, and `W: 300x12`.

The check replays the attempt02 cube known-answer and nodal-to-rigid-wrench
scaling fixtures, then authenticates that attempt04 used the pinned quotient
solver and stopped on any failed chunk gate. Its 50 completed bodies imply
288 projected right-hand-side chunks passed; the maximum unchanged nodal KKT
relative residual is `9.2618e-11`. Seventeen legacy zero-multiplier checks
still fail and remain reported separately; none is relabeled as a physical
support reaction or suppressed.

It also repeats the earlier source-only rigid-branch rank screens directly on
the corresponding row subsets of `D`; all four ranks and nullities match at
all four cutoffs. In the optimistic all-normal envelope with the 200
conditional floor-tangent rows excluded, `D` has rank 297 and nullity 3 at
`1e-10`; common global Tx, Ty, and Rz residuals are at most `2.89e-14` after
row normalization, and separated gravity loads do zero virtual work on those
modes to `4.1e-10 N·mm`. The all-open bilateral-only branch still has 74
additional relative-body mechanisms beyond its six common modes. These are
branch screens only: the all-normal tangent is not a selected gravity-start
state, and conditional floor-stick rows do not supply initial support.

Attempt04's pinned assessment reports 50 bodies complete, `H` reciprocity
`9.3832e-11` against `1e-8`, and minimum symmetric-part eigenvalue
`2.3942e-10 mm/N`. This review checks those recorded values and their output
hash; it does not recompute `H` or the eigenspectrum. `D` and `W` remain elastic
operator maps. Global `D.T @ f = W` has not been solved, so these results are
not a physical body-load response or mechanical acceptance.
