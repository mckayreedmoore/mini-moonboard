# Luna coordinator consistency audit — attempt06

Audit date: 2026-09-28. This read-only audit binds the coordinator snapshot listed below. It checks the queue, status, handoff, criteria method map, artifact manifest, the prior attempt05 audit, and current T04 face-pair-atlas attempt01 packet/reviews. It does not change coordinator records, source-snapshot authority, criteria, or candidate evidence.

## Verdict

**PASS WITH ONE SCOPED SOURCE-CONTEXT DRIFT.** All 304 artifact-manifest paths exist and match their hashes; all 12 immutable queue source-snapshot pins match; coordinator bindings, queue references, local documentation links, criteria states, and T04 review/parent-validation artifact hashes are internally consistent. The T04 atlas remains valid as a frozen, geometry-only packet with its frozen reviews and parent validation.

One of the atlas packet's own 217 source pins no longer matches current bytes: its `criteria-method-map.md` pin predates the current coordinator edit. This audit therefore does not describe the atlas as freshly verifier-clean against all present source bytes. The mismatch is in mutable criteria-method documentation (which now includes the atlas note and a group-action method clarification), not in candidate geometry or atlas output. No mechanics, criterion, readiness, or release disposition follows from it.

## Bound coordinator snapshot

| File | SHA-256 |
| --- | --- |
| `docs/wood-joints-mvp/luna-max-task-queue.json` | `225db5c4f1c3d0fed279443131c99c42db52a10024c8a45d6a353df1eac9c611` |
| `docs/wood-joints-mvp/luna-max-status-2026-09-28.md` | `c693b6c4bc465593c97556cdcc489aa60f9cdbdaba5a9e4f7636d99ad9cb5189` |
| `docs/wood-joints-mvp/luna-max-completion-handoff.md` | `77b682c6ca8a2c614f03d6bd410113bd7e4bb62288da5ec0376a74f34034096e` |
| `docs/wood-joints-mvp/criteria-method-map.md` | `bd356fc8751e17c860fd6df8150c3076b9cfbd742fff9b0de518b970868f324a` |
| `docs/wood-joints-mvp/artifact-manifest.json` | `790a99ebad5ba504225c0792569a4d286b6c2bbdedc112770320a0a9f480749a` |

The queue and manifest pass strict duplicate-key-rejecting JSON parsing and declare `wood_joint_luna_max_completion_queue/v1` and `wood_joint_artifact_manifest/v1`. The criteria register, face-pair atlas, and atlas source-pins JSON also pass duplicate-key-rejecting parsing with their declared schemas. The manifest contains 304 entries; every path exists and every recomputed SHA-256 matches. It binds the live queue, status, handoff, and criteria-method map to the four corresponding digests above. `plan_review.handoff_document_sha256` equals the live handoff digest.

The queue has 363 distinct repository-relative file references, all resolving. The status has 38 local Markdown links, the handoff has 69, and the criteria-method map has 3; all 110 targets resolve. T04's 56 terminal-artifact paths exist. The queue source snapshot has 12 entries and all 12 hashes match. Candidate/revision remain `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`; the six current case IDs remain `a12-rear`, `a12-forward`, `a12-left`, `k12-right`, `k12-rear`, and `a1-rear`.

Attempt05 remains valid for the earlier snapshot it audited, not for these newer bytes. The current queue's historical review record binds attempt05 report SHA-256 `d2e02fa32e814ea704ff9957b01281971c78dffc06f0c4f940515ea6c1ea0b27` and sidecar SHA-256 `215a1c233560aeb313b75a023e57768de7935e56ae76197d572c3b23e6967842`; both match their files and the sidecar entry matches the report. Attempt05 identifies its reviewed queue `7fe3f33b98a9dc2369a91c345848a67e8c1aee18b55496181a88d26ed2f06ca0`, manifest `1afcb9be49b1d92feb45edc90956a10c77222d5f8a146534d217f2e517a1686c`, and handoff `667673720ad417f36da50742aa50862c9e8d14fabfa4d4134c8d49d8f1c21f33`. Those are explicitly historical and differ from the current snapshot; the live status accurately calls attempt05 a pre-closure audit.

## T04 face-pair atlas attempt01

T04 remains `active`. The atlas subtask remains `parent_and_independent_review_pass_geometry_only_mechanics_open_nonblocking_architecture_note`; `native_execution=false`, `criterion_id=overlap_contact`, and `criterion_disposition=pending`. All 16 paths in its queue `artifact_sha256` map exist, match their exact hashes, and are also bound by the current manifest. The subtask's producer, independent-review, and parent-validation paths exist. The full T04 terminal-artifact list contains 56 existing paths.

