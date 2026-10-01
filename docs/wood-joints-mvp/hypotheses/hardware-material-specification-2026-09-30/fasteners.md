# Fastener material and catalog-source screen

**Checked:** 2026-09-30. **Status:** conditional source and dimensional screen;
no item selected, purchased, received, or accepted. This note supports the
current wood-joint candidate's hardware evidence only. It changes no geometry
or frozen input and establishes no structural capacity or assembly fit.

## Scope and finding

The current axis basis is the frozen
[grip-screen attempt 02](../evaluation-resume-2026-09-24/grip-screen-attempt02.json),
SHA-256 `9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a`.
It has 92 candidate bolt axes, plus the separate 12 retained frame-bolt
arrangements. The primary-corner scope here is the **left** pair of axes for
each group. Each has a two-axis right-side counterpart in the same hardware
length family, for four axes across left and right:

| Group | Primary left-corner axes (2) | Same-length right-side axes (2) | Modeled wood grip | Nominal model length | Sourced length lead |
| --- | --- | --- | ---: | ---: | --- |
| `BG001` outer post | `knee_outer_left_post_{1,2}` | `knee_outer_right_post_{1,2}` | 76.2 mm | 101.6 mm / 4 in | Exact 1/4-20 × 4 in Grade 5 cap-screw catalog leads; exact material/class detail remains incomplete. |
| `BG003` outer side | `knee_outer_left_side_{1,2}` | `knee_outer_right_side_{1,2}` | 215.9 mm | 241.3 mm / 9.5 in | Ro-Brand `HC5127` is listed at 9.5 in, but its page does not establish the required part-specific standard/property set. |
| `BG045` inner header | `knee_outer_left_inner_header_{1,2}` | `knee_outer_right_inner_header_{1,2}` | 177.1 mm | 202.5 mm / 8 in alternative | Lawson/FalconGrip `FA21103` is a source-backed 1/4-20 × 8 in Grade 5 partial-thread cap screw. |

This is a product/material source screen only. Shared length-family geometry
does not transfer left-corner action evidence, demands, or conclusions to the
right-side axes.

The Lawson 8 in bolt, K.L. Jack `25CNFH5Z` 1/4-20 Grade 5 finished nut,
and K.L. Jack `25NWUS` Type A Wide washer form the strongest **catalog
candidate combination** for the four-axis `BG045` length family (two left
primary-corner bolts plus two right-side siblings) and the 16 existing 8 in
side axes. Their published size, pitch, and material specifications align at
the catalog level. The Lawson page states SAE J429 material and mechanical
conformance, partial thread, and a 1 in minimum thread-length field, but it
does not separately state an external thread class or locate the first
full-form thread, runout, or actual shank/thread transition. ASME B18.2.1
§2.5.2 supplies a default external Class 2A if the item conforms to that
standard before coating; the supplier page is not a part-specific conformity
certificate or a zinc-coated thread-gauge result. The nut's 2B class alone
does not prove complete engagement. No group has a source-qualified delivered
fit.

For `BG001`, BrightonBest's Grade 5 cap-screw catalog lists exact 1/4-20 × 4
in item `847030`, and the existing K.L. Jack `25C400HCS5Z` catalog listing is
another exact nominal-length lead. BrightonBest calls out B18.2.1, whose
default external Class 2A applies conditionally if the product conforms before
coating; neither source establishes exact-item J429 minima or provides a
part-specific thread-transition drawing. For
`BG003`, Ro-Brand lists `HC5127` as 1/4-20 × 9-1/2 in Grade 5 coarse, but the
category's generic “105,000 minimum tensile” statement is not diameter-banded
or tied to SAE J429. It neither establishes nor disproves the 1/4 in J429
minimum; obtain part-specific documentation before assigning those values. No
inspected source provides a complete 9.5 in bolt/nut/washer fit solution.

These groupings retain the 12 existing frame-bolt arrangements and the 66
Hillman panel/kicker screws as separate policies. The 12 retained bolts remain
their existing Bolt Depot catalog references; this screen neither replaces
them nor transfers any candidate result to them. The modeled 6.35 mm shaft is
an occupancy envelope, not a purchased diameter or delivered-part inspection.

## Grade 5 bolt and nut material references

