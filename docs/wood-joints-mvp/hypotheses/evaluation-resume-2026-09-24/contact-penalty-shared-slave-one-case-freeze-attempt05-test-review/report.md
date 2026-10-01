# Attempt05 independent test coverage review

Reviewed candidate: `contact-penalty-shared-slave-one-case-freeze-attempt05`  
Input-freeze SHA-256: `115c66e25969258c8cdd183e6c0c034a4ca872c392da7d0943a2287a3d3d83e0`  
Review scope: exact frozen inputs, the 10 offline tests, same-byte freeze snapshots, runner authorization gates, schema/runtime parity, and root/case receipt bindings. No candidate files were modified. No Docker, solver, native process, or candidate CLI runner command was invoked.

All 12 artifact hashes listed in `input-freeze.json` matched the corresponding files. The freeze digest matches both `validation.json` and `terminal-hashes.json`; the terminal manifest's validation digest also matches the current validation file. The candidate remains `FROZEN_PENDING_PARENT_REVIEW`, with false candidate readiness and authorization, no execution record, and no output directory.

The offline suite passed: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` — 10 tests run, 10 passed. The false-readiness test enters only the fail-closed in-process runner path with `subprocess.run` and `Popen` patched to raise; it confirms that readiness blocks before either entry point or output creation.

The requested coverage is present for both same-byte freeze paths. The runner test replaces the temporary copy of the freeze immediately after its first read and confirms that verification returns the parsed record from the bytes whose digest was checked (`tests/test_candidate.py:154-186)). The verifier test requires its root audit to use `read_json_snapshot()` once and prevents a separate freeze hash read (`tests/test_candidate.py:389-413)). The positive pure execution-gate test accepts an authorization bound to the frozen readiness bytes while process entry points are forbidden, and rejects modified readiness snapshots (`tests/test_candidate.py:215-249)).

Authorization parsing and schema/runtime parity are covered with the pinned `jsonschema==4.10.3`, duplicate-key rejection, true/false gate fixtures, exact dynamic hash binding, source and case pins, extra fields, and UTC timestamp cases (`tests/test_candidate.py:199-213,266-331`). Receipt fixtures cover absent receipts, receipt digest mismatch, freeze/readiness/source/oracle/case mismatches, and false gates. The verifier's synthetic root fixture stubs only the per-case mechanics audit, so these checks establish the evidence gate and do not establish solver output or mechanics.

## Finding

**Low — root/case authorization-record checks lack asymmetric regression fixtures.** The verifier checks freeze, case, readiness, gate, source, and receipt bindings on both the root and case execution records (`verifier.py:1111-1159`). However, the test fixture creates both records with identical valid authorization metadata; current negative cases change the root's top-level `cases` list or make the receipt itself invalid (`tests/test_candidate.py:333-427`). They do not independently corrupt one binding in only the root record or only the case record, so removal of one side of the verifier's loop could escape the existing suite.

I ran a pure verifier probe against temporary synthetic records, with per-case mechanics audit stubbed. Independent changes to the root receipt digest, case receipt digest, and case readiness digest were each rejected by `audit_root()`. This confirms the current implementation guards those paths; it does not close the regression-test gap. Add asymmetric root-only and case-only binding mutations to lock that behavior.

No blocking authorization-gate or schema/runtime defect was found in the requested scope. The candidate remains unauthorized, and this review does not approve native execution, mechanics, or release.
