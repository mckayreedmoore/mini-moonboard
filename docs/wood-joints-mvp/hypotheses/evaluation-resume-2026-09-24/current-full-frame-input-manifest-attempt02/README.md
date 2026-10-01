# Current full-frame input manifest — attempt02

## Decision and result

Refresh the source-bound current-frame inventory after the MVP-E plan changed
to record the attempt03 terminal result. Preserve attempt01 as its earlier
snapshot. Attempt02 binds the current plan at SHA-256
`46227c3a0e57744d2c0fc07f4b2e12c954bef2d02739f3d80d749e8aab19775c` and has
manifest digest
`1ad6b404c8658147e9d10f54daf4ebd393116c1934654f5521421dc96667e0a0`.

The attempt is **inventory-complete, inputs-not-ready**. It reconciles 50
physical-member identities, 92 candidate bolt axes, 12 retained frame-bolt
axes, 66 panel/kicker screw axes, and six current applied load cases. Its
independent cross-checks pass. It does not supply an exact full-frame solid
set, per-member material assignments, selected structural hardware, complete
contact/attachment/engagement behavior, dead-load application map, boundary
conditions, solver DOFs, reactions, demands, stability results, or criteria.
Every acceptance and release flag remains false; no CAD rebuild or native solve
was run.

## Reproduction

The existing root producer hardcodes the attempt01 identity. This attempt uses
the small local wrapper to keep attempt01's producer and data unchanged while
binding a distinct attempt02 identifier. The wrapper also pins the base
producer hash in the generated record.

From the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt02/produce.py --write
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt02/produce.py --verify
```

The read-only verification reports `inventory_complete=true`,
`inputs_ready=false`, and checks the canonical content digest, both producer
identities, current source pins, load reconstruction, and independent
cross-checks. The second command passed after generation.

## Next input work

Continue Step 4 with a separate source-bound dead-load scenario contract using
the [current dead-load basis](../../../current-frame-dead-load-map.md), the
[778-row mass-centroid export](../current-mass-centroids-attempt01/mass-centroids.json),
and the [source-topology map](../current-mass-topology-map-attempt03/source-topology-map.json).
That work should preserve body-level gravity where member bending matters and
keep the 25 kg accessory placements explicitly scenario-based. It supplies
load inputs only; it must not assert force sharing, reactions, or demands.

The six-case contract still provides applied climber wrenches only. Defer full
frame cases until the source-bound solids, materials, hardware and mechanical
transfer model are ready.
