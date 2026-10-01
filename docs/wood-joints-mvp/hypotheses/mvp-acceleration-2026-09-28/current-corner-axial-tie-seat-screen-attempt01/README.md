# Current outer-corner axial tie and washer-seat component screen

This bounded calculation inventories the six BG001/BG003/BG045 outer-seat
bolt ties and all twelve end seats at load factor 1.0 in the source-bound
a12-rear response. It reports uniform-average washer-seat pressure and
conditional component references only. It does not accept a complete joint,
qualify hardware or material, reopen the twelve preserved LEG/RUNNER
arrangements, or change the model.

The input is the passing
[`corner-demand-report.json`](../current-corner-native-demand-export-attempt03/corner-demand-report.json),
SHA-256
`812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17`. It
binds a12-rear model `8a90452d…1cda8`, response
`892dadee…e1274`, the parent all-body audit, and the parent terminal
assessment. The full-load response/corner gates and independent all-body
balance passed for this one conditional case; its selected floor branch is
still diagnostic-only. No new native solve was performed.

Reproduce and verify with the standard library plus the pinned local bearing
helper:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-axial-tie-seat-screen-attempt01/produce.py --write
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-axial-tie-seat-screen-attempt01/produce.py --verify
```

The complete source-bound seat inventory and calculations are in
[`screen.json`](screen.json), SHA-256
`cae5c67d1166205aaa442c8ae889c95245162b7d1569cf264b13bc260d712ac4`.

| Group / bolt axis | Two outer seats (head / nut) | Positive tie tension (N) | CAD full-annulus average pressure (MPa) | 25NWUS minimum-annulus pressure (MPa), where the axis has that candidate lead | Applicable base-timber Fc⊥ reference ratio | Separate block DF-L No. 2 what-if ratio |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| BG001 `post_1` | spine / base post | 64.96606 | 0.291686 | 0.304109 | 0.07057 at base post | 0.07057 at spine, hypothetical only |
| BG001 `post_2` | spine / base post | 18.47315 | 0.082941 | 0.086474 | 0.02007 at base post | 0.02007 at spine, hypothetical only |
| BG003 `side_1` | spine / inner-frame block | 95.96739 | 0.430876 | — | — | 0.09999 at both seats, hypothetical only |
| BG003 `side_2` | spine / inner-frame block | 43.50841 | 0.195345 | — | — | 0.04533 at both seats, hypothetical only |
| BG045 `inner_header_1` | base header / inner-frame block | 119.34300 | 0.535828 | 0.558649 | 0.12964 at base header | Not applicable: block seat load is parallel to proposed grain |
| BG045 `inner_header_2` | inner-frame block / base header | 19.88171 | 0.089265 | 0.093067 | 0.02160 at base header | Not applicable: block seat load is parallel to proposed grain |

Each physical bolt carries the same tension magnitude at its two outer seats;
the exported force vectors on those two receivers are equal and opposite.
BG003's three-member stack has two end seats only: its `base_side_left` middle
receiver has no independent axial washer-seat tie.

The geometry source derives a CAD annular plan area of about `222.7262 mm²`
from the modeled washer solid volume and thickness. The first pressure column
is `T / A_CAD`; this is a uniform-average model conversion, not effective wood
contact area or a local pressure field. For the four axes with a 25NWUS washer
lead (BG001 and BG045), a separate dimensional scenario uses the existing
Type A Wide range (`OD 0.727–0.749 in`, `ID 0.307–0.327 in`, thickness
`0.051–0.080 in`) at minimum OD / maximum ID. The model bore diameter is
`7.5 mm = 0.29528 in`, so the candidate ID governs the inner annulus. The
resulting full-annulus area is `213.6279 mm²`. That range is not a selected or
delivered washer; the exact finished wood support polygon, head/nut footprint,
flatness, cuts and gaps are still absent. BG003 has no washer product lead, so
its pressure column remains CAD-area-only.

For the two base-post seats and two base-header seats, the existing
`dfl_axial_wood_bearing_reference_lbf` helper was applied with the Type A
minimum-annulus scenario, modeled bore, and dry DF-L No. 2 `Fc⊥ = 625 psi`.
It gives `920.570 N` per ideal full-supported seat; the component ratios above
range from `0.02007` to `0.12964`. These are unadjusted wood-bearing
comparisons only, conditional on DF-L No. 2, transverse loading, sound wood,
and full annular support. They are not allowable/design resistance or
washer/joint checks. The current model's base timber scenario is itself
unreceived and elastic-only.

Candidate blocks have a different model material category: the pinned
`material_binding` calls them a Douglas-fir elastic diagnostic and records no
received properties or strength grade. The model therefore does not assign
the base timber's conditional DF-L No. 2 `Fc⊥` to the blocks. To show the
consequence if a future project specification explicitly assigned the same
DF-L No. 2 scenario, `screen.json` separately reports a hypothetical
perpendicular-bearing comparison for the six transverse candidate-block end
seats. For BG001 it uses the candidate Type A minimum annulus; for BG003 it
uses only the full-supported modeled CAD annulus because no washer lead or
opening dimensions are bound. The ratios `0.02007–0.09999` are arithmetic
what-ifs, not material mapping or acceptance. The two BG045 block seats load
parallel to the proposed grain, so the `Fc⊥` method is inapplicable there.

A separate bolt-only scenario is numerically possible from the existing
conditional 1/4-20 UNC Grade 5 project-property basis: `Fy = 92 ksi` and
`At = 0.0318 in²` give an unadjusted tensile first-yield reference
`Fy × At = 13.014 kN` per bolt. Across the six signed tie demands, the
component ratios are `0.00142–0.00917`. This is not a design capacity,
connection pass, or delivered-bolt claim. The post pair has 1/4-20 Grade 5
and 25NWUS candidate leads; the two side axes have no exact bolt SKU at the
modeled 9.25-in length and no washer lead; the header axes have no exact
7.75-in bolt SKU, with a separate 8-in Grade 5 alternative and 25NWUS washer
lead. None is selected, received, or fit-qualified as a complete stack. The
`bolt_first_yield_reference` API also requires a shear-plane area and basis;
this screen does not invent those inputs or report axial/lateral interaction.

Remaining physical inputs and resistance methods are exact: selected and
delivered bolt/nut/washer identities and properties; actual thread class,
tensile section/thread placement and nut engagement; actual washer ID/OD/
thickness and head/nut contact footprint; finished bore and supported wood
area/condition; strength assignment for the candidate blocks; and a reviewed
washer-steel bending/spreading method. Bolt/nut thread stripping, pull-through,
bolt fracture and combined tension/shear resistance are not calculated. No
preload or friction is credited. Other load cases, sensitivities, and
complete-joint criteria remain open.

Pinned method sources are the existing
[conditional a12 corner screen](../current-corner-a12-conditional-resistance-screen-attempt01/README.md),
[modeled washer seat geometry](../current-corner-washer-seat-screen-attempt01/README.md),
[bolt resistance basis](../../../bolt-resistance-basis.md),
[conditional Grade 5 steel scenario](../../evaluation-resume-2026-09-24/ordinary-bolt-steel-reference-attempt01/README.md),
[ordinary washer dimensional/material boundary](../../../current-ordinary-nut-washer-property-basis.md),
and [current hardware coverage](../../../current-hardware-coverage.md). The
JSON stores hashes for all input reports and helper/source files. No
historical response or retained original-frame force is reused.
