# Current timber cut/section inventory — attempt01

## Result

This inventory covers the reviewed
`led-clearance-2x6-runner-seated-blocks-v1` geometry: 20 frame timbers and 24
candidate blocks. It binds each row to the current STEP file hash and the
current raw/finished geometry summaries. Frame rows carry the source inventory
blank and section records. Block rows carry the source-pattern or builder
dimensions available for their constructed blanks. Conditional grain-frame
references point to the existing 20-member frame map and 24-member block map.

The axis maps include 92 candidate bolt axes, 12 retained frame-bolt axes, and
66 panel/kicker screw receiver axes. Candidate rows retain the modeled shaft
diameter and receiver intervals. Those fields describe modeled fastener
occupancy; they do not supply a timber clearance-bore diameter.

## Identified geometry

- The 20 frame members use source-inventory section values in local X/N and
  source blank dimensions. These are unreceived CAD/source records, not actual
  delivered-stock measurements.
- The frame source names open inner-face runner recesses with a 1:12,
  457.2 mm grain-aligned runout on both legs. The source maximum recess depth
  is 38.1 mm. The floor runner ends are modeled flush to the outer-post and
  inclined rear-leg planes. The source also names header-back flush-profile
  trims on both base sides. Their cut profiles are not dimensioned here.
- The 15 common blocks use the source pattern's 88.9 × 88.9 × 119.7 mm
  X/T/N blank. Two center-post blocks are constructed as 88.9 × 88.9 ×
  128.9 mm boxes. Two center-principal blocks retain the report's 5 mm
  outer-face and top trims.
- Two inner-frame blocks are builder-created 88.9 × 133.35 × 139.0 mm
  prisms. Two runner-seated outer spines use 38.1 × 139.7 × 276.3 mm
  constructed blanks after a 50.8 mm thickness reduction and 6.35 mm
  downward seat extension. The G7 block uses the pinned 88.9 × 88.9 ×
  86.9 mm X/T/N crosscut shape.

These dimensions describe source or constructed blanks and profiles, not
approved shop cuts. The current finished STEP solids are available and hashed.
The listed global AABBs are envelopes, not cross-sections. The inventory does
not compute finished net sections at bolt holes, tapers, or notches. Inherited
profile geometry outside the named operations above remains represented by
the STEP solids but is not decomposed into a complete cut-operation schedule.

## Source and limits

`inventory.json` records the SHA-256 and size of every JSON/source input and
producer. Each member row records its own STEP SHA-256, source shape
fingerprint, BRep summary hash, bounds, volume, and topology counts. Its
`record_sha256` is `0aadf60106145ba09477f286a4b97c5639c71aee4e9fe328def31a3d5e99dba8`.

Analytical cut/section inputs still absent are local net-section slices at
critical bore, taper, or notch planes; an authoritative per-axis timber
clearance-hole diameter and its source/model basis; and machining tolerances
and setup details if cut-ticketing is in scope.

Physical receiving observations also remain unobserved: delivered lumber
dimensions, grade, treatment, moisture, defects, and connection-zone condition.
Their absence records the state of this geometry-bound inventory; it does not
make receipt inspection a prerequisite to a specified conditional material
scenario. See the separate wood-property [README][property-readme] and
[JSON][property-json] for conditional product/section inputs and their
physical-observation limits.
No wood inspection, resistance, capacity, drilling, cutting, candidate
acceptance, or release is established here. All release flags remain false.

[property-readme]: ../current-wood-property-scenario-attempt01/README.md
[property-json]: ../current-wood-property-scenario-attempt01/scenario.json

## Reproduction

Run the source/artifact verification from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/\
current-timber-cut-inventory-attempt01/produce.py --verify
```

`--verify` checks the pinned inputs, all 44 STEP hashes and member identities,
the 20/24 frame/block material-map coverage, and the recorded inventory
digest. `--write` creates the inventory once and refuses to overwrite it.
