# Independent review: unmatched-length hardware screen

**Checked:** 2026-09-25. **Disposition:** no factual correction identified in
the reviewed scope. This read-only review checks axis coverage, dimensional
arithmetic, and the named listing claims in
[`current-unmatched-length-hardware-options.md`](../current-unmatched-length-hardware-options.md).
It selects no hardware and does not establish received-part fit or suitability.

## Frozen inputs and method

The reviewed note SHA-256 is
`25f4ec31fb84d32cdf70bdbddd8c67f86d020c60851e7d4ae29dbd39fffeab03`.
The axis source is frozen grip-screen attempt02, SHA-256
`9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a`.
I independently parsed its 92 axis rows and compared the selected IDs with
the corresponding family memberships in
[`current-hardware-coverage.json`](../current-hardware-coverage.json), SHA-256
`8e1a5325d99aa83a82cfd7dba1e6767ea2e2ba484be38e5fb12df39b227afdea`.

All sixteen listed IDs appear exactly once in attempt02 and exactly match the
four current-coverage families, four axes per family, with no extra IDs. The
attempt02 receiver sums, ordered receiver identities, nut-side receiver
lengths, and modeled endpoints agree:

| Family | Grip | Head-to-nut receiver lengths (mm) | Nut-side receiver (mm) | Modeled endpoint |
| --- | ---: | --- | ---: | ---: |
| Center post | 127.000 | 88.9 + 38.1 | 38.1 | 139.2174 mm |
| Center post header | 167.000 | 38.1 + 128.9 | 128.9 | 179.2174 mm |
| Center principal header | 172.800 | 134.7 + 38.1 | 38.1 | 190.0174 mm |
| Knee outer side | 215.900 | 38.1 + 88.9 + 88.9 | 88.9 | 241.3000 mm |

## Arithmetic check

The screen's adopted dimensional basis is two Type A Wide washers at
1.2954–2.032 mm each, a finished 1/4-in hex nut at 5.3848–5.7404 mm, and
3.175 mm of physical tip projection. These values and their dimensional
source trail are in
[`current-center-sandwich-hardware-options.md`](../current-center-sandwich-hardware-options.md)
and [`current-ordinary-hardware-basis.md`](../current-ordinary-hardware-basis.md).
They produce earliest bearing `G + 2.5908`, latest nut face `G + 9.8044`, and
physical-tip target `G + 12.9794` mm, with no added timber-length allowance.
The tip allowance is for the physical bolt end; it does not require full-form
thread beyond the nut.

I recalculated the standard minimum lengths using the cited allowance of
0.10 in through 6 in and 0.18 in above 6 in. The `LG,max` and `LB,min` values
agree with the table values and definitions recorded in the pinned
[`six-inch source correction`](../bolt-dimension-source-correction.md), the
[`current center/knee length screen`](../current-center-sandwich-hardware-options.md),
and the earlier [`WJ24 length screen`](../wj24-bolt-length-screen.md). `LG` is a
gage coordinate and `LB` ends at the last-thread-scratch datum; neither gives
the first full-form thread, runout, or functional nut engagement.

| Screen row | Nominal class | Minimum length | Tip target | Length margin | Next-shorter class margin | `LG,max` / earliest-bearing margin | `LB,min` | Potential table-bounded interval in nut-side wood / receiver quarter |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Center post | 5.75 in | 143.510 | 139.9794 | +3.5306 | 5.50 in: −2.8194 | 127.000 / +2.5908 | 120.650 | 8.382 / 9.525 |
| Center post, listed alternative | 6.00 in | 149.860 | 139.9794 | +9.8806 | n/a | 133.350 / −3.7592 | 127.000 | 2.032 / 9.525 |
| Center post header | 7.50 in | 185.928 | 179.9794 | +5.9486 | 7.25 in: −0.4014 | 165.100 / +4.4908 | 158.750 | 10.282 / 32.225 |
| Center principal header | 7.50 in | 185.928 | 185.7794 | +0.1486 | 7.25 in: −6.2014 | 165.100 / +10.2908 | 158.750 | 16.082 / 9.525 |
| Knee outer side | 9.25 in | 230.378 | 228.8794 | +1.4986 | 9.00 in: −4.8514 | 209.550 / +8.9408 | 203.200 | 14.732 / 22.225 |
| Knee outer side, longer-class comparison | 9.50 in | 236.728 | 228.8794 | +7.8486 | n/a | 215.900 / +2.5908 | 209.550 | 8.382 / 22.225 |

