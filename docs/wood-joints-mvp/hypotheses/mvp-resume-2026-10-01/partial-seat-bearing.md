# Central bearing scenario at the center-principal right nut seat

The original `center_principal_right_2` nut washer overlaps the retained F1-G1
service passage. Its full annulus remains partly unsupported. This calculation
asks whether a smaller central load footprint has support without moving the
bolt, changing the passage or selecting new hardware. It is a conditional
bearing scenario, not a complete washer/joint resistance result.

## Geometry and selected force source

[partial_seat_footprint.py](partial_seat_footprint.py) imports the unchanged
finished `base_principal_center_right` STEP, SHA-256
`9053a7210a781e919038a4a823f867325dd5c78907bd028d8b9e76dc0b46df58`. The nut
seat is `(50.95, -90.3098313788, 367.0102220661)` mm. Its inward direction
comes from the source member center; grain is perpendicular to the X-directed
bearing load.

A concentric **10 mm outer / 7.3 mm inner diameter** ring has 36.68595 mm²
wood-bearing area. Exact STEP intersections find full support at inward
depths 0.01, 0.05 and 0.1 mm. The missing outer washer crescent receives no
area credit. [update_central_seat.py](update_central_seat.py) reuses these
geometry probes with the selected saved force comparison. Optional
`--clearance` accepts a comparison directory or `comparison.json`; its
default remains `all-outer-corner-frame-attempt01/`.

The current calculation uses `two-receiver-frame-attempt03/comparison.json`,
SHA-256
`0ff0dfc00c112a906910641141fd242f4a58295aa3324ca569132a3fa2d388a5`, and
`response.npz`, SHA-256
`774c3bbddf8061f6b9d1cfdd5f22efbeb1025bd57431a249912ae8e60a731f52`. All six
nominal states have bounded finite fixed-force seating. Response ranks are
296 for A12-rear, A12-forward, K12-rear and A1-rear; 297 for A12-left and
K12-right. Bounded seating permits replay of saved forces, while establishing
neither a unique pose nor strict tangent stability or complete joint
acceptance.

The ties below come from each same state's checked raw row 1535:

| Nominal case | Signed tie, N | Mean pressure, MPa | Pressure / conditional Fc-perp | Equal-area outer diameter, mm | Response rank |
| --- | ---: | ---: | ---: | ---: | ---: |
| A12-rear | 10.760567 | 0.293316 | 0.0680670 | 7.514613 | 296 |
| A12-forward | 8.935597 | 0.243570 | 0.0565230 | 7.478649 | 296 |
| A12-left | 11.446499 | 0.312013 | 0.0724059 | 7.528086 | 297 |
| K12-right | 22.525552 | 0.614010 | 0.1424875 | 7.742454 | 297 |
| K12-rear | 10.623934 | 0.289591 | 0.0672027 | 7.511926 | 296 |
| A1-rear | 6.438536 | 0.175504 | 0.0407276 | 7.429158 | 296 |

Peak current wood-bore-only footprint mean pressure is **0.614010 MPa**, or **0.1424875** of
conditional DF-L No. 2 base perpendicular bearing, 4.30922 MPa. It occurs at
K12-right with same-state signed tie **22.525552 N**. The minimum equal-area
outer circle is **7.742454 mm diameter** around the 7.3 mm bore. That is an
area requirement, not a measured nut face or hardware specification.

## Current catalog washer-opening comparison

The conditional quarter-inch USS washer has a **7.7978–8.3058 mm ID**,
wider than the 7.3 mm wood bore in the geometric probe. Use that actual
washer-opening range when declaring a nut-to-washer-to-wood pressure route.
The larger openings leave concentric subsets of the already-supported
10/7.3 mm ring, so its saved support at the three sampled inward depths
also supports these smaller annuli. This set-inclusion argument needs no
new CAD query; it establishes sampled wood geometry, not actual contact.
It does not bound a shifted or tilted washer footprint across the source
frame's nonunique seating positions.

For the current six nominal force states, the uniform-pressure comparisons
are:

