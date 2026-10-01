# `overlap_contact` geometry inventory — attempt 05

Status: **partial geometry evidence only; criterion remains pending** for
`led-clearance-2x6-runner-seated-blocks-v1`.

Attempt06 retains the reviewed geometry inventory and tolerance checks. It
uses attempt05's public packet verifier, rejects duplicate JSON object keys,
requires the exact source-pin fields, and compares canonical JSON encodings so
JSON booleans and numbers cannot compare equal by Python's loose value rules.

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
.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt06 --verify
(cd docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-overlap-contact-geometry-evidence-attempt06 && sha256sum -c SHA256SUMS)
```

The verifier checks the attempt05 packet and its reviews, reuses its validated
source-hash chain, validates the candidate/revision/scope metadata, applies the
upstream-consistent measurement thresholds, and compares canonical JSON
representations of the frozen and regenerated evidence. It rejects duplicate
JSON object keys and unrecognized source-pin fields. The packet pins
53 repository inputs. The criterion status stays
pending.
