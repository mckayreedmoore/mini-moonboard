Attempt06 independent test and coverage review, September 28, 2026

The pinned attempt06 package passes its documented offline suite: 30 tests,
zero failures, zero errors, and zero skips. The requested behaviors work in
the reviewed package and the additional probes described below. Two retained
regression controls need strengthening: the reader test does not isolate
combined pass counts, and the footer-flush fault is injected before the footer
is written. These are test-coverage findings; this review did not demonstrate
a corresponding defect in the current implementation.

The review is bound to attempt06 `source-pins.json` SHA-256
`869b5d7121b8cea80e95f9d87de159f225ec1c1d9b1a0e327e8693bc0e5684c5`.
Its patch is
`e98a5dd69aa1d992b18256a2cbd7dfedce6a2001b4af6085fdcac9c31ba8ba67`,
sink is
`4f8c541eabefc926a133f6f8e93d3e58facc86fb792f06768aee898795f2a121`,
and reader is
`1b2b9299db08a18d43415383b0ae860d82bca31f95dd198872d0afd77d3e5e42`.
[pins-before.json](pins-before.json) contains the complete inventory and 31
passing pin, regeneration, predecessor, and authorization checks.
[base-pin-cross-check.json](base-pin-cross-check.json) additionally confirms
that all 1,197 archived source-file hashes match the inherited base manifest
and that the recorded base-image tag and ID agree. No local Docker image was
queried. The final [pins-after.json](pins-after.json) records that all 15
attempt06 files are unchanged.

1. **P2 — The reader's combined cap can regress to a per-summary cap without
   failing its retained tests.** At
   [test_capture.py](../implicit-bounded-contact-capture-attempt06/tests/test_capture.py):242,
   the boundary control has one `MAP_SUMMARY` containing 250,000 candidates;
   its negative mutation makes that one summary exceed 250,000. The separate
   writer control at line 261 correctly exercises two passes, but its output
   has `GEN_END.complete=0`, which the reader rejects before checking summary
   accumulation. Consequently, neither control isolates the reader's
   cross-summary sum. Replacing only `candidates_by_gen[gen] += candidates`
   with `candidates_by_gen[gen] = candidates` in an in-memory reader copy
   leaves all 23 sink/reader tests passing, as recorded in
   [reader-cap-mutant-suite.txt](reader-cap-mutant-suite.txt). The review's
   otherwise consistent synthetic two-pass stream with 125,001 candidates
   per pass is rejected by the original reader with the combined-cap message
   and accepted by that mutant. The 125,000-per-pass companion passes both.
   Retain these paired controls in the package suite so the required total
   across observed passes is protected independently of the writer.

2. **P2 — The retained footer-flush control misses the flush after
   `RUN_END`.** At
   [sink_harness.c](../implicit-bounded-contact-capture-attempt06/tests/sink_harness.c):12,
   `fail-footer-flush` fails the third flush. Its normal two-generation route
   flushes once at each generation end, then once at finalizer entry, and
   finally once after writing `RUN_END`. The third call therefore precedes
   the footer; the fourth call is the intended footer flush. The
   [documented-call-3 trace](documented-call-3.trace.txt) observes
   `footer_seen=0` at injection. A temporary harness copy retargeted to call
   four observes `footer_seen=1`, and the current sink correctly leaves both
   the configured destination and temporary sidecar absent; see the
   [actual-footer-call-4 trace](actual-footer-call-4.trace.txt). Retarget or
   supplement the retained fault so it protects failure after the complete
   footer has been emitted. Keep the pre-footer fault as a separate control
   if that behavior is also intended to remain covered.

The requested coverage was assessed as follows. Source line references are
within the hash-bound attempt06 files above.

| Behavior | Evidence and assessment |
| --- | --- |
| Energy completeness | `test_capture.py:272` exercises a missing trial row, disabled energy, nonfinite energy, and finite inputs whose energy sum overflows. It asserts unavailable energy, false trial completion, false run completion, and reader rejection. Line 295 independently changes an otherwise successful summary and verifies that `require_energy=false` cannot waive `nener==1`. Line 412 rejects a nonfinite summary value; line 436 confirms `nener==0` reports unavailable energy. Review-only mutations additionally confirm that unexpected energy rows or a numeric energy value in `nener==0` are rejected. These are meaningful checks of the current energy invariant. |
| Explicit route lifecycle | `test_capture.py:135` runs the two-step explicit harness route and verifies no sidecar. `test_patch_policy.py:78` ties the preparation result to the exact `iexpl<=1 && mortar==1` generation guard at the second contact call, checks hook arguments, and checks the single job-level finalizer. The harness models that guard; it does not execute production `nonlingeo.c`. This is useful offline structural coverage, with no claim of native route execution. |
| Combined candidate cap | The writer control at `test_capture.py:261` genuinely reaches the combined 250,000-row cap across two passes. The retained reader coverage has finding 1. Additional isolated synthetic controls verify that the current reader accepts exactly 250,000 combined rows and rejects 250,002 despite each individual pass being below the ceiling. |
| Provenance mismatch | `test_capture.py:233` changes one syntactically valid input hash and requires the specific frozen-binding mismatch error. This reaches the comparison rather than failing hash syntax or footer size. The review separately mutated all seven provenance fields; every field was rejected with the same intended error. These checks validate reported bindings against the supplied expectation, not the authenticity of a binary or input outside the stream. |
| Existing destination collision | `test_capture.py:311` creates an owner-data sentinel, executes capture, verifies byte-for-byte preservation, and requires no temporary sidecar. This meaningfully exercises no-overwrite publication. |
| Disabled capture | `test_capture.py:140` uses an empty path across two steps and asserts no published output. The harness also checks disabled state, zero generations, no pending lifecycle, and no open stream. An additional run with the environment key actually absent also completed with no files. Source policy checks the active predicate and post-results guard. There is no runtime performance measurement or production Fortran execution. |
| Fail-closed output | The suite exercises generation flush failure, finalizer pre-footer flush failure, close failure, destination collision, byte overflow, candidate overflow, incomplete energy, malformed roster, missing record classes, and invalid counts/identity. Output failures leave the configured path unpublished; logical validation failures may publish an explicitly incomplete diagnostic stream which the reader rejects. The final-footer flush coverage gap is finding 2; the independent probe confirms that the current code handles that failure correctly. Arbitrary short-write, allocation, and filesystem-failure injection are not established by this suite. |

The documented command was run from attempt06:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
```

[offline-suite.json](offline-suite.json) records the command, times, exit code,
and compiler (`cc` 13.3.0). The complete unittest output is in
[offline-suite.stderr.txt](offline-suite.stderr.txt). The suite compiles three
standalone C sink harness variants and checks Python reader and patch
preparation behavior. The extra review probes are reproducible with
`PYTHONDONTWRITEBYTECODE=1 python3 -B probe_coverage.py` from this review
directory. They alter only an in-memory reader or temporary standalone
harness copies; [coverage-probes.json](coverage-probes.json) records the
results. The synthetic cap TSV files are constructed reader controls, not
native captures, and their auxiliary digests are not evidence of replayed
solver events.

No attempt06 source or test was edited. No production CalculiX compilation,
Docker operation, native solver execution, coupon run, joint-input freeze,
geometry change, or readiness promotion was performed. The recorded
attempt06 readiness and native-execution authorization remain false. This
review establishes bounded offline behavior and identifies the two retained
coverage gaps; parent-owned integration and native-mechanics decisions remain
outside its result.
