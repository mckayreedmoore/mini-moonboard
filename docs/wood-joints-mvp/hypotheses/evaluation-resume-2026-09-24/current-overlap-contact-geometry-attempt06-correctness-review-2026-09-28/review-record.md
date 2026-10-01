# Attempt06 overlap-contact geometry correctness review

Review date: 2026-09-28  
Subject: `scripts/wood_joint_wj08_overlap_contact_geometry_attempt06.py`, `tests/test_wood_joint_wj08_overlap_contact_geometry_attempt06.py`, and the frozen `current-overlap-contact-geometry-evidence-attempt06` packet  
Candidate/revision: `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`  
Verdict: **one low-severity packet-label inconsistency; verifier behavior, pins, regenerated evidence, and geometry-only claim boundary otherwise checked out.**

## Scope and claim boundary

Attempt06 wraps attempt05's public packet verifier and source-hash chain, adds duplicate-key rejection for both packet JSON files, requires the exact source-pin key set, and compares canonical JSON encodings of frozen and regenerated evidence. The frozen evidence reports 50 member/panel nodes and 1,225 pairs: 147 exact-BRep evaluations, 1,078 AABB-only exclusions, 26 exact-BRep separated pairs, 115 finite opposed planar geometries, and six zero-area/unresolved pairs. The class counts reconcile to 1,225. The candidate, revision, source inputs, output hash, predecessor packet and reviews are pinned. The packet keeps `overlap_contact` pending and expressly leaves contact law, active contact, bearing or pressure, load-path ownership, force transfer, capacity, case response, and acceptance unestablished.

The attempt06-specific verifier paths were inspected along with the inherited threshold and evidence builders. The frozen graph is pinned through the inherited source chain. No mismatch was found between its regenerated and frozen evidence or between its counts and the packet's documented limits. This review validates the geometry inventory's source and packet consistency; it does not independently repeat the CAD geometry calculations or establish physical fit or mechanics.

## Finding

### F-01 — README identifies the attempt06 packet as attempt05

Severity: **low; packet identification ambiguity. This does not alter the pending disposition or promote a mechanical claim.**

`_render_readme` hard-codes “attempt 05” in its heading (`scripts/wood_joint_wj08_overlap_contact_geometry_attempt06.py:188`), and the frozen README repeats that heading, while its path, source-pins `attempt_id`, and remaining text identify attempt06. Because the verifier regenerates the README from the same function, the contradictory heading passes verification and is preserved in the frozen packet. A reader can mistake this artifact for its predecessor.

Change the generated heading to “attempt 06” and regenerate the packet so its README and checksums agree with the packet identity.

## Validation

- `.venv/bin/python -m pytest -q tests/test_wood_joint_wj08_overlap_contact_geometry_attempt06.py` — 20 passed.
- `.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt06 --verify` — `PASS_GEOMETRY_ONLY_CRITERION_PENDING`; reported counts and tolerances matched the frozen packet.
- `sha256sum -c SHA256SUMS` in the frozen attempt06 packet — all three packet files passed.
- Reviewed the v6 source-pin field set, frozen source hashes and predecessor bindings; inspected the evidence mechanics flags and follow-up/limits text.

No producer, test, packet, queue, status, or handoff files were changed. This review record is the only file created.
