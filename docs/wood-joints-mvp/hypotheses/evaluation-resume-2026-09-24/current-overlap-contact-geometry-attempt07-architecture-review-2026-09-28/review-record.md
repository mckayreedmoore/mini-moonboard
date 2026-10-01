# Attempt07 architecture review

Review date: 2026-09-28  
Candidate: `compact-floor-flush-wood-joints-development`  
Revision: `led-clearance-2x6-runner-seated-blocks-v1`  
Scope: attempt07 producer, tests, and frozen geometry evidence packet; architecture, lineage, interfaces, reproducibility, and separation of geometry from mechanics.

## Assessment

Attempt07 has a focused role: it wraps attempt06's geometry consistency and evidence-building interfaces, adds stricter JSON handling and exact evidence comparison, and binds the result to the attempt06 packet and review records. The frozen packet preserves the intended candidate and revision, labels the inventory as partial, keeps `overlap_contact` pending, and states that mechanics and acceptance are not established. I found no material architecture, interface, lineage, reproducibility, or claim-boundary defect in the reviewed scope.

The implementation keeps geometry inventory separate from mechanics. The evidence reports member/panel pair classifications and explicitly leaves face owners, active contact, contact law, load-path ownership, force transfer, and acceptance unestablished. It identifies the six unresolved pairs, the 1,078 AABB-only pairs, and excluded connector/fastener solids, and states the follow-up needed before mechanics evidence could be considered.

## Lineage and interfaces

- Attempt07 delegates `validate_geometry_consistency` and `build_geometry_evidence` to attempt06, then changes only the evidence schema. Packet generation and verification use the attempt06 public verifier and its validated source-hash chain.
- The pinned source set contains 62 inputs. It inherits attempt06's 53-entry source map and adds exact hashes for the attempt06 packet, its correctness/testing/architecture reviews, and the attempt07 producer and tests.
- The packet also records the exact predecessor packet hashes and review hashes. Candidate, revision, scope, criterion disposition, source hashes, generated evidence, README, and packet checksums are checked during verification.
- The attempt07 module provides a stable command-line interface for `--freeze` and `--verify`, with optional `--output-dir`. The tests exercise those commands and the documented checksum cycle, as well as identity/scope, tampering, duplicate JSON keys, unrecognized fields, numeric-versus-boolean equality, and geometry thresholds.

## Reproduction checks

- `.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt07 --verify` passed with `PASS_GEOMETRY_ONLY_CRITERION_PENDING` and the frozen counts: 50 nodes, 1,225 pairs, 147 exact-BRep evaluations, and 1,078 AABB-only pairs.
- `sha256sum -c SHA256SUMS` passed for all three frozen packet files.
- Tests were not run as part of this architecture review.

## Findings

None.
