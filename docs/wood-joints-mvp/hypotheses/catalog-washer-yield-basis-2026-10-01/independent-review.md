# Independent review: conditional catalog washer yield floors

Reviewed October 1, 2026. I reviewed the final `source-review.md` (SHA-256
`2035ce1e66cd5ecbb3538effd9e04040257474e9d80273ffe3096d356bd53262`),
`parent-review.md` (SHA-256
`df9f848e717aa0dd5d6cc68bd5fad6a85a97c2fad90a952e22136faf4730a446`), the
washer-bearing footprint disposition, and the cited manufacturer source
documents. The sources support conditional family-floor inputs for
option-level demand comparisons. They do not establish an exact delivered
part, geometric compatibility, actual contact, or washer-bearing resistance.

## Manufacturer source check

**Eaton B200.** I read the official [B-Line catalog section](https://www-dev.eaton.com/content/dam/eaton/products/support-systems/strut-systems-%26-accessories/strut-fittings-and-accessories/strut-fittings-catalog-section.pdf), not just its search
excerpt. Its opening p. 106 says the fitting family is hot-rolled, pickled
and oiled steel to ASTM A1018 with 33,000 psi minimum yield unless noted.
The same page lists ZN as an electro-plated-zinc finish and identifies its
finish specification separately. On p. 107, the B200 row lists a 3/8-in
hole and 5/16-in bolt size, and directs the reader to p. 106 for general
fitting and finish specifications. Eaton's exact `B200-1/4ZN` page calls it
a square washer, 1.625 in square by 0.25 in thick, material steel; it does
not publish a contrary base-metal property or exception. This supports
33,000 psi as a **conditional source-covered floor for an option-level B200
demand comparison**, provided the catalog mapping and standard-fitting
assumption are stated. The [exact Eaton SKU sheet](https://www.eaton.com/us/en-us/skuPage.B200-1%7B%7D4ZN.pdf)
does not certify a specific lot.

**Atkore P1062.** I fetched and read Atkore's official one-page [P1062
specification sheet](https://ideadigitalasset.com/DAMRoot/Original/10033/11163_P1062.pdf)
from its linked product page. Its SHA-256 was
`8416c503fb6396e389500106ed88e840f7e3bd749d33dbb6b57367e7e4b0e14e`.
The sheet's general material clause says fittings, unless noted, are made
from specified hot-rolled steels and that fitting steel also meets the
physical requirements of ASTM A1011 SS Grade 33. Its dimensional table lists
P1062 as a 5/16-in bolt-size fitting with an 11/32-in hole; the sheet gives
the standard 1-5/8-in width series. No P1062 material exception is shown.
This supports a **conditional Grade 33 property floor for option-level
demand comparison**, not a delivered certificate or an exact-lot grade
claim. The adjacent Atkore hardware catalog separately shows P1062 EG and ZD
entries and Power-Strut item 720881 / PS 619 / 1/4-in rod / 11/32-in hole.
That listing does not extend Unistrut's material floor to the distinct
Power-Strut item.

## Boundaries and disposition

The conditional floors are useful without requiring receipt or inspection of
a replacement part first. The old Type A Wide `25NWUS` still has no numeric
yield statement, and neither strut fitting matches its compact round
geometry: P1062 and B200 are listed for 5/16-in bolt size, with 11/32-in and
3/8-in bores respectively, and a 1-5/8-in square footprint. PS 619's 1/4-in
rod configuration also has an 11/32-in bore but no numeric material yield
floor in its Power-Strut material listing. The current washer's actual
compatibility and support, seating/contact area, pressure distribution,
retention, and strength remain unproved.

The head-circle comparison must remain a scenario. B18.2.1 §4.3 measures the
cap-screw washer-face diameter 0.004 in toward the head from the bearing
plane; that 10.0127–11.1252 mm gauge-circle range is not the actual
head-to-washer contact-plane profile. The footprint parent disposition
properly leaves this profile and actual nut/washer contact unresolved.

The earlier source-review draft made an exact SKU/drawing and part-specific
yield appear necessary to close the source screen. The final version correctly
allows the conditional family floors for option-level demand comparison
without a lot certificate or test. Exact product evidence remains necessary
for claims about a selected or supplied part.

The parent disposition resolves the two source-correction findings from my
initial review: the B18.2.1 washer-face gauge is correctly attributed to §4.3
(printed p. 9; §4.5 addresses the fillet), and 33,000 psi is converted to
227.527 MPa rather than rounded upward to 230 MPa. The latter remains the
separately published paired SI Grade 33 designation, not an exact conversion.
I find no remaining material source-interpretation issue in the final
source-review. Its family floors remain conditional and do not establish
delivered-lot conformity.

No material value is transferred to `25NWUS`; no geometry is adopted; no
contact area, pressure, resistance, or joint pass is inferred.
