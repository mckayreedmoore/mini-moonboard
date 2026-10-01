# Current-frame mesh source audit, attempt 01

This packet answers a narrow T09 readiness question for revision `led-clearance-2x6-runner-seated-blocks-v1`: do the reviewed 50 finished-member STEP exports have a source-authenticated current-frame mesh and complete body, element, node, and DOF map? The evidence says no. An authentic current-revision **ordinary-joint patch mesh** exists, but it covers three wood members and 16 local metal bodies only. It is not a full-frame mesh and it does not make T09 inputs ready.

## Evidence and identity joins

The reviewed revision record is `docs/wood-joints-mvp/hypotheses/led-clearance-2x6-runner-blocks-2026-09-24/revision.json` (SHA-256 `148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695`). Current full-frame manifest attempt04 (`.../current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json`, SHA-256 `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11`) binds 50 finished STEP member IDs to exact files. The member-solids descriptor (`.../current-full-frame-member-solids-attempt01/bundle/current-full-frame-member-solids.json`, SHA-256 `8979d678f7b45d3b75fa465e810b0910d72874c5c1c705290d1fcb2bf2b78420`) independently lists those 50 exports. All 50 join by member ID, kind, path, file SHA-256, byte size, shape-summary SHA-256, and source-shape fingerprint; every STEP file hash and size also matches on disk. Individual member rows are recorded in `mesh-source-audit.json` and pinned in `source-pins.json`.

The verified mesh record is `.../ordinary-port-motion-attempt09-common-map/mesh.json` (SHA-256 `1043bd4a7ac03e589d6f8819f98231b33a866ee917d1e9c7099d0104092d0a07`), with deck `.../mesh.inp` (SHA-256 `117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803`). Its status is `VERIFIED_C3D10_CURRENT_PATCH_MESH_ONLY_NO_SOLVER`; the report binds the reviewed revision and its input-inventory digest matches the 27-file patch input inventory. Its three wood bodies source-shape-join to these current full-frame identities:

- `bottom_center_right_cleat`
- `base_rail_bottom_right`
- `base_principal_center_right`

The deck/report provide 19 body records, per-body global element and node ID arrays, 57,643 C3D10 elements, and 116,162 globally unique nodes. The remaining 47 current member identities are absent: 18 timbers, six plywood panels, and 23 candidate blocks. The mesh also has 16 physical-metal bodies for four local bolt stacks. Those local bodies do not represent the complete 92 candidate bolt axes or the 12 retained frame-bolt arrangements. Interface/contact assignments are pending. The mesh report explicitly leaves `accepted`, `solved`, and `native_solve_run` false and says material/contact/solver cards are absent.

There are local DOF records for the patch: `external-ports.json` maps 43 nodes at each of the local `rail` and `principal` ports into six-component rigid-motion projections, with corresponding patch control equations; `nut-coupling.json` records local auxiliary coupling inputs. These are useful patch-only records. They do not assign full-frame DOFs, supports, mass transfer, or the six current load cases. In `current-frame-adapter-attempt01/current-frame-adapter-contract.json`, all eight solver mapping slots remain null, and every one of the 50 body bindings has null solver body, element, node, DOF, and material IDs.

The current mass/topology map attempt03 has 778 source rows but declares `GEOMETRY_TOPOLOGY_MAP_ONLY_NO_REDUCED_DOF_OR_TRANSFER_MAP`. The six load cases and load datums are source-bound input contracts, not solver loads or responses. The six plywood panel layups remain unassigned. These contracts therefore do not close the mesh-to-mass or load-to-DOF gap.

The older `fea/results/current-frame-response.json` (SHA-256 `7b115e88f3724ccef6c977f079d49a4214ca42d4f0e9f8edd9bf382e91ce7506`) and its native archive (SHA-256 `92a44e5ace1559f9e4dbcb2f7ff9090e4f43377784000a0b8e88b353182ef1c0`) identify `no-shoes-development`; the response says its workspace geometry sources do not match and it is not qualified for design. Those historical files are not evidence for this revision despite their `current-frame` filenames.

## Readiness and limits

`mesh-source-audit.json` sets every readiness, acceptance, solve, and release flag false. The live T09 queue is intentionally not a source dependency and is not pinned. This audit verifies exact file hashes and the recorded source-identity joins; it does not rebuild or re-export CAD, remesh, invoke a native solver, validate material properties, establish contact/load transfer, calculate forces or capacity, or qualify a design. The patch mesh is provenance evidence for its stated local scope only.

The next executable step is a separately frozen, append-only **full-frame mesh-preparation attempt** using the exact 50 attempt04 member IDs and STEP hashes. It should produce one body-to-element/node identity map for every member and preserve source IDs. Full-frame DOFs, materials, supports, contact/attachments, mass transfer, and load mapping remain separate unresolved records; no readiness or acceptance flag should change just because a mesh exists.

## Verification

From the repository root, run:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-mesh-source-audit-attempt01/verify_source_pins.py
sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-mesh-source-audit-attempt01/SHA256SUMS
```

The verifier checks 101 source pins, the exact 50-member full-frame join, all 27 patch input STEP hashes, the patch mesh body/element/node identity totals and uniqueness, the three shape-fingerprint matches and 47 uncovered identities, null full-frame solver mappings, and false readiness gates. `source-pins.json` contains paths, roles, exact SHA-256 digests, and byte sizes for each source, including every full-frame and patch STEP file. `SHA256SUMS` covers this packet's JSON, README, and verifier; it does not self-hash.
