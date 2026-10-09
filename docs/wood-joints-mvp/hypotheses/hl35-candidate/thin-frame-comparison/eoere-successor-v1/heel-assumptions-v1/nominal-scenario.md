# Owner-requested 6.35-mm thickness and radius

The owner requested using **6.35 mm as the working catalog thickness** and
testing an **inside radius of 6.35 mm**. The source mechanics geometry already
uses 6.35-mm steel. The original 6-mm comparison and the first
[assumption study](README.md) remain frozen; this is an additional nominal
reference scenario at the same saved actions.

[Input](nominal-scenario-input.json), [calculation](extend_scenario.py) and
[result](nominal-scenario-result.json) retain the exact six-case source chain.
The new helper reuses the original pin-verification helpers and steel kernel.
It verifies **650 source pins before and after**, recovers all **528 owned
case/band comparisons**, and checks the new section against an ideal
pure-bending known answer. No candidate geometry, stiffness or response is
rebuilt or solved.

| Quantity | Result |
| --- | ---: |
| Working thickness / assumed inside radius | 6.35 / 6.35 mm |
| Largest gravity-bounded heel screen | 140.479342 MPa |
| Unchanged conditional reference, 235/1.67 | 140.718563 MPa |
| Largest reference ratio | 0.998300 |
| Reference exceedances | 0 of 528 |
| Difference below reference | 0.239221 MPa, or 0.170000% |

The governing witness is still A12-left, `eoere_clip_single_top_left_1`,
`arm-z/far-plus`. Zero exceedances describe this mathematical scenario; the
small difference is not an established product strength reserve. Actual metal
thickness, material, bend geometry/thinning, hole datums, coupled
three-dimensional heel behavior and full joint resistance remain unverified.
No actual geometry, resistance or physical release flag is enabled.

An inside radius equal to thickness is a reasonable development assumption
for ordinary mild-steel air bending. It is not an automatic geometric law.
[WILA's guidance](https://www.wilatooling.com/applications/air-bending/)
suggests die openings of six to eight times the steel thickness and explains
that the die opening influences the formed radius. Its
[mild-steel chart](https://catalog.wilatooling.com/WILA-Catalog-GB/110/)
lists 0.225-inch radius at a 1.5-inch die opening and 0.300-inch radius at a
2-inch opening. Combining those with 0.25-inch material gives an **inferred
ballpark of 0.9–1.2 times thickness**, about **5.7–7.6 mm** here. This is
manufacturing guidance, not a verified eoere process or dimensional range.

The radius of interest is the **inside concave curve**, viewed from the side
of the bracket. A metric radius/fillet gauge compares known curved profiles
against it; [Starrett's gauge description](https://www.starrett.com/products/precision-measuring-tools/precision-hand-tools/fixed-gage-standards/radius-gages/272MB)
describes internal and external checks. Match the rounded gauge profile to
the inside arc, check for gaps, and repeat at multiple positions across the
bracket width. Record the matching range and measurement uncertainty rather
than claiming more precision than the gauge permits. Measure steel thickness
separately and account for coating and any bend thinning.

For a circular bend with constant thickness, `R_out = R_in + t`.
Thus the requested 6.35/6.35-mm case has a **12.70-mm outside
radius**. Measuring the outside curve alone requires verifying thickness and
concentricity before inferring the inside radius. A perspective listing
picture cannot establish that geometry precisely.

A dimensioned supplier profile or sample measurement would clarify the
dimensions. Radius equal to thickness defines the recorded nominal scenario;
the narrow reference margin makes actual dimensional evidence useful before
interpreting it as physical adequacy. Physical testing remains outside the
current completion scope. The previously described centered/off-center
low-load test is an unperformed optional diagnostic, not a new completion gate.

Reproduce into a new output path:

```sh
.venv/bin/python -B docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/heel-assumptions-v1/extend_scenario.py --input docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/heel-assumptions-v1/nominal-scenario-input.json --out /tmp/moonboard-heel-nominal-reproduced.json
```

Keep these compact supplemental files active with the original study and
closed reports. The original packet bytes, six-case evidence, selected
baseline and paused redesign work remain unchanged.
