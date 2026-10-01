# Attempt05 overlap-contact geometry correctness review

Review date: 2026-09-28  
Subject: `scripts/wood_joint_wj08_overlap_contact_geometry_attempt05.py`, `tests/test_wood_joint_wj08_overlap_contact_geometry_attempt05.py`, and the frozen `current-overlap-contact-geometry-evidence-attempt05` packet  
Candidate/revision: `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`  
Verdict: **two low-severity packet-verifier findings; no current geometry-classification discrepancy or mechanics/acceptance claim promotion found.**

## Scope and claim boundary

Attempt05 reuses attempt04's geometry validation and evidence construction, and adds canonical-JSON comparison to distinguish JSON booleans from numbers. Its source chain validates the frozen attempt04 packet and reviews before carrying forward source hashes. The frozen attempt05 packet reports 50 member/panel nodes and 1,225 unordered pairs, with 147 exact-BRep evaluations, 1,078 AABB-only exclusions, 26 exact-BRep separated pairs, 115 finite opposed planar geometries, and six zero-area/unresolved pairs. The pinned graph and receiver producer hashes are recorded in the source-hash chain. The evidence and README keep `overlap_contact` pending and explicitly do not establish contact law, active contact, load-path ownership, bearing/pressure, force transfer, capacity, response, or acceptance.

Attempt05's inherited validator checks graph revision/schema, per-class measurement consistency and thresholds, and fixed class counts (`scripts/wood_joint_wj08_overlap_contact_geometry_attempt03.py:105-217`; called by attempt04 and attempt05). The frozen README describes the AABB exclusions and the evidence limits consistently. No contradiction in the frozen geometry classifications or scope wording was found.

This was a static review of the requested implementation, tests, packet, predecessor interfaces, pinned graph/source records, and predecessor correctness review. No tests or native solves were run, and no source, test, packet, queue, status, or goal files were changed. Findings below concern tampered packet behavior with packet-local hashes refreshed; they do not indicate that the checked-in frozen packet currently contains those mutations.

## Findings

### F-01 — Duplicate JSON object names are collapsed before strict comparison

Severity: **low; verifier fidelity and cross-parser ambiguity. The frozen packet is unaffected, and this does not establish or promote any mechanical claim.**

`_load_json` calls the standard `json.loads` without duplicate-name detection (`scripts/wood_joint_wj08_overlap_contact_geometry_attempt05.py:76-77`). `verify_packet` then compares canonical encodings of the decoded evidence and regenerated evidence (`:260-263`). Canonicalization distinguishes booleans and numbers, but it cannot recover object members discarded by `json.loads`: a duplicate key resolves to its last value in Python. A tampered `geometry-evidence.json` can therefore include an earlier conflicting value, such as `"criterion_disposition":"accepted"` before the expected `"criterion_disposition":"pending"`, while Python decodes the final value and the canonical comparison succeeds. Refreshing `source-pins.json`'s `output_sha256` and the packet `SHA256SUMS` rows is sufficient to get past the packet-local hash checks. A first-wins consumer can read the conflicting value instead. The existing strict-type regression covers `false` versus `0`, but not duplicate names (`tests/test_wood_joint_wj08_overlap_contact_geometry_attempt05.py:159-175`).

Reject duplicate object member names while parsing each packet JSON file, for example with an `object_pairs_hook` that errors on a repeated key. Add a regression that inserts a conflicting duplicate in a verification-relevant field, refreshes packet-local hashes, and requires rejection.

### F-02 — The source-pins record accepts unrecognized top-level claims

Severity: **low; packet metadata can carry unverified assertions. The verifier's returned disposition remains pending, and this does not alter the frozen evidence.**

`verify_packet` checks selected source-pins properties with `.get(...)` (`scripts/wood_joint_wj08_overlap_contact_geometry_attempt05.py:252-273`) but does not require the exact generated key set or compare the complete pins object with an expected record. The packet-local checksum is recomputed from the file itself (`:278-288`), so adding an unknown field and refreshing that checksum does not make the field independently bound. For example, an added `"acceptance":"accepted"` field can coexist with the checked `"criterion_disposition":"pending"` and the verifier has no rejection path for it. The metadata mutation test covers changed known fields only (`tests/test_wood_joint_wj08_overlap_contact_geometry_attempt05.py:119-140`).

Enforce an exact source-pins schema/key set (or compare the parsed object with the complete pins record regenerated from current inputs) and add a test that adds an unknown assertion field, refreshes packet-local checksums, and expects verification to reject it.

## Validation notes

The report is a static source and artifact review; no test execution is claimed. The observed findings are confined to fail-closed packet parsing and metadata-shape behavior. The frozen attempt05 evidence remains partial geometry evidence for the named candidate revision, with `overlap_contact` pending.
