# Central bearing scenario at the center-principal right nut seat

The original `center_principal_right_2` nut washer overlaps the retained F1-G1
service passage. Its full annulus remains partly unsupported. This calculation
asks whether a smaller central load footprint has support without moving the
bolt, changing the passage or selecting new hardware. It is a conditional
bearing scenario, not a complete washer/joint resistance result.

## Exact geometry and simultaneous demand

[partial_seat_footprint.py](partial_seat_footprint.py) imports the unchanged
finished `base_principal_center_right` STEP, SHA-256
`9053a7210a781e919038a4a823f867325dd5c78907bd028d8b9e76dc0b46df58`.
The nut seat is `(50.95, -90.3098313788, 367.0102220661)` mm. Its inward
direction comes from the source member center; grain is perpendicular to
the X-directed bearing load.

A concentric **10 mm outer / 7.3 mm inner diameter** ring has 36.68595 mm²
wood-bearing area. Exact STEP intersections find full support at inward
depths 0.01, 0.05 and 0.1 mm. The missing outer washer crescent receives no
area credit. The six simultaneous ties at checked raw row 1535 are:

| Case | Signed tension, N |
| --- | ---: |
| A12-rear | 59.2235 |
| A12-forward | 75.7509 |
| A12-left | 53.1297 |
| K12-right | 76.4634 |
| K12-rear | 82.6281 |
| A1-rear | 6.4743 |

Under declared uniform central pressure, the peak mean is **2.25231 MPa**,
or **0.52267** of conditional DF-L No. 2 base perpendicular bearing,
4.30922 MPa. The minimum equal-area outer circle is **8.81499 mm diameter**
around the 7.3 mm bore. That is an area requirement, not a measured nut face
or a hardware specification.

## Working decision and missing input

Retain the current bolt and passage while resolving the actual nut/washer
footprint and metal compression/bridging. A supported central route is
geometrically available and its declared wood-pressure reference is favorable.
No full-annulus pressure, proportionally reduced crescent capacity, actual
pressure distribution or washer bending capacity is inferred. The original
partial-seat exception and complete joint remain HOLD.

The missing input is a defensible bearing footprint and compatible washer
transfer that load the supported region. Catalog across-flats dimensions
alone do not define the chamfered bearing face. Actual/Disposition cells
remain blank and every physical-release flag is false.

Frozen result: `partial-seat-footprint-attempt02/result.json`, SHA-256
`ffba33b640e3ae00e61049664a603cdb6fe27cf7561f0068a735878ed8e3bf1b`.
It binds the frame, material, STEP and producer. The first attempt stopped
at the inward-orientation preflight; its failure and producer are preserved.
No native solve, frame rerun, software test or model/hardware change was made.

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/partial_seat_footprint.py \
  --output /tmp/FRESH-PARTIAL-SEAT-FOOTPRINT
```
