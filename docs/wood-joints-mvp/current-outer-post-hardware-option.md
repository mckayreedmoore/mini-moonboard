# Conditional hardware basis for the four current outer-post axes

**Prepared:** 2026-09-25. **Status:** source-bound catalogue scenario; fit is
not closed and no item is selected. This note screens only the four
`knee_outer_{left,right}_post_{1,2}` axes in the current 92-axis WJ24
candidate. It does not alter geometry, establish capacity, or authorize
purchase, drilling, or assembly.

## Scope and current stack

The controlling source is the frozen [attempt 02 grip-screen JSON](hypotheses/evaluation-resume-2026-09-24/grip-screen-attempt02.json),
SHA-256 `9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a`.
The [current hardware schedule](current-hardware-schedule.md) reports these
four unmatched axes as 101.600 mm modeled under-head-to-tip length and
76.200 mm wood grip. The model provides a 6.35 mm unthreaded shaft
occupancy envelope, not a selected purchase length or measured bolt.

| Axial role, measured from the modeled under-head bearing plane | Current interval |
| --- | ---: |
| Head-side washer | 0.000–1.651 mm |
| First timber receiver | 1.651–39.751 mm |
| Second timber receiver | 39.751–77.851 mm |
| Nut-side washer | 77.851–79.502 mm |
| Nut | 79.502–85.242 mm |
| Modeled bolt tip | 101.600 mm |

The mirrored axes have the same dimensions. Each requires one bolt, one nut,
and two separate washers in the current count. The retained 12 frame
arrangements and the other 88 candidate axes are outside this screen.

## Named catalogue scenario

