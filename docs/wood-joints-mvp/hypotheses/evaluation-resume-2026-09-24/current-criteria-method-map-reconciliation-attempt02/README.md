# Criteria method-map pin reconciliation — attempt02

**Status: coordinator review passed for provenance only.** This versioned reconciliation
addresses two reviewed working-tree row edits, `additional_group_reduction_sensitivity`
and `steel_direct`, while retaining the frozen 47-row coverage file and its
historical map pin. It makes no claim about accepted resistance methods or
criterion dispositions.

The reconciler compares the current method-map bytes directly with the
historical Git blob that the frozen coverage identifies. It checks the exact
current map SHA-256, the exact frozen coverage and criteria SHA-256 values,
the two changed row IDs, and all 47 criterion IDs. It does not require the
working tree to be clean or the current map to exist in a Git commit: the
current source is identified by its exact reviewed working-tree byte hash.
Any byte change fails the pinned check and requires a new versioned review.

Run from the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-criteria-method-map-reconciliation-attempt02/reconcile.py
```

The machine-readable output is
[`source-reconciliation.json`](source-reconciliation.json). The associated
[`parent-review.json`](parent-review.json) records the coordinator's independent
review of the exact script, README and reconciliation record hashes. The
review accepts source provenance only; the aggregator still leaves all
criterion dispositions pending.

The frozen coverage remains SHA-256
`c07c786c37a745aec1c28f917ec6d326cef09b73fa9b14b0d76fb9d06c0d059c` and
continues to name historical method-map SHA-256
`1722eb81263db487579b83dd51f5ae90541ecf7c724d52bf997e5af41647da80`. The
exact current working-tree method map is SHA-256
`2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7`.

This artifact is provenance only. It does not edit frozen coverage, accept
the two method-map rows, resolve criteria, establish candidate readiness, or
change solver/release status. All 47 criteria remain pending.
