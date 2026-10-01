# Attempt08 independent test-coverage review

Reviewed September 28, 2026. The attempt08 offline suite passes all 37 tests.
The exact package inventory, source replay, and predecessor-pin review pass
47/47 checks. The regenerated additions-only patch matches byte-for-byte and
applies with zero fuzz to the pinned archive.

This report is bound to attempt08 `source-pins.json`, SHA-256
`998b35f0e8c885e76ea8c93435751871a07a97151ffde62f41a37479b33e00bb`. Attempt08
uses the exact attempt07 archived source input
(`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`) and
pins attempt07 `source-pins.json`
(`04649a3fe41d0b089b0cf9581185a17f10fb6d822a10c6cde94c3b1c4e85b91e`). The
attempt08 patch hash is
`abaaa6d65d709edb53043619e4a974184b2ec278ef0a3e1cba9dde7c92a84e5e`; the
pinned predecessor attempt07 patch is
`f7ff0f8b679d6d1d6448b368d134bc65ff8e038582ded1686a67f853155294f6`. The pin
check also confirms the attempt06/07 predecessor chain and inherited base
build/image records. Details are in [pin-check.json](pin-check.json), behavioral
and mutant probes in [coverage-probes.json](coverage-probes.json), and the
complete suite output in [offline-suite.log](offline-suite.log).

The suite command was
`PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v`; it
reported `Ran 37 tests` and `OK`. It builds only standalone C sink harnesses.
No production build, Docker invocation, solver, coupon, or native case was run.
Attempt08 and its predecessors were not edited.

The attempt07 coverage gaps for invalid transition closure, MAP_SUMMARY identity
fields, all six STATE_JOIN counts, retry reset, candidate-cap consistency, and
post-footer I/O failure have retained controls. The retry harness reports a
captured attempt 2 followed by a successful reset to attempt 1. The invalid
transition harness verifies one emitted link, cleared pending state, and an
erroneous/incomplete footer, with the reader rejecting the capture. The
mandatory-force-row mutation is rejected even in permissive caller mode. The
fixed-PID temp collision preserves the pre-existing sentinel, and injected
footer-flush-after-RUN_END and close failures do not publish an output.

Two test-coverage gaps remain; these are not demonstrated defects in the
current implementation.

1. **P2 — The production iteration-link order assertion is defeated by
   comparing offsets from different source versions.** The checked-in
   regenerated source currently calls `checkconvergence` before
   `ccxcap_iteration_link_`, and the test asserts exactly one link call.
   However, the test compares the link offset in patched `nonlingeo.c` with the
   convergence offset in the unpatched archive member. An in-memory mutant that
   moved the link before `checkconvergence` still passed the test because
   inserted patch lines shift the offsets. Compare both locations in the same
   regenerated production text (or use a stable structural relation). The
   duplicate-call mutant is correctly rejected.

2. **P3 — The empty-state join test does not cover old candidates disappearing
   in the current generation.** Its two-generation fixture covers an empty
   prior set followed by one current candidate (`new_missing=1`) and a
   zero-to-zero tie. It does not exercise the `old_missing` count when the
   prior set is nonempty and the current set is empty. A temporary sink mutant
   that skips `wjcc_join_previous` whenever the current candidate count is zero
   passes the retained test. Add a prior-nonempty/current-empty fixture if that
   old-missing counter is part of the required contract.

The combined-cap reader control is diagnostic: an in-memory mutant that
replaces cross-pass accumulation with per-pass assignment accepts the valid
125000 + 125000 candidate fixture, so the test fails as intended. The current
attempt08 package remains offline-only and its readiness, production build,
and native execution authorization flags remain false.
