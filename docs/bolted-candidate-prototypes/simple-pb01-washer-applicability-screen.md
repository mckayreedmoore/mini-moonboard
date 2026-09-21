# PB-01 1/4-in washer applicability screen

Status: **source screen only; no qualified washer, metal/wood bearing capacity,
joint rating, or drilling release.** Checked 2026-09-20. Scope is ordinary
Lowe's/Home Depot washers for the PB-01 wood-to-wood through-bolt head and nut
seats. No part was bought, inspected, or submitted to a manufacturer.

## Governing source and edition

[AWC NDS 2024 §12.1.3.3][nds12] calls for a **standard cut washer**, or a metal
plate or strap of equal or greater dimensions, between wood and **each** bolt
head and nut. Its reference to Appendix Table **L6** conflicts with the
published [2024 Appendix, p. 195][ndsl]: **L8** is the standard-cut-washer
table; L6 is roof-sheathing ring-shank nails. L8 lists basic inside diameter,
outside diameter, and thickness starting at **3/8 in** (0.438, 1.000, and
0.083 in). It contains no 1/4-in row. Its footnote sends other standard cut
washers and tolerances to **ANSI/ASME B18.22.1**. The missing 1/4-in row does
not by itself prohibit a compliant 1/4-in washer; it also supplies **no**
1/4-in dimensions to borrow from the 3/8-in row.

[ASME's current B18.21.1 page][asme] says B18.21.1-2009 (R2016) incorporated
B18.22.1-1965 and covers dimensional requirements, physical properties, and
test methods for plain washers. Its [public preview][asme-preview] confirms
revision/consolidation and identifies Type A, Type B, and fender-washer tables,
but does not publish their 1/4-in rows or product certification. Thus the
NDS's legacy B18.22.1 citation can be traced to the consolidated edition;
neither ASME source classifies any retail SKU or makes a similar-sized washer
equivalent to an NDS standard cut washer. A product-specific conformance
statement, applicable ASME table/type and edition, and toleranced dimensions
would be needed for that route. A plate/strap route would need its own
equal-or-greater dimensional and material/bearing substantiation.

## Retail evidence and applicability

| Lead | Confirmed by primary source | Inference and missing proof |
| --- | --- | --- |
| Home Depot [Everbilt 807276][hd-cut] | Listed as **1/4-in hot-dipped galvanized cut washer**, steel, 3/4-in OD, **0.032-in thickness**; called-out 1/4 in is nominal opening/fit, not a toleranced bore. | Retail name is evidence of product description, **not** B18.22.1/B18.21.1 conformance. No cited ASME type/table/edition, ID/OD/thickness tolerances, steel grade/yield strength, or washer bending/bearing resistance. Its listed thickness is about half the 0.065-in PB-01 trial washer; it cannot silently replace that stack. The 3/8-in L8 thickness is 0.083 in, but that is **not** a 1/4-in minimum. |
| Home Depot [Everbilt 807210][hd-wide] | 1/4-in zinc flat-washer retail lead. Home Depot's [generic USS/SAE dimension sheet][hd-sheet] gives a 1/4-in USS pattern of 5/16-in ID, **0.734-in OD**, **0.065-in thickness**; [retailer filters][hd-filter] associate 807210 with 0.734-in OD, 0.065-in thickness, and carbon steel. | The sheet describes a pattern, not SKU tolerances or certification. The trial PB-01 0.065-in stack and ideal annulus follow this pattern conditionally. “Wide”/USS/flat is not documented as an NDS cut washer or equal-dimension plate/strap. No product metal strength or stiffness basis. |
| Lowe's [Hillman 811070][lowes] | 1/4-in hot-dipped galvanized **standard flat** USS washer; listed steel, **3/4-in OD** and **1/16-in thickness**. | Nominal ID is labeled 1/4 in, without actual bore or tolerances. No published B18.22.1/B18.21.1 cut-washer classification, type, steel grade, or bearing/flexure values. Similar OD and thickness to 807210 are not conformance evidence. |

Home Depot's 807276 page calls the part a cut washer while its specification
categorizes it as a flat washer. Those descriptions are not inherently
inconsistent: a cut washer can be flat. The missing applicable dimensions and
conformity basis, rather than the wording alone, reinforce the need for a
product-specific standard statement. The published **0.032-in** thickness is
confirmed as a listing value, not an accepted minimum or metal capacity. No
reviewed Lowe's or Home Depot product source establishes that any of these
three leads conforms to the applicable ASME cut-washer pattern or supplies an
equivalent metal plate/strap design basis.

## Bearing calculation gate

A conditional *wood footprint* can be written as
`A = π/4 × (OD² − max(actual wood-bore diameter, washer ID)²)` only if the
entire annulus bears on sound wood. The 807210 pattern has nominal geometry
for a sensitivity input, as the existing [PB-01 component comparison][pb01]
already does. This is **not** a washer/wood bearing capacity: actual OD/ID
and bore, edge clipping, wood grade and perpendicular-to-grain design value
and adjustments, washer seating, and the load actually delivered to each
washer remain to be established. For 807276, even the actual ID and
toleranced thickness are absent.

A provisional **metal/wood** check also needs a justified washer model and
material properties (at least steel grade/yield or allowable stress and
elastic modulus), toleranced thickness and diameters, bolt-head/nut bearing
footprints, support/contact assumptions, and the relevant axial/prying and
preload demand. None is established for these SKUs. The existing PB-01
positive spring-axial value is a modeled host action, **not** authenticated
washer force. It cannot supply the missing demand or prove full annular wood
contact. No numerical metal capacity or combined metal/wood utilization is
assigned here; a new calculation script would have no reproducible material
or load input to use.

**Disposition:** these are retail leads only. Resolve an exact washer's ASME
classification or a substantiated plate/strap alternative, its product
dimensions/material, delivered stack, and actual PB-01 bearing demand before
revisiting a metal/wood screen. No hardware selection or drilling release.

[nds12]: https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf
[ndsl]: https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf
[asme]: https://www.asme.org/codes-standards/find-codes-standards/b18-21-1-washers-helical-spring-lock-tooth-lock-plain-washers
[asme-preview]: https://www.asme.org/getmedia/9a1bbfb1-e1e5-4b02-b96a-c96f90194dca/22284.pdf
[hd-cut]: https://www.homedepot.com/p/204633086
[hd-wide]: https://www.homedepot.com/p/204284538
[hd-sheet]: https://images.thdstatic.com/catalog/pdfImages/13/1353fc43-4c14-45d4-ba92-5745b045eae3.pdf
[hd-filter]: https://www.homedepot.com/b/Hardware-Fasteners-Washers-Flat-Washers/Same-Day-Delivery/0734-in/100/N-5yc1vZc2ckZ1z1415qZ1z175a5Z1z1bszx
[lowes]: https://www.lowes.com/pd/Hillman-1-4-in-Hot-Dipped-Galvanized-Standard-SAE-Flat-Washer/3037537
[pb01]: simple-pb01-hybrid-component-comparison.md
