# Independent review: ordinary nut and washer property basis

**Reviewed:** 2026-09-25. **Disposition:** supports the stated conditional nut
proof-load reference and washer property boundary. No material correction is
needed.

## Pin reviewed

`docs/wood-joints-mvp/current-ordinary-nut-washer-property-basis.md`,
SHA-256 `98a151ae040232aa1f2485826ba4c29dc0e0d0fb1ce6ac87ddd9bf062eeb6bcf`.

## Findings

The K.L. Jack `25CNFH5Z` listing identifies supplier part `AFH5Z0250C` as a
1/4-20, zinc-plated Grade 5 finished hex nut with SAE J995 Grade 5, ASME
B18.2.2, and ASME B1.1 UNC Class 2B specifications. The listing's 7/16 in
hex and 7/32 in nominal thickness agree with the 1/4-in finished-hex row of
ASME B18.2.2-2022: 0.428–0.438 in across flats, max 0.505 in across corners,
and 0.212–0.226 in thickness. The standard envelope is correctly described
as a conditional dimensional reference, not delivered-nut conformity.

For a regular hex Grade 5 nut in the 1/4-through-1-in size range, the J995
technical table lists 120,000 psi proof-load stress for UNC/8UN and 109,000
psi for UNF/12UN and finer. Its 1/4-20 UNC tensile-stress-area row is
0.0318 in²; `120,000 × 0.0318 = 3,816 lbf`. Thus the note's conditional
per-nut proof-load reference uses the correct nut type, grade, thread series,
size range, units, and arithmetic. J995's published definition computes
proof load from the listed stress and thread-series tensile-stress area.
This is a proof-test reference for a conforming nut; it is not a stripping
capacity or evidence that the supplier-listed item or a received lot passed
that test. The note keeps those limits, actual 2B/2A engagement, usable
thread length, and entry/exit chamfers separate.

The numerical J995 tables are publicly reproduced in [STS Industrial's
J995 technical data](https://www.stsindustrial.com/services-resources/fastener-specifications/sae-j995-technical-data),
including the proof-stress row, area row, and multiplication rule; the
[SAE Mobilus J995_201707 record](https://saemobilus.sae.org/standards/j995_201707-mechanical-material-requirements-steel-nuts)
confirms the revision and scope (1/4–1-1/2 in steel nuts, with dimensions
per SAE J482 or ASME B18.2.2), but exposes only bibliographic/scope data.
Other supplier technical tables reproduce the same Grade 5/UNC values. The
review therefore confirms the conditional calculation against published
J995 transcriptions; it does not represent a received nut, its lot, or a
specific edition's conformity as verified.

The ordinary washer boundary is accurate. K.L. Jack `25NWUS` says plain/light
oil, low-carbon steel, and ASME B18.21.1 Type A Wide regular series, and lists
1/4-in size, 0.312-in ID, 47/64-in OD, and 0.051–0.080-in thickness. These
nominals/ranges correspond to the 1/4-in Type A Wide entry in ASME
B18.21.1-2009 (R2016) (ID 0.307–0.327 in, OD 0.727–0.749 in,
thickness 0.051–0.080 in). The page does not name a steel grade, heat
condition, hardness, or yield strength. The note expressly says it does not
claim 25NWUS conforms to ASTM F844; that avoids conflating the product's
ASME dimensional specification with a separate ASTM product specification.
ASTM F844-19(2024) covers unhardened plain washers and defaults dimensions to
ASME B18.21.1 Type A Table 11 unless otherwise specified, but its public
record provides no numeric washer yield minimum.

The separate K.L. Jack `25NWUS8Z` listing expressly identifies a 1/4-in
Type A Wide, quenched-and-tempered washer, ASTM F436, with through/core
hardness 38–45 HRC. The note preserves it as an unselected alternate and
does not assign that harder washer's material or geometry to `25NWUS` or the
current stack. ASTM F436/F436M-24 identifies hardness among its specified
properties, but neither that record nor the product hardness callout supplies
a numeric yield minimum. No hardness-to-yield conversion or washer bending
capacity is asserted. I found no incorrect claim that `25NWUS` is F844 or
that `25NWUS8Z` has a sourced yield strength.

## Source references checked

- [SAE J995_201707 official standard record](https://saemobilus.sae.org/standards/j995_201707-mechanical-material-requirements-steel-nuts)
- [STS Industrial J995 technical tables](https://www.stsindustrial.com/services-resources/fastener-specifications/sae-j995-technical-data)
- [K.L. Jack 25CNFH5Z listing](https://www.kljack.com/products/25cnfh5z/)
- [ASME B18.2.2-2022 standard record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts)
- [K.L. Jack 25NWUS listing](https://www.kljack.com/products/25nwus/)
- [ASME B18.21.1-2009 (R2016) standard record](https://www.asme.org/codes-standards/find-codes-standards/b18-21-1-washers-helical-spring-lock-tooth-lock-plain-washers)
- [ASTM F844-19(2024) standard record](https://store.astm.org/standards/f844)
- [K.L. Jack 25NWUS8Z listing](https://www.kljack.com/products/25nwus8z/)
- [ASTM F436/F436M-24 standard record](https://store.astm.org/f0436_f0436m-24.html)
