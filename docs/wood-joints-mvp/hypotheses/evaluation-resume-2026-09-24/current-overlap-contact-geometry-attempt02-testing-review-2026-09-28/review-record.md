# Attempt02 overlap-contact geometry testing review

Review date: 2026-09-28  
Subject: `test_wood_joint_wj08_overlap_contact_geometry_attempt02.py`, its producer, and the frozen attempt02 packet.  
Verdict: **one low-severity test-coverage finding; current reproduction passes**.

## Checks performed

- Ran `.venv/bin/python -m pytest -q tests/test_wood_joint_wj08_overlap_contact_geometry_attempt02.py`: **9 passed**.
- Ran `.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt02 --verify`: **PASS_GEOMETRY_ONLY_CRITERION_PENDING**; counts reconcile to 50 nodes, 1,225 pairs, 147 exact-BRep pairs and the four frozen geometry classes.
- Ran the README checksum command verbatim from the repository root: **PASS, 3/3**.
- Froze to a temporary directory, then called the producer verifier against that fresh packet: **PASS**, with criterion disposition `pending`.

The frozen output keeps `overlap_contact` pending and describes geometry only. It leaves active contact, bearing/pressure, load-path ownership, force transfer and acceptance unestablished. The six unresolved pairs and the excluded connector/fastener geometry remain explicit.

## Finding

### F-01 — The reproduction test checks command text but does not exercise reproduction

Severity: **low; no current packet failure**. In `tests/test_wood_joint_wj08_overlap_contact_geometry_attempt02.py:129-136`, `test_attempt02_readme_checksum_command_runs_from_repository_root` only renders the README and checks that it contains a literal command. It does not execute that command, call `freeze_packet`/`verify_packet`, or check a freshly generated packet. Those behaviors are implemented separately in `scripts/wood_joint_wj08_overlap_contact_geometry_attempt02.py:265-357`; a regression in the freeze/verify lifecycle or in the README's working-directory command could therefore leave this test green.

Add a focused integration test that freezes to `tmp_path`, verifies the result, and executes the documented checksum check from the repository root. The current README command and fresh packet both passed during this review, so this is a coverage gap rather than a defect in the frozen packet.
