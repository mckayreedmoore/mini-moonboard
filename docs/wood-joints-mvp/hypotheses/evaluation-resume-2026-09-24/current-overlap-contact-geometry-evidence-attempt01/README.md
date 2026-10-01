# `overlap_contact` geometry inventory — attempt 01

Status: **partial geometry evidence only; criterion remains pending** for
`led-clearance-2x6-runner-seated-blocks-v1`.

This packet adapts the independently reviewed T04 attempt02 member/panel pair
map into one record per unordered pair. It contains 50
nodes and 1225 pairs: 147
were evaluated by exact BRep, while 1078
were rejected by disjoint AABBs and were not exact-BRep evaluated. Geometry
classifications are 115 finite opposed
planar touches, 26 exact-BRep separated
pairs, 1078 AABB-only separated
pairs, and 6 zero-area/unresolved
pairs.

The adapter preserves measured areas and distances but emits no face-owner
IDs, contact law, active-contact state, or load-path owner. A finite face touch
remains geometry only. Connector and fastener solids are outside the 50-node
member/panel graph, and the six unresolved pairs remain unresolved. No bearing,
pressure, force transfer, capacity, case response, or acceptance is inferred.

The current criterion record remains `pending`. Completion requires an
integrated physical-interface inventory, finite unilateral contact behavior,
mechanical ownership, and accepted response evidence. This packet advances
inventory traceability only; it does not replace those gates.

## Reproduction

From the repository root, verify the input and output bindings with:

```sh
.venv/bin/python scripts/wood_joint_wj08_overlap_contact_geometry.py --verify
sha256sum -c docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-overlap-contact-geometry-evidence-attempt01/SHA256SUMS
```

The producer also reruns the upstream T04 verifier before freezing. The output
pins 10 repository inputs, including the producer and
focused tests. The graph source and exact geometry map are not modified.
