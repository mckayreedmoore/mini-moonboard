# `overlap_contact` geometry inventory — attempt 04

Status: **partial geometry evidence only; criterion remains pending** for
`led-clearance-2x6-runner-seated-blocks-v1`.

Attempt04 retains the attempt03 inventory and tolerance checks. It also
validates candidate, revision, and scope metadata in its source-pins record.
The verifier compares parsed evidence values with regenerated values and
checks the packet hashes. Its tests exercise successful and tampered packet
verification using temporary directories.

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
.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt04 --verify
(cd docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-overlap-contact-geometry-evidence-attempt04 && sha256sum -c SHA256SUMS)
```

The verifier validates the frozen attempt03 packet and its independent reviews,
revalidates the pinned upstream T04 verifier chain, checks all bound source
hashes, applies the upstream-consistent measurement thresholds, and compares
the parsed frozen evidence values with freshly generated values. The packet
pins 35 repository inputs. The criterion status stays
pending.
