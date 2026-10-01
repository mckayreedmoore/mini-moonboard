# Current frame timber transverse scenarios — attempt01

This source-only artifact adds two conditional transverse material frames to
each of the 20 timber grain directions in the preserved
[longitudinal map](../current-frame-timber-material-frame-map-attempt01/README.md).
It produces 40 orthonormal right-handed frames for the reviewed
`led-clearance-2x6-runner-seated-blocks-v1` revision. Geometry, grain proposals,
material properties and acceptance states are unchanged. No ring orientation
was observed and no case is selected.

## Explicit analysis choice

The material basis order is longitudinal/radial/tangential, `L/R/T`.
Source `X/T/N` are geometric axes; source T is not automatically material T.
For every member:

1. Retain the recorded longitudinal vector, normalizing only unit-roundoff.
2. Project source X perpendicular to L and normalize it to obtain `R_A`.
   Where X is parallel to L, use source T instead. This occurs for the eight
   timber members whose longitudinal grain follows global X. The other twelve
   use source X as their radial reference.
3. Set `T_A = L × R_A`. Case B uses the same L, `R_B = T_A` and `T_B = −R_A`.

The projection avoids snapping the oblique lumber-leg direction to a nearby
source axis. Both cases retain every longitudinal vector within 1e−12; the
full recorded source vector is also stored unchanged. These two cases are
analyst-selected sensitivity inputs, not observations of growth rings, a
selected orientation, or guaranteed bounds on all possible board orientations.
Uniform all-A and all-B frame runs cannot bound mixed-board arrangements. If
response is sensitive, investigate relevant individual-member swaps before
interpreting it. No material law, property table, solver orientation card or
element assignment is emitted by this artifact.

## Source and algebra checks

The producer pins the complete original map and the unchanged material-scenario
policy. It verifies the original map's canonical content digest and all its
upstream source pins, then checks each of the twenty exact STEP file hashes
and byte sizes. It reads these files; it does not rebuild or modify CAD.

Each material basis passes unit-vector, orthogonality and determinant +1 checks
at 1e−12. A separate NumPy matrix calculation confirmed all 40 bases, original
L retention and the A/B swaps; the worst Gram-matrix error was
2.220446049250313e−16. The [independent review](independent-review.md) confirms the source binding,
frame algebra and stated applicability limits.

The [machine artifact](transverse-scenarios.json) has canonical content digest
`fc1d5611d99cc7a5b8f7226e112af29a96ed83cd45d759e997bdb351261a2d7a`.
It records every member ID, STEP hash, source member-row hash and source-shape
fingerprint. Its producer hash is part of that digest. Use:

```sh
python3 produce.py --verify
```

The verification reproduces the map and refuses any mismatch. `--write` uses
exclusive creation and will not replace an existing result.

## Remaining work

These are orientation alternatives only. Delivered species, grade, treatment,
moisture and ring direction remain unobserved. The six plywood panel layups,
current-frame mesh/material assignment, connection transfer, six-case demands
and all structural criteria remain outside this result. No material, joint,
full-frame readiness, fabrication or release gate passes through this map.
The preserved original map and current full-frame manifest are unchanged;
this new sibling must be explicitly bound in a future input freeze before use.
