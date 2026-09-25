# WJ12 hardware count and ordinary-joint access boundary

Status: development inventory and review, 2026-09-24. This describes the
[twelve-duty composition](wj12-integrated-static/README.md), not the final
twenty-four-duty bill of materials or a purchasing release.

## Modeled shapes and provisional purchased pieces

| Stack group | Positions | Bolts | Nuts | Washers | Modeled shape roles |
|---|---:|---:|---:|---:|---:|
| Ordinary candidate stacks | 52 | 52 | 52 | 104 | 260 |
| Backer/header candidate stacks | 4 | 4 | 4 | 16 | 20 |
| Candidate total | 56 | 56 | 56 | 120 | 280 |

The provisional candidate count is 232 hardware pieces. Each ordinary stack
has two washers. Each backer stack has one bottom washer and three top
washers; the three top washers share one CAD envelope. Heads and shafts are
separate modeled roles but belong to one purchased bolt. These counts exclude
the twelve retained frame bolts and their hardware, the 66 Hillman screws,
the remaining twelve legacy clips/72 SDS screws, and future replacements.
Exact SKU/length mix, washer products, costs, delivery, and thread engagement
remain unresolved. In particular, the 12-inch backer bolt is not selected.

## Actual full-stock right inner joint

The WJ12 right inner family uses full-section cleats, including the upper
G7 cleat at 88.9 × 88.9 × 86.9 mm in X/T/N, grain N. Its four stacks each
have 127 mm nominal timber grip. All eight inner-family stacks use the
provisional K.L. Jack `25C600HCS5Z` six-inch bolt: 152.4 mm nominal,
149.86 mm minimum delivered-length bound, 127 mm minimum smooth body,
and 133.35 mm maximum thread-gage plane from the existing hardware basis.
The gage plane is not a guaranteed first full-form thread. Neither a length
margin nor a CAD cylinder establishes delivered thread transition or nut
engagement.

The earlier active narrow WJ04 trial has a 95.25 × 38.1 × 119.7 mm cleat,
a 76.2 mm rail grip with a 3.75-inch bolt, and a 133.35 mm principal grip.
Its dimensions, bolt lengths, axes, and access results cannot be transferred
to the full-stock G7 family. Both families use the provisional
`25CNFH5Z` nut and two Type A Wide washer envelopes per ordinary stack;
the exact washer seller SKU is still unselected. CAD bore diameter is not
a shop drill instruction.

The FACOM `34.7/16` tool envelope from the narrow trial can be reused only as
a separately placed geometric proxy. Its old report does not establish
access at the G7 joint, actual jaw fit, hand room, torque, or received-tool
tolerances. The right four-duty integrated report covers installed geometry,
not a complete forward/reverse assembly route.

The [sampled movement report](wj12-right-rail-motion/README.md) moves the upper rail with both attached inner
and outer cleats and their rail bolts, with the four principal/side X bolts
absent. It uses the complete composed obstacle set, excluding only the
source SDS axes already removed by WJ12. The seated pose clears; +25/+50 mm N
samples intersect five wire runs, while negative movement also intersects
panel geometry. A supported panel/wiring staging sequence remains necessary. Panel screws entering the
moving rail must be explicitly absent during that assembly step; cylinder
clearance is not permission to slide engaged wood threads. Separate tool,
hardware insertion, panel/support staging, and individual-part transport
records remain necessary. Sampled clear poses alone cannot prove the path.

The existing stock/cut packet still describes earlier candidate allocations.
It does not provide the full-stock G7/WJ12 blank allocation, yield, cost, or
receiving observations. These must be reconciled when the complete layout
is stable. No observations, assembly acceptance, or structural release are
recorded here.

## Right inner stack dimensional screen

The existing screening allowance is ±0.5 mm per timber layer, giving
126–128 mm combined grip around the 127 mm nominal value. This allowance is
not a received-stock tolerance or observation. Applying the documented washer
and nut bounds gives these coordinates from the bolt's under-head bearing face:

| Coordinate or margin | Screened bound, mm |
|---|---:|
| Timber end | 127.2954–130.0320 |
| Nut bearing face | 128.5908–132.0640 |
| Far nut face | 133.9756–137.8044 |
| Minimum bolt length beyond worst far nut face | 12.0556 |
| Margin after the separate 2.54 mm tip reserve | 9.5156 |

The minimum body bound ends at 127 mm, before the screened timber end.
The maximum gage plane is 4.7592 mm beyond the earliest nut seat. These
catalog bounds therefore establish neither smooth shank through all timber
nor full-form threads throughout the seated nut. Reversing the timber order
changes the shear-plane location but not these nut-face or overall-length
bounds. See the definitions and receiving limits in the
[ordinary hardware basis](../ordinary-hardware-basis.md) and
[ordinary bolt options](wj04-ordinary-bolt-options.md).

Receiving checks must compare the actual first full-form thread and usable
threaded extent with the actual measured stack. The 128.5908 mm earliest
seat is a conservative all-tolerance envelope, not a universal rejection
cutoff for an actual stack whose nut seat lies farther out. No such measured
thread or stack evidence is recorded here.

An unaccepted washer-count sensitivity illustrates why overall bolt length
alone is insufficient. Five total washers put the earliest nut seat at
132.477 mm, still before the 133.35 mm gage plane. Six total washers (one
head-side, five nut-side) move it to 133.7724 mm, while the worst far face
plus the 2.54 mm reserve reaches 148.4724 mm, only 1.3876 mm below the minimum
bolt length. Clearing that gage plane is still not first-full-thread evidence,
and this calculation does not accept a five-washer nut-side stack. No stack,
geometry, or bill-of-materials count has been changed.
