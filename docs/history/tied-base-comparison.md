# Side ties: matched comparisons and decision

**Keep the untied 2×8-foot100 frame as the development baseline. Do not add the
side rails solely for stiffness or tipping margin.** Their possible benefit is
redistributing spreading forces, which still needs an audited unanchored model
and designed connections. The Z=275 mm option remains the first connection
geometry to investigate, not a selected construction detail.

Original plywood, 2×8, 2×10 and 2×12 models/results are unchanged. This study uses
the separate [rail/spacer geometry](base-restraint-options.md), not a replacement
for the default viewer assembly. No anchors, pads or ballast are credited.

## Two different comparisons

The [bulk FEA report](../fea/results/tied_base_bulk/report.json) compares the
same six independent load cases with fixed actual floor nodes, no gravity,
E=7,000 MPa, ν=0.3, and perfectly bonded touching timber. This includes ideal
bonding of the **unresolved** new joints. Loads are split across five row-12
nodes; displacement below is the largest magnitude among those nodes, not the
maximum everywhere. Each 60 mm quadratic mesh passed positive-Jacobian,
connected-part, actual-floor, load/support and force/moment checks. No floating
rail or spacer received floor support. Exact launch snapshots and raw evidence
are archived separately for each candidate.

The [rigid-body report](../fea/results/tied_base_envelope.json) instead uses each
candidate's exact timber mass, centroid and actual floor polygon. It retains
96 combinations per candidate: 150/200/250/300 lb, static/2× weight, full/80%
uniform frame mass, 0/50/100 mm hold offsets and 0/300 N horizontal load, checking
every hold and worst horizontal azimuth at every support edge. These exploratory
sensitivities are not a validated dynamic envelope. Only mass and planar centroid
from the added rails enter this calculation; no tie stiffness is credited.

| Exact timber-only candidate | Mass, kg | Downward 1.2 kN sampled displacement, mm | Downward-case kicker reaction Fy, N | Minimum rigid-body moment factor |
| --- | ---: | ---: | ---: | ---: |
| Untied 2×8-foot100 | 183.963 | 0.84748 | +295.087 | 1.7143 |
| Rails centred Z=100 mm | 191.281 | 0.84565 | +268.758 | 1.7946 |
| Rails centred Z=275 mm | 191.281 | 0.84458 | +243.085 | 1.7946 |

Fy is a signed world-Y reaction from the **fixed-floor, no-gravity** FEA; it
is not measured friction or an allowable tie force. In that same downward case,
kicker Fz is −177.620, −175.386 and −172.149 N respectively. These tensile
incremental support reactions are retained, not accepted as unanchored contact
and not interpreted as uplift after adding gravity. The nonlinear gravity/contact
state cannot be recovered by adding an unrelated rigid-body reaction estimate.

The downward displacement reduction is only 0.22% or 0.34% on this coarse mesh.
The baseline reproduces the historical 60 mm result; the two new candidates
have not received a 40 mm refinement. Such small differences are not a strong
reason to add parts or choose a height. More notably, the reaction distribution
changes, including a lower opposing kicker Fy in this load case. Other cases
must remain visible: for the exploratory outward/downward normal load, the
magnitude of each leg's Fy increases with the ties. This is not a universal
reduction in support demand.

Fixed floor nodes already prevent spreading. Consequently these results neither
prove nor disprove the rails' usefulness when the floor can slip or open. No
rail end-force, fastener demand, joint-slip capacity or local stress rating has
been extracted from this comparison.

## Tipping screen: inventory and limits

The baseline here is **183.963 kg of undrilled timber**, not the previous
195.573 kg drilled-timber-plus-angle inventory. Its lower minimum factor is an
explicit inventory difference, not a regression in the unchanged leg geometry.
Both rail heights have the same mass and planar centroid, so their rigid-body
gravity tipping results coincide even though their vertical centroids differ.
Neither changes the actual support polygon; the 7.318 kg of added timber is
the reason for the improvement in this particular screen.

| Climber comparison | Untied minimum factor | Either tied variant |
| --- | ---: | ---: |
| 150 lb | 1.8045 | 1.8890 |
| 200 lb | 1.7734 | 1.8565 |
| 250 lb, intended maximum | 1.7433 | 1.8250 |
| 300 lb, sensitivity only | 1.7143 | 1.7946 |

All 96 cases per candidate meet the 1.5 moment-only screening target. The
governing combination is 300 lb at 2× weight, 80% frame mass, 100 mm offset
and 300 N horizontal loading at A12. These are not safe user ratings, local
sliding checks, yaw-equilibrium checks or proof of real joint integrity.

Both legacy board-normal vectors still require uplift in the separate sagittal
screen. Untied factors are 0.7690 and 0.5346; tied factors are 0.8050 and 0.5527.
Those directions remain exploratory rather than established governing use loads,
but adding side rails does **not** cure their tipping mechanisms.

## Recommendation and next discriminating work

1. Retain the untied 2×8-foot100 geometry and original alternatives. There is no
   evidence here that deeper rims or extra base rails are presently necessary
   for a defined strength/serviceability limit.
2. Carry Z=275 mm into connection feasibility work because of its front
   cheek/rim overlap, while retaining Z=100 mm as the lower-moment-arm comparison.
   Require a useful reduction in *audited unanchored* local demand before
   accepting the added width, mass, joints and access/fall-zone implications.
3. Resolve contact moment transfer using the [small formulation tests](contact-shear-coupon.md)
   and actual inclined leg before repeating full-frame gravity/loading. Keep
   the existing force/moment limits and distinguish supported coupon boundaries
   from a completely unanchored frame.
4. Apply the [material-selection plan](material-selection-recommendation.md).
   A specified structural panel and either qualified lamination or a verified
   no-adhesive-credit two-ply assembly are separate from increasing rim depth.
5. Once the load path is interpretable, compare connection/member demand against
   applicable product resistance, including asymmetric/reversed loads and joint
   slip. Qualified structural review and controlled physical verification remain
   construction/use gates; these studies do not authorize climbing.

Recheck the published results without rerunning a solver:

```sh
uv run pytest -q tests/test_tied_base_bulk.py tests/test_tied_base_envelope.py
```
