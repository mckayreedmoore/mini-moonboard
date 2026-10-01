# Attempt03 test and schema/runtime review

Reviewed `contact-penalty-shared-slave-one-case-freeze-attempt03` at input-freeze SHA-256 `9361d737035158a1e1f88a5d8751d81445d050b857942bf56edeb7088a2c75f7`.

The offline suite passed: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v` ran 6 tests with 0 failures. The freeze digest matches the requested value, and all 12 files listed in `input-freeze.json` match their recorded hashes. No execution record or output directory was created.

The tested fail-closed runner path keeps readiness false and raises before either patched `subprocess.run` or `subprocess.Popen` can execute. The schema and shared runtime validator agree on the tested authorization fields, true/false gate values, source pins, case scope, and UTC timestamp fixtures. Context hash mismatches remain schema-shaped SHA-256 values but fail the runtime's exact freeze/readiness binding. The strict parser rejects duplicate object keys, and the file loader returns the parsed authorization, digest, and original bytes from one read. Receipt tests verify byte-exact exclusive persistence; root-verifier fixtures reject missing receipts and mismatched digest, freeze, readiness, parent-readiness, source, oracle, case, and gate evidence before coupon PASS. These verifier tests stub only `audit_case`, so they do not establish solver output or mechanics.

I separately called `run.assert_execution_ready()` with authorization bound to the exact on-disk freeze and readiness snapshots while patching both subprocess entry points to fail if called. It accepted the authorization without a process or Docker call. The one-case deck/oracle pins, case order, false candidate gates, solver identity, and resource limits are bound by the freeze and exercised through the static-pin and freeze-verification paths.

Finding:

- **Low — positive readiness-gate regression coverage is indirect.** The suite's positive authorization fixture calls `run.check_external_authorization()` directly (`tests/test_candidate.py:210-218`), while the runner's actual pure gate that reads the false candidate snapshots and binds their current digests is `run.assert_execution_ready()` (`run.py:243-268`). The implementation passed a separate no-process check during this review, and `run.run()` calls `verify_freeze()` before that gate, so this is a test coverage gap rather than an observed behavior defect. A focused test of `assert_execution_ready()` with a valid authorization and patched process entry points would lock the intended end-to-end authorization boundary.

No blocking schema/runtime or receipt-verifier defect was found within this review scope. No Docker, solver, or native execution command was run.