The Stripe Directory route was already tried on 2026-09-24 before the public
supplier fallback, as recorded in the [ordinary-axis basis](current-ordinary-hardware-basis.md#bounded-follow-up-on-a-longer-thread-6-in-item-2026-09-24).
Those focused Directory searches returned no relevant fastener listing, and
the Directory results did not function as a hardware product catalogue. This
note reuses that route record. The pages below were checked read-only on
2026-09-25; no vendor was contacted and no purchase was made.

| Role | Conditional item | Published listing/specification | Four-axis quantity and package screen |
| --- | --- | --- | --- |
| Bolt | K.L. Jack [25C400HCS5Z](https://www.kljack.com/products/25c400hcs5z/) | Supplier listing names a zinc-plated, 1/4-20 × 4 in Grade 5 hex-head cap screw. The K.L. Jack listing shows a 100-piece box. A same-family 4.5 in Grade 5 product page lists partial thread, UNC Class 2A, ASME B18.2.1, SAE J429, and 3/4 in nominal thread length; that adjacent size is supporting family evidence, not an exact-part drawing. | 4 required; one 100-piece box if ordered in the listed package; 96 surplus. |
| Nut | K.L. Jack [25CNFH5Z](https://www.kljack.com/products/25cnfh5z/) | 1/4-20 zinc-plated Grade 5 finished hex nut; the page states ASME B18.2.2, SAE J995 Grade 5, UNC Class 2B, 7/16 in across flats, and 7/32 in nominal thickness. Page package: 100. | 4 required; one 100-piece box; 96 surplus. |
| Two washers per axis | K.L. Jack [25NWUS](https://www.kljack.com/products/25nwus/) | 1/4 in plain USS flat washer, low-carbon steel/light oil, ASME B18.21.1 Type A Wide; page package: 100. The page lists 0.312 in ID, 47/64 in nominal OD, and 0.051–0.080 in thickness. The washer finish differs from the bolt/nut finish; environmental finish compatibility is not decided. | 8 required; one 100-piece box; 92 surplus. |

This is a package-level quantity scenario, not a current purchase list. K.L.
Jack's 4 in Grade 5 listing was also shown as a substitute on its 4 in
Grade 2 product page at a different displayed box amount from a later
category listing. No fastener cost is assigned from those conflicting
displays. The supplier pages do not establish a lot-specific stock count,
delivery, or delivered-part conformity.

## Source-bounded dimensions and fit screen

The K.L. Jack 1/4-20 Grade 5 4 in item is a candidate catalogue match to the
model's 6.35 mm shaft diameter and 101.600 mm nominal axial envelope. Under
ASME B18.2.1-2012, the 1/4 in cap-screw body diameter bounds are 0.2450–0.2500
in (6.223–6.350 mm). A standard-conforming body therefore fits within the
model's nominal cylindrical diameter envelope, subject to bore clearance,
head-seat, under-head fillet, location, and delivered-part checks. No bore or
clearance result is inferred here.

ASME B18.2.1 Table 12 gives a 1/4 in × 4 in cap screw `LG,max` of 3.25 in
(82.550 mm) and `LB,min` of 3.00 in (76.200 mm). Table 13 permits a length
shortfall of 0.06 in for a 1/4 in screw at 4 in nominal length, so minimum
overall length is 3.94 in (100.076 mm). The manufacturer's technical sheet
lists `LT = 0.750 in` as a reference thread length for 1/4 in cap screws up
to 6 in, and a maximum transition-thread length `Y = 0.250 in`. `LT` is
reference data; it does not give a delivered first-full-thread coordinate.
`LG,max` and `LB,min` are separate standard gaging limits, not direct
coordinates for the complete-thread start, the runout end, or the bolt's
actual smooth-shank boundary. The related definitions and standard table
are documented in the [ordinary-axis source note](current-ordinary-hardware-basis.md#what-the-asme-thread-dimensions-establish)
and the [Tanner Grade 5/8 technical sheet](https://www.tannerbolt.com/media/akeneo_connector/CapScrewgr5-8.pdf).

The washer product's Type A Wide size limits thickness to 0.051–0.080 in
(1.2954–2.032 mm). Its 1/4 in Type A Wide bore standard is 0.307–0.327 in
(7.7978–8.3058 mm), wider than the 0.250 in maximum cap-screw body by at
least 0.057 in (1.4478 mm) diametrically. This is washer-to-body clearance
only; no drilled-bore, washer-footprint, or timber-support fit is established.
The finished 1/4 in nut standard envelope is 0.212–0.226 in thick
(5.3848–5.7404 mm); the product page's 7/32 in value is nominal. Holding the
current 76.200 mm timber grip fixed, those catalog/standard thickness limits
give this stack range:

| Quantity | Lower bound | Upper bound |
| --- | ---: | ---: |
| Under-head to earliest nut-bearing face: head washer + wood + nut washer | 78.7908 mm | 80.2640 mm |
| Under-head to far nut face: prior row + nut | 84.1756 mm | 86.0044 mm |
| Under-head to far wood face: head washer + wood | 77.4954 mm | 78.2320 mm |

At the current CAD washer thickness of 1.651 mm, the nut-bearing face is
79.502 mm and the modeled nut ends at 85.242 mm. The conservative standard
`LG,max` gage coordinate is 82.550 mm, 3.048 mm beyond that nominal nut
bearing face. With the Type A Wide washer limits, even the latest possible
bearing face in the fixed-grip screen is 2.286 mm short of `LG,max`; the
earliest is 3.7592 mm short. A nut-bearing plane at or beyond `LG,max` is a
conservative sufficient envelope for avoiding overlap with that maximum
grip-gage coordinate, not a necessary fit condition: an applicable part
drawing or matched functional check could establish a more favorable actual
thread location. The standard gage number alone does not prove the exact
thread start or prove this stack fails.

At 20 threads per inch, one nominal pitch is 1.270 mm. The physical nut
thickness range spans 4.24–4.52 nominal pitches; that is not a published
functional-thread engagement length because nut thread lead/chamfers reduce
the active region. The required fit is functional engagement across the
matched nut's active internal-thread region, with its source-defined entry
and exit geometry accounted for. The `LG,max` coordinate falls inside the
physical nut envelope for all washer combinations in this screen, by
2.286–3.7592 mm from the nut bearing face. This indicates why the current
position cannot be cleared from the gage limit alone; it does not locate the
actual external full-form-thread start or make a necessary-failure finding.

The `LB,min` value is 76.200 mm. It lies 1.2954–2.032 mm inward of the
current far-wood-face range above. This leaves a narrow part of the far
receiver in the standard's possible transition/thread region; `LB,min` does
not specify the delivered thread-root or last-scratch coordinate. It is
separate from the nut engagement question.

At the maximum far nut face, the inherited 3.175 mm WJ24 tip-projection
target is 89.1794 mm from the under-head datum. This 3.175 mm value is a
modeled physical-tip envelope, not a minimum full-form-thread extension.
The 4 in standard minimum overall length of 100.076 mm leaves at least
14.0716 mm of physical tip beyond the maximum nut face, and 10.8966 mm
beyond that modeled tip target. Overall bolt length is therefore not the
limiting part of this screen; complete functional nut-thread engagement
remains unresolved.

## Finding and evidence still needed

The named 1/4-20 Grade 5 cap-screw / Grade 5 nut / Type A Wide washer set is
a concrete source-backed candidate for these four axes. It is not cleared
for the unchanged current nut position: the catalog pages plus standard
limits do not establish that the bolt engages the matched nut across its
complete functional internal-thread region and seats clear of thread runout
or point interference. This does not require full-form bolt thread through
the nut's physical entry/exit faces or through the modeled tip extension.
Class 2A / 2B compatibility, when confirmed for the exact bolt listing and
lot, is a thread-fit designation; it does not by itself locate usable
full-form thread along the bolt.

To close this one class, use an applicable item drawing or an explicitly
bounded matched bolt/nut dimensional check that establishes full functional
engagement at the current bearing position and verifies that the physical
bolt tip extends at least 3.175 mm beyond the far nut face within the actual
length tolerance, plus washer dimensions/support at the timber face. The
3.175 mm is a physical-tip projection only; it does not require full-form
thread through that extra tail. A later outboard nut shift of 3.048 mm at
the modeled washer thickness, or 3.7592 mm from the earliest seat in the
source-bounded washer range, would bring the respective bearing plane
exactly to the `LG,max` coordinate. These shifts provide zero clearance
beyond that coordinate; positive clearance would require additional
movement. This is only a boundary diagnostic, not an adopted spacer or
geometry change. Provisional analysis may instead carry
explicit thread-location cases while this exact fit remains open.

No resistance, washer capacity, stock ownership, supplier availability, or
joint acceptance follows from this dimensional screen. Do not transfer the
candidate SKU or these coordinates to the other 88 current axes, the 12
retained frame arrangements, or the historical hardware schedules.

## Source trail

- Current geometry: [attempt 02 JSON](hypotheses/evaluation-resume-2026-09-24/grip-screen-attempt02.json),
  [rendered current grip screen](current-grip-screen.md), and
  [current hardware schedule](current-hardware-schedule.md); source hash is
  recorded above. Screen row IDs are `knee_outer_left_post_1/2` and
  `knee_outer_right_post_1/2`.
- K.L. Jack [25C400HCS5Z](https://www.kljack.com/products/25c400hcs5z/),
  [25CNFH5Z](https://www.kljack.com/products/25cnfh5z/), and
  [25NWUS](https://www.kljack.com/products/25nwus/), catalogue pages checked
  2026-09-25. The nut and washer page specs/package sizes are stated above;
  the exact 4 in Grade 5 bolt product page did not return a readable full
  specification through this source lookup, so same-family thread details
  are supporting evidence only.
- K.L. Jack [4.5 in Grade 5 25C450HCS5Z](https://www.kljack.com/products/25c450hcs5z/)
  and [4 in Grade 8 25C400HCS8Z](https://www.kljack.com/products/25c400hcs8z/)
  catalogue listings, used only for same-family specification context.
- [Tanner Grade 5/8 cap-screw technical sheet](https://www.tannerbolt.com/media/akeneo_connector/CapScrewgr5-8.pdf),
  which reproduces ASME B18.2.1-2012 dimensions, body limits, length
  tolerances, `LT` reference, and `Y` maximum transition length.
- [ASME B18.2.1-2012 table copy](https://www.nickel-systems.com/products/bolts-screws/hex-head-cap/)
  and [ASME B18.2.2 finished-hex nut table](https://www.nickel-systems.com/products/nuts/finished-hex/),
  also linked from the ordinary-axis source note. ASME's official
  [B18.2.1 standard record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws)
  identifies the standard edition used there as B18.2.1-2012 (R2021).
- K.L. Jack's [fastener technical data and charts](https://www.kljack.com/docs/default-source/technical-information/kl_jack_fasteners-technical_data_and_charts.pdf)
  and [plain USS washer page](https://www.kljack.com/products/25nwus/).
- [Fastenal Type A Wide washer dimensional sheet](https://www.fastenal.com/content/product_specifications/FW.LC.USS.A.P.00.pdf),
  used for the 1/4 in washer bore tolerance.
