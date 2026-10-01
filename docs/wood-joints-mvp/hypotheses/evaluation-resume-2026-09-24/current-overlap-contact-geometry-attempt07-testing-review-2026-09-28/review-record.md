# Attempt07 testing review — 2026-09-28

## Result

No actionable findings in the attempt07 focused tests, packet verifier, or frozen packet integrity checks reviewed here.

## Scope

Reviewed `scripts/wood_joint_wj08_overlap_contact_geometry_attempt07.py`, `tests/test_wood_joint_wj08_overlap_contact_geometry_attempt07.py`, and `current-overlap-contact-geometry-evidence-attempt07/` for candidate and revision `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`.

## Evidence

- `.venv/bin/python -m pytest -q tests/test_wood_joint_wj08_overlap_contact_geometry_attempt07.py` — **20 passed**.
- `.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt07 --verify` — **PASS_GEOMETRY_ONLY_CRITERION_PENDING**; reports 50 member/panel nodes, 1,225 unordered pairs, 147 exact-BRep evaluations, 1,078 pairs excluded by disjoint AABBs, and six unresolved pairs.
- `sha256sum -c SHA256SUMS` in the frozen packet — `README.md`, `geometry-evidence.json`, and `source-pins.json` all **OK**.
- Temporary packet probes, with packet sums refreshed where stated, were rejected as expected:
  - Duplicate JSON object keys in `source-pins.json` and `geometry-evidence.json` each raised `ValueError: Duplicate JSON object key`.
  - An extra source-pin field raised `ValueError: Attempt07 source-pins fields are missing or unrecognized`.
  - Replacing the attempt07 identity in the README with attempt05 raised `ValueError: Attempt07 README does not reproduce`.
  - Editing only a listed packet digest raised `ValueError: Attempt07 packet checksum mismatch: README.md`.

The tests also cover stale candidate/revision/scope metadata, evidence tampering after output and packet hashes are refreshed, boolean-versus-number JSON equality, threshold failures and tolerated boundary values, CLI freeze/verify, README identity, and the documented checksum cycle.

## Boundary

The checked evidence is a partial geometry inventory only. The 1,078 AABB-separated pairs were not exact-BRep evaluated; the six zero-area or unresolved pairs remain unresolved. Geometry classifications do not establish installed contact, active contact, bearing or pressure, load-path ownership, a contact law, force transfer, mechanics acceptance, or criterion acceptance. `overlap_contact` remains **pending**. This review covers verifier and packet integrity behavior; it does not independently validate the upstream CAD geometry or qualify the joint.