| Bound artifact | SHA-256 |
| --- | --- |
| Producer `scripts/wood_joint_current_face_pair_atlas_attempt01.py` | `016dbce14bff6408de418fc6cce35fa0590a72ceef43565164aa10f4b4bea3bb` |
| Focused tests `tests/test_wood_joint_current_face_pair_atlas_attempt01.py` | `db2ec219ebf25194a5137b6288c195c1c54b3b2ac97a46b31a0c62155782892a` |
| Packet README | `a2f86cbb9f58fa789fd87d721756cecc12d8ad5c99218cf1545e7573b6a51dc7` |
| `face-pair-atlas.json` | `d455b374b238039a509bc9254fd7ea36cfbf6078af52468fbe20b31ec72e3ee9` |
| Packet `source-pins.json` | `b92dcec2638fc335951033a0289cdc50bc0a949cb397b46bc03c1ad185e3c30d` |
| Packet `SHA256SUMS` | `0102b0336c912a162c9d79198b08eccd2e7f10ae0929a1154d4df33cc0cb4941` |
| Architecture review | `c5a202d21b6ec4eb98f41c718069c4ce9d129506d06fe1bdb5f60a0c7a24895a` |
| Architecture review `SHA256SUMS` | `b9b4d13f59b861c1c37fd136c031a2478f6d6564e0ab7ecf457e11c72e1bb39a` |
| Correctness review | `ce45c6a6e44ff24c0ec48a1a1d8bdd9e22c911e808498b7e0b96764a12a80da6` |
| Correctness `verification-results.json` | `ce61b53842a7574b9264a97ea45de92773302637d9a617649d45137542ac2e6d` |
| Independent reconstruction script | `9dfa5c9a657b81ce65f086489f158d472dbe440886019e70c7ad35dd04084359` |
| Correctness review `SHA256SUMS` | `88fd33e519c63ce7f3ce0fab60e525ec8b438ef987e23f704331fda47c6bc19e` |
| Testing review | `9271b56c61e6749af08ae9365e865bac49ab33cec8d3469e41e50950137db930` |
| Testing review `SHA256SUMS` | `37da5329cd5af0be4fe2b5bd6a9cabe6455c8c23a616832d8f3ffed0407d2fc9` |
| Parent-validation README | `7f7ff74c4bc7aa0b25d2f16002db791b0897f532daa040b795eaeb629bb27934` |
| Parent-validation `SHA256SUMS` | `bcf227c477671629486030bdcf6ceb3d6ec9d92bbaf9f4ac8bf2dc3e6a7b593a` |

The packet and review checksum lists were checked against their contents; all ten entries across the packet, three review packets, parent-validation packet, and attempt05 report checksum sidecar match. The atlas reports 50 STEP bodies, 378 planar faces, 115 finite opposed body-pair rows, 117 face-pair mappings, and 117 Boolean regions; six rows remain unresolved, 26 exact-separated pairs remain unmapped, and 1,078 AABB-only pairs were not evaluated exactly. The queue binds 217 source hashes. The frozen independent area-difference maximum is `8.28367774374783e-7 mm²`, below its `1e-6 mm²` absolute tolerance.

The face atlas is nominal face-identity/intersection geometry only. Its mechanics fields for active contact, bearing/pressure, capacity, contact law, criterion acceptance, force transfer, load-path ownership, readiness, and release are all false. It does not assign physical face ownership, active bearing/contact, solver maps, force transfer, engagement, response, resistance, equivalence, or mechanical duty closure. T04's exit gate still requires mechanical paths for 24 duties, 66 screws, center-kicker routes, and twelve retained frame-bolt stacks; those remain open.

The low architecture note is accurately scoped: each of the 117 mapped face pairs has one region in this frozen result, so both counts are 117 today. A future face-pair record with multiple disconnected regions could make the README's use of “intersection regions” misleading; a successor should count regions separately or call the current count face-pair mappings. This is a future-compatibility wording note, not a present geometry defect.

## Scoped finding A-01 — atlas source-context drift

The atlas `source-pins.json` contains 217 source paths. Current-byte recomputation matches 216. The only mismatch is:

- Path: `docs/wood-joints-mvp/criteria-method-map.md`
- Frozen atlas source pin: `2d9083d4286e328553183e0bb993cfb913985fbe4960717bfe0bb4ef416d32e7`
- Current map bytes: `bd356fc8751e17c860fd6df8150c3076b9cfbd742fff9b0de518b970868f324a`

The current method map adds the T04 atlas geometry-only note to `overlap_contact` and adds a method-only group-action clarification; both criterion rows remain `pending`. This is post-freeze documentation-context drift. The 16 frozen atlas/review/parent artifact hashes all match; the mismatch does not indicate an atlas-output mutation, and the atlas itself continues to explicitly leave mechanics and criterion disposition open. It does mean the 217-file source closure is not a 217/217 match against today's workspace. The current queue, status, handoff, and manifest accurately present the atlas as a reviewed frozen geometry packet and do not claim a fresh all-input verifier pass.

## Criteria and gate state

The queue has 47 unique `criterion_ownership` rows and all 47 `engineering_status_at_handoff` values are `pending`. The `criteria.json` register has 36 legacy rows and 11 candidate obligations; all 47 source statuses are pending. The criteria-method map has the same 47 IDs and 47 pending rows. `overlap_contact` remains pending in the queue and method map; the T04 atlas subtask separately says `criterion_disposition=pending`.

Queue `release=false`, queue `engineering_mvp_complete=false`, checkpoint `engineering_mvp_complete=false`, manifest `release=false`, and criteria-register engineering/release flags are false. T04's atlas `native_execution=false`; the queue's current-joint freeze/run fields remain false. Full-frame `inputs_ready` remains false in the status evidence. The queue also records `current_map_readiness=true` and `current_map_native_execution=true` for a scoped known-answer method fixture; those fields do not describe readiness or execution of the current joint/full-frame candidate. No T04 mechanical duty or criterion was promoted. `plan_review.status` remains `checkpoint_update_pending_independent_consistency_review`, pending coordinator binding of this attempt06 result.

## Method and limits

I strictly parsed the queue, manifest, criteria register, atlas, and atlas source-pins JSON with duplicate-key rejection; recomputed all 304 manifest hashes, 12 queue source pins, 217 atlas source pins, and 16 queue-pinned atlas artifact hashes; compared coordinator bindings; checked queue paths, T04 terminal paths, Markdown links, and packet checksum entries; and compared the 47 criterion IDs/dispositions across the queue, source register, and method map. I did not run project tests, the atlas producer/verifier, a solver, Docker, a native mechanics case, or any engineering disposition. Test/review counts are the frozen packet claims, not audit executions. This audit record and its checksum are outside the current artifact manifest and do not alter source-snapshot authority.
