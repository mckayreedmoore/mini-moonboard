# Catalog washer yield-basis source review

**Checked:** 2026-10-01. **Status:** option screen only. No washer is selected,
no strength or bearing capacity is assigned, and no material value is
transferred to the current `25NWUS` washer. No vendor was contacted and no
part was purchased.

## Finding

Atkore’s general Unistrut fitting clause and Eaton’s general B-Line clause
support conditional source-covered steel yield floors when mapped to their
listed catalog fittings. These are manufacturer-published family minima, not
delivered-lot certificates. P1062 and B200 remain oversized square items
cataloged for 5/16-in rod/bolt use. Power-Strut `PS 619` has a 1/4-in rod
variant with an 11/32-in bore, but its material listing does not specify a
numeric yield minimum. RAYCHIN publishes a minimum yield value for its 254
SMO washer family but not an exact orderable part number and dimensional
schedule. No screened option establishes a compact round washer with an exact
1/4-in SKU and item-specific yield table; the Atkore and Eaton conditional
floors can still support option-level demand comparisons under the stated
catalog scope.

## Manufacturer catalog options screened

| Catalog option | Manufacturer-published item and geometry | Material/yield evidence | Fit and evidence limit |
| --- | --- | --- | --- |
| Unistrut `P1062 EG` | Atkore’s General Engineering Catalog #1607 lists `P1062` for a 5/16-in rod with an 11/32-in hole, in the 1-5/8-in-wide washer family. The catalog identifies these as core products typically available from stock. The official Atkore hardware table identifies standard EG and ZD `P1062` entries. | Atkore’s general Unistrut material clause applies to fittings unless noted otherwise: it lists allowed steel specifications and states **all fittings meet or exceed ASTM A1011 SS Grade 33 physical requirements**. P1062 is listed as a fitting and has no contrary material note. ASTM A1011/A1011M-25 identifies structural Grade 33 [230 MPa] and yield-strength requirements; Cleveland-Cliffs’ hot-rolled product sheet gives the Grade 33 minimum yield as 33 ksi / paired 230-MPa designation. Converting 33,000 psi gives 227.527 MPa. This supports a **conditional P1062 fitting-family floor of 33,000 psi (227.53 MPa)** for option-level demand comparison. It is not a delivered-lot certification. | `P1062` is a 5/16-in rod size, not the 1/4-in variant. The 11/32-in bore is 8.731 mm, larger than the 1/4-in nominal bolt size. The 1-5/8-in square is 41.275 mm across, over twice the current washer’s approximately 18.6-mm OD; wood support and stack compatibility are unverified. |
| Power-Strut `PS 619 1/4 EG` (catalog item `720881`) | Atkore’s Power-Strut catalog lists the 1/4-in rod-size variant with an 11/32-in hole; the current Atkore Hardware sheet identifies `720881`, `PS 619`, 1/4-in rod, 11/32-in hole, EG finish. The catalog says to order by number, size, and finish, so this is a catalog configuration rather than a custom drawing. | Power-Strut’s material page says 1/4-in nominal-thickness fittings are ASTM A575/A576 and that **some** 1/4-in fittings use A36; it does not identify PS 619 as one of those A36 parts. No numeric yield floor for the PS 619 material listing is established, so no yield input is assigned to this variant. | Same 8.731-mm bore and 41.275-mm square-width class as the Unistrut plate. Using a declared 10.0127-mm circular face-diameter scenario, the nominal centered radial annulus is 0.641 mm before tolerances. This is not an actual B18.2.1 contact patch or a safe-seating/retention determination. |
| Eaton B-Line `B200-1/4ZN` | Eaton’s SKU page and attached specification sheet identify a standard square washer, 1.625 × 1.625 in and 0.25 in thick, material “Steel.” Eaton’s B-Line catalog lists the B200 hole as 3/8 in and identifies 5/16-in bolt size. | Eaton’s general B-Line page opens with the default that fittings are hot-rolled, pickled-and-oiled steel to ASTM A1018 with **33,000 psi minimum yield unless otherwise noted**. `B200-1/4ZN` is a B-Line square-washer SKU, and its product sheet says steel without a contrary base-metal exception. The catalog lists zinc treatment as a finish; that finish designation alone does not remove the general base-steel floor. Treat 33,000 psi as a **conditional source-covered floor for the B200 option**, while leaving delivered-lot conformity unasserted. | The 9.525-mm B200 bore is larger than the 1/4-in nominal bolt. Using a declared 10.0127-mm circular face-diameter scenario, the nominal centered radial annulus is 0.244 mm before tolerances. This is not an actual B18.2.1 contact patch or a safe-seating/retention determination. Its 41.275-mm square footprint is much larger than the current washer. |
| RAYCHIN 254 SMO USS family | RAYCHIN states that it offers 1/4-in-and-larger USS washers in standard thickness series, manufactured to ASME B18.22.1, and also offers custom dimensions. It does not publish a part number or a 1/4-in washer’s bore, OD, and thickness limits on the cited page. | RAYCHIN publishes minimum room-temperature `Rp0.2 ≥ 310 MPa` (`≥45 ksi`) for solution-annealed 254 SMO / UNS S31254 material, citing ASTM A479 / EN 10088-3. | This is a material-property lead, not an exact catalog item. The page includes both standard and custom offerings and directs the reader to request a quote; it does not establish which exact dimensions, SKU, production route, price, or stock status would be supplied. Compatibility with the current washer envelope remains unverified. |

## Dimensional comparison

