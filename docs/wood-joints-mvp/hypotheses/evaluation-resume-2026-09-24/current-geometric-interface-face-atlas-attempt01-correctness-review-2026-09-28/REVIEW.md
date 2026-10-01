# Face-pair atlas attempt01 correctness review

Review date: 2026-09-28  
Candidate: `compact-floor-flush-wood-joints-development`  
Revision: `led-clearance-2x6-runner-seated-blocks-v1`  
Verdict: **no substantive correctness finding for the requested geometry-only scope**.

## Review target and provenance

The target is `current-geometric-interface-face-atlas-attempt01-2026-09-28`, produced by `scripts/wood_joint_current_face_pair_atlas_attempt01.py` and covered by `tests/test_wood_joint_current_face_pair_atlas_attempt01.py`. The atlas source pins bind 217 current inputs, including every STEP body, the exact importer/toolchain, the reviewed attempt02 map and its independent review, the attempt07 geometry-only packet and its reviews, and the attempt04 full-frame input/member-solids manifests.

The reviewed predecessor identities are:

- Attempt02 map: graph `7806242ac48b198becf5db97b16b6a5605021b8d86b964f0f02adb6806aeec26`, pins `590112932d73dc57da015382a8ebf6e0fc85a8c5e8338549f381b8bd7732ba5c`, verifier `f839cfe233155bcd5ab56fea943cc2a13d211053d4876e98f4cb48dfdb3c3e43`, and prior independent review `2c0d3bc43ce3c48e923317fc426d93c2dae12e60abc211ef62d65582073254da`.
- Attempt07 geometry inventory: evidence `24282db614089fcff73d11fcfd1216aaaff5e2d7babc1af2fa971390c29a7448`, pins `c187f27a838a56407411a53a7a9b54285b651f414e3827697a2bbf6c40a71500`, and public producer `5b34c94bb1bf072b4128d694425129b651a144c44099b90f2bc7da2e312f2c57`.
- Current member-solids descriptor: `8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420`.

The exact target inputs reviewed are recorded in `verification-results.json`; target producer, test, atlas, README, and source-pin hashes are also included there. No target producer, target test, geometry, predecessor packet, or coordinator record was edited.

## Independent geometry reconstruction

I ran `independent_reconstruction.py`, which imports the 50 pinned STEP files with the specified CadQuery 2.8.0 / OCP 7.9.3.1.1 runtime and independently recomputes face descriptors, face-pair intersections, region geometry, normals, and area totals without calling the target producer's geometry helper functions. The full target `--verify` was also run, which exercises the pinned attempt02 and attempt07 public verifiers before rebuilding and comparing the complete atlas.

The independent reconstruction confirmed:

- All 50 STEP hashes and imported valid single-solid bodies join to the reviewed 50-body manifest. All 378 planar source faces match the atlas by one-based STEP face ordinal, geometry signature, and signature digest.
- All 115 finite opposed rows from the attempt02 graph independently reconstruct to the same 117 opposed source-face pairs. Each pair yields one planar Boolean region, for 117 regions total; 113 body pairs have one mapped face pair, and two body pairs have two.
- The maximum absolute per-body-pair discrepancy against either frozen graph area is `8.28367774374783e-7 mm²`. This is below the `1e-6 mm²` absolute floor in `max(1e-6 mm², expected_area × 1e-10)` for every row. The producer's region-level nine-decimal rounding was included in this comparison.
- Every retained source-face normal dot is `-1.0` at the recorded precision; the largest coplanar offset is `2.31e-7 mm`, below the `1e-5 mm` geometry tolerance. All 117 retained Boolean regions are planar and exceed the `1e-6 mm²` minimum-area threshold.
- The six exact-BRep zero-area/unresolved rows match attempt02 and attempt07 and remain unmapped. The 26 exact-BRep separated rows and 1,078 AABB-only rows are not promoted into the face map.

## Verification and tamper boundaries

- `.venv/bin/python -m scripts.wood_joint_current_face_pair_atlas_attempt01 --verify` — `PASS_FACE_GEOMETRY_ONLY_CRITERION_PENDING`; 217 sources, 50 STEP bodies, 378 planar faces, 115 finite body pairs, 117 face pairs, and six unmapped unresolved pairs.
- `.venv/bin/pytest -q tests/test_wood_joint_current_face_pair_atlas_attempt01.py` — 9 passed.
- Attempt02 `verify_packet.py --verify` — `PASS`; 142 source pins, 50 STEP files, and six unresolved pairs. Its packet checksums passed.
- Attempt07 `--verify` — `PASS_GEOMETRY_ONLY_CRITERION_PENDING`; its three packet checksum entries passed.
- Target packet `sha256sum -c SHA256SUMS` — all three entries passed.
- Isolated temporary copies of the target packet rejected five tampering cases: wrong candidate pin, stale revision pin, changed atlas output, duplicate JSON key, and altered source-pin digest. The existing source-hash mismatch unit test also passed. No workspace input was modified for these checks.

The verifier's boundaries are adequate for this packet: it requires exact source-pin fields, rejects duplicate object keys, rehashes the 217-input closure, compares the regenerated atlas and rendered README, verifies output and packet checksums, and enforces candidate/revision/scope/pending disposition. The atlas is scoped to the exact pinned STEP bytes and importer; a face ordinal is not a native CAD face name or portable identity across re-export.

## Findings and limits

No material correctness finding was identified in the requested face mapping, region geometry, area aggregation, tolerance application, opposed-normal filtering, unresolved-pair handling, or candidate/revision/hash/tamper boundaries.

This review confirms nominal geometry identity only. It does not independently qualify the STEP source against physical parts or independently validate the CAD kernel implementation. The 1,078 AABB-only pairs remain unevaluated by exact BRep, and the six unresolved pairs remain unresolved. A planar Boolean intersection does not establish active bearing, contact ownership/law, load transfer, stiffness, resistance, response, capacity, any of the 47 criterion dispositions, readiness, fabrication release, or climbing release. `overlap_contact` remains pending.
