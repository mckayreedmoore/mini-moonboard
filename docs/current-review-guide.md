# Current design review guide

The current candidate is **`round-bore-service-development`**: four horizontal
single-2x6 service rails, separated center principals, direct base angles and
eight complete leg bolt stacks. Its 32 enclosed round wiring passages replace
the preceding open-front grooves. It remains **not build-ready**.

## Open these first

1. [Current interactive model](https://mckayreedmoore.github.io/mini-moonboard/?model=round-bore-service-development&view=rear).
2. [Purchasing schedule, tools and assembly draft](round-service-build-plan.md).
3. [Round-passage drilling PDF](round-service-drilling/drilling.pdf) and
   [datum schedule](round-service-drilling/drilling.json), using the same revision
   as the [connection schedule](../exports/round-bore-service-development/connections.csv).
4. [Material cost ledger](material-costs.md), [disassembly guide](disassembly-guide.md)
   and [worn-hole insert assessment](threaded-insert-repair-guide.md).
5. [Current analysis and limits](round-service-analysis.md) and
   [assumptions for independent verification](provisional-design-assumptions.md).

The local export inventory has 24 wood/plywood parts, 56 panel/kicker screws,
24 ML24Z angles, 144 prescribed SDS25112 screws, eight bolts, eight nuts and
16 washers. The leg nuts face inward. Each main panel has twelve mirrored
attachments; each kicker has four. Panel screws have modeled 90-degree flush
head seats. There are zero installed panel inserts. The viewer depicts assembled
geometry, not an FE stress plot or a demonstration of installation access.

## Current evidence and release gates

| Topic | Current basis | Remaining qualification |
| --- | --- | --- |
| Revised rails and panels | Round-passage solids and their own geometry audit | Matching coupled panel/frame response, directional material properties, local drilled sections and resistance; historical grooved-frame FE does not transfer |
| Panel attachments | 56 ordinary SPAX screws, with mirrored straight rows; [necessity and appearance audit](panel-screw-necessity.md#current-mirrored-twelve-screw-layout) | Individual reactions, stiffness, withdrawal, head-bearing and combined-load resistance; twelve per panel is not a demonstrated minimum |
| Commercial angles and leg bolts | 24 ML24Z stations with specified SDS screws; eight complete inward-nut stacks | Applicable angle/group/wood and bolt resistance, bearing, splitting, slip and actual tool access |
| Removable-panel inserts | Separate [repair/insert assessment](threaded-insert-repair-guide.md); none installed | Current location fit, actual sound-wood condition, recess, effective engagement and connection resistance; historical 87-location reserves do not qualify this candidate |
| Floor behavior | Current source-bound rigid-floor feasibility at assumed friction | Actual friction, contact and mass; compatible flexible-frame response, rocking/uplift and transient behavior |
| Lumber and plywood | Dry DF-L No. 2 or better lumber basis; retain the owned Roseburg plywood | Delivered stamps, usable dimensions, thickness, strength axis and applicable properties; Structural I remains a reference alternative, not a replacement instruction |
| Lights and round passages | 132 LED bodies, 131 inter-light routes; owner reports approximately 304.8 mm bulb-base pitch and 12.7 mm maximum component diameter | Intact-strand feeding and withdrawal after panel assembly, bends, slack, strain relief and external lead placement |
| Hold hardware | 132 main plus ten kicker positions; recorded Escape 3/8-16 selection | Received inventory, per-hold bolt lengths, retention screws and rear clearance; excluded hardware is not included in modeled mass |
| Assembly and maintenance | Draft operations, tools and connection dependencies | Stage-specific temporary supports, handling and physical assembly/disassembly validation |

The [LED hookup schematic](horizontal-service-wiring.svg) retains the factory
connection topology; dashed external leads are schematic, not physically verified
routes. Use round-candidate timber drawings for the new passages.

The owner requests one climber with a 250 lb maximum; this is a design input,
not an established load rating. A numerically converged solve or geometry pass
is not itself strength or construction approval.

## Preserved evidence: compare without transferring approval

The [preceding grooved horizontal package](horizontal-service-build-plan.md)
and its 87/75-screw analyses are historical comparisons. They do not qualify
the new round passages or repositioned 56-screw pattern.

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