The supplier technical tables reproduce SAE J429 2014-05 Grade 5 mechanical
requirements. For nominal diameters 1/4 through 1 in, they report full-size
proof stress `Fp = 85 ksi`, machine-test yield `Fy = 92 ksi`, minimum full-size
tensile `Fu = 120 ksi`, 14% elongation, and 35% reduction of area. The next
diameter band, over 1 through 1-1/2 in, has 74 ksi proof, 81 ksi yield, and
105 ksi minimum tensile. Thus the 105 ksi value is a larger-diameter band in
the cited table; it does not create a contradiction for a quarter-inch bolt.
The exact part must still be tied to J429 and its correct band. Lawson
`FA21103` explicitly states J429 material/mechanical conformance. A generic
“Grade 5” label on other part pages does not provide the same evidence.

Keep this bolt-property basis separate from NDS dowel bending yield strength
`Fyb`. NDS-2024 §12.3.6.2 requires an adopted `Fyb` basis supported by the
specified bending-test route or another supported evaluation. The
Commentary's `(Fy + Fu)/2 = 106 ksi` for these minima is only an estimate; it
is not a normative value, test-derived result, or guaranteed minimum. The
NDS Table I1 / TR12-2026 example of 45 ksi is restricted to `D ≥ 3/8 in` and
does not establish quarter-inch `Fyb`. See the existing
[bolt resistance basis](../../bolt-resistance-basis.md).

The K.L. Jack `25CNFH5Z` page identifies a zinc-plated 1/4-20 steel Grade 5
finished hex nut, SAE J995 Grade 5, ASME B18.2.2, ASTM F1941 Fe/Zn finish, and
ASME B1.1 UNC Class 2B. It gives 7/32 in nominal thickness and 7/16 in across
flats. ASME B18.2.2-2022's dimensional envelope used by the current project
basis is 0.212–0.226 in thickness (5.3848–5.7404 mm), 0.428–0.438 in across
flats, and at most 0.505 in across corners. These are conditional standard
limits, not measurements of a delivered nut.

For a finished-hex J995 Grade 5 nut, the published J995 technical table gives
120 ksi proof-load stress for 1/4–1 in UNC/8UN nuts. With UNC 1/4-20 tensile
stress area `At = 0.0318 in²`, this gives the conditional nut proof reference
`120,000 × 0.0318 = 3,816 lbf`. This is a nut proof reference, not stripping
resistance or bolt capacity; it does not account for partial engagement,
internal chamfers, or wood-joint actions. No delivered `25CNFH5Z` lot is
verified.

## Washer material and dimensional candidates

K.L. Jack `25NWUS` is a 1/4 in plain/light-oil, low-carbon-steel USS washer
to ASME B18.21.1 Type A Wide, regular series. Its listing gives nominal
0.312 in ID, 47/64 in OD, and 1/16 in thickness, with thickness bounds
0.051–0.080 in. The dimensional envelope used here is ID 0.307–0.327 in,
OD 0.727–0.749 in, and thickness 0.051–0.080 in; the public supplier
technical standard lists the same dimensions. This is a viable washer
**geometry/material-description lead**, but “low carbon steel” carries no
numeric yield or hardness. Do not assign washer resistance from it.

K.L. Jack also lists `25NWUS8Z`, a 1/4 in yellow-zinc, ASTM F436, thru-hardened
Type A Wide washer, with Rc 38–45 and a similar dimensional envelope (its
listed OD range is 0.729–0.749 in). The
available material statement is hardness and F436 conformance; it is not a
numeric yield minimum. It is a traceable-material alternative to evaluate if
a hardened washer is needed, not a resistance-qualified substitution. Either
washer remains subject to actual bearing-footprint support and finish
compatibility checks.

## Dimensional screen: standards are not delivered thread coordinates

For the B18.2.1-2012 (R2021) cap-screw dimensional standard, the project
source correction verifies Table 12's ordering as `LG,max / LB,min`. For
1/4 in cap screws through 6 in, reference `LT = 0.75 in` and maximum
transition allowance `Y = 0.25 in`; for lengths over 6 in, `LT = 1.00 in`
and `Y = 0.25 in`. Applying that standard's table to the nominal classes
gives:

