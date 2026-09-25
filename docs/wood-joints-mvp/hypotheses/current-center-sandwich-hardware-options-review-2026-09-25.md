# Independent review: current center and knee hardware length screen

**Reviewed:** 2026-09-25. **Review result:** conditional dimensional screen is
arithmetically and geometrically consistent. No product is selected. The
`center_principal_header` NDS boundary remains explicitly unresolved, and the
new shared 8-inch route for the four inner-header knee axes is consistent with
the existing side-axis route.

## Frozen sources and scope

Review target:
[`current-center-sandwich-hardware-options.md`](../current-center-sandwich-hardware-options.md),
SHA-256 `644ddb4c42b3c14513739f96e44dc4d860de42ab4f4431af1d963ec1c6ef4a1c`.

The exact axis source is
[`grip-screen-attempt02.json`](evaluation-resume-2026-09-24/grip-screen-attempt02.json),
SHA-256 `9f84a15ed05ca9832f594c4a0b2c8d1322b90e74e462aa7c725b031bad69643a`.
The calculation basis was cross-checked against
[`bolt-resistance-basis.md`](../bolt-resistance-basis.md), SHA-256
`ff14564aeb3eb9d604d39d5386e8a1978862f4088a4f7e5483d9defbeb0b3c47`,
[`bolt-dimension-source-correction.md`](../bolt-dimension-source-correction.md),
SHA-256 `3933bf5bf9d2491b4618691a77d75f929dfc838da7dbd4fff02de9e986846555`,
and the 8-inch comparison basis
[`current-side-hardware-option.md`](../current-side-hardware-option.md),
SHA-256 `19906c7d8eba3aa035a36de9d6e936cdca222c8e24fde6325863585ecc145522`.

The 24 listed IDs occur as four exact axes per family in the frozen JSON.
Their grips and ordered head-to-nut receivers agree with the note: 127 mm
(`center_post_cleat` then 38.1 mm post), 122 mm (`center_principal_cleat`
then 38.1 mm principal), 167 mm (38.1 mm header then 128.9 mm cleat),
172.8 mm (134.7 mm cleat then 38.1 mm header), 177.1 mm (header then
139 mm inner-frame block for `_1`, reverse order for `_2`), and 215.9 mm
(38.1 mm spine, 88.9 mm side, then 88.9 mm inner-frame block). The current
6.35 mm shaft remains a CAD envelope, not a delivered bolt dimension.

The added 8-inch section maps exactly to the four
`knee_outer_{left,right}_inner_header_{1,2}` axes. Each has a 177.100 mm
grip and 202.500 mm modeled endpoint. The frozen receiver orders confirm
`_1`: 38.1 mm `base_header`, then 139 mm inner-frame block; `_2`: 139 mm
inner-frame block, then 38.1 mm `base_header`. Thus the far receiver for
`_1` is the block and for `_2` is the header, as the source text states.

## Independent dimensional recomputation

Using two Type A Wide washer thicknesses of 1.2954–2.032 mm, finished nut
thickness of 5.3848–5.7404 mm, and a 3.175 mm physical tip projection gives
`latest far-nut face = G + 9.8044 mm` and `tip target = G + 12.9794 mm`.
The six screened standard length classes, minimum overall lengths, and tip
margins recompute as:

| Grip `G` (mm) | Nominal length | Minimum length (mm) | Tip target (mm) | Margin (mm) | `LG,max` / `LB,min` (mm) |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 127.000 | 5.75 in | 143.510 | 139.9794 | +3.5306 | 127.000 / 120.650 |
| 122.000 | 5.50 in | 137.160 | 134.9794 | +2.1806 | 120.650 / 114.300 |
| 167.000 | 7.50 in | 185.928 | 179.9794 | +5.9486 | 165.100 / 158.750 |
| 172.800 | 7.50 in | 185.928 | 185.7794 | +0.1486 | 165.100 / 158.750 |
| 177.100 | 7.75 in | 192.278 | 190.0794 | +2.1986 | 171.450 / 165.100 |
| 215.900 | 9.25 in | 230.378 | 228.8794 | +1.4986 | 209.550 / 203.200 |

For each row, the immediately shorter quarter-inch class fails the same
minimum-length tip target. The result establishes the shortest *nominal
class in this standard-increment screen*; it does not establish that a class
is a stocked or available catalog item. The note keeps this distinction and
does not generalize the 5.50-inch K.L. Jack listing to other lengths. The
5.50-inch lead is context only: its detail page timed out, and the note does
not infer stock, thread class, `LG`/`LB`, functional fit, or a qualified
matched pair. No washer, nut, finish, or price field changes that boundary.

The source correction file records a transcription conflict in the linked
Nickel Systems PDF's six-inch 1/4-inch cell. The current screen's six
candidate `LG`/`LB` rows agree with the named ASME B18.2.1-2012 Tables 12–13
and the current Nickel Systems HTML table; the PDF discrepancy does not alter
these recomputed values. Keep the ASME standard as authority and the existing
source-correction note visible when reusing that PDF.

## NDS diameter screen and remaining ambiguity

The local NDS-2024 §12.3.7.2 basis requires the one-quarter threaded-bearing
condition in each member that holds threads to use nominal diameter `D`;
otherwise the lateral-yield input is thread-root diameter `Dr` or a more
detailed threaded-section method. It does not infer thread location from
nominal length. From each JSON receiver sequence, the last receiver is the
only member reached by the ASME `LB,min` boundary in the geometry screen. The
note's max-thread-length arithmetic is correct:

