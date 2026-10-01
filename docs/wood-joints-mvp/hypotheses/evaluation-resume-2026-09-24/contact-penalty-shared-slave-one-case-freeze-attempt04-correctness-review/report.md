# Attempt04 correctness review

Reviewed candidate freeze: `a31a12fa033e0f0ce31ec023c2b04c544d197c7c8f06f1c542b8a9be6b2f0816`.

## Integrity and scope

The `input-freeze.json` SHA-256 matches the reviewed digest. All 12 entries in
its `files_sha256` map match the current candidate files. The terminal manifest
also matches the freeze and validation digests; `validation.json` records
7/7 offline tests passing. Candidate readiness and parent-readiness remain
false. No execution record, output directory, or persisted authorization
receipt exists. This review did not invoke `run()`, tests, Docker, a solver, or
native execution.

## Findings

No blocking authorization or root/case-binding bypass found in the requested
data flow. `read_json_snapshot()` parses and hashes one byte read, rejecting
duplicate keys and non-finite numbers (`authorization_contract.py:45-74`).
`run()` verifies the supplied freeze first, compares both parsed readiness
snapshot digests to its frozen entries, checks their false gates, and validates
the external authorization before its first Docker subprocess call
(`run.py:191-222, 243-274, 327-346`). The authorization loader carries the
parsed bytes and digest together; receipt creation verifies that digest and
uses exclusive creation (`run.py:277-298`). The verifier hashes and parses the
same receipt bytes, binds its digest and semantic authorization to both the
root and case execution records, and later requires the case execution file to
equal the root's case record (`verifier.py:1110-1159, 1044-1047`).

Low-severity manifest consistency note: `audit_root()` validates the frozen
case list, root `case_order`, and the single `runs` entry, but does not compare
the redundant root `execution["cases"]` field with `[shared_slave_penalty]`
(`verifier.py:1222-1237`). A contradictory top-level `cases` value could
therefore accompany a coupon pass. The canonical `runs` and authorization
bindings still constrain the audited case, so this does not provide a route to
execute or accept a second case.

Residual concurrency limitation: the runner hashes `output/coupon.inp`, then
later launches Docker with the output directory mounted writable
(`run.py:348-373`). A concurrent process with write access could replace the
deck after that hash and before solver startup. The verifier would detect the
changed deck only after execution (`verifier.py:1091-1094`). This is not a
deterministic bypass in the stated parent-owned serialized-run workflow, but
that workflow relies on exclusive workspace ownership through launch.

The reviewer name remains an external parent-channel trust assumption. The
packet does not claim a cryptographic signature, consistent with its README.

## Evidence

- Frozen inventory: 12/12 current file hashes match `input-freeze.json`.
- `input-freeze.json` SHA-256: `a31a12fa033e0f0ce31ec023c2b04c544d197c7c8f06f1c542b8a9be6b2f0816`.
- `validation.json` SHA-256: `d677b2702e68610ff5364d423081f0bf93099436889973ac6c4caeead0760144`.
- `terminal-hashes.json` SHA-256: `6426fe6d52e1148bec3a269b77cfcfad4e12f5755b05c58e9b6c7b1643a35932`.
- The offline-suite result is taken from the frozen validation record; this review did not rerun it.

See `integrity-manifest.json` for this report's SHA-256.
