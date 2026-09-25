# Six-inch cap-screw dimension source correction

Status: source-attribution correction, 2026-09-24. The modeled six-inch
1/4-20 cap-screw bounds remain `Lb ≥ 127 mm` and `Lg ≤ 133.35 mm`.
This note corrects their attribution; it changes no geometry, product
selection, capacity, or inspection record.

The [Nickel Systems partial-thread table](https://www.nickel-systems.com/wp-content/uploads/2025/01/Hex-Head-Cap-Screws-Partially-Threaded-Minimum-Body-Maximum-Grip-Gaging-Lengths-1.pdf)
labels its entries `Lb min / Lg max`, but the six-inch, 1/4-inch cell visibly
prints `5.25 / 5.00`. That row cannot support the stated ordering. Parent
checked the rendered PDF, not only its extracted text. Do not silently swap
the supplier's printed values and call them a faithful transcription.

The inspected **ASME B18.2.1-2012, Table 12, printed page 21** instead orders
its entries `Lg max / Lb min`. Its six-inch, 1/4-inch entry is
`5.25 / 5.00`, supporting the modeled 133.35 mm grip-gage maximum and
127 mm body minimum. Section 4.7 and Table 6 agree: the reference thread
length is 0.75 inch for this diameter and nominal length, and the transition
allowance is 0.25 inch. Thus `6 − 0.75 = 5.25` and
`5.25 − 0.25 = 5.00` inches. See the
[ASME standard record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws).
This is an independent check against the named standard, not a supplier
correction or confirmation of a delivered product.

`Lb` measures body length from under the head to the last thread scratch.
`Lg` is a grip-gaging criterion. Keep both distinct from a measured first
full-form thread and functional nut engagement. A head washer offsets the
wood from the under-head datum. Smooth shank through every millimetre of wood
is also distinct from the member-specific threaded-bearing condition in
NDS 2024 §12.3.7.2; the latter needs its own dimensional and method check.

The source files inspected locally have these SHA-256 values:

| Publication | SHA-256 |
| --- | --- |
| ASME B18.2.1-2012 PDF, including its front correction sheet | `4c7bcb75223b7e89fc27f132bc44e8b422ba672c97f7803259a24fab6bd99ba0` |
| Nickel Systems 2025 partial-thread table | `7ca413048ba2281c23fd073520eee680f81d9c5539f48e7453ab779d75f33182` |
| AWC NDS 2024 Chapter 12 PDF used for the threaded-bearing provision | `5fc837523ff10acc097a162718700a9b4ba64e627d2b0023439146d42fe4ee2a` |

Preserve the older source-bound hardware note and generated reports as
history. For current development, read their six-inch numeric bounds with
this corrected source attribution. Their thread-fit and resistance gates
remain open.
