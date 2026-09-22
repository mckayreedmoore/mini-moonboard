# Integrated barrel frame: nominal installed-stack reach

This screen reads the 46-pair **integrated** assembly with
`build_integrated_viewer_assembly()` and passes it to
`owner_barrel_installed_stack_audit.build_report(assembly)`. It is distinct from
the [historical 48-pair outward-post audit](owner-barrel-installed-stack-audit.md).
The table groups all 46 rows by original connection-duty family and nominal
bolt length. Values are millimeters and apply to each row in that group.

| Duty family | Rows | Bolt length | Tip past assumed barrel axis | Fully threaded tip length needed just to reach near wall | Maximum possible body overlap | Tip-to-bore-cap clearance |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Base center | 2 | 127.0 | 25.349 | 30.353 | 10.008 | 4.000 |
| Base outer side | 4 | 127.0 | 17.249 | 22.253 | 10.008 | **0** |
| Bottom center | 4 | 127.0 | 17.249 | 22.253 | 10.008 | **0** |
| Bottom outer rail | 4 | 152.4 | 1.849 | 6.853 | **6.853** | 5.155 |
| Header center | 4 | 101.6 | 22.949 | 27.953 | 10.008 | 4.000 |
| Header outer post | 4 | 127.0 | 23.900 | 28.904 | 10.008 | 4.000 |
| Lower center rail | 4 | 127.0 | 17.249 | 22.253 | 10.008 | 4.000 |
| Lower outer rail | 4 | 152.4 | 1.849 | 6.853 | **6.853** | 5.155 |
| Top center | 4 | 127.0 | 17.249 | 22.253 | 10.008 | **0** |
| Top outer | 4 | 127.0 | 6.449 | 11.453 | 10.008 | **0** |
| Upper center rail | 4 | 127.0 | 17.249 | 22.253 | 10.008 | 4.000 |
| Upper outer rail | 4 | 152.4 | 1.849 | 6.853 | **6.853** | 5.155 |

The count is 4 × 4 in, 30 × 5 in and 12 × 6 in bolts, across 24 original
connection duties. All 46 modeled shafts reach the *assumed* barrel-body
center; none exceeds its modeled machine-bore cap. All have provisional head
and washer envelopes. Yet **16 modeled tips end exactly at their bore cap**:
the nominal classification “within bore” does not supply positive tip
clearance. Eighteen rows have 4 mm clearance and twelve have about 5.155 mm.

The **12 outer-rail rows** have the least nominal axial reach: their tips pass
the assumed barrel axis by only 1.849 mm and stop 3.155 mm before the far wall.
Even with a fully threaded shaft, no more than 6.853 mm of the modeled barrel
body can overlap. The **two base-center rows** require the longest threaded
tip span merely to reach the near wall, about 30.353 mm. Neither measure is
actual usable thread engagement. Delivered bolt thread start/runout, barrel
internal thread location/depth, compatible thread form, head/washer dimensions,
tolerances, adequate engagement, wood and hardware resistance, and assembly
access remain unverified. The deep blind bores also need an insertion,
alignment, extraction and rim-withdrawal rehearsal against this **46-pair**
assembly; earlier service probes used the 48-pair composition.

The corrected 6-in
[outer-rail setback probe](../../scripts/owner_barrel_outer_rail_setback_probe.py)
also accepts the current 46-pair assembly as input. Its six-station, 12-bolt
nominal screen found no protected-feature, unrelated-wood or peer-hardware
hits at the current 60 mm setback or read-only 58 and 56 mm setbacks. These
numbers use the same provisional centered barrel thread axis and dimensions:

| Barrel setback from rail butt | Tip past assumed axis | Tip before barrel far wall | Smallest axis/far-wall margin | Probe gate |
| ---: | ---: | ---: | ---: | --- |
| 60 mm (maintained) | 1.849 mm | 3.155 mm | 1.849 mm | Nominal geometry only |
| 58 mm (read-only) | 3.849 mm | 1.155 mm | 1.155 mm | Nominal geometry only |
| 56 mm (read-only) | 5.849 mm | −0.845 mm | −0.845 mm | Far-wall gate fails |

Moving to 58 mm improves axis reach but **reduces** the smallest longitudinal
margin and leaves less wood ahead of each barrel. At 56 mm the bolt tip passes
the modeled barrel far wall; the
[Lowe's Hillman 880543 description](https://www.lowes.com/pd/Hillman-20-x-5-8-in-Slotted-Drive-Zinc-plated-Barrel-Nut/3012559)
says its threaded portion passes through the sides, but does not establish the
usable thread depth, exit geometry, or an installed tip-clearance allowance.
Neither read-only pose is selected or a reach/wood-strength solution. The
60 mm assembly and public viewer remain unchanged pending a qualified hardware
stack and an owner-approved physical revision.

Separately, two left center-rail machine bores cross existing service voids
in the current cut scene. This reach screen does not clear those crossings.
No installed-fit pass, drilling, fabrication, load-test or climbing release
follows from these nominal numbers.
