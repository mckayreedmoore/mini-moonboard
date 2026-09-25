# Provisional complete-layout hardware and stock inventory

The parent ran the frozen inventory consumer against the completed WJ24 object
in 0.434547 seconds. Seven focused inventory tests pass. This report gives
source-bound quantities and modeled blank classes, not a priced purchase list
or approved cut schedule.

The 104 candidate bolts have 104 nuts and 216 physical washer equivalents,
for 424 proposed pieces. Bolt heads are integral, while each of four backer
`top_washer` CAD roles represents three physical washers. This reconciles the
520 CAD roles without treating every role as a purchased part. The twelve
retained frame-bolt assemblies and 66 Hillman screws are separate; 144 removed
SDS axes are not candidate BOM items.

| Proposed bolt group | Axes | Modeled wood grip (mm) |
|---|---:|---:|
| Nominal 6-inch model | 60 | 127 |
| Nominal 8-inch model | 24 | 177.8 |
| Nominal 12-inch backer model | 4 | 270 |
| Catalog length unassigned | 4 | 100.915644 |
| Catalog length unassigned | 8 | 127 |
| Catalog length unassigned | 4 | 167 |

Length groups describe the CAD and recorded stack basis; they do not select
one SKU or establish delivered shank, nut seating, thread engagement, washer
fit, tool access or strength. In particular, no catalog length is invented
for the sixteen center axes. Prices remain null.

The [inventory](inventory.json) covers all 28 connector blanks with source
paths, declared grain, cut basis and raw/finished shape fingerprints. It also
groups the actual ordered receiver pairs into 52 physical interface groups.
Legacy null station fields remain null; this report does not invent duty
ownership from spatial proximity. Whole-stock yield, source stock, machining,
fit, costs and receiving still require completion. All acceptance and release
fields remain false, and no native solve or physical observation is claimed.
