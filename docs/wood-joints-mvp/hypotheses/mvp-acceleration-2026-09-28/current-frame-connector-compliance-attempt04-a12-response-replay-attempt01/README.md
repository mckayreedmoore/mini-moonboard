# A12-rear response replay against the frozen elastic reduction

This bounded, read-only replay checks one already-authenticated `a12-rear`
native response against the frozen attempt04 source operators. It uses the
existing 1,840-row `B` map and `H`, `D`, `e`, and `W`; it performs no native
solve, stiffness factorization, or support-state selection.

The replay authenticates the response and its parent all-body audit, confirms
that all 12,549 physical node coordinates and 50 body ownership maps match the
operator source, and uses the pinned CCX 2.23 DAT parser to retain half-last-
place intervals for every printed displacement and reaction. It reconstructs
each body's rigid coordinates with the same centered, 1,000 mm-scaled `R`
basis and `R.T * (u - R*a) = 0` gauge used by the reduction.

The 1,292 SPRINGA multipliers use the source-oriented native endpoint internal
forces. The 348 SPRING2 multipliers use the signed local force on the first
endpoint, checked against the existing `k*q` interval. For active floor-T
rows, the corrected physical action is raw reference RF minus the recorded
transferred source-load correction. Since each row's `B` translation
coordinate increases along its owner tangent basis, the multiplier in
`D.T*f = W` is the negative corrected physical action. Released floor-T rows
have no native tangent equation or spring and contribute exact zero. The 12
load columns are composed as `lambda * (gravity + climber)` for the matching
`a12-rear` case; the emitted CLOAD map agrees with the source sum within
`3.6e-11 N`.

All seven increments pass. The maximum rowwise ratios of residual to
propagated DAT-token interval are 0.433 for `q = D*a + e - H*f` and 0.912 for
`D.T*f = W`. Across increments, all 1,640 SPRINGA/SPRING2 displacement rows
also intersect their existing native source-q intervals (worst ratio 0.814),
all 350 active floor-T displacement intervals contain zero, and all 1,050
released floor-T actions are zero. The detailed per-increment residuals and
input hashes are in `assessment.json`; reproduce with:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-connector-compliance-attempt04-a12-response-replay-attempt01/replay.py
```

DAT intervals cover printed U/RF rounding only. The reduction's separately
recorded KKT residual diagnostics are included but are not relabeled as
physical uncertainty bounds. This supports applicability of the reduction to
this single conditional response; it does not accept the frame or joint,
select other contact states, prove recontact or uniqueness, or authorize
fabrication or climbing.
