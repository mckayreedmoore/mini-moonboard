# WJ-05 relieved center-node probe

Status: blocked nominal geometry diagnostic. This archived hypothesis does not
change active configuration or manifest and gives no structural, purchase,
drilling, fabrication, or build release.
Trial: `wj05-center-node-rear-4x4-upper-l82-wire-relief-v2`.

## Reproduction and recorded inputs

Run from the repository root:

```sh
uv run python -m scripts.wood_joint_wj05_center_node_probe > /tmp/wj05-center-node-relieved.json
```

The corrected archived JSON is byte-identical to the preserved report,
SHA-256 `0fc03b3f6faf810d09e70a1dd8b10871ca75abb53b1e7d16ded6f6e5391a9cd1`.
The producer SHA-256 recorded in its input fingerprints and matching the
current script is
`eafffbc95d5989bcc21a7cfed90ff25e917c778bf9758154b915cbba0ec3d173`.
`source_fingerprints_sha256` records 11 file hashes, including the two wiring
references, source inventory, geometry modules, protected-layout helper, and
producer. Those hashes matched the listed files at archive time. This is the
report's declared input set, not a claim of complete transitive source closure
or a pinned repository revision.

## Nominal geometry screen

- The upper rear 4×4 principal/header cleat has an 82 mm nominal grain length
  with a triangular wire relief. The lower 4×4 cleat remains unchanged.
  The right relief is 2.303793 mm from `wire_072_F1_G1`, above the 2.0 mm
  nominal gate. The mirrored left-side result is a 9.25 mm bounding-box lower
  bound, not an exact nearest-wire distance.
- The checked body, bore, and installed-component maps report no collision
  hits for four candidate cleat bodies, 16 bore axes, or 80 installed fastener
  components. All reported washer-seat fractions are 1.0. The 48 panel axes
  and 18 kicker axes remain unchanged (66 total); all 12 starting frame bolts
  are retained.
- The corrected model places each 25.4 mm diameter × 50 mm head-tool proxy
  from the installed head face outward over the 0–50 mm axial span. Two proxy
  volumes overlap the center posts at the upper header row-2 positions (left
  and right), 1,481.459916 mm³ each. These are
  proxy-to-wood results, not actual tool-access findings; no wrench sweep or
  physical access conclusion is established. Installed fastener components
  remain clash-free in the checked geometry.
- Conditional end/edge screens and the oblique-axis method remain unresolved.
  In particular, the upper header-bolt minimum conditional 4D margin is
  −1.202205 mm; the report does not establish the applicable design category,
  signed demand, or member resistance.

The probe covers only part of the center node; it does not close the four
center structural duties. Its conclusion assigns no capacity and reports no complete
center load path. Geometry and clearances are nominal diagnostics, not
acceptance.