The `LG` margin is earliest bearing plane minus `LG,max`. The conditional NDS
table-boundary screen treats `max(0, G + 2.032 − LB,min)` as the potential
threaded interval in the nut-side receiver and compares it with one-quarter
of that receiver. This is not a measured thread location. It reproduces the
reported 8.382/9.525,
10.282/32.225, 16.082/9.525, and 14.732/22.225 mm outcomes for the four
selected families; the 9.5-in class comparison gives 8.382/22.225 mm. The
principal-header row requires `LB ≥ 165.307 mm` to reach the quarter-length
limit, 0.207 mm above `LG,max = 165.100 mm`. As the author note says, table
limits alone do not prove that a specific part fails or meets this condition;
part-specific dimensions or measurement, or a root-diameter/detailed method,
would be needed if the nominal-diameter exception is used.

The computed minimum-length margins to the modeled endpoints also agree with
the note: +4.293 mm (center post), +10.643 mm (6-in alternative), +6.711 mm
(center post header), −4.089 mm (principal header), −10.922 mm (9.25-in knee),
and −4.572 mm (9.5-in knee comparison). These compare a standard minimum
overall length with an unthreaded CAD occupancy endpoint; they do not predict
the delivered smooth-shank reach.

## Listing-source check

The author’s named listing statements match the sellers’ pages checked for
this review:

- [HiStrength 104-044](https://histrength.com/104-044) lists 1/4-20 × 6 in,
  SKU 25C600HCS5P, coarse, partially threaded, Grade 5, plain/light protective
  oil, package quantity 50, 120,000 tensile-strength field, 3/4-in “Thread
  Length,” and displayed $1.23 each with 25/50 quantity breaks. The note
  correctly leaves the minimum order interpretation unresolved.
- [HiStrength 104-049](https://histrength.com/104-049) lists 1/4-20 × 7.5 in,
  SKU 25C750HCS5P, coarse, partially threaded, Grade 5, plain/light protective
  oil, package quantity 1, a 120,000 tensile-strength field, a 3/4-in “Thread
  Length,” and displayed $2.54 each. Its linked [Grade 5 cut sheet](https://eadn-wc04-12343463.nxedge.io/cdn/pub/media/akeneo_connector/media_files/G/r/Grade_5_Hex_Cap_Cut_Sheet.pdf)
  states SAE J429 Grade 5, 120,000 psi minimum, ASME B18.2.1 dimensions, and
  ASME B1.1 UNC/UNF Class 2A threads, but provides no axial location for this
  part's thread transition or runout.
- [Fastener SuperStore item 412254](https://www.fastenersuperstore.com/products/412254/hex-cap-screws)
  independently lists 1/4-20 × 7.5 in, Grade 5, zinc, partial thread,
  Kanebridge cross-reference 14120CH5O, carton quantity 275 and displayed
  $382.42/carton. Eight units leaving 267 in a carton is arithmetically correct.
- [Ro-Brand HC5127](https://www.robrandinc.com/screws-grade-coarse-p-310.html)
  identifies 1/4-20 × 9.5 in Grade 5 coarse and “Call for Pricing.” Its
  [Grade 5 category](https://www.robrandinc.com/grade-screws-c-3_4_360.html)
  states medium-carbon steel, quenched and tempered, zinc plated, and 105,000
  minimum tensile strength. Those category statements conflict with the
  HiStrength cut sheet's 120,000 psi minimum statement for SAE J429 Grade 5.
  The author correctly records a public-source discrepancy, not a
  determination that HC5127 is defective or unsuitable.

The notes preserve the distinction between nominal length classes and named
parts: no exact 5.75-in or 9.25-in listing is claimed, and the 9.5-in Ro-Brand
listing is only a dimensional-class lead. The 6-in and 7.5-in listings also
remain unselected because their catalog “Thread Length” fields do not resolve
the complete axial thread transition, matched-nut engagement, tolerance, or
endpoint fit. The [ASME B18.2.1 official record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws)
confirms the cited 2012 (R2021) standard revision remains in effect; numeric
table checks above rely on the locally pinned standard copy/source correction,
not on table data displayed on ASME's product page.

No actual delivered bolt, nut, or washer was inspected. This review does not
infer suitable SKU, full thread-through-wood, capacity, purchase quantity,
installation, or joint acceptance.