| Nominal class | `LG,max` | `LB,min` | B18.2.1 minimum overall length | Comparator margin over inherited CAD tip comparator* |
| ---: | ---: | ---: | ---: | ---: |
| 4 in | 3.25 in / 82.550 mm | 3.00 in / 76.200 mm | 3.94 in / 100.076 mm | +10.8966 mm (`BG001`) |
| 8 in | 7.00 in / 177.800 mm | 6.75 in / 171.450 mm | 7.82 in / 198.628 mm | +8.5486 mm (`BG045`) |
| 9.5 in | 8.50 in / 215.900 mm | 8.25 in / 209.550 mm | 9.32 in / 236.728 mm | +7.8486 mm (`BG003`) |

\*These are B18.2.1 class comparators, not universal minimum dimensions for
every listed SKU. The project [4 in outer-post note](../../current-outer-post-hardware-option.md)
and [8 in side note](../../current-side-hardware-option.md) document the
Table 13 length tolerances: −0.06 in for the 1/4 in × 4 in class and −0.18 in
above 6 in. Lawson
`FA21103` identifies ANSI B18.2.1 dimensions, and BrightonBest `847030` is
cataloged to ASME B18.2.1. Ro-Brand's `HC5127` page does not claim B18.2.1, so
the 9.5 in margin is a conditional standard scenario, not an HC5127 product
tolerance finding. The comparator is the current grip plus maximum head- and nut-washer
thickness, maximum nut thickness, and the inherited 3.175 mm CAD tip
allowance. That inherited allowance is not a required minimum physical
projection or a full-form thread extension beyond the nut. A separate
three-pitch profile scenario at 1/4-20 is 3.81 mm; it is not used in these
endpoint calculations and is not an adopted receipt requirement. The 8 in
minimum permitted length can be 3.872 mm shorter than the `BG045` model
endpoint, and the 9.5 in minimum can be 4.572 mm shorter than the `BG003`
model endpoint. Clearance to other geometry must use the actual
delivered endpoint in the parent geometry workflow.

With the washer/nut dimensional bounds above, the under-head coordinate of
the nut's bearing face is 78.7908–80.2640 mm for `BG001`, 179.6908–181.1640
mm for `BG045`, and 218.4908–219.9640 mm for `BG003`. Thus the bearing plane
falls 2.286–3.7592 mm before the 4 in `LG,max` coordinate, and 1.8908–3.3640
mm / 2.5908–4.0640 mm after the 8 in / 9.5 in `LG,max` coordinate. These
comparisons are gage-envelope observations only: neither side of `LG,max`
determines the delivered first full-form thread or proves complete nut
engagement. Lawson's `Thread Length Minimum = 1 in` likewise does not locate
the transition. `LB,min` is a separate body/last-scratch gage limit; it does
not equal an actual thread-root or first-full-thread position.

The project correction explains why the ASME table is used instead of a
mis-transcribed supplier reproduction: the six-inch 1/4 in row is `LG,max /
LB,min = 5.25 / 5.00 in`, and a Nickel Systems copy reverses its labels. Do
not turn any `LG`, `LB`, `LT`, `Y`, or minimum-thread-length value into an
assumed delivered thread profile. See the existing
[B18.2.1 source correction](../../bolt-dimension-source-correction.md) and
[thread-boundary screen](../../current-bolt-thread-boundary-screen-2026-09-27.md).

## Conditional sourcing paths and evidence gaps

