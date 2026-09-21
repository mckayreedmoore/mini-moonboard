# PB01 qualified retail cross-dowel search

21 September 2026. Public-source check only; no contact, purchase, sample, or
fabrication. Question: is a factory **1/4-20 cross dowel sold online by Lowe's
or Home Depot** supported by both a manufacturer-authored, part-specific
dimension drawing (OD, length, cross-hole axis, usable thread engagement) and
a defensible part-specific material specification or strength/test source for
the complete PB01 joint analysis?

**Bounded result: none found.** This is a finding about the public documents
located for the SKUs below, not proof that a part or the joint would fail.
No catalog description, generic nut grade, analogous drawing, or furniture
marketing claim supplies the missing resistance.

| Retail part and direct listing | Public geometry / drawing | Strength evidence and disqualifier |
| --- | --- | --- |
| Lowe's [Hillman 880543][h543], also [Home Depot 880543][hd543] | Hillman's [retailer-hosted answer][ha] gives nominal OD 0.394 in and length 0.630 in, plus 1/4-20. No located Hillman part drawing gives axis offset, tolerances, complete-thread span, or engagement. | Listed as zinc-plated steel; “All-Purpose” is a retail category. No identified grade, minimum material property, proof test, or joint value. Nearest nominal geometric lead, still **unqualified**. |
| Lowe's [Hillman 880544][h544] and [880545][h545]; Home Depot [880544][hd544] and [880545][hd545] | Nominal 3/4-in and 1/2-in lengths respectively, 1/4-20; no located part-specific offset/engagement drawing. The [880544 Q&A][h544qa] repeats the 880543 question and 0.630-in answer; its shared content cannot dimension a 3/4-in part. | Same ungraded steel/finish description; no part-specific strength or PB01 joint result. Different lengths do not cure the information gap. |
| Home Depot [Everbilt 817828][e16], 16 mm Type F; older [50058][e50058] has the same store SKU 458270 | Current listing's 1/4-20 × 16 mm callout and [supplier Q&A][eq] establish thread/nominal length. “1/4 in. diameter” is the thread callout, not a controlled barrel OD. Linked [buying guide][guide] is generic; no located part drawing gives OD limits, axis, or complete-thread span. Legacy 50058 is not an independent qualified geometry source. | Zinc plating and worktable/vibration wording do not identify steel grade, proof load, or assembly resistance. No usable strength source located. |
| Home Depot [Everbilt 817818][e13] (13 mm Type F), [801914][e14] and [801924][e24] (1/4-20 four-packs) | Retail titles identify nominal length only for 817818 and thread for the four-packs. No located SKU drawing establishes the required cross-hole and engagement dimensions. Distinct four-pack models cannot be interchanged by title. | 801914 says zinc-plated steel; no part-specific grade, proof result, or installed-joint value located for any of these. |
| Home Depot **Canada** [Paulin 224-883][p] (3/8 × 5/8 in, 1/4-20) | A separate national retailer lead. Page lists nominal dimensions and says an accessible manual is available upon request; no public part drawing with axis or engagement found. | “Steel” and furniture use are not a material minimum or test result. No public part-specific strength source found. Canadian listing does not establish a US procurement route. |
| Manufacturer comparator: [Stafast JCD14201606 catalog, JC-31][s] | Manufacturer table gives 1/4-20, `L = .630 in`, `L1 = .236 in`, `d1 = .394 in` with a schematic. Catalog says functional dimensions may change and requests a current print for exact dimensions. It does not dimension complete usable threads. | Catalog says steel / quality cold-rolled steel, without a grade, minimum yield/ultimate, proof result, or wood-joint value. No verified retailer-to-Stafast part identity; matching OD and length do **not** identify Hillman or Everbilt stock. |
| Strength-document comparator: [Howmet F1800 sales drawing][howmet] | Manufacturer drawing dimensions the barrel assembly and first-thread datum. Its smallest listed thread is **.2500-28 UNJF**, not 1/4-20; no Lowe's/Home Depot retail listing identified. | Names alloy/heat treatment and tabulates barrel tensile test minima. Shows what part-specific evidence can look like, but its values cannot be transferred to a furniture cross dowel or a complete wood joint. |

