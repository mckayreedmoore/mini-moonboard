# Attempt10 independent test and coverage review

No actionable finding was identified in this scoped review. All 47 hash/replay checks, 51 supplied focused tests, and 187 independent synthetic probes passed. This is a method software review; it provides no candidate capacity, structural criterion acceptance, fabrication authorization, or solver validation.

The reviewed artifact is `../current-group-action-method-attempt10/`. Its patch SHA-256 is `bf8cffa8a4954a0bf96a3c73aec0c5ea6212c518efb8eae56925a1260c469e8a`. The replayed module SHA-256 is `121ec9d5399aa3e856b4038232e6d61c628aac42ce2addf8d1ff7e3a0e4c3df9`; the supplied test file SHA-256 is `741ef514d6a7ea6a88c24f95a53241d126b61e4cd8af6c13d7288268b18adef9`. [replay-verification.json](replay-verification.json) records the complete artifact snapshot, source pin comparisons, patch commands, and observed hashes. [review.json](review.json) binds the conclusions to these bytes; [terminal-hashes.json](terminal-hashes.json) binds this report and its executable evidence.

The review used the exact artifact files and directly referenced chain manifests/artifacts. No prior review report was read, and no broad repository search was performed. Original attempt files and maintained source/tests were not edited. Only this report directory and disposable `/tmp` replay trees were written. There was no solver, Docker, native mechanics execution, geometry change, or criteria-method-map change.

Both replay steps used `patch --batch --forward --fuzz=0 -p1` in separate copied trees. Attempt07 replay reproduced the attempt10 base byte for byte, and attempt10 replay reproduced the pinned maintained files byte for byte. Neither patch reported fuzz, offsets, or rejected hunks. The attempt10 source-pins and terminal manifests agree with actual files, maintained files, the directly referenced attempt07 patch/terminal manifest, attempt09 terminal manifest, and criteria-method-map hash. Entries in both referenced terminal manifests were independently hashed. The entire attempt10 artifact snapshot remained unchanged after replay and tests, including both base files. Attempt09 was verified as historical chain metadata; it is not used as the replay base.

The supplied focused suite passed `51 passed in 0.09s`; the independent suite passed `187 passed in 0.29s`. Both ran with bytecode writes and pytest cache disabled in the isolated replay tree. An independent assertion checked the imported module's exact filesystem path. Commands, environment, exit codes, and transcript hashes are recorded in [test-execution.json](test-execution.json); full outputs are [focused-test-output.txt](focused-test-output.txt) and [independent-test-output.txt](independent-test-output.txt).

| Independent probe group | Cases | Observed behavior |
| --- | ---: | --- |
| Multi-digit paths | 18 | Rows of 12, 21, and 103 fasteners calculate with numeric, lexical, reversed, and duplicated declarations of the same path set. Missing, extra, zero-padded, wrong-index, and wrong-component paths remain pending. |
| List growth/removal | 34 | Actual fastener rows grow or shrink across index 10; complete declarations require `.length` and every added/removed whole-item path. Length-only, item-only, missing-item, wrong-leaf, and extra declarations remain pending. Empty extension lists with scalar, null, object, or nested-array items behave consistently in both directions. |
| Escaped keys | 52 | Dot, brackets, backslash, empty, space, tab, mixed whitespace, Unicode whitespace, and literal escape-token keys work at root, object, and array positions. Nine simultaneous literal/nested/array/escape-token changes remain distinct; omitting any one remains pending. |
| Ignored metadata boundary | 7 | Root scenario/source metadata does not become a declared factor change. Identically named keys under both ordinary and empty object keys are tracked. |
| Contract and independent evidence | 66 | Every required contract-field omission, stale-hash field mutation, rehashed mutation with an unchanged binding, rebound semantic mismatch, malformed path container, missing/mutated external binding, and missing/wrong payload evidence remains pending. |
| Output claim boundary | 2 | Ratios above and below one remain dimensionless method sensitivities. Injected producer capacity/acceptance fields do not become output dispositions. The claim-boundary assertions also run for every independent sensitivity result. |
| Exact scalar/structure comparisons | 7 | Integer/float, boolean/integer, signed zero, empty-key addition/removal, list/object replacement, and list reordering retain their exact changed paths. |
| Import isolation | 1 | The imported module is the no-fuzz replayed file. |

Source inspection confirms that every public result is formed either by the shared pending helper or one of two explicit success dictionaries. All three fix `capacity` to `None` and `criterion_disposition` to `pending`. Successful factor outputs say `calculated_method_only`, successful comparisons say `calculated_method_sensitivity_only`, and their explanatory text excludes resistance or an adopted demand/capacity ratio. These checks establish the structured output boundary for the reviewed implementation; they cannot prevent a downstream consumer from mislabeling results.

Contract path declarations are treated as sets: order and duplicate declarations are normalized intentionally. Added or removed list objects are represented by a whole-item path, with their complete content independently bound by the payload digest. The review did not establish external manifest authority, validate the upstream engineering source or actual candidate loads, or independently qualify the NDS mechanics. The supplied published-table fixtures were executed as software tests only. Current structural criteria remain pending.

To reproduce without modifying the reviewed artifact, run these commands from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt10-test-review/audit_replay.py
PYTHONDONTWRITEBYTECODE=1 python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-group-action-method-attempt10-test-review/run_review_tests.py
```

The scripts create fresh temporary replay trees and replace generated receipts/transcripts in this report directory. A later rerun therefore needs a new report hash manifest. The reviewed application files and base remain untouched.
