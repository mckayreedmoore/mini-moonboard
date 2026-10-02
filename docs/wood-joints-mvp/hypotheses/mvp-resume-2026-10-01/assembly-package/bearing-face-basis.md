# Head and nut bearing-face basis

**Checked:** 2026-10-02. **Decision:** the purchased-policy routes do not yet
establish the assumed 10 mm rail / 12 mm side flat bearing circles at both
washer interfaces. This finite source investigation closes with the exact
missing dimensions below; it does not qualify hardware or joint resistance.
The current radial-strip maximum, **198.152610 MPa**, remains a required
washer stress under the declared footprints; washer `Fy` is unqualified.
See [hardware engagement](hardware-engagement.md) and
[top-corner fit](../top-corner-hardware/assembly-fit.md).

## Evidence and circle requirements

Dimensions are diameters, not radii. Catalog declarations, conditional
standard geometry, and observed hardware are separate evidence levels.

| Interface / policy route | Required flat circle | Primary evidence / source | Supported dimension and disposition |
| --- | ---: | --- | --- |
| Rail head: 1/4 in Grade 5 partially threaded hex cap screw; existing Lawson `FA21103` route | 10 mm | [Lawson listing](https://www.lawsonproducts.com/products/hex-cap-screw-grade-5-1-4-20-x-8-fa21103); pinned B18.2.1-2012 §4.3 and Table 6, printed pp. 9–10 | Conditional washer-face **gage-plane** minimum 0.3942 in = **10.01268 mm**, only 0.01268 mm above the assumption. The actual flat bearing-plane OD and its centering are not established. |
| Side head: 5/16 in Grade 8 partially threaded cap screw, Bolt Depot `28650` | 12 mm | [Exact listing](https://boltdepot.com/Product-Details?product=28650), B18.2.1/J429; same standard clause/table | Conditional washer-face **gage-plane** minimum 0.4500 in = **11.43000 mm**, **0.57000 mm below** the assumption. Standard conformity alone cannot support 12 mm; no exact flat-circle guarantee is listed. |
| Rail nut: 1/4-20 J995 Grade 5 finished hex, Bolt Depot `2569` or K.L. Jack `25CNFH5Z` | 10 mm | [2569](https://boltdepot.com/Product-Details?product=2569); [pinned K.L. Jack source record](../../hardware-material-specification-2026-09-30/fasteners.md#source-record) | Bolt Depot lists B18.2.2/J995 and 0.428–0.438 in across flats, but no flat bearing-circle minimum, face style, or countersink envelope. K.L. Jack's pinned record likewise supplies no circle; live page was unavailable. **Unknown.** |
| Side nut: 5/16-18 J995 Grade 8 finished hex, Bolt Depot `2583` | 12 mm | [2583](https://boltdepot.com/Product-Details?product=2583) | B18.2.2/J995 and 0.489–0.500 in across flats are listed; flat bearing-circle minimum, face style, and countersink envelope are absent. **Unknown.** |
| Rail washer: low-carbon USS `2994` | Real opening within the 10 mm footprint | [2994](https://boltdepot.com/Product-Details?product=2994) | ID 7.7978–8.3058 mm; OD 18.4658–19.0246 mm; thickness 1.2954–2.0320 mm. These are catalog bounds, not measurements. No numerical `Fy` is listed. |
| Side washer: low-carbon USS `2995` | Real opening within the 12 mm footprint | [2995](https://boltdepot.com/Product-Details?product=2995) | ID 9.3980–9.9060 mm; OD 22.0472–22.9870 mm; thickness 1.6256–2.6416 mm. These are catalog bounds, not measurements. No numerical `Fy` is listed. |

## What the standard actually establishes

The existing [B18.2.1 source pin](../../../bolt-dimension-source-correction.md)
matches `/tmp/thread-gage-functional-fit/ASME-B18.2.1-2012-mirror.pdf`:
SHA-256 `4c7bcb75223b7e89fc27f132bc44e8b422ba672c97f7803259a24fab6bd99ba0`.
Section 4.3 and Tables 6/10 were read directly from that copy; Table 6 was
also checked against the existing rendered page. The
[publisher record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws)
identifies B18.2.1-2012 (R2021); its public page does not expose these tables.

Section 4.3 explicitly sets washer-face diameter to Table 6's maximum
across-flats dimension with a −10% tolerance: `0.90 × 0.438` and
`0.90 × 0.500` in. This is a specified circular feature, not an inscribed
circle inferred from a hexagon. Its measurement plane is **0.004 in
(0.1016 mm) toward the head from the bearing plane**. Therefore neither
computed minimum is adopted here as an actual flat contact-circle minimum.
The §4.2 top chamfer circle is a different feature and supplies no underside
contact guarantee. Supplier standard callouts do not inspect delivered parts.

Section 4.5/Table 10 also limit the long-screw fillet: Style 1 radius maxima
are 0.025 in; Style 2 transition-diameter maxima are 0.300 / 0.362 in
(7.6200 / 9.1948 mm) for 1/4 / 5/16 in. These inner limits are distinct
from the missing outer flat diameter; actual alignment with the washer hole
and the chosen face profile still need a supported contact interpretation.

No inspectable pinned B18.2.2 numerical bearing-circle table was located.
The [ASME B18.2.2-2022 record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts)
does not expose it. Existing supplier references
[Value Fastener, printed p. 114](https://www.valuefastener.com/documents/products/nutsfinishedgr5-8.pdf)
and [Global Supply, §1.0](https://globalsupplyinc.com/wp-content/uploads/2023/11/Finished_Hex_Nuts_11-7-23.pdf)
show flats/corners/thickness only. Those are generic alternative catalog
families, not conformity evidence for Bolt Depot or K.L. Jack. No nut-circle
minimum or deficit is invented from those dimensions.

## Effect on the saved current washer comparison

The parent reused all 48 simultaneous states in
`../corner-component-attempt05/component-results.json`, SHA-256
`1e163479d8ed80a353a133bd234fe5e4b069470756f42c922051aef512d73648`.
As an **illustrative circle-size sensitivity only**, inserting the gage-plane
diameters as if they were flat contact diameters gives:

| Family / 24 states | Declared circle and peak strip stress | Illustrative circle and peak strip stress | Governing same-state tuple |
| --- | ---: | ---: | --- |
| Rail | 10 mm / 198.152610 MPa | 10.01268 mm / 197.398018 MPa | K12-right, right `rail_1` on `clip_single_top_right_2` |
| Side | 12 mm / 94.805918 MPa | 11.43 mm / 109.046400 MPa | K12-rear, right `side_2` on `clip_single_top_right_2` |

This arithmetic preserves each state's pressure, catalog outer-radius bound
and minimum washer thickness. With `r=d/2` and the unchanged outer radius `R`,
strip stress is proportional to
`K(r)=((R³-r³)/3-r(R²-r²)/2)/r`; each saved stress is multiplied by
`K(r_new)/K(r_old)`. Rail `R=0.749*25.4/2 mm`, side
`R=0.905*25.4/2 mm`. This reproduces the existing radial-strip model without
another frame or CAD run. Independent peaks are not combined.

The gage-plane minima are **not adopted flat contact diameters**, so the
illustration does not replace the original 198.152610 MPa requirement or
establish available washer resistance. The 0.57 mm side dimensional gap
alone does not demonstrate a failed part or justify changing hardware.
Actual contact profiles and washer material remain the deciding inputs.

## Finite next action

Obtain an exact-item dimensional guarantee or a recorded measurement for
each head and installed nut face: a flat annular face containing the model's
10 / 12 mm outer circle about the bolt axis, with the inner fillet/countersink
and centering envelope reconciled to the actual washer opening. Give no
pressure credit over the hole. The side-head request must explicitly cover
the model's 12 mm assumption, or supply the smaller actual profile, because
the standard gage minimum does not guarantee that circle. If the documented
footprint is smaller or noncircular, return that input to main for a supported
washer-contact calculation; the present stress cannot be transferred.
Washer yield remains a separate exact material datum. No head/nut capacity,
hardness-to-yield conversion, delivered observation, or release is assigned.
