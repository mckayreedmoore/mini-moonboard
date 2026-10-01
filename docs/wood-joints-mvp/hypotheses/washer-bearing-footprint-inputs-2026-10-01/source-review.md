# Conditional washer-facing bearing geometry

Checked 2026-10-01 for the quarter-inch primary-corner stacks. This is a
source-input review only. It does not establish delivered-part conformance,
contact pressure, resistance, or joint acceptance.

## Findings

For a conforming 1/4-20 hex cap screw under ASME B18.2.1-2012 (R2021), Table 6
gives maximum width across flats `Fmax = 0.438 in` (minimum `0.428 in`).
Paragraph 4.3 makes washer-face diameter equal to `Fmax` with a −10% tolerance,
but directs measurement **0.004 in toward the head from the bearing-surface
plane**. This supports a washer-face gauge-circle diameter of
`0.3942–0.438 in` (`10.0127–11.1252 mm`) at that offset plane. Washer-face
thickness is `0.015–0.025 in` (`0.381–0.635 mm`) for this size. The across-flats
and across-corners values are head-envelope dimensions, not the contact
circle.

The offset-plane circle does not give the flat footprint diameter at the
head-to-washer contact plane. The standard's text and table do not provide the
radial/axial profile connecting those planes. Do not use `0.3942–0.438 in` as
the contact-face diameter without an explicit profile assumption. The missing
input for a bounded head footprint is the washer-face outside radius at the
actual bearing plane, with its transition profile to the specified
0.004-in-offset gauge circle. An exact-product drawing or a separately
declared profile scenario would supply that input.

For the K.L. Jack `25CNFH5Z` 1/4-20 finished hex nut, the catalog identifies
ASME B18.2.2 dimensional specification. For a standard-conforming nut of this
size, B18.2.2-2022 §3.3 says nuts no larger than 5/8 in are double-chamfered
unless otherwise specified; §3.3.2 bounds the chamfer-circle diameter by
maximum across flats with a −10% tolerance. Table 1.1.1-5 gives
`Fmax = 0.438 in`, so the conditional outer chamfer-circle diameter is also
`0.3942–0.438 in` (`10.0127–11.1252 mm`). This is a separate circular
end-face boundary; neither across-flats nor across-corners is a circular
bearing diameter.

Section 3.4 limits the bearing-face countersink for a 1/4-in nut to the basic
thread major diameter plus `0.030 in`, or `0.280 in` (`7.112 mm`). The
conditional 25NWUS Type A Wide washer bore is `0.307–0.327 in`
(`7.7978–8.3058 mm`), larger than that maximum countersink. Thus, under an
explicit concentric, flat-seating idealization, the washer-top overlap with
the nut face is a circular annulus bounded inside by washer ID and outside by
the nut chamfer circle. Its radial width ranges from `0.0336 in` (`0.8534 mm`)
to `0.0655 in` (`1.6637 mm`); its projected annular area ranges from about
`24.56` to `49.45 mm²`. These are geometric scenario bounds, not actual
contact area or effective pressure-bearing area. Nut-hole true-position
tolerance, washer/bolt clearance, face runout, seating, finish, and delivered
dimensions can make the assembled contact eccentric or partial; the
concentric annulus is not guaranteed by the catalog listing.

The washer-to-wood footprint remains the washer's own conditional Type A Wide
annulus (`ID 0.307–0.327 in`, `OD 0.727–0.749 in`, thickness
`0.051–0.080 in`) intersected with the supported wood face and cuts. It must
not be replaced by the smaller head/nut footprint. No wood or metal capacity
follows from any of these areas.

## Source record and limits

- Local hardware packet `fasteners.md`, SHA-256
  `aac25eaccfcd123f41c180c93c6449e9f2da11c306c5b78fbf125c0ea81959f6`,
  documents the 25CNFH5Z, 25NWUS, and Type A Wide dimensional inputs. The local
  ordinary-nut/washer basis is SHA-256
  `98a151ae040232aa1f2485826ba4c29dc0e0d0fb1ce6ac87ddd9bf062eeb6bcf`.
- The local B18.2.1-2012 mirror at
  `/tmp/thread-gage-functional-fit/ASME-B18.2.1-2012-mirror.pdf` is SHA-256
  `4c7bcb75223b7e89fc27f132bc44e8b422ba672c97f7803259a24fab6bd99ba0`.
  Paragraph 4.3 is printed p. 9 (PDF p. 21); Table 6 is printed p. 10
  (PDF p. 22). The [ASME record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws)
  identifies the standard; the inspected full-text copy is a mirror.
- The [official ASME B18.2.2-2022 record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts)
  confirms the edition. Sections 3.3.2 and 3.4 are printed p. 2; Table
  1.1.1-5 is printed p. 9. No B18.2.2 PDF was found locally in the repository,
  `/tmp`, or the searched home tree, so there is no local standard-PDF hash.
  The [third-party-hosted text/PDF mirror](https://ul.isodoc.my/asme/ASME%20B18.2.2%202022.pdf)
  was available in indexed text but did not fetch for local inspection; this
  note does not claim a full local PDF review. The exact clauses should be
  checked against the standard copy before adopting these nut geometry inputs.
- The [K.L. Jack 25CNFH5Z listing](https://www.kljack.com/products/25cnfh5z/)
  identifies the nut and B18.2.2 specification. Its catalog entry is not a
  drawing or a delivered-lot inspection.

No hardness-to-yield conversion or material property inference is made.
