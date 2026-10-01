# `overlap_contact` geometry inventory — attempt 02

Status: **partial geometry evidence only; criterion remains pending** for
`led-clearance-2x6-runner-seated-blocks-v1`.

Attempt02 retains the attempt01 member/panel pair inventory and adds strict
consistency checks against the pinned upstream distance (`1e-5 mm`) and face
area (`1e-6 mm²`) classification tolerances. It rejects exact-separated rows
at or below the distance tolerance, finite-touch rows beyond that tolerance,
and contradictory AABB/unresolved measurement states. The prior independent
review recorded these classifier and README command findings; this packet
addresses both.

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
.venv/bin/python -m scripts.wood_joint_wj08_overlap_contact_geometry_attempt02 --verify
(cd docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-overlap-contact-geometry-evidence-attempt02 && sha256sum -c SHA256SUMS)
```

The verifier reruns the reviewed upstream T04 check, validates all bound source
hashes, applies the stricter distance/state checks, and compares the frozen
output byte-for-byte after canonical JSON parsing. The packet pins
15 repository inputs, including the attempt01 review,
both geometry producers, this producer, and its focused tests. The criterion
status stays pending.
