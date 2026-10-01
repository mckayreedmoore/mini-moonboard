# Conditional corner washer-seat wood compression screen

This packet reuses the exact 252 source-bound seat states from the [three-case
axial-seat register](../current-corner-three-case-axial-seat-register-attempt01/README.md)
and compares each state with two declared full-annulus areas: the minimum
catalog USS ring (`213.627873 mm²`) and the frozen washer CAD annulus
(`222.726212 mm²`). It records 21 increments, 126 signed tie states and 252
physical seat states. All 126 source scalars are positive tie tension; their
magnitude is treated as the normal wood-seat compression demand in the stated
annulus scenario.

The mean-stress arithmetic is `p = |T| / A`, with N/mm² reported as MPa. The
minimum USS ring uses the hardware packet's 0.727-in minimum OD and 0.327-in
maximum ID. Its 8.3058-mm opening exceeds the modeled 7.5-mm bore. This is a
catalog dimension envelope, not a selected or delivered washer. The frozen CAD
area is retained as a separate model comparison. Both assume a complete,
sound and supported annulus with uniform mean pressure. Neither determines
actual pressure distribution, wood contact area or washer load spreading.

The proposed grain vectors in the pinned material input classify 10 physical
seats per increment as perpendicular to grain and the two BG045 inner-block
seats as parallel. The full source state and member/role/point/force identity
are preserved in [`seat-compression-screen.json`](seat-compression-screen.json),
SHA-256
`54b780a015fb01615361b41a4ade4cf1ced3d7f3842bc7f40963e3c1c2fca487`.

| Axis | Peak tie / case | USS minimum-ring mean stress (MPa) | Frozen-CAD mean stress (MPa) | Conditional material comparison |
| --- | --- | ---: | ---: | --- |
| BG001 `post_1` | 64.96606 N / A12-rear | 0.304109 | 0.291686 | `Fc⊥ 625 psi`: ratio 0.070572 / 0.067689 |
| BG001 `post_2` | 47.00119 N / A1-rear | 0.220014 | 0.211027 | `Fc⊥ 625 psi`: ratio 0.051057 / 0.048971 |
| BG003 `side_1` | 99.23822 N / K12-rear | 0.464538 | 0.445561 | `Fc⊥ 625 psi`: ratio 0.107801 / 0.103397 |
| BG003 `side_2` | 73.62760 N / K12-rear | 0.344654 | 0.330574 | `Fc⊥ 625 psi`: ratio 0.079980 / 0.076713 |
| BG045 `inner_header_1` | 119.34300 N / A12-rear | 0.558649 | 0.535828 | Header `Fc⊥`: 0.129640 / 0.124345; block `Fc`: 0.060019 / 0.057567 |
| BG045 `inner_header_2` | 98.44241 N / A1-rear | 0.460813 | 0.441988 | Header `Fc⊥`: 0.106936 / 0.102568; block `Fc`: 0.049508 / 0.047485 |

Each cell gives ratios in USS-minimum-area / frozen-CAD-area order. For
BG045, the same tie pressure is compared against a different source property
for each end seat: the header seat is transverse to its proposed grain, while
the block seat is parallel to its proposed grain. The highest mean stress is
0.558649 MPa in A12-rear at load factor 1.0. Its transverse `Fc⊥` reference
ratio is 0.129640. The parallel block's `Fc` ratio is 0.060019; that row is a
stress/reference comparison only because no local parallel washer-bearing
method is adopted here.

## Conditional property and adjustment scenario

The selected calculation scenario is conditional DF-L No. 2 under
normal-duration, dry-service conditions, with unincised wood at normal
temperature. The [material packet](../../hardware-material-specification-2026-09-30/materials.md)
and its [machine-readable inputs](../../hardware-material-specification-2026-09-30/material-inputs.json)
give the unadjusted Table 4A values `Fc⊥ = 625 psi` (4.309223 MPa) and
`Fc = 1,350 psi` (9.307921 MPa). These are arithmetic scenarios; species,
grade, service condition and grain have not been observed on actual stock.

The adjustment selection is explicit in the JSON. Normal duration and dry
service use `CD=1.0` and `CM=1.0`; normal temperature and unincised condition
are scenario assumptions `Ct=1.0` and `Ci=1.0`. Table 4A `CF` does not apply
to `Fc⊥`. The two ripped BG045 block-seat references use the packet's
hypothetical final-section No. 2 `CFstudy=1.0` only; the packet assigns no
code Table 4A size class or `CF` to those rips. For the transverse BG003 block
seats, `Fc⊥` is likewise carried within that explicitly hypothetical ripped
block material scenario, without assigning a post-rip grade. No bearing-area
increase or compression-stability credit is applied. The precise support
patch and member-end conditions needed to consider a bearing-area increase
remain unverified.

The ten transverse seats receive a conditional `Fc⊥` stress/reference ratio.
The two BG045 inner-block seats use `Fc=1,350 psi` only as the specified
hypothetical parallel-grain property comparator. The supplied sources do not
establish an applicable local washer-on-end-grain parallel bearing method,
so this packet reports stress/reference values there and makes no code pass
claim. The generated arithmetic status means only that source checks and
replay succeeded.

## Pinned inputs and open evidence

[`source-pins.json`](source-pins.json), SHA-256
`37b2c98c0bb0f60c9f4b7d5d683a0376d3200f8cd8e8b83a340409ca0e039fde`, pins the
252-state axial register, its source pins, frozen washer geometry, the
hardware/material packet, and the listed material, geometry and standard
sources. The reused demand register SHA is
`7e1c393f0670b4f7428946a856dde757315307d0e92ecfa77e72d70f40bdde90`. No
response force is recomputed or changed here. Packet lineage records the
hardware-requirements base `cf6ebe55262f963494d8086adee599b4c9a293d8` and
material/adjustment update `858688a985b17bfc67762288b480da3cb37103c9`;
per-file hashes control replay.

Remaining seat evidence is the selected/delivered washer and its material and
flatness; actual head/nut footprints; the finished wood support polygon,
cuts, gaps, edge distances and actual bearing area; wood species/grade,
moisture, treatment and physical grain; and washer bending/spreading behavior.
No metal capacity, pull-through, splitting, or local pressure field is
inferred. The ripped inner block has no transferred source-stock grade.

Replay with Python 3 standard library only:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-catalog-washer-wood-compression-screen-attempt01/produce.py --write
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-catalog-washer-wood-compression-screen-attempt01/produce.py --verify
```

This result is a conditional wood-seat stress/reference screen, not a physical
seat, product or complete-joint acceptance.