| Axes | Catalog candidate(s) | What the checked sources establish | What remains source-gap / fit-unresolved |
| --- | --- | --- | --- |
| `BG001` (primary left pair; 4-axis length family) | BrightonBest `847030` or K.L. Jack `25C400HCS5Z`; K.L. `25CNFH5Z` nut and `25NWUS` washers | BrightonBest catalog labels `847030` a 1/4-20 × 4 in Grade 5 hex cap screw, coarse, medium-carbon, zinc CR+3, to ASME B18.2.1. K.L. lists the exact 4 in SKU. The nut/washer candidates above share nominal 1/4 in size. The B18.2.1 comparator minimum length clears the left-pair inherited CAD tip comparator. | Neither exact bolt source establishes this SKU's SAE J429 numeric minima. BBI's B18.2.1 callout conditionally invokes default external Class 2A for a conforming product before coating; the K.L. exact-item details were not retrievable. Neither source supplies part-specific transition, runout, or matched functional engagement evidence. No fit-qualified combination. |
| `BG045` (primary left pair; 4-axis length family) | Lawson/FalconGrip `FA21103`; K.L. `25CNFH5Z` and `25NWUS` | Lawson lists exact 1/4-20 × 8 in carbon-steel Grade 5, bright zinc, UNR coarse partial thread, minimum 1 in thread length; it states 120 ksi minimum tensile, SAE J429 material/mechanical conformance, and ANSI B18.2.1 product dimensions. K.L. nut is 2B/J995 Grade 5; K.L. plain USS washer is Type A Wide. | Lawson does not separately state external Class 2A; B18.2.1 §2.5.2 provides the default if the item conforms before coating. The page supplies no part-specific conformity certificate, coated-thread gauge result, or first-full-thread/transition drawing. Nut chamfers and active-thread dimensions are not in the matched set. No source-qualified delivered fit. |
| `BG003` (primary left pair; 4-axis length family) | Ro-Brand `HC5127`; K.L. `25CNFH5Z` and `25NWUS` are size-family candidates only | Ro-Brand lists 1/4-20 × 9-1/2 in Grade 5 coarse cap screw. | Page's generic 105 ksi statement has no diameter band or part-specific standard; no exact SAE J429 confirmation, 2A class, B18.2.1 compliance, or thread-transition evidence. The standard dimensional and min-length row is only a conditional comparator unless the bolt is shown to conform. No source-complete matched set. |

The adjacent 16 side axes already have the named Lawson 8 in route and the
same nut/washer candidates in the hardware-coverage record. If those 16 and
the four-axis `BG045` length family are later evaluated as one procurement
scenario, the catalog package sizes shown are 25 bolts, 100 nuts, and 100
washers for 20 stacks (five bolts, 80 nuts, and 60 washers left over). This is quantity
arithmetic, not a purchase instruction, fit closure, or price estimate.

The 48 ordinary 6 in axes retain K.L. Jack `25C600HCS5Z` as an existing lead
with the same 1/4-20 nut/washer candidates. That 6 in source path and its
separate `LG` comparison are documented in
[current hardware coverage](../../current-hardware-coverage.md) and
[ordinary hardware basis](../../current-ordinary-hardware-basis.md); no 6 in thread
detail is transferred to the 4, 8, or 9.5 in items here. The twelve retained
3/8 and 1/2 in arrangements need their own retained-bolt and load-path
reviews; this quarter-inch nut/washer discussion does not transfer to them.

## Input and evidence levels

Conditional arithmetic can proceed now using explicitly declared,
source-backed material and profile scenarios. For example, the J429 values
above may define an assumed 1/4 in Grade 5 material case where the analysis
explicitly assumes conformance to that diameter band. That assumption does
not assert that every catalog lead or any received bolt conforms. Thread
transition positions may likewise be declared as bounded or discrete profile
scenarios and varied in analysis. Keep such inputs separate from product
suitability, manufacturer qualification, actual fit, and joint acceptance.

For an **exact catalog-fit scenario**, bind the model to an exact SKU and its
source-supported specification. Require the applicable thread series/class
and dimensional standard plus an exact part drawing or explicitly bounded
profile for under-head to first full-form thread, transition/runout,
last-thread-scratch/body end, point, and length tolerance. Specify the
matched nut's internal class, active-thread region, height, and entry/exit
chamfers. A functional check of exact parts can also establish fit, but then
it describes checked pieces rather than an assumed catalog dimension. `LG`,
`LB`, `LT`, `Y`, and a minimum thread-length field alone do not locate
complete nut engagement.

For claims about **actual received hardware**, use lot paperwork and/or
measurements that identify the observed pieces and relevant dimensions. No
receipt, inventory, or delivered-part observation is claimed here; checklist
Actual/Disposition cells remain blank until observed. Lot traceability and
receipt inspection are not prerequisites for the conditional arithmetic
scenarios in this note.

The 3,816 lbf nut proof reference remains conditional on the declared J995
Grade 5 finished-hex UNC case; it is not a stripping value. For washers, a
low-carbon material description or Rc 38–45 hardness alone does not furnish
a yield minimum. If a numerical washer-resistance scenario is needed, define
and source that property independently; any later claim about actual pieces
still requires observed evidence. These input tiers support analysis without
qualifying a complete corner joint or authorizing an order or physical work.

