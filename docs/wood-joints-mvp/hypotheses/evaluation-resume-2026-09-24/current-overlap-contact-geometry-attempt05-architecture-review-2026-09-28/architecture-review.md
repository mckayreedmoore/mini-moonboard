# Attempt05 overlap-contact geometry architecture review

Review date: 2026-09-28  
Subject: `scripts/wood_joint_wj08_overlap_contact_geometry_attempt05.py` and its frozen evidence packet  
Candidate/revision: `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`  
Criterion: `overlap_contact` remains `pending`  
Scope: read-only dependency-boundary and provenance review.

## Assessment

**No findings.** Attempt05 uses a narrow direct-predecessor surface: `attempt04.ATTEMPT_REL`, `verify_packet`, `validate_geometry_consistency`, and `build_geometry_evidence` (`scripts/wood_joint_wj08_overlap_contact_geometry_attempt05.py:14,96-127`). It does not reach through attempt04 into earlier implementation modules. It first runs the predecessor's packet verifier, then imports the predecessor's source-hash map; it separately fixes the attempt04 packet's four files and three review records, and adds its own producer and test hashes (`:39-65,96-114`). The predecessor verifier validates attempt04's packet and inherited source chain before that map is used. This avoids the transitive implementation coupling identified in the attempt04 review.

The packet binds the requested identity and scope. Attempt05 verifies the exact candidate, revision, and scope strings, reproduces evidence from the current graph and validated source chain using canonical JSON (including JSON value types), matches source and output hashes, binds the predecessor packet and reviews, regenerates the README, and requires an exact three-file checksum manifest (`:247-288`). The frozen source pins carry the requested candidate/revision and the scope `partial member/panel geometric pair inventory; no mechanics or acceptance`. The predecessor chain includes the candidate authority, criteria and coverage inputs, graph inputs, prior packets, and reviews.

The geometry-only boundary is preserved. The evidence and README identify a partial 50-node member/panel inventory, exclude connector and fastener solids, leave six pairs unresolved, disclaim mechanical inferences, and retain `criterion_disposition: pending`. The verifier returns `PASS_GEOMETRY_ONLY_CRITERION_PENDING`; it does not convert geometric classifications into contact, load transfer, or acceptance.

## Validation

- `.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt05 --verify` returned `PASS_GEOMETRY_ONLY_CRITERION_PENDING` with 50 nodes, 1,225 pairs, 147 exact-BRep evaluations, 1,078 AABB-only exclusions, and six unresolved pairs.
- The packet's `sha256sum -c SHA256SUMS` passed for `README.md`, `geometry-evidence.json`, and `source-pins.json`.
