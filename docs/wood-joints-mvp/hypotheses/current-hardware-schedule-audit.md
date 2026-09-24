# Current trial hardware schedule audit

**Status: planning audit only.** This is a count of provisional bolt positions
and envelopes in separate geometry trials. It is not a purchase list, selected
hardware schedule, fit result, or capacity assessment. Nominal envelope length
does not establish delivered length, thread transition, or nut engagement.

## New trial positions in the current schedule

| Trial source | Positions | Modeled hardware / length basis | Unresolved purchase facts |
| --- | ---: | --- | --- |
| [WJ-03 compact tool trial](wj03-compact-outer-tools.md) | 20 | Ordinary 1/4-20 through-bolt envelopes: 12 × 6 in and 8 × 8 in | Grade, SKU, supplier, delivered length, thread transition, washer, and nut selection are open. |
| [WJ-05 backer transfer](../wj05-center-backer-transfer.md) | 4 | Ordinary 1/4-20 through-bolt envelopes, 12 in | No SKU or grade selected; length and thread engagement remain receiving conditions. |
| [WJ-05 relieved center-node trial](wj05-center-node-relieved.md) | 16 | 1/4-in body envelope; no nominal bolt length assigned. Its 113.133, 139.217, and 179.217 mm values are under-head length screens, not catalog lengths. | SKU and bolt class are null; detailed hardware quantities and fit remain open. |
| [WJ-04 upper G7 crosscut archive](wj04-upper-g7-crosscut.md) | 8 | 127 mm grip; provisional 6-in `25C600HCS5Z` partially threaded cap-screw envelope | Hardware is not selected or received; 6 in is the provisional modeled length. Thread transition, full nut engagement, and access remain unresolved. |
| [WJ-06 outer pair](wj06-outer-pair.md) | 8 | Four 127 mm-grip, 6-in `25C600HCS5Z` cap-screw model envelopes; four 177.8 mm-grip, 8-in ordinary-bolt envelopes | Side bolt [Forces F086013](https://shop.forcesinc.ca/products/hex-head-bolt-1-4-20-x-8-partial-thread-plain-steel-grade-5) is a catalog lead only: unselected and unreceived. The model's 6.35 mm shaft is not a SKU fit result. |
| **Subtotal** | **56** | All nominally 1/4-20-class positions | This is only the positions itemized above; 12 retained frame bolts are excluded. |

Use the G7 crosscut archive for the current eight-position WJ-04 pair. Its
preserved predecessor, [`wj04-upper-pair-probe.json`](wj04-upper-pair-probe.json),
is historical and is not an additional schedule row. The broader 104-new-bolt
project projection has 48 positions beyond this 56-position subset; those
positions need their own sourced geometry and must not inherit these length or
hardware labels.

## Separate WJ-03 procurement baseline

The preserved [WJ-03 procurement note](../wj03-hardware-procurement.md) lists
20 ordinary zinc-plated hex bolts as 8 × 6-in Bolt Depot #10 and 12 × 8-in
Bolt Depot #14, both vendor-described Grade 2 or A307A. It also lists 20
Grade 5 hex nuts (#2569) and 40 USS washers (#15021) as dimensional candidates.
Those counts belong to that procurement baseline, not the newer compact
geometry trial above: the newer trial models 12 × 6-in and 8 × 8-in generic
bolts. Neither note selects or receives the listed parts, and neither count
should be added to the 56 trial positions.

## Nut, washer, and diameter planning

If the 56 through-bolt positions each retain one nut, the arithmetic is 56
nuts; no common nut SKU is selected across these trials. Two washers per
position would be 112 washers. The WJ-05 backer model explicitly uses one
head-side washer and three nut-side Type A washers at each of its four bolts,
adding eight above a two-washer-per-bolt assumption. That makes 120 a
**conditional planning estimate**, not an established BOM: the WJ-05 center
trial records head- and nut-washer seat support but does not define its washer
parts list. The WJ-03 baseline's 40 USS washers and the WJ-04 Type A Wide
dimensional candidate also remain unselected; a washer seller SKU is open.

Keep ordinary hex bolts distinct from hex cap screws. WJ-04 G7 and WJ-06 rail
share a provisional 6-in `25C600HCS5Z` cap-screw model (12 positions), a useful
single-candidate procurement lane to evaluate after the open thread, assembly,
and access checks close. The WJ-03 generic 6-in ordinary bolts are a different
class. WJ-03's eight generic 8-in ordinary positions and WJ-06's four 8-in
ordinary positions have the same 177.8 mm modeled grip, so `F086013` could be
screened as one shared lead for those twelve; it is not selected or received,
and WJ-03 has no nominated SKU.

The cap-screw product envelope used in the WJ-04 basis has a published maximum
body diameter of 6.35 mm. The ordinary-bolt dimensions in [ASME B18.2.1,
Table 2](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws)
permit up to 0.260 in (6.604 mm) body diameter for the 1/4-in nominal size.
Run an ordinary-bolt geometry sensitivity at 6.604 mm where ordinary bolts
are evaluated; this is an envelope check only. It does not change the nominal
1/4-in design diameter, the nominal bore, or any fastener capacity.

Sources: [WJ-04 ordinary hardware basis](../ordinary-hardware-basis.md),
[WJ-03 hardware procurement basis](../wj03-hardware-procurement.md),
[WJ-05 center-node report](wj05-center-node-relieved.json), and
[WJ-06 materialized stack report](wj06-outer-pair.json) and its
[producer's hardware-source declaration](../../../scripts/wood_joint_wj06_outer_pair_probe.py).
