# A1-rear outer-corner axial tie and washer-seat screen

This case-local packet applies the existing conditional washer and bolt
component scenarios to the authenticated `a1-rear` response. It inventories
the six BG001/BG003/BG045 bolt ties and twelve outer washer seats, then compares
each A1 tie with the corresponding a12-rear tie. It does not change or reuse
the a12 producer, transfer its floor mask or response, qualify a product,
assign new stock properties, or accept a joint.

The A1 input is the case-bound
[`corner-demand-report.json`](../current-corner-a1-rear-case-bound-export-attempt01/corner-demand-report.json),
SHA-256 `2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce`.
It binds selected model `72d043e1…74f5fd`, deck
`f92db385…d52d13ab`, native DAT `b5b9997e…e929e2`, response
`257b5b74…a09678c`, and case context `8383c311…f92922f6`. The separate
parent audit has SHA-256 `24784592…344deca`; its seven increments each pass
50-body and global raw/rounding-interval balance. The response's case-local
root and increment gates and five-corner-body balances also pass. The parent
terminal assessment leaves `joint_accepted=false`. The selected floor branch
is still conditional, and neither floor friction nor anchorage is qualified.

Reproduce and check all pinned sources, parent evidence, static A1/A12 model
compatibility, twelve unchanged seat records, and the arithmetic:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-a1-rear-axial-seat-screen-attempt01/produce.py --write
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-a1-rear-axial-seat-screen-attempt01/produce.py --verify
```

The complete report is [`screen.json`](screen.json), SHA-256
`0f1160a62bdba6d5a8baf7607d4ecfc148bad44bbaee36d1971cecebf693eb19`.

| Group / axis | A1-rear tie (N) | a12-rear tie (N), comparison only | A1−A12 (N) | A1/A12 | CAD-area pressure (MPa) | 25NWUS min-annulus pressure (MPa), if a lead exists | Base-seat Fc⊥ component ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| BG001 `post_1` | 44.48336 | 64.96606 | −20.48270 | 0.6847 | 0.199722 | 0.208228 | 0.04832 at base post |
| BG001 `post_2` | 47.00119 | 18.47315 | +28.52804 | 2.5443 | 0.211027 | 0.220014 | 0.05106 at base post |
| BG003 `side_1` | 21.79439 | 95.96739 | −74.17300 | 0.2271 | 0.097853 | — | — |
| BG003 `side_2` | 49.66872 | 43.50841 | +6.16031 | 1.1416 | 0.223003 | — | — |
| BG045 `inner_header_1` | 9.524928 | 119.34300 | −109.818072 | 0.07981 | 0.042765 | 0.044587 | 0.01035 at base header |
| BG045 `inner_header_2` | 98.44241 | 19.88171 | +78.56070 | 4.9514 | 0.441988 | 0.460813 | 0.10694 at base header |

Each physical tie carries the same positive tension magnitude at its two outer
seats; the exported seat actions are equal and opposite. BG003 has only two
outer washer seats per bolt. Its middle `base_side_left` receiver has no
separate axial washer-seat tie.

The model/material/geometry comparison is exact for the static inputs checked:
candidate and geometry revision, nodes, fixed nodes, body geometry, geometry
audit, source geometry hashes, physical body nodes/elements, all elements,
material binding, connection ownership/scenario, all 1,840 carrier rows, all
1,292 SPRINGA bindings, all 348 bilateral springs, and source spring counts.
All 12 seat member/role/point/CAD-area records also match between the A1 and
a12 exports and the pinned washer geometry screen. A1's loads/body wrenches
and selected floor state remain case-bound; A1 has 46 selected / 54 inactive
cells versus a12's 25 / 75. Only the a12 per-axis tie numbers are used as
comparison values. No a12 force, response gate, or floor state enters the A1
calculation.

The CAD-derived washer annular plan area is `222.7262 mm²`; the CAD-area
pressure is `T/A`. The shared Type A Wide / 25NWUS candidate dimensional range
is OD `0.727–0.749 in`, ID `0.307–0.327 in`, and thickness `0.051–0.080 in`.
For axes with a 25NWUS lead (BG001 and BG045), the minimum-annulus scenario
uses minimum OD, maximum ID, and the modeled 7.5 mm wood-bore diameter. It
gives `213.6279 mm²`. The washer dimensions are not selected or delivered, and
the finished wood support polygon, head/nut footprint, cuts, gaps, and
flatness remain unresolved. BG003 has no listed washer lead, so its pressure
is CAD-area-only.

For the two base-post seats and two base-header seats, the existing
wood-bearing helper applies the conditional DF-L No. 2 `Fc⊥ = 625 psi`
reference to the Type A minimum annulus. It gives `920.570 N` per ideal
full-supported seat. The ratios above are unadjusted bearing-component
comparisons, conditional on sound DF-L No. 2 wood loaded transverse to grain
with full annular support; they are not design resistance or washer/joint
checks. Candidate blocks remain a separate elastic-only Douglas-fir
diagnostic material category with no strength grade in the model. Their
optional DF-L No. 2 numbers are separately labeled what-if arithmetic for
transverse seats only: `0.02271–0.05175` on the two BG003 bolts and `0.04832`
and `0.05106` on BG001. These values do not assign that grade to the blocks.
BG045 block seats load parallel to the proposed grain, so Fc⊥ is inapplicable.

The same hypothetical 1/4-20 UNC Grade 5 project-property scenario is reused
for bolt-only component arithmetic: `Fy=92 ksi`, `At=0.0318 in²`, and
`Fy×At=13.014 kN` unadjusted tensile first-yield reference per bolt. A1 tie
ratios range from `0.00073` to `0.00756`. The axis inventory does not show
matching products selected for all six positions: the BG001 pair has a 4-in
Grade 5 cap-screw lead and washer lead; BG003 has no exact 9.25-in bolt SKU or
washer lead; BG045 has no exact 7.75-in bolt SKU, with separate 8-in Grade 5
and washer leads. None is delivered or fit-qualified. This material component
reference is not bolt design resistance, nut stripping capacity, or a
tension/shear interaction; no shear section area is invented.

The A1 group maxima over the two axis ties are below a12-rear for all three
groups (BG001 `47.001/64.966 N`; BG003 `49.669/95.967 N`; BG045
`98.442/119.343 N`). Nevertheless, the A1 demand is higher on post 2,
side 2, and header 2. A lower group maximum therefore does not replace
axis-specific comparison. These are still individual component demands, not
group capacities or complete-load-path acceptance.

Sources reused from the prior conditional screen are the
[A12 axial/washer component screen](../current-corner-axial-tie-seat-screen-attempt01/README.md),
[washer geometry screen](../current-corner-washer-seat-screen-attempt01/README.md),
[bolt resistance basis](../../../bolt-resistance-basis.md),
[conditional Grade 5 scenario](../../evaluation-resume-2026-09-24/ordinary-bolt-steel-reference-attempt01/README.md),
[washer dimensional/material boundary](../../../current-ordinary-nut-washer-property-basis.md),
and [current hardware coverage](../../../current-hardware-coverage.md). Input
hashes, A1/A12 compatibility digests, all twelve seat records, force deltas,
and per-axis conditional ratios are stored in `screen.json`. No unchanged
original LEG/RUNNER resistance check is reopened.
