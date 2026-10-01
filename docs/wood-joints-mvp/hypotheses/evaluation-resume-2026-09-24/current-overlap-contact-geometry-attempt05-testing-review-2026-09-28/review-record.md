# Attempt05 testing review

Candidate: `compact-floor-flush-wood-joints-development`  
Revision: `led-clearance-2x6-runner-seated-blocks-v1`  
Review date: 2026-09-28

The focused test file passes: `17 passed` with
`.venv/bin/python -m pytest tests/test_wood_joint_wj08_overlap_contact_geometry_attempt05.py -q`.
The tests cover the inherited tolerance rejection cases, candidate/revision/scope
metadata, evidence value tampering, boolean-versus-number equality, the CLI
freeze/verify cycle, and a successful checksum cycle. The producer calls
attempt04's public verifier before importing its source hashes, binds the
predecessor packet and reviews, and keeps both generated evidence and verifier
results pending.

## Findings

### F-01 — Low: duplicate JSON keys pass frozen-evidence verification

`_load_json` uses the default `json.loads` behavior, which silently keeps the
last value for duplicate object keys. `_canonical_json` then compares only the
resulting Python objects ([producer, lines 76–77 and 136–143](../../../../../scripts/wood_joint_wj08_overlap_contact_geometry_attempt05.py)).
I copied the frozen packet to a temporary directory, inserted a second
`criterion_disposition` key with value `"accepted"` before the existing
`"pending"` key, refreshed `source-pins.json`'s `output_sha256` and the packet
checksums, and called `verify_packet`. It returned
`PASS_GEOMETRY_ONLY_CRITERION_PENDING` and accepted the ambiguous evidence.
Consumers that reject duplicate names or select the first value can interpret
the same file differently, including reading an accepted disposition.

Reject duplicate object names while parsing both `geometry-evidence.json` and
`source-pins.json` (for example, with an `object_pairs_hook` that raises), and
add a regression test that inserts a duplicate disposition key and refreshes
the outer hashes before verifying. The existing boolean/number regression
does not cover this JSON ambiguity.

## Verification

The test command above passed. The duplicate-key reproduction was performed
against a temporary copy of the packet; repository source, tests, frozen
packet, queue, status, and goal files were not changed by this review.
