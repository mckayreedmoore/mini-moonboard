# Panel screw necessity audit

The published horizontal-service layout has **87 panel screws**, including 39 on the two center
principals. The dense center rows came from an inherited **150 mm maximum interval
rule**, not a demonstrated minimum fastener count. No exact duplicate axis was
found. No individual screw has yet been proved removable.

The [complete 87-row CSV](../fea/results/panel-screw-necessity-v1.csv) records each
screw's panel, receiver, original/infill provenance, purpose, position, gross
stock end/edge distances, actual spacing, penetration, historical repair reserve,
signed demand witnesses and both proposed removal classifications. The
[JSON audit](../fea/results/panel-screw-necessity-v1.json) also records group totals
and input hashes. Original means a retained non-infill axis, including subsequently
added service-rail screws; it is not proof that the screw is essential.

| Receiver purpose | Screws | Actual arrangement | Reduction status |
| --- | ---: | --- | --- |
| Center principals | 39 | Four original axes per main panel, plus 23 interval infill screws; 9–10 per panel | Coordinated 12-infill removal is the primary test candidate |
| Outer rims | 16 | Four per main panel; gaps approximately 306–406 mm | Untested reductions; retain perimeter load paths for the first comparison |
| Top and bottom rails | 8 | Two per main panel at its top or bottom boundary | Untested reductions; preserve edge retention |
| Horizontal service rails | 16 | Four per main panel near the horizontal joint | Untested reductions; preserve independent panel-edge attachment |
| Kicker posts | 8 | Two at each of four kicker/post connections | Untested reductions; main-panel load samples do not establish kicker sufficiency |
| Total | 87 | Four main panels: 20, 20, 19 and 20 screws; kickers: four each | This is neither a verified minimum nor an optimized schedule |

The four center-principal rows currently have gaps of approximately 100–150 mm.
Their original four-screw rows were supplemented when six interior principals
existed; only two center principals remain. That history explains the dense-center,
sparse-outer difference. It does not establish that either density is correct.
See the [reference review](panel-screw-reference-review.md) for why generic wall
schedules and MoonBoard guidance do not establish this frame's minimum count.

All modeled #8 ×2 inch panel screws have 32.54375 mm gross penetration behind the
18.25625 mm panel. For XFT08P-2000, nominal embedded thread is 31.496 mm including
the tapered tip. Across all 87 gross-stock calculations, the smallest face edge
distance is 19.05 mm and the smallest end distance is 46.9 mm. These calculations
include the actual lower bevel plane for sloping receivers; they do not replace
solid checks of round passages, fasteners, drivers or machining tolerances.

Historical future-insert reserves are 12.1412 mm diameter ×17 mm deep, and all
87 passed their original grooved-model fit audit. Retaining an axis preserves
its reserved location, but its fit must be rechecked against the round-bore
candidate. A removed screw does not need a pilot or reserved insert hole drilled.
Reserves are possible future repair space, not approved insert substitutions.

## Defined removal hypotheses

The primary **75-screw candidate** removes twelve existing infill axes while
retaining all 64 original/service axes and eleven infill axes. Within each original
center-principal interval, it keeps the minimum number of existing infill positions
needed for a maximum 300 mm gap. It preserves the original first and last screws,
all perimeter and horizontal-joint screws, and all kicker connections. The 300 mm
criterion is a comparison hypothesis, not a manufacturer instruction.

The [completed 75-screw comparison](panel-screw-sensitivity.md) found only a
1.61% maximum panel-displacement increase but a 20% increase in the controlling
F10 withdrawal demand. Neither pattern is qualified. A straight, symmetric
12-screw-per-face layout is the next comparison requested by the owner; the
existing results do not prove that more than twelve screws per face are needed.

The exact twelve removals are the `_1_1`, `_2_1` and `_3_1` infill positions in
each of the four main-panel/center-principal groups; the CSV lists every complete
connection name. This is a simultaneous joint-pattern change, not a claim that
twelve individually small reactions prove collective redundancy. A more aggressive
**64-screw hypothesis** removes all 23 infill screws. It remains an optional,
untested alternative rather than a recommendation.

Existing signed demands do not justify simply deleting low-force-looking screws.
One upper-left original principal screw reaches approximately 1064 N withdrawal
at F10; an upper-left infill screw reaches approximately 455 N. Some lower screws
attract substantial lateral load under C6. Right-side reactions look smaller in
the previous batch because its sampled holds were left/center biased. Symmetric
geometry alone does not validate asymmetric deletion.

The reduced pattern requires coupled and mirrored load cases, comparison of
retained individual withdrawal/lateral forces, stresses, displacement and bearing
state, plus separate geometry and repair-space checks. A modest displacement
change alone cannot qualify a reduction. Every screw category above remains
subject to that reasoning; the first 75-screw test is deliberately limited and
cannot establish the optimal minimum across all 87 screws.

## Product-specific installation references

For evaluated SPAX Construction Screws, TER 2010-02 §9.5 does not require lead
holes; §9.6 requires flush installation without overdriving. Table 2 identifies
XFT08P-2000's T20 drive. Table 10 permits its face-grain withdrawal calculation
with at least one inch of embedded thread, including the tip. That specific
condition explains why the general 1.5 inch rule in §9.7 does not alone reject
this withdrawal calculation. Table 13 separately lists 1 9/32 inch penetration
for the two-inch #8/23/32-inch plywood combination, but its SPF main-member scope
does not automatically establish DF-L lateral capacity. Combined action and all
applicable adjustments remain unresolved. [Current SPAX evaluation report](https://www.drjcertification.org/report/download/1936).

SDS25112 is a different product and follows the selected Simpson connector
instructions. Simpson describes SDS as normally installed without predrilling.
Its manufacturer catalog additionally specifies a 5/32 inch wood pilot **where
predrilling is required**; that is conditional guidance, not a command to predrill
every ML24Z screw and not a steel-hole dimension. The accessible cited catalog
edition is 2021; current connector/application instructions must establish when
the condition applies. CAD's 6.35 mm SDS shaft and 4.1402 mm SPAX shaft are not
installation pilot diameters. [Simpson SDS catalog page](https://palmerdonavin.cld.bz/simpson-strong-tie-wood-construction-connectors/347/).

The opposed header SDS screws have staggered axes and at least 4.624 mm nominal
shaft clearance. Retaining the specified SDS schedule preserves the evaluated
fastener type, though it still does not qualify this frame. A twelve-through-bolt
alternative requires aligned bracket holes and independent evaluation of the
modified bracket/bolt joint; it is not established as stronger. Choose it for an
explicit fabrication or service objective, not to remedy a collision that the
present nominal geometry does not contain.

## Reproduction and authentication

```sh
uv run python -m fea.panel_screw_inventory --output /tmp/new-panel-screw-inventory
uv run pytest tests/test_panel_screw_inventory.py -q
```

The script requires all eight coupled force cases and authenticates their reports
against the batch summary, matching source snapshots, final-cycle reports and
native input/deck/DAT/log hashes. Force witness locations must match each CSV axis.
It rejects missing/extra panel-force names and coincident axes across groups.
Current round-bore geometry and removal-sensitivity results remain separate
artifacts; the historical force inventory does not claim to solve either change.
