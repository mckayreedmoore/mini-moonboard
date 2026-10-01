# Attempt04 independent test/schema review

Reviewed candidate: `contact-penalty-shared-slave-one-case-freeze-attempt04`  
Input-freeze SHA-256: `a31a12fa033e0f0ce31ec023c2b04c544d197c7c8f06f1c542b8a9be6b2f0816`  
Review scope: authorization gating, external authorization at the pure execution gate, byte-bound readiness and receipt handling, schema/runtime parity, verifier receipt checks, source pins, and resource limits. No candidate files were modified. No Docker, solver, native process, or runner execution was invoked.

The offline suite passed: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` — 7 tests run, 7 passed. All 12 frozen artifact hashes in `input-freeze.json` matched their files; see `integrity.json`.

The requested gate and evidence checks are present. `run.py` checks a false candidate gate before Docker/process calls (`run.py:327-346`), and the suite patches `subprocess.run` and `Popen` to assert no calls (`tests/test_candidate.py:152-161`). A valid external record passes `assert_execution_ready()` on a temporary copy with process calls patched (`tests/test_candidate.py:179-213`). That gate reads and hashes each readiness file from the same byte snapshot, checks both digests against the verified freeze, and still requires the candidate snapshots to be false (`run.py:243-275`). Tests mutate each snapshot and check rejection. External authorization parsing rejects duplicate JSON keys and carries the parsed bytes through receipt creation (`authorization_contract.py:45-74`, `run.py:277-298`); the receipt is exclusive and byte-equal to the authorization input (`tests/test_candidate.py:215-228`).

Schema/runtime fixtures use the pinned `jsonschema==4.10.3`, verify the Draft 2020-12 schema, and exercise accepted and rejected records (`tests/test_candidate.py:230-295`). Static input/oracle/source pins and false gates are checked (`run.py:90-150`); `verify_freeze()` enforces the exact frozen artifact inventory, source pins, solver identity, and complete limits map (`run.py:191-222`). The runner applies one-case, one-run, process, time, output, CPU, memory, and PID constraints (`run.py:38-50`, `327-400`); verifier receipt checks bind both execution records to the freeze, readiness hashes, case, source pins, false acceptance claims, and exact receipt digest before coupon pass (`verifier.py:1110-1257`). The synthetic verifier test stubs only the per-case mechanics audit, as the packet documents; it does not establish solver output (`tests/test_candidate.py:297-351`).

## Finding

**Low — freeze hash/parse use separate reads.** `run.py:191-196` computes `sha(freeze_path)` and then separately calls `read_json(freeze_path)`. `verifier.py:1166-1189` similarly parses the freeze and later hashes the path. A concurrent replacement between reads can make the parsed freeze differ from the bytes whose digest is bound by the external authorization. This is a local concurrency condition; under stable packet files, the checks pass. Use `read_json_snapshot()` once for the freeze and carry that parsed object and digest through validation/audit. Readiness and external authorization already follow that same-byte pattern.

No other test/schema finding was identified in the requested scope. Reviewer identity remains an external parent-channel trust boundary, not a cryptographic signature claim.
