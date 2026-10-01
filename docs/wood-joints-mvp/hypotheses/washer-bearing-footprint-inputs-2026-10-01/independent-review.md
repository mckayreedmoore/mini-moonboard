# Independent review: washer-facing dimensional inputs

Reviewed October 1, 2026. I checked the frozen worker trace and the parent
disposition against the local B18.2.1 text and the readable full-text
transcription of B18.2.2-2022. The conditional geometry interpretation is
sound; I found one provenance wording issue in the parent disposition.

## Reviewed bytes and sources

| Item | SHA-256 / source |
| --- | --- |
| [Worker source review](source-review.md) | `1a7a236ddf92f5fb1487619ebe8493de5f6ddfa97e924bc48cf5ebb5fe83f975` |
| [Parent review](parent-review.md) | `952b5753823048135822985659e8c0150602dd534f005564233fe957e2b291be` |
| Local B18.2.1-2012 file | `/tmp/thread-gage-functional-fit/ASME-B18.2.1-2012-mirror.pdf`, `4c7bcb75223b7e89fc27f132bc44e8b422ba672c97f7803259a24fab6bd99ba0` |
| B18.2.2-2022 text inspected | [Third-party-hosted full-text transcription](https://studylib.net/doc/27188368/asme-b18.2.2-2022); edition cross-checked against the [ASME publisher record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-2-nuts-general-applications-machine-screw-nuts-hex-square-hex-flange-coupling-nuts) |

The local B18.2.1 file hash matches the worker trace. The inspected B18.2.2
text includes the standard title and edition and the requested clauses, so
this review is based on the full text, not a search excerpt. No authenticated
B18.2.2 PDF or figure copy was available; the transcription and numeric text
do not remove that source limitation.

## Dimensional interpretation

The B18.2.1-2012 local text confirms §4.3 (printed p. 9 / PDF p. 21) and
Table 6 (printed p. 10 / PDF p. 22): the 1/4-in hex-cap screw washer-face
diameter is measured 0.004 in toward the head from the
bearing-surface plane, and the 1/4-in Table 6 maximum width across flats is
0.438 in. Applying the stated −10% tolerance gives a gauge-circle range of
0.3942–0.438 in at that offset plane. The offset measurement does not supply
the washer-face diameter at the actual head-to-washer plane or the transition
profile between planes. The worker trace correctly leaves the head contact
face unadopted and does not substitute across-flats/corners for a circular
contact boundary.

In the B18.2.2-2022 transcription, §§3.3–3.4 and Table 1.1.1-5 support the
conditional 1/4-in regular-hex-nut bounds: the default for sizes through
5/8 in is double chamfer unless otherwise specified; the chamfer-circle
diameter has a −10% tolerance from maximum across flats; the 1/4-in table
row gives `Fmax = 0.438 in`; and the maximum bearing-face countersink is the
basic 0.250-in thread major diameter plus 0.030 in, or 0.280 in. Thus
0.3942–0.438 in is a conditional outside chamfer-circle diameter. With the
catalog washer ID range 0.307–0.327 in, the reported 24.56–49.45 mm² annulus
is correct only for the declared concentric, flat-face idealization. The
maximum countersink is smaller than the washer's minimum listed ID, but that
comparison does not establish actual face contact, seating, or a pressure
area.

Section 3.8 limits the tapped-hole axis true position relative to the nut-body
axis to a diametrical zone equal to 4% of maximum across flats for this size.
Using 0.438 in gives 0.01752 in diameter (0.445008 mm), or 0.00876 in
(0.222504 mm) radial offset under a circular-zone interpretation. This is a
nut-body-to-thread-axis tolerance, not a direct assembled nut-to-washer
eccentricity bound; thread/washer clearance and the relationship of the
chamfer circle to the nut-body datum remain relevant.

Section 3.9 makes the bearing face flat and perpendicular to the threaded-hole
axis within the table's FIM limit. Table 1.1.1-5 lists 0.015 in for the
quarter-inch regular hex nut in the up-to-150-ksi specified-proof-load band,
0.010 in in the higher band, and 0.015 in for hex jam nuts. The hardware
packet's conditional J995 Grade 5 case has 120-ksi proof stress, placing it
in the first regular-hex-nut band if the product is conforming. The 0.015-in
value is an indicator limit (0.381 mm), not an assembled tilt or additional
washer thickness. Neither §3.8 nor §3.9 prescribes which permitted alignment,
face profile, or contact distribution occurs in a particular assembly.

Accordingly, the parent disposition correctly treats the annulus as a
declared geometry scenario, retains eccentric/partial overlap possibilities,
and does not infer contact pressure, metal resistance, or joint acceptance.

## Provenance finding and disposition

An earlier parent-review draft called the local B18.2.1-2012 PDF
“authenticated.” The frozen worker trace identifies the same hash and path as
a **mirror**, and points to the ASME record for standard identification. I
flagged that a hash pins bytes but does not establish publisher origin. The
reviewed parent version now calls it a “hash-pinned local B18.2.1-2012 PDF
mirror,” which resolves the wording issue without affecting the independently
read §4.3/Table 6 values. The parent disposition also correctly retains the
separate limitation that no authenticated B18.2.2 PDF or figure copy was
reviewed. No open source-interpretation finding remains.

This review supplies no product conformity, delivered-part observation,
contact mechanics, strength, or joint pass.
