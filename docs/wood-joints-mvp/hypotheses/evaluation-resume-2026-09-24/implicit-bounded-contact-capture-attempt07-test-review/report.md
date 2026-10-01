# Attempt07 independent test-coverage review

Reviewed September 28, 2026. The attempt07 offline suite passes all 34 tests.
Package pin and replay checks pass 49/49. The checked-in patch regenerates
byte-for-byte from its pinned archive and sink, and attempt06's archive and
patch still match the recorded predecessor hashes.

This report is bound to attempt07 `source-pins.json`, SHA-256
`04649a3fe41d0b089b0cf9581185a17f10fb6d822a10c6cde94c3b1c4e85b91e`, whose
packet inventory was verified in full. The pinned source archive is
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`; the
regenerated patch is
`f7ff0f8b679d6d1d6448b368d134bc65ff8e038582ded1686a67f853155294f6`.
Detailed pin results are in [pin-check.json](pin-check.json), mutant and
behavior probes are in [coverage-probes.json](coverage-probes.json), and the
complete suite output is in [offline-suite.log](offline-suite.log).

The prior attempt06 footer-flush coverage finding is closed: attempt07 injects
the failure at the fourth flush, after the file position advances beyond the
pre-footer flush, and verifies that the configured destination is not
published. The reader-cap test now kills the representative per-summary
accumulation mutant. Its over-cap mutation leaves the face span at 125000, so
the mutant fails on a different invariant than the expected cap error. A
separate consistent synthetic stream confirms the pinned reader rejects
125001 + 125001 rows with the combined-cap error while a per-summary mutant
accepts it. A face-span-consistent fixture would make that retained regression
control more diagnostic.

The following coverage gaps remain; these describe tests, not demonstrated
defects in the current implementation.

1. **P2 — Production iteration-link order is not asserted.** The pinned
   generated source currently calls `checkconvergence` before
   `ccxcap_iteration_link_`. The nonconvergence sink test models the increment
   before the link, and the cutback test checks captured attempt 1, following
   attempt 2, and `accepted=0`. However,
   [test_patch_policy.py](../implicit-bounded-contact-capture-attempt07/tests/test_patch_policy.py):103
   only checks that the hook text exists; it does not assert that the
   production hook occurs after `checkconvergence` or occurs exactly once. A
   source-order regression or duplicate early hook could leave the standalone
   sink tests green. Add an order and call-count assertion against the pinned
   regenerated `nonlingeo.c`.

2. **P2 — Invalid transition closure has no regression case.** The new sink
   behavior is to emit and close a pending generation link while marking an
   invalid native iteration/cutback transition as erroneous. The harness
   exercises valid nonconvergence and a valid one-cutback transition, but has
   no invalid transition mode. An early return on an invalid identity could
   leave a generation unlinked without failing the current lifecycle tests.
   Add a harness case with an invalid iteration or attempt transition and
   assert one emitted link, cleared pending state, and an erroneous/incomplete
   footer.

3. **P3 — MAP_SUMMARY identity coverage checks only the step field.** The
   retained mutation changes field 2. An in-memory reader mutant that omits
   field 5 (native iteration) from the identity tuple passes that retained
   identity test and accepts a stream where the map summary iteration differs
   from `GEN_BEGIN`; the pinned reader rejects the same stream. Cover all four
   identity fields (step, increment, attempt, native iteration).

4. **P3 — Negative STATE_JOIN coverage checks only one measure.** The
   retained negative mutation changes field 9 (same mapping count). A reader
   mutant that omits field 10 (remapped mapping count) from the negative guard
   passes the retained mutation test and accepts a consistent synthetic row
   with a negative remapped count; the pinned reader rejects it. Exercise each
   count field from 9 through 14.

The remaining named attempt07 controls are meaningful: exclusive-temp
collision preserves the sentinel bytes, force rows remain mandatory with
`require_force=false`, and the two-pass writer cap fails closed above 250000
combined rows. The suite compiles only standalone sink harnesses and checks
Python/source-patch behavior. No Docker invocation, patched production build,
solver, coupon, or native case was run. The package readiness and native
execution authorization flags remain false. Neither attempt07 nor its
predecessors were edited.
