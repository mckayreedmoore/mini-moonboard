# Attempt04 overlap-contact geometry architecture review

Review date: 2026-09-28  
Subject: `scripts/wood_joint_wj08_overlap_contact_geometry_attempt04.py`, its frozen packet, and its predecessor chain  
Candidate/revision: `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`  
Criterion: `overlap_contact` remains `pending`  
Scope: read-only architecture and provenance review.

## Assessment

Attempt04's packet verifier binds its candidate, revision, and geometry-only scope; reproduces the full evidence object from pinned inputs; fixes the four attempt03 packet files and three attempt03 review records; and asks attempt03 to verify its packet and inherited chain. Attempt03 in turn checks attempt02 and its review records and verifies the upstream T04 packet; attempt02 and attempt01 pin the candidate/criteria/coverage inputs and upstream geometry source. This provides a complete hash-checked predecessor chain for the current packet.

The frozen evidence remains a partial nominal-geometry inventory: 50 member/panel nodes, 1,225 pairs, 147 exact-BRep evaluations, 1,078 AABB-only exclusions, and six unresolved pairs. The evidence explicitly leaves active contact, bearing/pressure, load-path ownership, contact law, force transfer, and criterion acceptance false. Connector and fastener solids remain outside the inventory. Neither the packet nor verifier promotes the geometry observations into mechanics or acceptance.

Validation performed:

- `.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt04 --verify` returned `PASS_GEOMETRY_ONLY_CRITERION_PENDING` with the expected counts and tolerances.
- The attempt04 packet's `sha256sum -c SHA256SUMS` passed for all three packet files.
- Reviewed the attempt04 tests and predecessor verifiers/reviews. The attempt04 tests cover candidate, revision, and scope metadata tampering after refreshing packet checksums, plus evidence tampering after refreshing both recorded hashes.

## Finding

### F-01 — Attempt04 reaches through predecessor implementation layers

Severity: **Low; no current integrity failure.**

Although attempt04 imports attempt03 as its direct predecessor, it accesses the transitive `attempt03.attempt02.attempt01` module for the hash helper, candidate/revision constants, and graph path (`scripts/wood_joint_wj08_overlap_contact_geometry_attempt04.py:71,84-89,109,196-199,226-239,261`). It also calls attempt03's private `_current_source_hashes` helper (`:80`). This couples attempt04 to attempt02 and attempt01 implementation details, so an internal refactor of either layer can break the new adapter even if attempt03's intended interface stays stable. The pinned hashes make the current behavior reproducible, and the verifier passes, so this is a maintainability concern rather than a provenance defect.

For a future successor, expose a small supported attempt03 adapter interface for the candidate/revision identity, graph input path, source-hash collection, and checksum helper, then have the successor consume that interface without reaching through nested modules. Keep the existing predecessor hash checks and geometry-only boundary.

## Other checks

- **Pin validation:** `verify_packet` enforces schema and attempt ID, exact candidate/revision/scope values, regenerated evidence equality, source hashes, output hash, pending disposition, predecessor packet/review records, generated README, and an exact three-file checksum manifest (`:219-269`).
- **Candidate/revision binding:** attempt04 reads identity constants from attempt01, whose pinned-input check validates the candidate authority, criteria register, current coverage revision, and upstream graph revision. The generated evidence also reproduces candidate/revision fields from those constants.
- **Predecessor integrity:** attempt04 hash-checks the entire attempt03 packet and three attempt03 review records before calling attempt03 verification. Attempt03 verifies attempt02's frozen packet, review bindings, and T04 verifier/checksum inputs; attempt02 rechecks the upstream verifier chain.
- **Evidence boundary:** the README and JSON preserve the partial member/panel scope, unresolved pairs, omitted connector solids, and unbound mechanical facts. The disposition remains `pending` throughout.
