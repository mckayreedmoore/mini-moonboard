# Current geometric interface face-pair atlas — attempt 01

Status: **geometry-only face identity evidence; `overlap_contact` remains pending** for `led-clearance-2x6-runner-seated-blocks-v1`.

The atlas binds all 50 reviewed member/panel STEP bodies and maps 115 finite opposed body-pair rows to 117 exact planar source-face intersection regions. Per-body-pair area sums reproduce the independently reviewed attempt02 graph's opposed and total shared planar areas within the recorded tolerance. All 378 planar source faces are cataloged with a source-body face ordinal and geometry signature.

The mapping was rebuilt with CadQuery 2.8.0 / OCP 7.9.3.1.1 using the repository `.venv`. The face ordinal is scoped to the pinned STEP bytes and importer version; it is not a native CAD face name. Source-face normals, areas, and derived Boolean overlap-region geometry are included only for these reproducible exact intersections.

## Unresolved and excluded geometry

The six upstream zero-area/unresolved pairs remain unmapped:

- `pair:center_principal_cleat_left|kicker_left`: `center_principal_cleat_left, kicker_left` (preserved unresolved)
- `pair:center_principal_cleat_right|kicker_right`: `center_principal_cleat_right, kicker_right` (preserved unresolved)
- `pair:kicker_left|main_lower_right`: `kicker_left, main_lower_right` (preserved unresolved)
- `pair:kicker_right|main_lower_left`: `kicker_right, main_lower_left` (preserved unresolved)
- `pair:main_lower_left|main_upper_right`: `main_lower_left, main_upper_right` (preserved unresolved)
- `pair:main_lower_right|main_upper_left`: `main_lower_right, main_upper_left` (preserved unresolved)

The 26 exact-BRep separated pairs and 1078 AABB-only pairs are not promoted into this map. No AABB-only pair is reported as an exact result.

## Reproduction

From the repository root, run:

```sh
.venv/bin/python -m scripts.wood_joint_current_face_pair_atlas_attempt01 --verify
(cd docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-geometric-interface-face-atlas-attempt01-2026-09-28 && sha256sum -c SHA256SUMS)
```

The verifier first checks attempt02's current geometric-interface packet and attempt07's strict geometry-only inventory, then imports and checks all 50 exact STEP bodies, reconstructs the face signatures and Boolean face intersections, compares the complete canonical atlas, validates source/predecessor hashes and checksums, and rejects stale revision metadata or duplicate JSON object keys. The packet pins 217 source files.

## Mechanical and release limits

This is nominal CAD geometry only. A face-pair identity is not a contact owner, contact law, active-bearing state, or load-path edge. The atlas establishes no bearing, pressure, force transfer, stiffness, fastener engagement, resistance, response, equivalence, capacity, criterion acceptance, engineering readiness, fabrication release, or climbing release. All readiness, acceptance, and release flags remain false.
