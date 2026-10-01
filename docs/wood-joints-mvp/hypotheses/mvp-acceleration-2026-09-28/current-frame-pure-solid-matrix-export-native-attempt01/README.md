# Authenticated pure physical-solid frame export, attempt 01

The parent-owned CalculiX 2.23 export completed with exit zero in 2.342314 seconds. Its container was confirmed terminal. Exact frozen input SHA-256: `614c9b466fd05c0b5ee6917aa26e108fd8151b36459b8b84999cd474f13d9ed3`. The separate readiness review authorized one 120-second / 6 GiB export; no retry occurred.

The parent assessment authenticates the live/frozen sources, exact independent review and all recorded output hashes. The sparse checks pass for 37,647 physical translations over 12,549 nodes, 2,320,506 unique upper-triangle pairs, complete positive finite diagonals, exact reconstructed symmetry and zero nonzero coefficients between distinct physical bodies. All 300 source-coordinate rigid fields across 50 bodies pass; maximum normalized residual is 2.6186013240290654e-13.

This exports the unloaded source solid stiffness only. It does not establish full rank or positive stiffness on the elastic subspace, assemble connector stiffness, solve gravity or select contact states. Auxiliary density exists solely for the export companion mass; `.mas` is excluded from physical gravity. No response or joint acceptance follows. The three authenticated rear responses remain the only usable cases.

The [six-case source identity contract](../current-six-case-operator-reuse-contract-attempt01/README.md) supports reuse of this underlying operator and linear projections across six distinct load maps; each response/state requires separate validation. The next bounded result is a checked free-body elastic reduction retaining all six physical force/moment balances per body, followed by the separate gravity-settle/contact-event scenario.

Replay from repository root:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-pure-solid-matrix-export-native-attempt01/assess.py --verify
```

Assessment SHA-256: `ba41b9c75815f7daf27b3517ac01afff109d5f3e3611aa985811e92c269e69ec`.


## Observed keyword warning correction

The native log emits two warning lines for the redundant explicit `GLOBAL=YES`. Pinned 2.23 `frequencys.f` initializes `global=.true.` and recognizes only the `GLOBAL=NO` override; explicit YES is ignored with a warning. The default remains global, as the native output states and the physical/rotated coupon checks observe. Earlier proposal/review descriptions of explicit YES as a recognized parameter are superseded by this narrower observed behavior. Existing frozen inputs and their passing operator oracles are preserved. Future new decks should omit the redundant parameter, without a rerun solely for this syntax cleanup.

[warning-audit.json](warning-audit.json) binds all three observed logs to their execution hashes and the pinned source archive/member. Replay `audit_export_warnings.py --verify` with the repository virtual environment. Warning-audit SHA-256: `28f569bf3222ad2fe990a396c66c6990a516a0336c979f86de837063e8141b4c`. This finding does not waive unrelated warnings or qualify the frame.
