# Independent review: partial-seat nut projection

Reviewed October 1, 2026 against these bytes:

- `check_footprint.py`: `6c67a2fddc01c9fc65d27a55b0f242c96015408509b842f52c6a595bef8ee3b1`
- `README.md`: `9304b076f58d4b771cf56f4a9c2a3295859ce384b549f3bf50cdfbda721f7704`
- Raw report: `16c5c06a1be0e5cd00df960d903bf2fbe02d99b8630f1958d69e11c41637ce4b`

I ran the checker against the pinned inputs. It returned the documented exit
status 1 and `PROJECTION_ENCLOSURE_EXCEPTIONS`: one of two projection
enclosures is contained. This is an expected geometric exception, not a
strength or joint criterion failure.

## Source and geometry checks

The checker hash-pins the prior seat method, the nut-bearing source
disposition, and `timber-passages.json`. It selects the single
`bore_base_principal_center_right_072` record and checks its member and F1/G1
datums. The source direction is +X, parallel to the nut seat's inward normal;
the entry coordinate matches the seat plane and the source cut extends beyond
the three tested inward depths. The checker also matches the STEP cylindrical
face's radius, axis line, and axial X bounds (`50.95..89.05 mm`) to the source
record. The imported member STEP hash matches the model binding and frozen
bundle manifest. The source member bore is separately matched at 3.65 mm
radius. The checked source-to-STEP chain is specific to this service cut and
does not imply that the source cut is qualified for machining.

The circular scenario uses a 5.5626 mm radius, derived from the conditional
0.438 in maximum across-flats/chamfer-circle dimension. It is explicitly a
centered flat circular end-face idealization. The source trace is a
third-party B18.2.2 text transcription rather than an authenticated standard
PDF or figure, and does not establish an actual bearing or pressure patch.
The 0.222504 mm displacement is half the 4%-of-maximum-across-flats
diametrical nut thread-axis position zone, under the source trace's
circular-zone interpretation. Adding it to the 0.475 mm nominal-body/bore
radial clearance assumes the nut thread axis follows the modeled bolt axis;
neither delivered thread fit nor bolt-body/thread runout is bounded.

For either circular scenario, every possible translated disk point outside
the centered wood bore lies in the tested annulus from bore radius 3.65 mm to
the disk's maximum translated outer radius. The larger across-corners disk
likewise encloses the full hex silhouette for every in-plane orientation. The
solid-intersection tests therefore check continuous in-plane location and
orientation enclosures, not finitely sampled directions. These annuli are
conservative geometric supersets; they do not model a contact patch or
pressure distribution.

The report gives a 6.5598763474 mm nearest service-passage edge. For the
circular end-face idealization, the 6.260104 mm enclosing radius leaves
0.299772 mm clearance and the inward support fractions range from
`0.999999999999936` to 1.0 at depths 0.01, 0.05, and 0.1 mm; outward overlap
is zero. The 6.4135 mm across-corners radius produces a 7.111004 mm enclosure,
which crosses the passage edge by 0.551128 mm. Its BREP support fraction is
about 0.985094249 at all three depths, while outward overlap remains zero.
That result says the conservative complete-hex silhouette enclosure reaches
the passage. It does not establish that the actual nut bearing face is
unsupported, nor does the smaller idealization establish washer support.

## Claim limits

The finding is limited to the saved STEP geometry and conditional nominal
6.35 mm body, catalog nut-dimension, and alignment scenarios. The source
passage record itself is not machining qualification. The calculation does
not bound a minimum delivered shank, actual nut/thread fit, washer movement,
tilt, seat tolerance, or the bearing-face profile. The washer annulus remains
partially supported. Nothing here establishes metal or wood resistance,
contact pressure, load transfer, joint acceptance, a six-case envelope, or
physical inspection; no model change, native solve, or physical work was
performed.
