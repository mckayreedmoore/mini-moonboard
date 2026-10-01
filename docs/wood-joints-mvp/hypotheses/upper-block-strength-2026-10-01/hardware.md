# Upper-block hardware applicability

The 32 upper axes are a subset of the already replayed
[92-axis hardware requirements](../hardware-material-specification-2026-09-30/requirements.md).
Their outer receiver identities and underhead coordinates must stay bound to
the upper action packets. The existing twelve leg/runner arrangements are
outside this subset.

## Conditional length and shank results

These comparisons assume a full-body 1/4-20 bolt conforming to the stated
ASME dimensional class, with the catalog washer and nut bounds used by the
hardware packet. They do not assert a selected or delivered conforming part.
`LB` locates the last thread scratch; it does not locate the first usable
full-form external thread. The member requirement counts every potentially
bearing thread or runout as threaded.

| Upper cohort | Axes | Required minimum LB (mm) | Conditional class | Class LB minimum (mm) | LB margin (mm) | Physical tip target (mm) | Class minimum length margin (mm) |
| --- | ---: | ---: | --- | ---: | ---: | ---: | ---: |
| 88.9 mm then 38.1 mm receivers | 16 | 119.507 | 6 in | 127.000 | 7.493 | 140.6144 | 9.2456 |
| 38.1 mm then 88.9 mm receivers | 8 | 106.807 | 6 in | 127.000 | 20.193 | 140.6144 | 9.2456 |
| Two 88.9 mm receivers | 8 | 157.607 | 8 in | 171.450 | 13.843 | 191.4144 | 7.2136 |

The requirements use the maximum published 2.032 mm head washer. They apply
the quarter-thread limit separately to each wood bearing interval. Thus the
conditional class minima clear that geometric limit on all 32 upper axes.
This is a useful specification result; it does not need actual receiving
observations to be calculated. Actual conformity remains a separate question.

The lateral comparison's deliberately shorter smooth-body scenarios put the
earliest possible thread/runout at 120.650 mm for the 127 mm grip, and
158.750 mm for the 177.8 mm grip. Those scenarios also clear the respective
quarter-thread thresholds. They are declared scenarios, not profiles inferred
from a catalog length or a gage coordinate.

## Nut travel remains separate

The same hardware requirements give the following sufficient external
full-form coverage intervals across the complete nut-height envelope:

| Wood grip | Required continuous external full-form coverage, underhead (mm) | Conditional class LG maximum (mm) | Earliest nut bearing plane minus LG maximum (mm) |
| --- | --- | ---: | ---: |
| 127.0 mm | 129.5908–136.8044 | 133.350 | -3.7592 |
| 177.8 mm | 180.3908–187.6044 | 177.800 | 2.5908 |

The negative 6 in comparison exposes a travel question. The positive 8 in
comparison does not prove usable engagement. `LG` is a gage coordinate;
neither sign locates the first full-form thread, the transition profile, or
the nut's active internal threads. The functional-fit work owned by the MVP
agent should be applied to these upper cohorts as well as the primary corner.
The sufficient coverage interval above is not an exact active-thread height
or a thread-stripping capacity.

The physical tip target includes a 3.81 mm three-pitch projection beyond the
worst-case nut far face. That length allowance does not require full-form
threads through the tail. Both class minimum lengths can fall short of the
CAD shaft endpoint while still reaching this physical target. The CAD
endpoint therefore cannot substitute for the purchase or engagement check.

## Material and transfer boundaries

The [fastener source screen](../hardware-material-specification-2026-09-30/fasteners.md)
provides a conditional J429 Grade 5 direct-steel yield basis and a J995 Grade 5
nut proof reference. The nut reference presumes its applicable standardized
engagement; it does not rate a short or partly engaged nut. The 6 in upper
lead has a weaker exact-item source path than the Lawson/FalconGrip 8 in lead.
Neither has a source-qualified delivered bolt/nut/washer combination.

NDS-2024 §12.3.6.2 identifies the F1575/F606 methods for the dowel bending
yield input. The 106 ksi value used in the lateral study is an unadopted
Commentary estimate. A J429 minimum tensile yield is not automatically that
input. Chapter 12's tabulated bolt values instead assume 45 ksi bending
yield for their tabulated diameters, starting at 3/8 in. That assumption
does not qualify a quarter-inch bolt; 45 ksi here is a hypothetical
sensitivity, not a source-qualified candidate property.

NDS-2024 §12.1.3.3 requires the standard-cut-washer arrangement under both
head and nut, or the stated dimensional alternative. That installation
provision identifies a detailing route; it does not supply a numeric washer
bending capacity or close coupled axial transfer. The authenticated 2024
appendix places standard cut washers in Table L8; Table L6 covers roof
sheathing nails. Chapter 12's L6 reference is inconsistent with that
appendix. Table L8 lists 3/8 in and larger washers and refers other sizes to
ASME B18.22.1. The quarter-inch `25NWUS` lead instead names ASME B18.21.1
Type A Wide. A supported standard/dimensional crosswalk remains necessary
before asserting that this particular lead satisfies the NDS provision.

The [washer method investigation](../corner-washer-method-investigation-2026-10-01/source-note.md)
also separates a computable conditional metal demand from a supported
material resistance. The upper seat checks establish nominal modeled support
and ideal wood-seat pressure only. Head/nut bearing-face geometry, washer
movement, bending, prying, bolt moment and physical contact remain separate.

## Replay and evidence identity

The parent checked all 32 upper axis IDs against `requirements.json`; they
form exactly the three cohorts above. Reproduce the underlying requirements:

```sh
python3 docs/wood-joints-mvp/hypotheses/hardware-material-specification-2026-09-30/produce.py --verify
```

| Local source | SHA-256 |
| --- | --- |
| Hardware `requirements.json` | `15ec799c4ad02e1f8900537fad56eef2000afec4c9474d0e6c5591017f6ed100` |
| Requirements producer | `2fe71daf2ff49bbefa2105547bdba128f63db7b38644943c5ec7b84bd2c47a10` |
| Upper thread-scenario freeze | `2ac51798bb5814edfe73c315279cfcc0c4ad4100038f6a15c7c1c2c1f04c321b` |
| Official Chapter 12 PDF | `5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a` |
| Official 2024 appendix, September 11 version | `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31` |

The official source is [AWC's 2024 NDS Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf),
PDF pages 3, 17 and 23. Despite its filename, the cached document supplies
specification pages, not the matching Commentary or appendices. The separate
[official 2024 appendix](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website-Appendix.pdf)
was located through AWC's current publication page and checked at PDF page
30, printed page 195. Raw local
sources are required for replay and remain outside the public source packet.
No hardware is ordered, selected, inspected or approved by this evaluation.