Search included retailer dowel-nut categories and individual SKU pages, older
model numbers, Hillman/Everbilt/Paulin part-number PDF queries, and the
Stafast manufacturer catalog. The [Home Depot dowel-nut category][hdcategory]
lists the four current Everbilt models; the separately found Hillman listings
were checked too. This is a bounded searchable-public-record result, not an
inventory claim about every marketplace listing or unpublished manufacturer
record. Product Q&A and buyer photographs were not treated as technical prints.

The Stafast catalog is the closest manufacturer-authored *dimension* source,
but [its own caveat][s] calls for a current print; it cannot be transferred
to a retail SKU without an exact factory-part identity. The [Everbilt generic
buying guide][guide] linked as “From the Manufacturer” is not an 817828
drawing. [AWC TR12][awc] provides general lateral dowel equations and lists
member strength, fastener limits, group action and tolerances separately; it
does not assign a cross-dowel anchorage or thread rating to any SKU here.
A published method for testing barrel nuts would supply a route to evidence,
not a test result for these parts. The [Howmet drawing][howmet] references
NASM1312-32 for its own barrel-nut tensile minimum; that minimum says nothing
about an unidentified retail nut or its installed wood joint.

## Concrete engineering gates

1. For one **exact retail SKU**, obtain a public, controlled factory print
   or equivalent measured low/high limits tied to identified production parts:
   OD, length, insertion-end-to-axis offset, cross-hole orientation, complete
   internal-thread span, minor diameter/chamfers and tolerances. Specify the
   mating bolt's complete threads, washer seat and tip clearance. The retained
   [PB01 geometry screen](simple-pb01-cross-dowel-geometry-screen.md) can then
   test worst-case placement and overlap; it is not a drilling instruction.
2. Establish a traceable minimum barrel material/heat-treatment and thread
   property, part-specific proof/ultimate test, or a bounded qualification
   program for identified factory lots. Geometry measurement alone cannot
   establish steel strength. If none can be obtained without the prohibited
   contact/purchase route, keep this alternative parked.
3. With that evidence, calculate barrel section/bending and thread stripping,
   bolt/washer resistance, actual barrel-to-rail bearing and split/end tear-out,
   rail net section and group effects. Use changed-topology PB01 actions,
   contact and stiffness; do not inherit the corner-block result. Check both
   opposite-face assemblies and protected screw/access envelopes before any
   selection or fabrication release.

No structural selection or failure conclusion follows from this search.

[h543]: https://www.lowes.com/pd/Hillman-20-x-5-8-in-Slotted-Drive-Zinc-plated-Barrel-Nut/3012559
[hd543]: https://www.homedepot.com/p/202242356
[ha]: https://www.lowes.com/questions/hillman-880543-specialty-nuts/3012559/0d07d7d4-94c9-59c7-b300-30a2fd0be7bd
[h544]: https://www.lowes.com/pd/Hillman-1-4-in-x-3-4-in-Plain-Steel-Barrel-Nut/3012562
[h545]: https://www.lowes.com/pd/Hillman-20-x-1-2-in-Slotted-Drive-Zinc-plated-Barrel-Nut/3012565
[hd544]: https://www.homedepot.com/p/202242357
[hd545]: https://www.homedepot.com/p/202242358
[h544qa]: https://www.lowes.com/questions/hillman-880544-specialty-nuts/3012562/0d07d7d4-94c9-59c7-b300-30a2fd0be7bd
[e16]: https://www.homedepot.com/p/204281673
[e50058]: https://www.homedepot.com/p/203088620
[eq]: https://www.homedepot.com/p/questions/Everbilt-1-4-in-x-16-mm-Type-F-Zinc-Cross-Dowel-Nut-817828/204281673/1
[guide]: https://images.thdstatic.com/catalog/pdfImages/ba/bad5940a-010a-45c2-a00c-92934d4b52e5.pdf
[e13]: https://www.homedepot.com/p/204281672
[e14]: https://www.homedepot.com/p/204276112
[e24]: https://www.homedepot.com/p/204276113
[p]: https://www.homedepot.ca/product/paulin-3-8-x-5-8l-inch-slot-drive-cross-dowel-zinc-plated/1000120699
[s]: https://shop.stafast.com/catalogdownloads/downloads.aspx
[hdcategory]: https://www.homedepot.com/b/Hardware-Fasteners-Nuts-Dowel-Nuts/N-5yc1vZ2fkpfot
[awc]: https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf
[howmet]: https://catalog.howmetfasteners.com/Asset/s_F1800-%28%29_C.PDF
