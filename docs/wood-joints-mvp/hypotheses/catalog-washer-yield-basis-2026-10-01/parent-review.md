# Parent disposition of catalog washer material options

Checked October 1, 2026. The parent asked the author to correct a prerequisite
that was too restrictive: a manufacturer material statement covering the
catalog fitting can support a conditional yield input even when the SKU row
does not repeat a numeric yield. A delivered-lot certificate or new physical
test is not a blanket prerequisite to that comparison.

Parent directly inspected the rendered official
[P1062 specification sheet](https://ideadigitalasset.com/DAMRoot/Original/10033/11163_P1062.pdf),
SHA-256 `8416c503fb6396e389500106ed88e840f7e3bd749d33dbb6b57367e7e4b0e14e`.
Its general steel clause and P1062 table are on the same sheet. The named
steel fitting has no contrary item note; the applicable Grade 33 physical
requirements provide an option-level material floor. The nominal square
width, bore and thickness differ substantially from the current washer.

Parent also inspected Eaton's official
[fittings catalog](https://www-dev.eaton.com/content/dam/eaton/products/support-systems/strut-systems-%26-accessories/strut-fittings-and-accessories/strut-fittings-catalog-section.pdf),
printed pp. 106–107. The opening material default gives 33,000 psi minimum
yield unless noted; the B200 page expressly refers to those general fitting
and finish specifications and includes zinc as a standard finish. Treating
zinc alone as a reason to discard the base-steel default was unsupported.
This is an inference mapping the catalog default to the steel/zinc B200
option, with no delivered-part conformity claim.

Use **33,000 psi = 227.527 MPa** when converting that imperial floor.
The paired SI Grade 33 [230] value in the
[steel producer's property table](https://d1io3yog0oux5.cloudfront.net/_5ef3fcce137dc523a6c7a1e39a5194c2/clevelandcliffs/db/1190/10480/file/CLF_ProductData_HotRolled_062025.pdf)
is a dual-standard designation, not an exact conversion permitting the
imperial material input to be rounded upward to 230 MPa.

The parent additionally checked the existing hash-pinned B18.2.1 mirror:
its head washer-face gauge is in §4.3, printed p. 9; §4.5 concerns the fillet.
The gauge lies 0.004 in toward the head from the bearing plane. The
[bearing-face input disposition](../washer-bearing-footprint-inputs-2026-10-01/parent-review.md)
records why it does not establish the actual head contact patch. Any nominal
annulus comparison using that diameter remains a declared face scenario.

The revised [source review](source-review.md) and
[independent review](independent-review.md) distinguish these conditional
option inputs from current hardware acceptance. No screened part has been
selected, installed or purchased. These floors cannot be assigned to
`25NWUS` or the PS 619 variant. Larger square plates still need actual seat,
hole/face, stack, tool and metal/contact analysis; changing the reviewed
hardware/model would require reporting the changes first. This packet
supplies no washer capacity, physical inspection or joint pass.
