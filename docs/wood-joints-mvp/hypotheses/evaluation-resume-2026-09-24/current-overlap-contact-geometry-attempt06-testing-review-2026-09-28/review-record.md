# Attempt06 testing review

Date: 2026-09-28

Scope: independent review of `wood_joint_wj08_overlap_contact_geometry_attempt06.py`, its focused tests, and the frozen attempt06 packet for candidate `compact-floor-flush-wood-joints-development`, revision `led-clearance-2x6-runner-seated-blocks-v1`.

## Result

The focused suite passes: `.venv/bin/python -m pytest -q tests/test_wood_joint_wj08_overlap_contact_geometry_attempt06.py` reported **20 passed**. The packet verifier returned `PASS_GEOMETRY_ONLY_CRITERION_PENDING` with 50 nodes and 1,225 unordered pairs (147 exact-BRep evaluations, 1,078 AABB-only pairs; 115 finite opposed planar geometries, 26 exact-BRep separated pairs, and 6 unresolved pairs). `sha256sum -c SHA256SUMS` reported `OK` for the README, evidence JSON, and source pins.

Temporary packet copies were used to repeat fail-closed probes. The verifier rejected an attempted `accepted` disposition, an added source-pin field, an evidence boolean changed to numeric zero with output and packet hashes refreshed, a duplicate evidence key with hashes refreshed, a changed README with packet hashes refreshed, and a checksum manifest missing a required row. The focused tests also exercise geometry values just beyond the upstream thresholds and accept values at the subthreshold boundary.

The evidence remains geometry-only and pending: it identifies the expected candidate and revision, reports `criterion_disposition: pending`, and marks active contact, bearing/pressure, load-path ownership, contact law, force transfer, and criterion acceptance as not established. The packet leaves six pairs unresolved, excludes connector/fastener solids and physical face ownership, and explicitly says the inventory does not establish mechanics or acceptance. The current criteria method map and coverage record also leave `overlap_contact` pending. A verifier pass confirms packet integrity and reproduction; it does not close the criterion.

## Finding

**Low — README identifies attempt06 as attempt05.** The README generator hard-codes “attempt 05” in its title at `scripts/wood_joint_wj08_overlap_contact_geometry_attempt06.py:188`, and the frozen packet repeats that title at `README.md:1`. Reproduction: run `.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt06 --verify`; it passes while the README still says “attempt 05,” because the verifier compares the README to the same generator. The test checks generated README content for a canonical-JSON phrase but does not assert the attempt number. This is a documentation identity error; it does not change the evidence or pending criterion.

No other findings.
