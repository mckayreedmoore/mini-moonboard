# Generic screw-head pull-through reference check

October 2, 2026. This is a source and arithmetic check of the quoted
250 lb dynamic-model comparison for the purchased Hillman/Fas-n-Tite
No. 10 × 2.5 in screws. Existing source geometry, force packets, reference
outputs, 47-criterion authority and release HOLD remain unchanged.

## Decision

The **277–629 N calculation is correct for its declared inputs**. It is
an unadjusted allowable-stress-design (ASD) reference for a head pulling
through plywood, not a measured Hillman capacity or a breaking-load range.
The range combines deliberately different geometry and plywood assumptions;
it is not a tolerance range for the delivered screws.

The prior product-dimension packet already records a retailer-listed
Hillman 42605 head diameter of **0.355 in = 9.017 mm**. That input was omitted
from the earlier version of this note and is ingested below as a separate
nominal-product branch. It is not a measured head diameter or tolerance.
Under otherwise identical thin-panel inputs, it lowers the references by
**2.204%** relative to the generic 0.363-inch head. The original 250 lb
force comparison remains outside the declared references.

There is a correction to the earlier
[panel attachment explanation](../panel-attachment/README.md): NDS Table
12.2F footnote 2 explicitly directs the head calculation to Table 12.3.3B
for panel specific gravity. Consequently `.42/.50` has a normative path
for this head reference, rather than being only an unrelated bearing
sensitivity. `.50` applies to Structural I/Marine plywood; `.42` applies
to other grades and unknown ply species. The table also permits known-species
values or a weighted average for mixed species. No actual panel grade or
species has been observed here. The research paper's effective `.50` for
all structural panels does not override the NDS grade/species assignment.

## Equation, dimensions and adjustments

NDS §12.2.5.1 and Table 12.2F give, with dimensions in inches and output
in pounds:

```text
WH = 690 π DH G² tns       when tns ≤ 2.5 DH
WH = 1725 π DH² G²        when tns > 2.5 DH
W'H = WH CD CM Ct         for ASD, per Table 11.3.1
```

All retained head scenarios use the first branch and lie within Table
12.2F's head-diameter and net-thickness bounds. Table L3 supplies a standard
No. 10 head diameter of `.363 in = 9.2202 mm`, an average of specified
diameter limits. It does not establish the delivered deck-screw head size.
The separate 7.5 mm diameter and 14 mm net thickness are hypotheses.

