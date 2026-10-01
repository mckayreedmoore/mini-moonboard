# Attempt04 overlap-contact geometry correctness review

Review date: 2026-09-28  
Subject: `scripts/wood_joint_wj08_overlap_contact_geometry_attempt04.py`, `tests/test_wood_joint_wj08_overlap_contact_geometry_attempt04.py`, and the frozen `current-overlap-contact-geometry-evidence-attempt04` packet  
Candidate/revision: `compact-floor-flush-wood-joints-development` / `led-clearance-2x6-runner-seated-blocks-v1`  
Verdict: **one low-severity verifier finding; no current geometry-classification discrepancy or claim-boundary promotion found.**

## Scope and claim boundary

The packet reports a partial nominal member/panel geometry inventory: 50 nodes, 1,225 unordered pairs, 147 exact-BRep evaluations, 1,078 AABB-only exclusions, and six unresolved pairs. Its source-pins record identifies the intended candidate/revision, fixes the geometry-only scope, and leaves `overlap_contact` pending. The packet and README explicitly state that active contact, bearing/pressure, contact law, load-path ownership, force transfer, capacity, case response, and acceptance are not established. The inspected geometry classifications do not establish any of those mechanical claims.

Attempt04 delegates pair completeness and geometry-evidence construction to its pinned attempt03/02/01 chain. The inspected tolerance checks preserve the upstream distance, face-area, and common-volume distinctions. Attempt04 also enforces candidate, revision, scope, predecessor packet, and predecessor-review bindings; the packet README accurately describes its evidence comparison as parsed-value comparison.

This was a static review of the requested source, tests, packet, predecessor validators, and pinned contact-graph/receiver geometry producers. No tests were run, and no source, test, packet, queue, status, or goal files were changed.

## Finding

### F-01 — Parsed JSON equality accepts boolean/number substitutions

Severity: **low; verifier fidelity only. The frozen packet is unaffected, and this does not promote any mechanical claim.**

At `scripts/wood_joint_wj08_overlap_contact_geometry_attempt04.py:232-235`, the verifier parses `geometry-evidence.json` with `json.loads` and compares the resulting objects using Python equality. Python treats `False == 0` and `True == 1` as equal. The expected evidence contains boolean mechanics flags and zero-valued numeric geometry measurements (inherited from `scripts/wood_joint_wj08_overlap_contact_geometry.py:363-370` and the pair measurements), so a JSON type substitution such as `false` to `0` can leave `evidence != expected` false. Since the output digest and packet checksum rows are records inside the same packet, refreshing those rows would not catch that substitution. The current frozen packet uses the expected types and its geometry result remains unchanged.

Use a type-sensitive JSON comparison or validate the decoded evidence schema and primitive types before equality. Add a temporary-packet regression case that substitutes a boolean and a numeric zero while refreshing the packet-local hashes, and requires verification to reject the packet.
