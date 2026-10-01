# T04 face-pair atlas attempt01 architecture review

Review date: 2026-09-28  
Candidate/revision: `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`  
Scope: read-only architecture review of the attempt01 producer, focused tests, frozen packet, and exact predecessor bindings. Reviewed module boundaries, reproducibility, source/hash closure, data semantics, maintainability, and the geometry/mechanics boundary.

## Assessment

The attempt01 packet is a narrowly scoped geometry post-processor. It maps the 115 finite opposed body-pair rows from the independently checked T04 attempt02 graph to source planar face identities from the 50 exact member/panel STEP bodies. The frozen result contains 117 face-pair mappings and 117 Boolean intersection regions; it preserves six zero-area/unresolved pairs, leaves 26 exact-BRep separated pairs unmapped, and does not recast the 1,078 AABB-only exclusions as exact results.

I found no current provenance, reproducibility, or claim-boundary defect. The implementation keeps geometry separate from mechanics: source face identity is tied to an imported face ordinal and a geometry signature; the atlas and README say that this is not a contact owner, contact law, active-bearing state, load-path edge, or acceptance result. The packet keeps `overlap_contact` pending and all mechanics/readiness/release flags false. It establishes nominal geometry only.

## Architecture, lineage, and reproducibility

- The producer combines source validation, STEP import, face-signature creation, pair intersection, evidence assembly, and packet freeze/verify in one attempt-specific module. This is a fairly large module, but its stages are separated into named functions and the single-command verifier rebuilds the same expected object, so the scope remains understandable and the packet is straightforward to reproduce. `_shape` handles stay in memory and are excluded from serialized face records.
- The producer calls the attempt02 map's pinned public `verify_packet.py` and its own exact verifier for attempt07. The attempt02 binding records the map graph, source pins, public verifier, and independent review record hashes. The attempt07 evidence/source-pin pair is also bound, and attempt07's verifier authenticates its inherited geometry-only chain before the atlas consumes its classifications. The current member-solids manifest is bound by hash and revision, then its 50 STEP descriptors are joined to the graph's exact 50 member identities.
- The atlas source closure has 217 files. It includes the 50 STEP bodies through the inherited source inventories, the relevant predecessor packet and verification inputs, this producer, and its tests. `verify_packet` rebuilds the source hash map and predecessor bindings, compares the complete canonical atlas, verifies the output hash, regenerates the README, and checks an exact three-file packet checksum list. The README's SHA256 command also passed.
- Output ordering is explicit for face edges, vertices, face pairs, interfaces, unresolved pairs, body identities, and JSON keys. Numeric signatures and geometry values are finite-checked and rounded to nine decimals. The verifier pins Python 3.12.3, CadQuery 2.8.0, cadquery-ocp 7.9.3.1.1, and OCP 7.9.3.1, and it reimports all 50 bodies and reruns the geometry operations before accepting the frozen output. Face ordinals are explicitly limited to these pinned STEP bytes and importer/toolchain; they are not claimed as persistent CAD-native identifiers.
- The source-face identity signature records surface type, area, center, oriented normal, bounds, vertices, edge signatures, and wire count. Pair selection applies AABB, parallel-normal, coplanarity, opposed-normal, and finite-area checks, then reconciles each body-pair area with both frozen attempt02 area fields. This provides a useful exact-geometry cross-check while keeping those measurements distinct from contact mechanics.
- The boundary is explicit in the JSON, README, and producer docstrings: intersection and normal results do not establish bearing, pressure, gap law, active contact, load-path ownership, force transfer, stiffness, fastener engagement, resistance, response, capacity, criterion acceptance, or release. Connector/fastener solids are excluded, and the 1,078 AABB-only pairs and six unresolved pairs remain identified as open geometry scope.

## Verification performed

- `.venv/bin/python -m scripts.wood_joint_current_face_pair_atlas_attempt01 --verify` returned `PASS_FACE_GEOMETRY_ONLY_CRITERION_PENDING`, with 50 bodies, 378 planar source faces, 115 finite opposed body pairs, 117 source-face pair mappings, six unresolved pairs, and 217 pinned source files.
- `.venv/bin/pytest -q tests/test_wood_joint_current_face_pair_atlas_attempt01.py` passed: 9 tests.
- `sha256sum -c SHA256SUMS` in the frozen attempt01 packet passed for README, atlas JSON, and source pins.
- The attempt02 and attempt07 predecessor verification paths were exercised by the documented atlas verifier. No native solver or geometry modification was performed.

## Findings

### A-01 — README calls face-pair mappings “intersection regions”

Severity: **Low; current frozen counts agree, with no current evidence defect.**

The atlas schema's `finite_opposed_source_face_pairs` count sums each `face_pair_count` in the face-pair records (`scripts/wood_joint_current_face_pair_atlas_attempt01.py`, `counts` construction near line 849). Each record separately contains an `overlap_regions` array. The README calls the resulting count “exact planar source-face intersection regions” (`current-geometric-interface-face-atlas-attempt01-2026-09-28/README.md`, paragraph 3). In this frozen output, each of the 117 face-pair records has exactly one region, so the two counts are both 117. If one source-face pair later intersects as multiple disconnected regions, the field/count would still count one face pair while that README wording would count multiple regions. For a successor packet, either call this a count of face-pair mappings or emit and verify a distinct intersection-region count.

## Reviewed artifact hashes

- Producer: `016dbce14bff6408de418fc6cce35fa0590a72ceef43565164aa10f4b4bea3bb`
- Focused tests: `db2ec219ebf25194a5137b6288c195c1c54b3b2ac97a46b31a0c62155782892a`
- Frozen README: `a2f86cbb9f58fa789fd87d721756cecc12d8ad5c99218cf1545e7573b6a51dc7`
- Frozen atlas: `d455b374b238039a509bc9254fd7ea36cfbf6078af52468fbe20b31ec72e3ee9`
- Frozen source pins: `b92dcec2638fc335951033a0289cdc50bc0a949cb397b46bc03c1ad185e3c30d`
- T04 attempt02 graph: `7806242ac48b198becf5db97b16b6a5605021b8d86b964f0f02adb6806aeec26`
- T04 attempt02 source pins: `590112932d73dc57da015382a8ebf6e0fc85a8c5e8338549f381b8bd7732ba5c`
- Attempt07 geometry evidence: `24282db614089fcff73d11fcfd1216aaaff5e2d7babc1af2fa971390c29a7448`
