# Attempt04 overlap-contact geometry testing review

Reviewed 2026-09-28. Subject: `tests/test_wood_joint_wj08_overlap_contact_geometry_attempt04.py`, its producer, and the frozen attempt04 packet. Candidate/revision: `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`.

## Result

No findings.

## Evidence

- `.venv/bin/python -m pytest -q tests/test_wood_joint_wj08_overlap_contact_geometry_attempt04.py` — **16 passed**.
- `.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt04 --verify` — **PASS_GEOMETRY_ONLY_CRITERION_PENDING**; 50 nodes, 1,225 unordered pairs, and 147 exact-BRep evaluations reconcile. Reported thresholds are 1e-5 mm distance, 1e-6 mm² area, and 1e-6 mm³ common volume.
- In the frozen packet directory, `sha256sum -c SHA256SUMS` — all three packet files verified.
- The tests exercise measurement contradictions over the distance, area, and volume tolerances, plus accepted measurements at the area/volume threshold (`tests/test_wood_joint_wj08_overlap_contact_geometry_attempt04.py:63-117`). They assert geometry-only output, no established active contact, and `overlap_contact` pending (`:49-60`).
- Candidate, revision, and scope mutations are written to packet files and the packet checksum rows are refreshed before verification (`:120-140`). A separate test mutates frozen evidence, updates its output digest and packet checksums, and requires regenerated-evidence rejection (`:143-157`).
- The CLI test freezes and verifies a temporary packet, checks pending disposition, and runs the documented checksum cycle (`:160-190`).
- I copied the checked-in packet to temporary directories and independently mutated candidate metadata, changed the criterion disposition to `accepted`, changed an evidence count while refreshing both hashes, and corrupted a checksum row. The verifier rejected them respectively as stale candidate metadata, prohibited disposition change, non-reproducing evidence, and packet checksum mismatch. The checked-in packet was not modified.

The verifier enforces candidate, revision, and scope identity and preserves the pending boundary in its success result (`scripts/wood_joint_wj08_overlap_contact_geometry_attempt04.py:219-268`). The tested packet remains geometry-only evidence; these checks do not establish active contact, mechanics, or acceptance.