The current ordinary washer basis is K.L. Jack `25NWUS`, plain low-carbon
steel, ASME B18.21.1 Type A Wide: ID 0.307–0.327 in, OD 0.727–0.749 in,
thickness 0.051–0.080 in. Its product listing supplies no numeric yield
minimum; the [existing ordinary nut/washer property basis](../../current-ordinary-nut-washer-property-basis.md)
records that limit. The current washer geometry used for comparison has an
OD near 18.6 mm. The published 1/4-in B18.2.1 head measurement interval is
10.0127–11.1252 mm, but this dimension is measured 0.004 in above the
bearing face and does not bound the actual contact patch. For the plate
comparisons, 10.0127 mm is only a declared circular-face scenario diameter;
it is not an actual or minimum bearing-face diameter.

Both 1-5/8-in-square strut plates have an overall width of 41.275 mm and a
nominal thickness of 6.35 mm. The Atkore 11/32-in hole is 8.731 mm; the
Eaton 3/8-in hole is 9.525 mm. The P1062 and Eaton B200 catalog entries
identify 5/16-in rod/bolt sizes; Power-Strut separately lists a 1/4-in PS 619
rod-size variant using the same 11/32-in bore. The centered annulus values
above compare these bores against the declared circular-face scenario only.
They are not actual contact footprints or pull-through checks and do not
address head or nut chamfers, washer flatness, wood support, or tolerances.

RAYCHIN’s separate 254 SMO washer page is the only screened round-family
source with a direct numeric minimum-yield statement. Its family-level
availability claim is not a specific purchasable configuration: the page
does not bind the yield statement to a 1/4-in SKU with dimensions inside the
current Type A Wide envelope. The earlier
[ordinary-size washer yield option note](../../washer-property-options/ordinary-washer-yield-options.md)
records this same limitation.

## Source boundary and next input

Primary manufacturer sources consulted:

- [Atkore Unistrut General Engineering Catalog #1607](https://dam.atkore.com/api/public/content/ee6a51c1ef8a4a56b40450e1a04dde68?v=eb3a1f1d), flat plate fittings and material sections. It lists P1062 geometry, the `core products typically available from stock` designation, allowed fitting-steel specifications, and the general ASTM A1011 Grade 33 physical-property floor. Atkore’s [P1062 family page](https://www.atkore.com/products/strut-and-fittings/p1062-p1063-p1064-p1964-p2471-and-p2490) links a [P1062 specification sheet](https://ideadigitalasset.com/DAMRoot/Original/10033/11163_P1062.pdf) with the same size/part table and general material clause.
- [Atkore Hardware catalog](https://dam.atkore.com/api/public/content/be8597330506494f8004955d7cdbe6e2?v=2ef5fbe7), square-washer table, including P1062 finish variants and Power-Strut `720881 / PS 619 / 1/4 / 11/32 / EG`.
- [ASTM A1011/A1011M-25](https://store.astm.org/a1011_a1011m-25.html), active standard whose public abstract identifies structural Grade 33 [230 MPa] and yield-strength requirements; Cleveland-Cliffs’ [hot-rolled steel product data sheet, Table 2](https://d1io3yog0oux5.cloudfront.net/_5ef3fcce137dc523a6c7a1e39a5194c2/clevelandcliffs/db/1190/10480/file/CLF_ProductData_HotRolled_062025.pdf) gives the 33-ksi minimum alongside the paired Grade 33 [230 MPa] SI designation; 230 MPa is not the exact conversion of 33,000 psi.
- The pinned-mirror clause check in [parent-review.md](parent-review.md) identifies B18.2.1-2012 §4.3, printed p. 9, for the washer-face measurement 0.004 in from the bearing-surface plane toward the head. That dimension does not specify the actual contact patch; §4.5 concerns the fillet.
- [Power-Strut Engineering Catalog](https://powerstrut.com/Power-Strut-Catalog_2017.pdf), p. 10, `Materials`, says 1/4-in nominal-thickness fittings are ASTM A575/A576 and only some are A36; p. 50, `PS 619 – Square Washer`, lists 1/4-in rod, 11/32-in hole and directs ordering by number, size, and finish.
- [Eaton B-Line B200-1/4ZN product page](https://www.eaton.com/us/en-us/skuPage.B200-1%7B%7D4ZN.html) and its [specification sheet](https://www.eaton.com/us/en-us/skuPage.B200-1%7B%7D4ZN.pdf), which identify 1.625-in square × 0.25-in thick and steel, but no bore or steel grade on the SKU sheet.
- [Eaton B-Line strut-fittings catalog section](https://www-dev.eaton.com/content/dam/eaton/products/support-systems/strut-systems-%26-accessories/strut-fittings-and-accessories/strut-fittings-catalog-section.pdf), p. 106 general default of 33,000-psi minimum yield unless otherwise noted and p. 107 B200 3/8-in hole, 5/16-in bolt size, and reference to the general material/finish specifications.
- [Eaton B-Line material and finish statement](https://www.eaton.com/us/en-us/catalog/support-systems/strut-fittings-and-accessories.html), which states the general 33,000-psi ASTM A1018 minimum-yield basis and lists electro-zinc finish standards separately.
- [RAYCHIN 254 SMO flat-washer page](https://www.ray-chin.com/Special-Fasteners/254-SMO-Fasteners/254-SMO-Flat-Washers.html), 254 SMO family, standard size range, material condition, and minimum `Rp0.2` table.

For an option-level metal-demand comparison, map each SKU to its applicable
manufacturer material clause and use the conditional floors supported above.
This does not assert delivered-lot identity or conformity and does not require
a new lot certificate or test for the source comparison. The strut plates
still require geometric review of their actual hole, fastener bearing
surface, wood support footprint, and stack access before they could be
considered as washer options. Neither yield data nor a geometric fit screen
alone establishes washer-metal resistance or joint acceptance.
