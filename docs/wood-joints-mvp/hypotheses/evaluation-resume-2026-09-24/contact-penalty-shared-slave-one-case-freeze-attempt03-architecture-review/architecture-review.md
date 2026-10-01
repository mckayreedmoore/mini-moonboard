# Attempt03 architecture and lifecycle review

**Assessment:** The freeze matches the assigned SHA-256, all 12 frozen-file hashes match, the packet remains one case (`shared_slave_penalty`), both readiness snapshots remain false, and no authorization record is stored in the candidate. The external authorization contract and verifier receipt flow make the intended transition legible and independently auditable. One medium-severity lifecycle gap remains in how the runner snapshots readiness records.

## Finding

**P2 — Readiness checks and authorization digests use separate file reads.** In `run.py:254–268`, `assert_execution_ready` parses each readiness file via `read_json`, then reopens the paths through `sha()` to obtain the hashes used in external authorization validation. `verify_freeze` checked the frozen hashes earlier (`run.py:191–217`), but the later parsed values and the later digest are not guaranteed to describe the same bytes. A concurrent replacement between reads can make the runner check false gates from one snapshot and bind authorization to another snapshot. This weakens the stated requirement that authorization name the exact frozen readiness snapshots. Read each readiness file once with the byte-snapshot helper, validate the parsed values, and require each digest to equal the corresponding digest in the verified freeze before checking authorization.

## Verification

- Assigned freeze SHA-256: `9361d737035158a1e1f88a5d8751d81445d050b857942bf56edeb7088a2c75f7` (matches).
- Frozen inventory: 12 of 12 file hashes match `input-freeze.json`.
- Readiness and parent-readiness gates: false; candidate authorization record: absent.
- This was a read-only review; no runner, Docker, solver, or native execution was invoked.