The AWC [supporting study](https://web-media.awc.org/wp-content/uploads/2021/12/17210650/2018-nds-head-pull-through-paper.pdf)
includes flush countersunk flathead screws, so a flat/countersunk profile
does not by itself exclude the reference. Its net-thickness convention
subtracts one-third of head depth for countersunk screws. The retained
17.25625 mm example is 18.25625 mm panel thickness minus one-third of a
hypothetical 3 mm head depth. Actual countersink geometry remains unknown.
An extra recess below flush needs its own net-thickness treatment.

NDS §§2.3.2 and 11.3.2 cap connection load-duration factor `CD` at **1.6**.
The ten-minute duration is cumulative at the full maximum load; "dynamic"
alone does not establish that duration. The following 1.6 column is an
explicit favorable short-duration scenario with dry service and ordinary
temperature (`CM=Ct=1`), not a newly adopted resistance. A 2.0 impact
duration factor is not permitted for these connections. Duration adjustment
changes the reference; it does not remove the separate 2× force assumption
from the frame load model.

| Inputs: G; head diameter; net plywood thickness | Unadjusted WH | WH × 1.6 | 1871.251 N / adjusted reference |
| --- | ---: | ---: | ---: |
| .42; 7.5 mm; 14 mm | 276.825 N | 442.921 N | 4.225 |
| .42; 9.2202 mm; 17.25625 mm | 419.472 N | 671.156 N | 2.788 |
| .50; 9.2202 mm; 17.25625 mm | 594.490 N | 951.184 N | 1.967 |
| .50; 9.2202 mm; 18.25625 mm | 628.941 N | 1006.306 N | 1.860 |

The last row omits countersink reduction and is the most favorable retained
reference. Even that adjusted scenario remains below the saved nominal-gap
head demand. This is an exceeded conditional design-reference comparison;
it does not establish physical failure.

## Retained Hillman retailer-nominal head branch

The existing [42605 dimension packet](../../../../bolted-candidate-hillman-42605-dimensions.json)
records the exact [Tractor Supply item 1549417](https://www.tractorsupply.com/tsc/product/hillman-fas-n-tite-exterior-coated-wood-screws-%28-10-x-2-1-2%29-50-pack-1549417).
Parent and this worker rechecked that product page on October 2, 2026. Its
specification fields identify manufacturer part **42605**, No. 10 × 2.5 in,
**0.355-inch head diameter**, carbon steel and **bugle** head. It supplies
no head tolerance, head depth, controlled profile drawing or pull-through
rating. The nominal conversion is exactly **9.017 mm**, radius **4.5085 mm**.
The product-dimension packet remains unchanged.

This value is separate from Table L3's generic 0.363-inch standard No. 10
head and from the hypothetical 7.5 mm branch. Both listed head diameters use
the thin-panel equation for the retained thicknesses. The following rows
replace only `DH` in that equation; grade, net thickness, duration and method
applicability remain explicit conditions:

| Retailer nominal DH = 9.017 mm; G; net plywood thickness | Unadjusted WH | WH × 1.6 | 1871.251 N / adjusted reference |
| --- | ---: | ---: | ---: |
| .42; 17.25625 mm | 410.228 N | 656.364 N | 2.851 |
| .50; 17.25625 mm | 581.389 N | 930.222 N | 2.012 |
| .50; 18.25625 mm, no countersink reduction | 615.080 N | 984.128 N | 1.901 |

The favorable gross-thickness retailer branch is therefore **984.128 N**,
versus **1006.306 N** in the preserved favorable generic branch. Neither
reaches the original nominal-gap 1871.251 N demand. Existing head outputs
and saved forces are preserved; this is additional direct arithmetic, not
a regenerated producer result or a Hillman capacity assignment.

The small diameter change can affect near-threshold sharing arithmetic:
two ideal equal references at `.50`, 17.25625 mm and `CD=1.6` now total
**1860.443 N**, below 1871.251 N. That particular idealized comparison
would need three equal shares instead of two. This does not specify an
additional screw count, a layout or compatible force sharing; the purchased
66-screw policy and all axes are unchanged.

## Design allowance and breaking strength

The supporting AWC paper, p.7, explains that modeled pull-through capacities
were divided by approximately five when developing the design equations.
Its Table 4 reports an average test/design ratio of 4.92 across the studied
configurations, with substantial variation. This explains why the quoted
design allowance is well below typical research breaking loads. Multiplying
the reference by five does not qualify these Hillman screws in this plywood,
define a lower-bound breaking capacity, or establish an acceptable margin.
No physical test has failed in this study.

## Purchased product and practical next check

The [model 42605 listing](https://www.lowes.com/pd/Hillman-10-x-2-1-2-in-Ceramic-Deck-Screws-50-Count/999995042)
identifies No. 10, 2.5 in, flat head, coarse thread and steel. It supplies no
numerical head diameter, head depth or head pull-through rating on that
listing. Tractor Supply supplies the separate nominal diameter above and
calls the head bugle. The retailer profile descriptions remain inconsistent;
neither description settles delivered bearing/countersink geometry. The owner
confirmed model **42605** during this check, along with No. 10 × 2.5 in.
The 2.5 in length affects timber thread embedment, not the plywood head
equation directly. Withdrawal, lateral action, screw strength and compatible
sharing remain separate from this check; screw stiffness is unqualified.

The next useful geometry facts are the delivered head profile/depth and its
diameter tolerance or measurement, together with plywood grade and intended
flush seating. The retailer's nominal diameter is already usable as the
explicit product-input branch above; obtaining those additional facts is
not required to calculate that branch. They can refine its assumptions
without another frame solve, but cannot alone establish complete joint
capacity. Main coordinator owns updates to the frozen summaries.

## Reproduction and retained evidence

The table is direct evaluation of the equations above, converting mm/25.4
to inches and multiplying pounds by `4.4482216152605 N/lbf`. Standard-library
arithmetic reproduced the existing endpoints and intermediate references.
Primary PDF pages and table grids were inspected. No software tests, frame
solve, CAD run, source-model change or release claim was added.

| Retained evidence | SHA-256 / checked location |
| --- | --- |
| [NDS Chapter 12](../../upper-block-strength-2026-10-01/source-cache/chapter12-2024-awc-20260911.pdf) | `53f6ec05dfd1ceabeccd4d6e88c342111678d3da4631ee7b482b706f77c1780f`; printed pp.84, 90, 95 |
| [NDS Chapter 11](../../upper-block-strength-2026-10-01/source-cache/chapter11-2024-awc-20260911.pdf) | `45a3d78de1a4fba573589be0fc776e37bd581e4cedec24e38d63856161092d33`; printed p.72 |
| [NDS Chapter 2](../../upper-block-strength-2026-10-01/source-cache/chapter2-2024-awc.pdf) | `6bb62f3560ab5bcdbed297cd03bba560f20882a638ee591c0c97013f7c075100`; printed pp.12–13 |
| [NDS Appendix](../../upper-block-strength-2026-10-01/source-cache/appendix-2024-awc-20260911.pdf) | `1fa2bcf52803b1bbed8ea30cf13551dd5f76c90bf110ac475b401f81d116ec31`; printed pp.170, 193 |
| [Prior Hillman 42605 nominal dimension packet](../../../../bolted-candidate-hillman-42605-dimensions.json) | `d6c3c3ce8d27a02a98a4d9cdca7dce66d2cc5c982cb73b6fb3731ce80d70e72c`; retailer nominal only, live source rechecked 2026-10-02 |
| `/tmp/upper-panel-awc-head-pull-through-paper.pdf` | `b0f7b80cfa891b4babea733894ee856b3da944abb8ce9a982477cb90c4887e2f`; pp.2, 7, 9 |
| [Retained head comparison](rawlocal/head-check/attempt01/comparison.json) | `847cd69109df991fc39756899a3313b2063f66b3ec4fab9af4f3c41bef21fe7b` |
| [250 lb saved response](frame-250-attempt02/response.npz) | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |

The quoted 1871.251 N is the **nominal-gap** peak at the unchanged upper-left
`edge_2`, A12-rear, into `base_rail_top`; simultaneous lateral demand is
726.611 N. The retained zero-gap peak is 1923.816 N. Neither reference
comparison authenticates the material, delivered part or frame demand as a
measured performance limit.
