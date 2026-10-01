# Attempt07 correctness review

Review date: 2026-09-28  
Candidate: `compact-floor-flush-wood-joints-development`  
Revision: `led-clearance-2x6-runner-seated-blocks-v1`  
Scope: verifier behavior, source pins, README identity, generated geometry evidence, and claim boundary.

## Result

No correctness findings identified.

The verifier rejects duplicate JSON keys, requires the exact source-pin field set, and compares canonical JSON with non-finite numbers disallowed. This catches type changes such as JSON `false` to numeric `0`. It reproduces the evidence from the source-bound graph, checks candidate/revision/scope and criterion disposition, binds the reviewed attempt06 packet and three reviews, reproduces the README, and verifies the packet checksums. The inherited source chain and fixed attempt06/review hashes validated during packet verification.

The README identifies attempt07 and the correct revision. Its counts match the generated evidence: 50 nodes, 1,225 pairs, 147 exact-BRep evaluations, and 1,078 AABB-only pairs. The four classifications sum to 1,225: 115 finite opposed planar, 26 exact-BRep separated, 1,078 AABB-only, and six zero-area/unresolved. All six unresolved pairs remain unresolved. The evidence leaves active contact, bearing/pressure, contact law, load-path ownership, force transfer, and criterion acceptance unestablished. The repository coverage entry for `overlap_contact` is also `pending`.

The packet and README keep the geometry-only boundary clear: connector/fastener interfaces are outside this 50-node inventory, and the evidence establishes no mechanical acceptance. No geometry or mechanics claim is transferred from the historical packet chain.

## Verification

- `.venv/bin/python -m pytest -q tests/test_wood_joint_wj08_overlap_contact_geometry_attempt07.py` — **20 passed**.
- `.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt07 --verify` — **PASS_GEOMETRY_ONLY_CRITERION_PENDING**.
- Packet `sha256sum -c SHA256SUMS` — all three listed files **OK**.

This review covers attempt07's verifier and evidence binding. It does not independently qualify the upstream geometry-generation method or establish physical contact, load transfer, or joint acceptance.