| Case | Tie, N | Pressure at ID 7.7978 mm, MPa | Pressure at ID 8.3058 mm, MPa | Maximum-ID pressure / Fc-perp |
| --- | ---: | ---: | ---: | ---: |
| A12-rear | 10.760567 | 0.349560 | 0.441766 | 0.102516 |
| A12-forward | 8.935597 | 0.290276 | 0.366843 | 0.085130 |
| A12-left | 11.446499 | 0.371843 | 0.469926 | 0.109051 |
| K12-right | 22.525552 | 0.731750 | **0.924767** | **0.214602** |
| K12-rear | 10.623934 | 0.345122 | 0.436156 | 0.101215 |
| A1-rear | 6.438536 | 0.209158 | 0.264328 | 0.061340 |

Areas are 30.783143 and 24.358092 mm² respectively. At the governing
22.525552 N, the minimum equal-area outer diameter around the maximum
washer opening is **8.697235 mm**, within the supported 10 mm circle.
These numbers retain the uniform-pressure and conditional 4.309223 MPa
wood-bearing hypotheses. The corrected washer-opening comparison remains
below one; it supplies no washer metal, actual nut bearing-face, bridging,
tilt or pressure-distribution acceptance.

The numeric washer envelopes reuse the unchanged
[hardware engagement specification](assembly-package/hardware-engagement.md)
and its local `assembly-package/rawlocal/hardware-engagement/hardware-engagement.json`,
SHA-256 `93c24fe5fb421152b0294cc35106bfb6d595b558f45e0be826406405084c111a`.
Its 81.364757 N force comparison belongs to the preserved six-joint source;
this subsection uses the current force result below, not that older force.
The calculation is simply `A=π(10²−ID²)/4`, `p=T/A`, and
`Drequired=sqrt(ID²+4T/(π Fc-perp))`, repeated for six saved ties and both
ID endpoints. Frozen machine results and earlier geometry/force comparisons
remain unchanged.

## Preserved historical six-joint values

The previous `partial-seat-footprint-current-attempt02/result.json`, SHA-256
`67fa4cb8f819ae5225f1c269291c1f57b6f51835b81efe7a6c1f9170a1981fe3`, used the
older `all-outer-corner-frame-attempt01/` force source. Its historical ties
were A12-rear 58.9855 N, A12-forward 74.8676 N, A12-left 53.6042 N,
K12-right 77.6920 N, K12-rear 81.3648 N and A1-rear 16.7125 N. The associated
historical peak pressure was 2.21787 MPa, ratio 0.51468, and equal-area outer
diameter 8.79379 mm. These values remain tied to attempt02; current variation
above uses attempt03's exact same-state forces and ties.

## Working decision and missing input

Retain the current bolt and passage while resolving the actual nut/washer
footprint and metal compression/bridging. A supported central route is
geometrically available and its declared wood-pressure reference is
conditional. No full-annulus pressure, proportionally reduced crescent
capacity, actual pressure distribution or washer bending capacity is inferred.
The original partial-seat exception and complete joint remain HOLD.

The missing input is a defensible bearing footprint and compatible washer
transfer that load the supported region. Catalog across-flats dimensions
alone do not define the chamfered bearing face. Actual/Disposition cells
remain blank and every physical-release flag is false.

Current result:
`partial-seat-footprint-current-attempt03/result.json`, SHA-256
`f77afe52c27af7b81dc433af33d7afeb98cd4ff04c10bd7e63e999ef90318290`. It has
six state records and 131 source bindings, including comparison, response,
producer and `frame_state_contract.py`. Helper SHA-256 is
`22e1f8b864c03469701010fc856a815b3604a4efde2748531e36d284050266e5`. The
underlying geometry probes remain
`partial-seat-footprint-attempt02/result.json`, SHA-256
`ffba33b640e3ae00e61049664a603cdb6fe27cf7561f0068a735878ed8e3bf1b`; the
update reuses them instead of repeating CAD intersections. No geometry,
hardware or authority changed; no native solve, software test or frame solve
was run.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 uv run python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/update_central_seat.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/partial-seat-footprint-current-attempt03 \
  --clearance docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/two-receiver-frame-attempt03
```
