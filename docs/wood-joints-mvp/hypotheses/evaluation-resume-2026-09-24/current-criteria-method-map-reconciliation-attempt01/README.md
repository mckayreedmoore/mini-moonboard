# Criteria method-map pin reconciliation — attempt01

**Disposition:** the frozen 47-row coverage file still hashes its method-map
pin to an earlier tracked revision. The checked-out method map differs from
that pinned blob in one row, `steel_direct`; the current row reports only
specified-scenario first-yield component references and a nominal co-located
von Mises axial/shear interaction, with major capacity and demand limits still
open. This source-provenance reconciliation does not establish an accepted
method or resolve any criterion.

Run from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-criteria-method-map-reconciliation-attempt01/reconcile.py
```

The script compares the frozen coverage source pin to the historical Git blob,
the working method map to the checked-out revision, both method-map versions,
and all 47 criterion IDs to the source criteria. It fails closed if either
authority file is modified or if changes exceed the single `steel_direct`
table row. Its machine-readable output is
[`source-reconciliation.json`](source-reconciliation.json).

Do not rewrite `current-criteria-coverage.json` to erase the historical pin.
The follow-on criteria aggregator must preserve that source digest and consume
a versioned current-source overlay with explicit provenance. Until its
independent source reconciliation is implemented and reviewed, the aggregator
cannot present the updated row as silently covered by the old pin.
