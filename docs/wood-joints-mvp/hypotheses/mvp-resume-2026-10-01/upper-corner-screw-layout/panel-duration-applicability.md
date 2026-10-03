# Plywood reference duration applicability

## Result and scope

N14's frozen [panel-reference completion](panel-reference-completion.md),
`rawlocal/panel-reference-completion/attempt01`, compares plywood gross cuts
at **CD = 1.00, normal duration**. Its rolling-shear maximum
**1.4736027737095434** is a normal-duration reference exceedance. With the
same saved demand and a conditional cumulative ten-minute peak-duration
reference, **CD = 1.60**, that ratio is **0.9210017335684646**. With the
seven-day reference, **CD = 1.25**, it remains **1.1788822189676347**.

The ten-minute comparison uses the existing favorable full-peak duration
hypothesis for brief high loads. It does not establish actual cumulative
use from the word “dynamic.” Repeated full-peak events accumulate over the
service life. These are reference comparisons of saved results; N14's
producer, normal-duration exceedance counts, results and acceptance flags
remain frozen.

## Direct primary basis

[APA Panel Design Specification D510C (2012)](https://design.medeek.com/resources/structural/D510C_2012.pdf),
§4.5.1/Table 5, printed page 19, identifies normal-duration strength values
and lists 0.90 permanent, 1.00 normal, 1.15 two months, 1.25 seven days and
1.60 wind/earthquake. It excludes impact adjustment for panels. Tables 9
(pages 23–25) and 10 (page 26) supply the frozen grade/category values and
species-group multipliers. This APA-authored mirror was read and its bytes
matched the helper's existing PDF pin; a newer edition was not substituted.

[AWC NDS 2024 Chapter 2](../../upper-block-strength-2026-10-01/source-cache/chapter2-2024-awc.pdf),
§2.3.2.1/Table 2.3.2, printed pages 12–13, bases duration on cumulative
maximum loading: approximately ten years for normal duration, seven days
for 1.25 and ten minutes for 1.60. Footnote 2 prohibits factors above 1.60
for wood structural panels. [NDS 2024 Appendix B](../../upper-block-strength-2026-10-01/source-cache/appendix-2024-awc-20260911.pdf),
B.1.2(b), page 170, gives the ten-minute factor by duration; B.1.2(d)
also identifies its wind/earthquake application. The appendix is
nonmandatory; §2.3.2.1 supplies the governing cumulative-duration rule.
Thus the conditional ten-minute comparison has a duration basis without
classifying climbing as wind or assigning an impact factor of 2.0.

## Factors applied to the actual references

Values below use the helper's A-A/A-C 23/32 category. Paired values are
parallel/perpendicular to the declared strength axis. N14 already includes
the width factor `Cs` on bending/tension; at the peak bending witness,
1217.6125 mm gross width gives `Cs = 1.00`.

| Reference | Normal Group 1 base | Existing Group 4 multiplier | Duration treatment |
| --- | --- | ---: | --- |
| Bending `FbS` | 775 / 455 lbf-in./ft | 0.67 | Strength: 1.00 normal; 1.25 seven days; conditional 1.60 ten minutes |
| Axial tension `FtA` | 5100 / 3400 lbf/ft | 0.67 | Same strength factors |
| Axial compression `FcA` | 4800 / 2900 lbf/ft | 0.61 | Same strength factors; no buckling acceptance implied |
| Planar/rolling shear `Fs(Ib/Q)` | 350 / 350 lbf/ft | **1.00** | Same strength factors |
| Helper's separate membrane shear `Fvtv` | 105 lbf/in. | 0.68 | Strength duration eligible; not the transverse-cut denominator |
| Elastic stiffness `EI`, `EA` | Frozen directional helper values | 0.56 | No duration multiplier; no stiffness change |
| Helper's face-bearing reference | 360 psi, deformation limited | None in helper | No strength-duration increase |

The first four rows are N14 gross-cut references. The last three distinguish
other helper properties; they introduce no additional comparison. APA
Tables 9–10 support the strength/group values; NDS Table 2.3.2 footnote 1
excludes elastic moduli and deformation-limited perpendicular bearing
from duration adjustment.

For an eligible strength capacity, use
`R = base × existing group factor × applicable Cs × CD`, with units converted
once. For this note, `ratio(CD) = saved ratio(CD=1) / CD`.
Do not reapply the Group 4 reductions or multiply 1.25 by 1.60.

| Saved gross maximum | Normal, CD 1.00 | Seven days, CD 1.25 | Conditional ten minutes, CD 1.60 |
| --- | ---: | ---: | ---: |
| Group 1 axial | 0.026061 | 0.020849 | 0.016288 |
| Group 4 axial sensitivity | 0.042723 | 0.034179 | 0.026702 |
| Group 1 bending | 0.654407 | 0.523525 | 0.409004 |
| Group 4 bending sensitivity | 0.976726 | 0.781381 | 0.610454 |
| Planar/rolling shear, both groups | **1.473603** | **1.178882** | **0.921002** |

The shear witness is `a12-forward`, `main_upper_left`, cut axis 1,
station −441.138044 mm, gross width 1217.6125 mm. Its signed mean demand
is −7.526965546630302 N/mm. Normal capacity is 350 lbf/ft
(5.107866028022227 N/mm); seven-day capacity is 437.5 lbf/ft;
ten-minute capacity is 560 lbf/ft (8.172585644835562 N/mm).
N14 retains **24 normal-reference exceeded traces per group**, not 24
independently failed panels.

## Fixed demand and remaining applicability limits

The [frozen load basis](frozen-load-basis.md) retains one 250 lb climber
times the existing dynamic demand factor 2, 25 kg equipment once, current
gravity, signed 300 N horizontal action and the 100 mm hold lever.
The force multiplier 2 and strength-duration factor have separate purposes.
No second dynamic multiplier, reduced force or 140 lb load variant enters
this note. Frame CD 1.25 and Hillman favorable CD 1.60 are separate existing
hypotheses; neither automatically establishes plywood duration or product
applicability. Hillman's existing adjustment is already applied once.

NDS §2.3.2.2 requires the controlling applicable load combination; these
saved combined-case ratios do not establish a permanent-only panel check
at CD 0.90. The Group 4 comparison retains the saved Group 1 elastic response.

Purchased Roseburg AC identity is retained. Delivered grade/species group,
23/32-category applicability, layup, strength-axis placement and dry-service
applicability remain declared assumptions. Neither species-group comparison
establishes delivered plywood properties. No additional measurement gate is
introduced here.

The below-reference ten-minute **gross mean** does not qualify local rolling
shear, veneer/interlaminar stresses, concentrated hold/head transfer,
hole/countersink ligaments, kicker cutouts, net sections, effective widths,
combined plate strength, buckling or serviceability. Saved cuts retain
`local_plate_or_net_section_strength_ratio=null` and
`complete_panel_acceptance=false`; N14 acceptance remains false. No model,
load variant, test, solve or CAD execution was performed for this note.

## Authenticated source identities

SHA-256 values identify the exact bytes read. Primary PDFs were read directly;
APA retrieval remained in memory. Saved output hashes were checked against
the N14 receipt; the receipt itself is separately identified below.

| Source | SHA-256 |
| --- | --- |
| APA D510C 2012 PDF, URL above | `6141e0fe02ad0db8ddec20becf2ec25c85accd21c9796e51411d19448e5762ca` |
| NDS 2024 Chapter 2, linked cache | `6bb62f3560ab5bcdbed297cd03bba560f20882a638ee591c0c97013f7c075100` |
| NDS 2024 Appendix, linked cache | `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31` |
| `fea/reinforced_panel_checks.py` | `1cf47584c36ab5c513ee74072f66782b0aa3907cca6b0ee940218d84693d634d` |
| `panel-reference-completion.py` and attempt01 snapshot | `1943198db40ed6729f6c93c3a1196e1642d3a3843fb2bbf5e826aa6b35a116b1` |
| N14 attempt01 `receipt.json` | `5b42272f49c1924546abab3bd4d036a0a95f7afb2700055fb2e769ab56a3db91` |
| N14 attempt01 `summary.json` | `dfa8a93d686e82b5ee8099ad55fce66f436d1720ab5fb51b4cdf6c1b2761c6f5` |
| N14 attempt01 `sources.json` | `bb4ef5b08a4cfa58218a9f8da2749d4b5bc447d3062abbb3c68ff718b2a2792f` |
| N14 attempt01 `panel-cuts.jsonl` | `8078ad3ff8237af2ee51d3ce01f3036613a77eadb26864ed00ac3ade2314b398` |
| Preserved `frozen-load-basis.md` | `fed6312287c074fbe85c35168ef84388e283be027eb0dc27445b0b30e87b4425` |
