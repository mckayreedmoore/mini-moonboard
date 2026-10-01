# T04 face-pair atlas attempt01 — parent validation

Date: 2026-09-28  
Candidate: `compact-floor-flush-wood-joints-development`  
Revision: `led-clearance-2x6-runner-seated-blocks-v1`  
Disposition: **parent validation pass for source-bound nominal face geometry only; `overlap_contact` remains pending.**

## Parent reproduction

From the repository root, the coordinator ran:

- `.venv/bin/python -m scripts.wood_joint_current_face_pair_atlas_attempt01 --verify` — `PASS_FACE_GEOMETRY_ONLY_CRITERION_PENDING`; 217 source hashes, 50 exact STEP bodies, 378 planar faces, 115 finite opposed body pairs, 117 face-pair mappings, six unresolved pairs unmapped.
- `.venv/bin/python -m pytest -q tests/test_wood_joint_current_face_pair_atlas_attempt01.py` — 9 passed.
- `.venv/bin/ruff check scripts/wood_joint_current_face_pair_atlas_attempt01.py tests/test_wood_joint_current_face_pair_atlas_attempt01.py` — all checks passed.
- Packet `sha256sum -c SHA256SUMS` — all three entries passed.
- The correctness reviewer's independent CadQuery/OCP reconstruction script was rerun by the coordinator. It verified 50 bodies and 378 planar face identities, reconstructed 115/115 finite graph rows as 117 opposed face pairs and 117 Boolean regions, and left all six unresolved pairs unmapped. Maximum absolute opposed/shared area difference was `8.28367774374783e-7 mm²`, below the `1e-6 mm²` absolute tolerance floor. All 217 pinned source hashes were rechecked.

The six zero-area/unresolved pairs remain unresolved; 26 exact-BRep separated pairs and 1,078 AABB-only pairs remain outside the face mapping. The face ordinals and signatures apply to the pinned STEP bytes and CadQuery/OCP importer; they are not portable CAD names.

## Independent reviews

- Correctness: no substantive finding. The review independently reconstructed face signatures, normals, intersections, regions, and areas and exercised source/revision/tamper checks. Review SHA-256: `ce45c6a6e44ff24c0ec48a1a1d8bdd9e22c911e808498b7e0b96764a12a80da6`; reconstruction script: `9dfa5c9a657b81ce65f086489f158d472dbe440886019e70c7ad35dd04084359`.
- Testing: no findings. Nine focused tests, the verifier and packet hashes passed; temporary probes rejected stale identity, altered source, duplicate IDs/keys, area mismatches, and promotion of unresolved/AABB-only pairs. Review SHA-256: `9271b56c61e6749af08ae9365e865bac49ab33cec8d3469e41e50950137db930`.
- Architecture: no provenance, reproducibility, or mechanics-boundary defect. One low, non-blocking wording note says the README calls 117 face-pair mappings “intersection regions.” Those counts agree in this snapshot because each face pair has one region; a future multi-region face pair should use a distinct region count or clearer wording. Review SHA-256: `c5a202d21b6ec4eb98f41c718069c4ce9d129506d06fe1bdb5f60a0c7a24895a`.

All review packet checksums passed. The reviews do not qualify the STEP geometry against physical parts or validate a mechanical model.

## Limits and next step

This evidence adds exact source-face identities and nominal Boolean intersection regions. It does not identify physical/contact ownership, a contact law, active bearing, load-path edges, force transfer, stiffness, fastener engagement, resistance, response, equivalence, capacity, or criterion acceptance. All mechanics/readiness/release flags remain false and all 47 criteria remain pending.

Use these geometry identities as inputs for a separately source-bound interface-ownership and behavior map. Mechanical closure still depends on a response-validated T03 ordinary joint and current T09 solver maps. Do not alter reviewed geometry on the basis of this atlas.
