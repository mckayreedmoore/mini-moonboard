# T04 face-pair atlas attempt01 — independent testing review

Date: 2026-09-28

## Result

**PASS for the tested geometry-only packet contract; no implementation or test finding.** This review supports reproducible, source-bound face identity evidence only. It does not validate mechanical contact, force transfer, resistance, criterion disposition, engineering readiness, or release.

## Inputs reviewed

- Producer: `scripts/wood_joint_current_face_pair_atlas_attempt01.py`
- Focused tests: `tests/test_wood_joint_current_face_pair_atlas_attempt01.py`
- Packet: `docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-geometric-interface-face-atlas-attempt01-2026-09-28/`

Input SHA-256 values:

| File | SHA-256 |
|---|---|
| `scripts/wood_joint_current_face_pair_atlas_attempt01.py` | `016dbce14bff6408de418fc6cce35fa0590a72ceef43565164aa10f4b4bea3bb` |
| `tests/test_wood_joint_current_face_pair_atlas_attempt01.py` | `db2ec219ebf25194a5137b6288c195c1c54b3b2ac97a46b31a0c62155782892a` |
| `README.md` | `a2f86cbb9f58fa789fd87d721756cecc12d8ad5c99218cf1545e7573b6a51dc7` |
| `face-pair-atlas.json` | `d455b374b238039a509bc9254fd7ea36cfbf6078af52468fbe20b31ec72e3ee9` |
| `source-pins.json` | `b92dcec2638fc335951033a0289cdc50bc0a949cb397b46bc03c1ad185e3c30d` |
| Packet `SHA256SUMS` | `0102b0336c912a162c9d79198b08eccd2e7f10ae0929a1154d4df33cc0cb4941` |

## Checks run

- `.venv/bin/python -m pytest -q tests/test_wood_joint_current_face_pair_atlas_attempt01.py` — **9 passed**.
- `.venv/bin/python -m scripts.wood_joint_current_face_pair_atlas_attempt01 --verify` — **PASS_FACE_GEOMETRY_ONLY_CRITERION_PENDING**; 217 source files checked, with 50 STEP bodies, 378 planar source faces, 115 finite opposed body-pair rows, and 117 source-face pair records.
- `sha256sum -c SHA256SUMS` in the packet directory — README, atlas JSON, and source pins all **OK**.

## Isolated fail-closed probes

All probes used temporary data/output directories and left the producer, tests, reviewed geometry, and coordinator records unchanged.

- Stale candidate and stale geometry revision metadata were rejected by the full packet verifier.
- A changed temporary source-body byte sequence failed its pinned digest check. A separately altered packet source-pin hash was rejected against rebuilt current inputs.
- Duplicate JSON object keys in a packet pin file were rejected. Duplicate body/pair identities were rejected by the unique-index check.
- A 100 mm² exact face intersection rejected an expected opposed area of 99 mm² and independently rejected a mismatched total shared area of 101 mm².
- Relabeling one of the six unresolved graph pairs as finite was rejected. Relabeling an AABB-only pair as finite was also rejected.
- Adding a forged finite atlas row for either an unresolved pair or an AABB-only pair failed full reconstruction comparison.

The unmodified packet retains six unresolved pairs, excludes all 1,078 AABB-only pairs and 26 exact-BRep separated pairs from the mapped set, and has all mechanics/readiness/release flags false.

## Limits

The verifier and producer use the same pinned CadQuery/OCP toolchain and the predecessor's reviewed geometry inputs. This review tests packet reproducibility, tamper rejection, roster boundaries, and area reconciliation; it is not an independent CAD-kernel calculation or a mechanical validation. The nine committed focused tests do not separately cover every verifier branch; the temporary probes above exercise the requested candidate/revision, source integrity, duplicate, area, and excluded-pair failure paths.
