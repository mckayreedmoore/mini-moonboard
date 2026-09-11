# Current design review guide

The current candidate is **`horizontal-service-development`**: four horizontal
single-2x6 service rails replace four intermediate principals and their posts.
The separated center pair, outer rims, direct base angles and eight leg bolt
stacks remain. The model includes 132 LED bodies, 131 inter-LED routes and
open-front timber grooves. It is a development package, **not build-ready**.

## Open these first

1. [Current interactive model](https://mckayreedmoore.github.io/mini-moonboard/?model=horizontal-service-development&view=rear).
2. [Purchasing schedule and assembly plan](horizontal-service-build-plan.md),
   including named members, rail datums and exact-candidate export links.
3. [Drilling references and datum rules](horizontal-service-drilling.md) and
   [drilling PDF](horizontal-service-drilling/drilling.pdf).
4. [Complete LED hookup schematic](horizontal-service-wiring.svg) and
   [manufacturer wiring reference](led-wiring-reference.md). Dashed external
   leads are schematic; their physical routes are not established by the 3D model.
5. [Provisional floor and density assumptions](provisional-floor-load-assumptions.md)
   for independent verification of numerical inputs.

The CAD/CSV export passed its artifact check. The 16-page drilling PDF is
generated and checked for text bounds. The verified inventory
has 24 wood/plywood parts, 87 panel/kicker screws, 24 ML24Z angles, 144 SDS25112
screws and eight full leg bolt stacks. There are zero installed panel inserts.
The current geometry checks pass; geometry clearance does not establish strength.
The viewer depicts assembled geometry, not a live FE solution or stress plot.

## Current evidence and release gates

| Topic | Current basis | Remaining qualification |
| --- | --- | --- |
| Revised rails and panels | Current horizontal-rail geometry and replayed [conditional coupled frame/panel diagnostic](horizontal-frame-diagnostic.md) | Applicable directional material behavior, stress refinement, panel/member strength and serviceability |
| Panel attachments | 87 ordinary SPAX panel/kicker screws in the installed model | Current individual reactions versus applicable withdrawal, head-bearing and combined-load resistance; assumed stiffness is not a product rating |
| Commercial angles and leg bolts | 24 ML24Z stations with prescribed SDS screws; eight complete leg bolt stacks | Applicable angle/group/wood and bolt resistance under current demands, bearing, splitting and slip |
| Removable-panel inserts | All 87 [prospective reserve and head-clearance checks passed](horizontal-insert-fit.md); none installed | Verify installation, effective thread engagement and connection resistance for the provisional product pair, then analyze the revised attachment behavior |
| Floor behavior | Conditional rigid-floor feasibility and separately assumed restrained-frame diagnostics | Actual interface/friction and mass inputs; compatible compliant support, rocking/uplift and transient behavior; fixed restraints do not authorize anchors |
| Lumber and plywood | Selected purchasing basis: dry DF-L No. 2 or better and APA PS 1 Structural I 23/32 category, 48/24 square-edge plywood | Delivered stamps, usable dimensions and thickness; applicable material-property verification; existing isotropic FE does not qualify selected stock |
| Harness and timber grooves | Owned V5 kit, approximate 304.8 mm bulb-base pitch, modeled inter-LED paths and cutouts | Actual LED projection, cable/connector envelopes and slack, external leads and strain relief; residual timber section strength after machining |
| Hold hardware | 132 main plus ten kicker hold positions; historical Escape 3/8-16 selection | Received T-nut/hold inventory, per-hold bolt lengths, retention screws and rear clearance; these complete bodies are not included in current modeled mass |

The owner requests one climber with a 250 lb maximum; this is a design input,
not an established load rating. Results at assumed materials, connectors and
supports must retain those conditions. A numerically converged solve is not
itself strength or construction approval.

## Preserved evidence: compare without transferring approval

The [angle-base candidate](angle-base-development.md) retains the preceding
151-screw infill arrangement. Its panel results and attachment checkpoint do
not establish the revised horizontal-rail behavior.

The [wide-principal package](wide-principal-development.md),
[assembly sequence](wide-principal-assembly.md), [machining references](wide-machining.md)
and [purchase BOM](wide-purchase-bom.md) describe historical geometry with different
posts, inserts and backing. The [historical local package audit](current-package-audit.md),
[leg-bolt study](leg-bolt-resistance.md), [coupled joint analysis](coupled-leg-release.md)
and [wide-frame floor screen](wide-floor-screen.md) remain useful evidence for
those identified models. Their counts, force results and passing tests must not
be presented as current-candidate acceptance.

The [active work ledger](connection-design-goal.md) preserves engineering history.
Use this guide and the exact-candidate manifest as the entry point; a historical
“next step” elsewhere is not the current design decision.
