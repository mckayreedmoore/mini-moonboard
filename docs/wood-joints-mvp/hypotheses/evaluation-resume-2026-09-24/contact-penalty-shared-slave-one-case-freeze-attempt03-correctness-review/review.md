# Attempt03 correctness review

Reviewed freeze `9361d737035158a1e1f88a5d8751d81445d050b857942bf56edeb7088a2c75f7` read-only. No runner, Docker, solver, or native execution was invoked.

## Finding

- **Low — bind readiness hashes to the freeze at the execution gate.** In `run.py`, `run()` validates and hashes the frozen files through `verify_freeze()` at lines 323 and 191–217, then calls `assert_execution_ready()` at line 330. That function separately parses `readiness.json` and `parent-readiness.json` at lines 254–255 and hashes them in later reads at lines 256–257. It checks the false booleans from the parsed values but does not compare those later hashes with `frozen["files_sha256"]`. If the files change in this interval and the caller supplies a record for the changed digests, the runner can reach Docker before its final frozen-input check at lines 470–480 detects the change. A correctly bound record for the reviewed snapshots would not match that mutation; this is a narrow filesystem race, not a static bypass under an unchanged packet. Use the same-byte `read_json_snapshot()` helper and require its digests to equal the already-verified freeze entries before any Docker call.

## Authorization-chain assessment

No other static authorization bypass was found. Runner and verifier share exact-field, true/false gate, scope, path, source-pin, digest-format, and UTC timestamp checks. Strict JSON parsing rejects duplicate keys recursively and non-finite values. The runner hashes and parses one external authorization byte snapshot and writes those exact bytes exclusively as the receipt. The root verifier checks the receipt digest against both root and case records, binds both to the freeze/readiness/source/case values, and does so before it can return the coupon pass. The case execution file must equal the root's case record.

Reviewer identity remains an external parent-channel trust assumption, as documented; the packet does not claim a signature. I did not test solver behavior or run the offline suite.

## Integrity

The input-freeze digest matched the requested SHA-256. All 12 frozen file digests matched `input-freeze.json`. No execution record, output directory, or authorization record was present in the candidate at review time. See `integrity-manifest.json` for the verified digest inventory and report hash.
