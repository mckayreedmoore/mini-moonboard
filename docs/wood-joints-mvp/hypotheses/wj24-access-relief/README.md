# WJ24 access-relief geometry archive

Status: source-bound geometry diagnostics, updated 2026-09-24. Attempt 03 is
the corrected report for this bounded study. It does not accept a connector,
cut, fastener, LED service path, or structural capacity.

The [attempt 03 geometry report](attempt-03/geometry.json) is bound to WJ24
candidate `compact-floor-flush-wood-joints-development`, source commit
`df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb`, nine source-fingerprint bundles,
and ten geometry trial IDs. Its execution record says the baseline composition
was reproduced exactly and source geometry stayed unchanged; no native solve
ran and release remained false. The [archive manifest](attempt-03/sha256.json)
records read-back SHA-256 and byte size for the geometry, execution record,
producer and test snapshots, and parent launcher. The producer/test snapshots
match the frozen files and the execution pins.

## Attempt history

| Attempt | Result | Record |
| --- | --- | --- |
| 01 | Stopped before geometry generation. The producer incorrectly required the retained family fingerprint keys and trial ID keys to be identical; the real WJ24 composition has nine source bundles and ten trial IDs. The exact-composition replay and source-unchanged checks were true. | [execution](attempt-01/execution.json), [traceback](attempt-01/traceback.txt) |
| 02 | Geometry completed in 50.804 s with exact composition and unchanged sources. Its washer summary incorrectly expected four rows while storing eight role rows, so all-four aggregate flags were false despite every individual seat resolving. Its G7 route also used the radially enlarged envelope for the post-relief route screen. Keep this report as historical diagnostic evidence. | [execution](attempt-02/execution.json), [geometry](attempt-02/geometry.json) |
| 03 | Corrected schema `v2` completed in 55.053 s with exact composition and unchanged sources. Washer reporting now counts eight roles and separates connector-side from other-receiver-side seats. G7 now tests the nominal LED core separately from enlarged envelopes. | [execution](attempt-03/execution.json), [geometry](attempt-03/geometry.json) |

Attempt 03's source snapshots are pinned to producer SHA-256
`619f986f922089cd86b2ae4b10f945345f645df1413215e3352d1329613babd9` and test
SHA-256 `09bbffa778c2fe973d076b29b8188de91bed9b1a42f750e4504b6f37870ccbec`.
The report SHA-256 is
`5c230fbfcf3802918cb425a96840a60eb06eb71ef200b1823446c9961a8f817d` and its
archived size is 1,201,103 bytes. The [manifest](attempt-03/sha256.json) SHA-256
is `b2791dd3bca78129d2a7748fa7cd2750d5a6054316833344635341de360600eb` (1,593
bytes). The attempt 03 directory preserves the parent launcher and exact
producer/test snapshots alongside the report. The pinned focused suite passed
18 tests, and the focused Ruff check and format check passed.

## Attempt 03 geometry findings

Each of the nine variants maps two distinct connector contact faces and fully
supports the 0.05 mm local contact-probe slabs. Each variant has four clear
7.5 mm diameter by 127.2 mm long bore envelopes with exact installed hardware
role sets. The washer audit records eight distinct annular role probes per
connector: four supported on the modified connector and four on the other
receiver. All eight resolve and remain fully supported in both baseline and
variant geometry. These are local contact probes, not bearing pressure or
capacity results.

All section numbers below use sampled 0.1 mm N-normal slabs. A station counts
as changed when its local area reduction exceeds 1e-6 mm². The global
sampled-minimum change is 0.0 mm² for every variant, although local sampled
sections lose material. The report now lists the affected-station count and
largest local reduction explicitly.

| Target | Added radial margin | Finished material removed | Stations with local sampled loss | Largest local section loss (station N) |
| --- | ---: | ---: | ---: | ---: |
| G1 / `bottom_center_right_cleat` | 0 mm | 745.512902 mm³ | 28 | 18.272375 mm² (11.05 mm) |
| G1 / `bottom_center_right_cleat` | 0.5 mm | 996.070910 mm³ | 28 | 24.413503 mm² (11.05 mm) |
| G1 / `bottom_center_right_cleat` | 1 mm | 1,279.566662 mm³ | 28 | 31.361928 mm² (11.05 mm) |
| G12 / `top_center_right_cleat` | 0 mm | 562.789151 mm³ | 25 | 18.272375 mm² (25.65 mm) |
| G12 / `top_center_right_cleat` | 0.5 mm | 751.935883 mm³ | 25 | 24.413503 mm² (24.40 mm) |
| G12 / `top_center_right_cleat` | 1 mm | 965.947382 mm³ | 25 | 31.361928 mm² (24.40 mm) |
| G7 / `wj04_lower_full_stock_cleat` | 0 mm | 319.657955 mm³ | 12 | 28.398264 mm² (30.05 mm) |
| G7 / `wj04_lower_full_stock_cleat` | 0.5 mm | 403.180815 mm³ | 12 | 35.818396 mm² (30.05 mm) |
| G7 / `wj04_lower_full_stock_cleat` | 1 mm | 495.705455 mm³ | 12 | 44.038242 mm² (30.05 mm) |

For G1, the two contact hosts are `base_principal_center_right` and
`base_rail_bottom_right`; G12 uses `base_principal_center_right` and
`base_rail_top`; G7 uses `base_principal_center_right` and
`base_rail_service_lower_right`. The report binds all four candidate axes and
hardware shapes at each target and preserves the fixed 66 panel axes and twelve
frame-bolt arrangements.

G1 and G12 use finite source-bound hold corridors 11.1125 mm in core diameter
and 50.8 mm long. The added radial values enlarge their cutter diameters to
11.1125, 12.1125, and 13.1125 mm. For G7 the nominal physical LED core remains
12.7 mm diameter, 30.25625 mm core length, 19.25625 mm rearward stroke, and
1 mm panel-rear tip clearance: a 49.5125 mm axial sweep. The 0.5 and 1 mm
variants enlarge a separate clearance envelope to 13.7 and 14.7 mm; they do
not enlarge the physical LED.

The nominal G7 core route has no wood hit after each connector relief, but its
straight-run wire proxies `wire_078_G6_G7` and `wire_079_G7_G8` overlap the
screen by 130.522957 and 114.871040 mm³. The larger 0.5 and 1 mm clearance
envelopes also intersect the owning panel `main_lower_right` by 267.985167 and
675.196444 mm³. Those are enlarged-envelope overlaps, not nominal LED-core
collisions. Removing the cleat for a separate service hypothesis removes only
`wj04_lower_full_stock_cleat`, its four reported axes, and 20 CAD role shapes;
the 66 panel axes and twelve frame bolts remain. Its nominal route screen still
shows the same two wire-proxy overlaps. These straight-run proxy intersections
do not establish that a flexible harness cannot be moved, nor do they prove a
workable service sequence.

## Bounded next geometry hypothesis

Carry the zero-added-radial-margin case forward as the smallest of these three
geometry hypotheses for a tolerance and fit study. It removes the least
material and avoids the G7 panel overlap caused by the larger envelopes.
Treat 0.5 and 1 mm only as sensitivity cases. Zero added margin does not
establish usable clearance: no tolerance stack, delivered fastener or LED
dimensions, fabrication method, physical inspection, wire handling sequence,
temporary support, or structural adequacy is established. The geometry remains
conditional and no cut or drilling is released.