## Source record

Read-only supplier/manufacturer pages were checked 2026-09-30. Public pages
and cached files are listed below; hashes apply to the local bytes in
[`fastener-source/`](fastener-source/). K.L. Jack and STS pages were readable
through indexed supplier page results but returned HTTP 403 when fetched to
the local source cache; their URLs remain linked for recheck. Prices are
omitted because listings are dynamic and not needed for this screen.

| Source | Evidence used | Local cache / SHA-256 |
| --- | --- | --- |
| [Lawson `FA21103`](https://www.lawsonproducts.com/products/hex-cap-screw-grade-5-1-4-20-x-8-fa21103) | Exact 8 in bolt listing and technical fields; checked 2026-09-30. | [`lawson_fa21103.html`](fastener-source/lawson_fa21103.html) · `f55332f347024e3e73e3334e8e996bb5b6cdfc91bd8fdec6d62395983ec9d0d3` |
| [BrightonBest Grade 5 catalog PDF](https://www.brightonbest.com/download/catalogs/usa/BBI_USA_G5.pdf) | 1/4-20 × 4 in Grade 5 cap screw code `847030`; page 22. | [`bbi_usa_grade5_catalog.pdf`](fastener-source/bbi_usa_grade5_catalog.pdf) · `407e7f1e5bbf8cec5d6d1dc5737bd48909e1c012de9ccbc88d66e265c277c665` |
| [Ro-Brand Grade 5 USS cap-screw catalog](https://www.robrandinc.com/grade-screws-c-3_4_360.html) | `HC5127` listing and category-level grade description; checked 2026-09-30. | [`robrand_grade5_uss_cap_screws.html`](fastener-source/robrand_grade5_uss_cap_screws.html) · `cb150220987943eff5f5f6b4c311e04676784b1c2b3995d4f791e6c0e98467f1` |
| [K.L. Jack `25CNFH5Z`](https://www.kljack.com/products/25cnfh5z/) | Nut grade, thread, dimensional/finish designations, nominal geometry, and package size. | Browser supplier result; local fetch returned HTTP 403. |
| [K.L. Jack `25NWUS`](https://www.kljack.com/products/25nwus/) and [Fastenal low-carbon Type A Wide specification](https://www.fastenal.com/content/product_specifications/USA.FW.LC.USS.A.P.00.pdf) | Washer material callout and Type A Wide dimensional bounds. | Browser supplier result; local fetch returned HTTP 403. |
| [K.L. Jack `25NWUS8Z`](https://www.kljack.com/products/25nwus8z/) | F436 Type A Wide alternative, Rc 38–45 and dimensions; no yield minimum. | Browser supplier result; local fetch returned HTTP 403. |
| [STS SAE J429 technical data](https://www.stsindustrial.com/services-resources/fastener-specifications/sae-j429-technical-data) | J429 size-banded Grade 5 strength table and 2014-05 attribution. | Browser supplier result; local fetch returned HTTP 403. |
| [STS SAE J995 technical data](https://www.stsindustrial.com/services-resources/fastener-specifications/sae-j995-technical-data) | J995 Grade 5 finished-hex proof stress and 1/4-20 At table. | Browser supplier result; local fetch returned HTTP 403. |
| [ASME B18.2.1-2012 (R2021) record](https://www.asme.org/codes-standards/find-codes-standards/b18-2-1-square-hex-heavy-hex-askew-head-bolts-hex-heavy-hex-hex-flange-lobed-head-lag-screws), [project correction](../../bolt-dimension-source-correction.md), and linked 4 in / 8 in project screens | Standard edition attribution, Table 13 length-tolerance values, and corrected 1/4 in `LG/LB` table ordering. | Standard copy/hash are already pinned by the linked project correction; no duplicate standard file created here. |
| [ASTM F436/F436M-24 record](https://store.astm.org/f0436_f0436m-24.html) | Scope of material/dimensional/hardness sampling requirements for hardened washers; it does not publish a washer yield minimum here. | Public abstract only; not copied. |

The ignored [`fastener-inputs.json`](fastener-inputs.json) records the three
source-axis snapshots, screen calculations, source URLs, and local cache
hashes. It is raw local evidence, not a maintained specification.
