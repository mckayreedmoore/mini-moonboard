# Current frame timber material-frame map — attempt01

## Result

This attempt maps a conditional longitudinal grain direction to the **20
source-frame timber IDs** in the reviewed candidate. The six plywood panels
are excluded, and all six layups remain unresolved. The machine-readable map
is [`current-frame-timber-material-frame-map.json`](current-frame-timber-material-frame-map.json);
[`produce.py`](produce.py) rebuilds and verifies it from pinned source records.

The exact 20 IDs reconcile across the
[source inventory](../../../source-inventory.json), attempt02 full-frame
manifest, and the current
[50-member STEP bundle](../current-full-frame-member-solids-attempt01/README.md).
The manifest also calls the 24 connector blocks `timber`; those block IDs are
not frame members and are excluded by exact source-inventory ID matching.
Sixteen frame members use the current composed finished-host geometry; four
retain their source part unchanged in composition.

## Grain and frame basis

Each proposal uses the source inventory's member-specific
`grain_axis_global_xyz`, built by its pinned `_grain_axis` rule from source
solid axes. The map carries the source-local `X/T/N` basis, homogeneous
local-to-global transform, recorded blank dimensions and section, and source
shape hashes. The local frames are checked for unit axes, orthogonality, and
right-handed orientation. The proposed grain vector is resolved back into
that local frame and reconstructed before it is recorded.

As an independent geometry consistency check, the producer imports each
already-exported current STEP BRep and compares the recorded proposal with the
minimum-principal-inertia direction of that exact solid. All 20 absolute dot
products are at least 0.999. This check uses no display mesh and does not
choose the grain direction; the pinned source-inventory rule supplies it. The
STEP files also match their recorded bounds and volume summaries. CadQuery
documents `matrixOfInertia` as inertia per density; this map uses its principal
direction only, not its magnitude ([Shape API][cadquery]). No CAD geometry was
rebuilt or changed.

The lumber-leg proposal is the stored oblique vector
`(0, -0.239151832, 0.970982184)`, preserved at full recorded precision. It is
not approximated by a nearby `X/T/N` axis. Every grain assignment is sign
equivalent and remains a conditional stock scenario, not an observation of a
delivered board. Per-board ring orientation and transverse `R/T` assignments
remain unresolved.

## Material and claim limits

The source inventory's `DF-L No. 2` entry is a scenario basis, not a received
grade claim. Delivered species group, grade, any regrade after remanufacture,
treatment, moisture, receiving condition, and elastic material values remain
open. This map emits no material values. All six panel layups remain open.

This is an orientation-input artifact only. Full-frame readiness, material
acceptance, native-solve status, candidate acceptance, and all release flags
remain false. It establishes no capacity, demand, structural result,
fabrication approval, or climbing release.

## Verification

Run read-only source and STEP verification from the repository root:

```sh
map_dir=docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/
map_dir+=current-frame-timber-material-frame-map-attempt01
uv run --no-sync python3 "$map_dir/produce.py" --verify
```

The producer pins the source inventory, reviewed attempt02 manifest, current
member-solid artifact, source grain-rule code, and the source inventory's
dependency hashes. It verifies exact ID reconciliation, all 20 local frames,
current geometry and STEP hashes, exact-BRep axis cross-checks, and the
canonical map digest. A changed input requires a new attempt; `--write`
refuses to overwrite this map.

Map digest: `69a99e91583a4a2e9064edf24335a921cc48395ba3699fd96bec1a2272a30bb5`.

[cadquery]: https://cadquery.readthedocs.io/en/latest/classreference.html
