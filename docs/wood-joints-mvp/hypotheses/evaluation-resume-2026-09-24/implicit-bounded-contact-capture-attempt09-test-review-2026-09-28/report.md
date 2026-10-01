# Attempt09 independent test-coverage review

Reviewed September 28, 2026. The attempt09 offline suite passes all 39 tests.
The exact packet inventory, regenerated patch, predecessor hashes, and
zero-fuzz replay pass 65/65 independent checks. The three modified source
members replay to their pinned hashes.

This report is bound to attempt09 `source-pins.json`, SHA-256
`bcbf1bc560cbf436fb0ad6547ac5e6abf10e83b849829c42eac256f66c60de62`. Attempt09
uses the exact attempt08 archived source input
(`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`) and
pins attempt08 `source-pins.json`
(`998b35f0e8c885e76ea8c93435751871a07a97151ffde62f41a37479b33e00bb`). The
attempt09 patch hash is
`abaaa6d65d709edb53043619e4a974184b2ec278ef0a3e1cba9dde7c92a84e5e`, identical
to attempt08's patch. The pin check also verifies attempts05–08 source-pins,
patch, and archive hashes, attempt08's complete packet inventory, and the
attempt08 review artifacts pinned by attempt09. See [pin-check.json](pin-check.json),
[coverage-probes.json](coverage-probes.json), and [offline-suite.log](offline-suite.log).

The suite command was
`PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v`; it
reported `Ran 39 tests` and `OK`. The suite compiles only standalone sink
harnesses. No production build, Docker invocation, solver, coupon, or native
case was run. Attempt09 and its predecessors were not edited.

Both attempt08 coverage gaps are closed by tests that exercise representative
regressions. The hook-order test compares the unique production hook and
`checkconvergence` positions in the same regenerated `nonlingeo.c` text. It
moves the hook before convergence in memory and verifies that the order guard
rejects the mutant. The empty-current join test starts with one prior candidate
for tie 1 and zero current candidates, requires `old_missing=1`, then compiles a
temporary sink mutant that skips `wjcc_join_previous()` when the current
candidate array is empty; the mutant is rejected.

The remaining attempt08 controls are retained in the passing suite, including
the consistent cross-pass candidate-cap mutation, mandatory force rows in
permissive caller mode, deterministic temporary-file collision, post-footer
flush and close failures, successful retry reset, invalid pending-link closure,
all four MAP_SUMMARY identity fields, and all six negative STATE_JOIN counts.
The package remains an offline source-delta and test artifact; its readiness,
production build, and native execution authorization flags remain false.
