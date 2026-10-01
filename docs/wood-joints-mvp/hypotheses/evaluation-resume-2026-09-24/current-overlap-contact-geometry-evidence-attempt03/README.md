# `overlap_contact` geometry inventory — attempt 03

Status: **partial geometry evidence only; criterion remains pending** for
`led-clearance-2x6-runner-seated-blocks-v1`.

Attempt03 preserves the attempt02 inventory and aligns consistency checks with
the pinned upstream distance, face-area, and common-volume classification
tolerances. It binds the three attempt02 independent review records, the full
attempt02 packet, and the upstream T04 verifier and checksum manifest. Tests
exercise a temporary freeze/verify/checksum cycle.

The inventory contains 50 nodes and
1225 unordered pairs: 147
were evaluated by exact BRep, while
1078 were excluded by disjoint
AABBs and were not exact-BRep evaluated. Classifications are
115 finite opposed planar touches,
26 exact-BRep separated pairs,
1078 AABB-only pairs, and
6 zero-area/unresolved pairs.

No face-owner IDs, contact law, active-contact state, or load-path owner is
inferred. Connector and fastener solids are outside the 50-node member/panel
graph. The six unresolved pairs remain unresolved. This evidence does not
establish bearing, pressure, force transfer, capacity, case response, or
acceptance; `overlap_contact` remains `pending`.

## Reproduction

From the repository root, run:

```sh
.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt03 --verify
(cd docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-overlap-contact-geometry-evidence-attempt03 && sha256sum -c SHA256SUMS)
```

The verifier revalidates the frozen attempt02 packet, reruns the pinned T04
verifier, checks every bound source hash, applies upstream-consistent
measurement thresholds, and compares the frozen output byte-for-byte after
canonical JSON parsing. The packet pins 26 repository
inputs, including the T04 verifier/checksum manifest and all three attempt02
independent reviews. The criterion status stays pending.