| Nut-side member | Receiver length (mm) | `LB,min` thread-length screen (mm) | One-quarter (mm) | Required actual `LB` (mm) |
| --- | ---: | ---: | ---: | ---: |
| `center_post` base post | 38.1 | 8.382 | 9.525 | 119.507 |
| `center_principal` base principal | 38.1 | 9.732 | 9.525 | 114.507 |
| `center_post_header` cleat | 128.9 | 10.282 | 32.225 | 136.807 |
| `center_principal_header` base header | 38.1 | 16.082 | 9.525 | **165.307** |
| `knee_inner_header_1` inner-frame block | 139.0 | 14.032 | 34.750 | 144.382 |
| `knee_inner_header_2` base header | 38.1 | 14.032 | 9.525 | 169.607 |
| `knee_side` inner-frame block | 88.9 | 14.732 | 22.225 | 195.707 |

The `center_principal_header` row's measured `LB` target is 165.307 mm,
0.207 mm greater than the standard table's `LG,max` of 165.100 mm. ASME
B18.2.1 defines `LB` at the last thread scratch and `LG` at the face of a GO
ring gage assembled by hand as far as the thread permits; Table 12 supplies
`LB,min` and `LG,max`, not this delivered bolt's measured relationship or
transition. I found no primary-source statement in the checked material that
lets this review declare the required actual `LB` impossible from `LG,max`
alone. The current document correctly leaves actual `LB` unknown. Its
nominal-`D` condition for that row therefore remains unestablished by these
table limits and needs part-specific dimensional evidence if that method is
later used; otherwise use `Dr` or a supported detailed threaded-section
method. This is a conditional diameter-input boundary, not a product failure
or capacity finding.

For the other two rows exceeding one-quarter at `LB,min`, the actual body
coordinates needed are below `LG,max` (114.507 vs 120.650 mm for
`center_principal`; 169.607 vs 171.450 mm for `knee_inner_header_2`). The
note appropriately treats their improvement as unproved until actual thread
transition/body measurements establish it. The four other nut-side rows pass
this geometric fraction using `LB,min`; that alone is not a wood-capacity or
joint result.

## Shared 8-inch route for the knee inner-header axes

The added route reuses, without extending its scope beyond the stated four
axes, the exact Lawson FA21103 bolt and K.L. Jack nut/washer candidates in the
source-bound 16-axis side option. The
[Lawson product page](https://www.lawsonproducts.com/products/hex-cap-screw-grade-5-1-4-20-x-8-fa21103)
currently identifies FA21103 as a 1/4-20, 8-inch, Grade 5, zinc-finished,
partially threaded hex cap screw. It shows a 25-piece pack and a 1-inch
minimum thread-length entry, states dimensions to ANSI B18.2.1, and requires
login / an availability check for price or current stock. These facts support
a catalog lead only; the listing does not locate the thread transition or
establish a matched nut fit or delivery. The source note keeps these fields
open.

For `G = 177.100 mm`, independent recomputation gives:

| Check | Recomputed result |
| --- | ---: |
| Earliest nut bearing plane | 179.6908 mm |
| Latest far-nut face | 186.9044 mm |
| Minimum physical-tip target | 190.0794 mm |
| B18.2.1 minimum overall length at 8 in | 198.628 mm |
| Minimum-length margin past tip target | +8.5486 mm |
| `LG,max` / earliest-bearing-plane margin | 177.800 / +1.8908 mm |
| `LB,min` | 171.450 mm |
| Minimum overall length minus CAD endpoint | −3.872 mm |

The far wood face at maximum head-washer thickness is `177.100 + 2.032 =
179.132 mm`. Extending the `LB,min` thread boundary to that face gives a
7.682 mm upper screen for possible thread bearing in whichever final
receiver is on the nut side. That is below one-quarter of either possible
far receiver: 34.750 mm for the 139 mm block and 9.525 mm for the 38.1 mm
header. The tighter case has a 1.843 mm geometric margin. This is correct as
a conditional screen using the standard minimum body boundary, not a claim
about the actual received transition or wood resistance. It does not infer
any ordering between actual `LB` and actual `LG`.

The combined piece count also checks: the prior 16-axis option plus four
adds to 20 bolts, 20 nuts, and 40 washers. One 25-piece Lawson pack leaves
5 bolts; one 100-piece nut box leaves 80 nuts; one 100-piece washer box
leaves 60 washers. The note carries the reused 2026-09-25 nut/washer listed
prices as package context and correctly leaves the Lawson bolt price, stock,
delivery, total cost, thread fit, finish match, washer support, and endpoint
fit unresolved. No quantity or price result implies a purchase or selection.

## Review disposition

The exact-axis binding, quarter-inch class selection, stack formulas,
minimum-length margins, and NDS thread fractions—including the new 8-inch
four-axis extension—are consistent with the frozen source data and stated
dimensional assumptions. The revised source note now clearly states that the
`center_principal_header` requires measured `LB ≥ 165.307 mm`, while its
7.50-inch row has `LG,max = 165.100 mm`; table limits alone do not establish
the part-specific relationship or satisfy the nominal-`D` exception. This
review makes no `LB ≤ LG` inference. No further correction is indicated.
Preserve that row as unresolved pending part-specific evidence if nominal
`D` is later needed. No full-form-thread tail, Grade 5 resistance, supplier
availability, or joint capacity is established by this review.
