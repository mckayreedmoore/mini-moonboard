# WJ-08 overlap-contact geometry packet: independent review

Review date: 2026-09-28  
Subject: `current-overlap-contact-geometry-evidence-attempt01` and its producer/tests  
Verdict: **confirmed with two non-blocking findings**. The frozen packet reproduces and its current geometry-only claims are bounded correctly. One classifier robustness gap and one documented checksum-command error should be addressed before relying on this adapter for a successor snapshot.

## Checks performed

- Ran `.venv/bin/python scripts/wood_joint_wj08_overlap_contact_geometry.py --verify`: **PASS_GEOMETRY_ONLY_CRITERION_PENDING**. This reruns the pinned upstream T04 packet verifier and reproduces the WJ-08 output.
- Independently recomputed SHA-256 for all 10 paths in the packet's `source_hashes`: **10/10 match**. The geometry-evidence file hash also matches `output_sha256`.
- Independently counted the upstream graph: 50 distinct member/panel nodes, all 1,225 unique unordered pairs, with 147 exact-BRep candidates and 1,078 AABB-only pairs. Class counts reconcile to 115 finite opposed planar touches, 26 exact-BRep separated pairs, 1,078 AABB-only separated pairs, and 6 zero-area/unresolved pairs.
- Ran `sha256sum -c SHA256SUMS` from the packet directory: **PASS, 3/3**.
- Ran `.venv/bin/pytest -q tests/test_wood_joint_wj08_overlap_contact_geometry.py`: **10 passed**.
- Ran `.venv/bin/ruff check` on the producer and focused test: **PASS**.
- Ran `.venv/bin/ruff format --check` on the producer and focused test: **PASS**.
- Probed malformed state/measurement combinations in memory through `build_geometry_evidence`; see finding F-01. No repository inputs or producer/tests were changed.

## Claim-boundary review

The packet retains `criterion_disposition: pending` and `evidence_status: partial_geometry_inventory_only`. Every pair leaves `face_owner_ids` and `load_path_owner_ids` null, `contact_law` null, `active_contact_state` as not established by geometry evidence, and `mechanical_disposition` unresolved. The aggregate mechanics flags, including force transfer and criterion acceptance, are false.

The README and evidence explicitly retain that connector/fastener solids are outside the 50-node graph, exact face IDs/owners are absent, the six unresolved pairs remain unresolved, and no active contact, bearing, pressure, load transfer, capacity, case response, or acceptance is established. The AABB-only pairs are explicitly not exact-BRep evaluated. I found no current geometry fact promoted to active bearing, load transfer, or criterion acceptance.

The six unresolved IDs remain present in the pair records:

- `pair:center_principal_cleat_left|kicker_left`
- `pair:center_principal_cleat_right|kicker_right`
- `pair:kicker_left|main_lower_right`
- `pair:kicker_right|main_lower_left`
- `pair:main_lower_left|main_upper_right`
- `pair:main_lower_right|main_upper_left`

This was a source-bound packet and classifier review. I did not rerun CadQuery or independently regenerate the upstream exact-BRep operations; the upstream T04 independent review has the same stated limit.

## Findings

### F-01 — Geometry-state classifier accepts contradictory distance/state pairs

Severity: **medium for successor-adapter robustness; no discrepancy in the current frozen graph**. In `scripts/wood_joint_wj08_overlap_contact_geometry.py`, `_classify_edge` accepts an exact-BRep `separated` pair whenever its minimum separation is finite and nonnegative, so a zero gap is accepted as exact-separated. The finite-touch branch checks positive contact area and exact-BRep provenance but does not check that the measured minimum separation is compatible with a finite face touch.

I confirmed both cases using copies of the pinned graph in memory: an exact-separated edge with `minimum_separation_mm = 0.0` was emitted as `exact_brep_separated_geometry`; a finite-contact edge with `minimum_separation_mm = 100.0` was emitted as `finite_opposed_planar_geometry`. The pinned source itself has positive gaps for all 26 exact-separated pairs (minimum 4.2112 mm), and finite-touch values no greater than about `2.31e-7` mm, so this does not alter this packet's present counts or output.

Before reusing the adapter for a changed graph, reject a zero/nonpositive gap paired with exact separation and check finite-touch distance consistency against a documented, pinned upstream geometry tolerance. Add focused regression cases so inconsistent pairs fail closed instead of retaining the upstream label.

### F-02 — README checksum command fails from the stated repository-root working directory

Severity: **low**. `README.md` says both reproduction commands are run from the repository root, but `sha256sum -c` resolves `README.md`, `geometry-evidence.json`, and `source-pins.json` relative to the current directory. Running the documented command from the repository root failed to open those three files. The checksum file itself passes when run from the packet directory.

Use a command that changes into the packet directory before checking, for example `(cd docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-overlap-contact-geometry-evidence-attempt01 && sha256sum -c SHA256SUMS)`, or state that the checksum command is run from that directory.
