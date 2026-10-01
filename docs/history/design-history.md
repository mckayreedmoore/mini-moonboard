# Design history: models, results and lessons

This catalog keeps the previous options explorable and provides starting
material for a presentation or writeup. It is a reading order, not a claim that
every design was built or tested physically. The selected baseline is governed
by [current-candidate.json](../../current-candidate.json); the active wood-joint
candidate has a [separate entry point](../wood-joints-mvp/README.md).

Open the [interactive viewer](https://mckayreedmoore.github.io/mini-moonboard/)
and use **Design** to compare options. All 70 existing menu choices are retained;
the complete link list below preserves the viewer's descriptive labels. Labels
such as “selected” or “current” in historical names are not today's authority.
The [decision log](decision-log.md) records the sequence and changing constraints.

## Milestones and what they taught us

| Design question | Result worth preserving | Models and primary records |
| --- | --- | --- |
| How should the original wall and backing fit together? | The plywood/hybrid and early connector studies preserve the geometry exploration. Their presence in the viewer is not a strength pass. | [Plywood reference](https://mckayreedmoore.github.io/mini-moonboard/?model=plywood), [early joint study](https://mckayreedmoore.github.io/mini-moonboard/?model=joint-development), [reference analysis](reference-analysis.md) |
| Could a compact lumber frame also accommodate wiring and removable panels? | Separate service-passage, panel attachment and insert options made the tradeoffs visible. Insert studies remain unqualified alternatives. | [Horizontal service frame](https://mckayreedmoore.github.io/mini-moonboard/?model=horizontal-service-development), [round passages](https://mckayreedmoore.github.io/mini-moonboard/?model=round-bore-service-development), [insert study](round-insert-analysis.md), [service analysis](round-service-analysis.md) |
| Was a passing leg-member check enough? | No. The assessed single 2×6 member passed its chosen case, but its connection failed. A longer-bolt/washer revision fit geometrically without solving the connection problem. | [Four-bolt frame](https://mckayreedmoore.github.io/mini-moonboard/?model=round-reinforcement-development), [leg assessment decision](leg-completion-decision.md) |
| Would larger bolts and wider patterns fix that joint? | No passing candidate was found within the investigated four-bolt family while retaining the single 2×6 leg and rim. This is a bounded negative result, not a verdict on every possible bolted joint. | [Bolt-pattern investigation](leg-bolt-pattern-decision.md), [wider-leg direction](wider-leg-decision.md), [2×8 model](https://mckayreedmoore.github.io/mini-moonboard/?model=wider-leg-development) |
| Could knees and splices improve the compact frame? | The knee trial recorded an initial interference and a revised fit; its machined-joint mechanics still required separate checks. The later spliced flush-top candidate passed all 21 listed conditional checks in six fresh cases, with bracket actions still unresolved. | [Knee trial](compact-knee-study.md), [spliced-knee model](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-spliced-knee-development), [flush-top results](compact-spliced-flush-top-study.md), [flush-top model](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-spliced-flush-top-development) |
| Could the floor-runner version reach a bounded analytical target? | The selected screw-and-bracket baseline has six authenticated no-slip cases passing 36 adopted checks. Unlisted bracket separation/couple actions and other recorded assumptions remain limitations. | [Selected model](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-floor-flush-development), [case record](../floor-runner-mvp-case-log.md), [criteria](../floor-runner-mvp-criteria.md), [completion ledger](../floor-runner-mvp-completion-ledger.md) |
| What happened when a solve did not converge? | A12-forward had three rejected contact searches before a fourth converged in 69 cycles under the same physical assumptions and final gates. A numerical search failure was not silently treated as a physical failure or an accepted result. | [Search history](../floor-runner-mvp-case-log.md#numerical-search-history), [six-case evidence](../floor-runner-mvp-evidence.json) |
| Could routine structural wood-screw removal be replaced by bolted connections? | V4, corner-block and barrel-nut layouts explored different paths. The later direction selected wood blocks for development; their predecessors remain valuable geometry and access studies, not accepted block capacities. | [Bolted plan](../bolted-candidate-plan.md), [V4 model](https://mckayreedmoore.github.io/mini-moonboard/?model=bolted-v4-development), [corner model](https://mckayreedmoore.github.io/mini-moonboard/?model=owner-corner-layout), [barrel model](https://mckayreedmoore.github.io/mini-moonboard/?model=owner-barrel-layout) |
| What did the detailed wood-joint simulation effort achieve and cost? | It produced useful method checks and exposed numerical problems, but did not establish a passing current joint. The September 29 direction uses whole-frame static demands and applicable connection checks, with detailed local work reserved for unresolved mechanisms. | [Reviewed WJ24 viewer](https://mckayreedmoore.github.io/mini-moonboard/wood-joints-wj24-viewer.html), [solver assessment](../wood-joints-mvp/solver-reuse-assessment-2026-09-27.md), [analysis reassessment](../wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/README.md) |

## Material for a presentation or writeup

Use the milestones as chapters: initial constraints, geometry exploration,
connection failures, the bracketed baseline's bounded success, removable-joint
alternatives, and the ongoing analysis-method lessons. Keep the limitations
beside each result rather than combining different revisions into one pass.

For each chapter, preserve the exact candidate/revision, the problem it aimed
to solve, the model link, a front/rear or joint-detail image, the result and its
source, and the reason for the next change. Existing visual material includes
the [baseline diagrams](../floor-flush-diagrams/), the two
[4×4](../floor-flush-construction/) / [kerf-right](../floor-flush-construction-kerf-right/)
construction packets, [historical exports](../../exports/), and meshes and
metadata under [site/hybrid](../../site/hybrid/). The interactive viewers supply
the source scenes for future comparable screenshots; this catalog does not
claim to have captured new images.

Retain original result bundles under [fea/results](../../fea/results/) and the
[wood-joint experiments](../wood-joints-mvp/hypotheses/), including failed runs
that support the narrative. Older documents can contain obsolete relative paths;
locate their source by original path/commit instead of rewriting frozen evidence.

Distinguish these outcomes explicitly:

- **Geometry or access result:** whether modeled parts, holes or tools fit.
- **Numerical result:** whether a method solved its stated equations and met its
  numerical checks.
- **Strength result:** whether applicable resistance checks passed under the
  recorded loads and assumptions.
- **Open question or preference:** missing evidence or an owner design choice,
  neither of which proves physical failure.

No cleanup should remove a currently available viewer choice, its required
assets, or the evidence needed to explain a success or failure. Archive complete
studies together; delete only scratch files established to be redundant and
unused. See the [retention evaluation](../repository-cleanup-evaluation-2026-09-28.md).

## Complete viewer collection

These are the 70 main-viewer choices recorded on September 29, 2026, in menu
creation order. Their original descriptive labels are retained as historical
metadata, not independently renewed engineering claims. The two wood-joint
viewers are separate pages:

- [Reviewed WJ24 block layout](https://mckayreedmoore.github.io/mini-moonboard/wood-joints-wj24-viewer.html)
- [Earlier WJ-03 / WJ-04 / WJ-05 trials](https://mckayreedmoore.github.io/mini-moonboard/wood-joints-outer-viewer.html)

The `2x10`, `2x12`, `2x8-shallow` and `2x8-foot100` assets are generated by the
[Pages workflow](../../.github/workflows/static.yml); those four manifests are
not present in this local checkout. The published viewer links are retained.
This catalog update does not rerun their CAD exporters or verify the live site.

| Viewer option | Stable model key |
| --- | --- |
| [Plywood reference](https://mckayreedmoore.github.io/mini-moonboard/?model=plywood) | `plywood` |
| [2×12 hybrid candidate](https://mckayreedmoore.github.io/mini-moonboard/?model=2x12) | `2x12` |
| [2×10 hybrid candidate](https://mckayreedmoore.github.io/mini-moonboard/?model=2x10) | `2x10` |
| [2×8 rotated-rear candidate](https://mckayreedmoore.github.io/mini-moonboard/?model=2x8-shallow) | `2x8-shallow` |
| [2×8 with 100 mm extended feet](https://mckayreedmoore.github.io/mini-moonboard/?model=2x8-foot100) | `2x8-foot100` |
| [Joint redesign · provisional](https://mckayreedmoore.github.io/mini-moonboard/?model=joint-development) | `joint-development` |
| [Independent leg plies · provisional](https://mckayreedmoore.github.io/mini-moonboard/?model=independent-leg-development) | `independent-leg-development` |
| [Revised screw spacing · provisional](https://mckayreedmoore.github.io/mini-moonboard/?model=screw-spacing-development) | `screw-spacing-development` |
| [Mid-batten clips · unselected hardware](https://mckayreedmoore.github.io/mini-moonboard/?model=mid-batten-clip-development) | `mid-batten-clip-development` |
| [Perimeter transitions · unselected hardware](https://mckayreedmoore.github.io/mini-moonboard/?model=lower-transition-development) | `lower-transition-development` |
| [Selected products · fit unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=selected-hardware-development) | `selected-hardware-development` |
| [Revised top joint · strength unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=top-joint-development) | `top-joint-development` |
| [Wood-first MVP · housed joints](https://mckayreedmoore.github.io/mini-moonboard/?model=wood-first-mvp) | `wood-first-mvp` |
| [Commercial-bracket MVP · factory connectors](https://mckayreedmoore.github.io/mini-moonboard/?model=commercial-bracket-mvp) | `commercial-bracket-mvp` |
| [Square-cut A · purchased connectors](https://mckayreedmoore.github.io/mini-moonboard/?model=square-cut-bracket) | `square-cut-bracket` |
| [Square-cut B · bolted wood blocks](https://mckayreedmoore.github.io/mini-moonboard/?model=square-cut-wood-blocks) | `square-cut-wood-blocks` |
| [Wider bolted A · purchased clips](https://mckayreedmoore.github.io/mini-moonboard/?model=bolted-clip-frame) | `bolted-clip-frame` |
| [Wider bolted B · wood blocks](https://mckayreedmoore.github.io/mini-moonboard/?model=bolted-block-frame) | `bolted-block-frame` |
| [Lean · 1½-in stock, single main layer](https://mckayreedmoore.github.io/mini-moonboard/?model=lean-38mm-frame) | `lean-38mm-frame` |
| [Lean · continuous top and bottom rails](https://mckayreedmoore.github.io/mini-moonboard/?model=continuous-lean-frame) | `continuous-lean-frame` |
| [Lean · lower bearing and ledge angles](https://mckayreedmoore.github.io/mini-moonboard/?model=bearing-lean-frame) | `bearing-lean-frame` |
| [Horizontal base · corrected grid · layout only](https://mckayreedmoore.github.io/mini-moonboard/?model=base-bearing-concept) | `base-bearing-concept` |
| [Lumber base · backing and connections](https://mckayreedmoore.github.io/mini-moonboard/?model=timber-base-development) | `timber-base-development` |
| [Lumber base · removable panel inserts](https://mckayreedmoore.github.io/mini-moonboard/?model=panel-insert-development) | `panel-insert-development` |
| [Wider central supports · backing bolt clearance](https://mckayreedmoore.github.io/mini-moonboard/?model=wide-principal-development) | `wide-principal-development` |
| [2x6 straight legs · +0 mm (0.00 in) · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-2x6-e0) | `lumber-leg-2x6-e0` |
| [2x6 straight legs · +150 mm (5.91 in) · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-2x6-e150) | `lumber-leg-2x6-e150` |
| [2x6 straight legs · +300 mm (11.81 in) · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-2x6-e300) | `lumber-leg-2x6-e300` |
| [2x8 straight legs · +0 mm (0.00 in) · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-2x8-e0) | `lumber-leg-2x8-e0` |
| [2x8 straight legs · +150 mm (5.91 in) · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-2x8-e150) | `lumber-leg-2x8-e150` |
| [2x8 straight legs · +300 mm (11.81 in) · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-2x8-e300) | `lumber-leg-2x8-e300` |
| [2x10 straight legs · +0 mm (0.00 in) · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-2x10-e0) | `lumber-leg-2x10-e0` |
| [2x10 straight legs · +150 mm (5.91 in) · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-2x10-e150) | `lumber-leg-2x10-e150` |
| [2x10 straight legs · +300 mm (11.81 in) · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-2x10-e300) | `lumber-leg-2x10-e300` |
| [2x12 straight legs · +0 mm (0.00 in) · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-2x12-e0) | `lumber-leg-2x12-e0` |
| [2x12 straight legs · +150 mm (5.91 in) · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-2x12-e150) | `lumber-leg-2x12-e150` |
| [2x12 straight legs · +300 mm (11.81 in) · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-2x12-e300) | `lumber-leg-2x12-e300` |
| [2x8 +300 mm · spread100×50 / top150 · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-spread-2x8-e300) | `lumber-leg-spread-2x8-e300` |
| [2x6 +300 mm · spread100×50 / top150 · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-spread-2x6-e300) | `lumber-leg-spread-2x6-e300` |
| [2x6 +0 mm (0 in) · long bolts / four washers · geometry only](https://mckayreedmoore.github.io/mini-moonboard/?model=lumber-leg-hardware-2x6-e0) | `lumber-leg-hardware-2x6-e0` |
| [Historical 2×6 · paired seam rails · failed baseline](https://mckayreedmoore.github.io/mini-moonboard/?model=square-2x6-development) | `square-2x6-development` |
| [Historical 2×6 · paired seam rails · revised connections](https://mckayreedmoore.github.io/mini-moonboard/?model=square-2x6-revised-development) | `square-2x6-revised-development` |
| [Single 2×6 · retained baseline · seam / bearing failures](https://mckayreedmoore.github.io/mini-moonboard/?model=single-2x6-development) | `single-2x6-development` |
| [2×6 base · selective single 3×6 / 2×10 · historical unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=selective-2x6-development) | `selective-2x6-development` |
| [2×6 paired rails · center base bracket · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=paired-rail-base-development) | `paired-rail-base-development` |
| [2×6 vertical principals · open middle bays · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=vertical-principal-development) | `vertical-principal-development` |
| [2×6 split center · open service corridor · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=split-center-development) | `split-center-development` |
| [2×6 split center · panel screw infill · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=infill-panel-development) | `infill-panel-development` |
| [2×6 split center · base angles · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=angle-base-development) | `angle-base-development` |
| [2×6 horizontal rails · lights and wiring · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=horizontal-service-development) | `horizontal-service-development` |
| [2×6 round passages · 12 screws per face · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=round-bore-service-development) | `round-bore-service-development` |
| [Historical removable-panel inserts · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=round-insert-development) | `round-insert-development` |
| [Structural screws · 1½-inch 2×6 passages · future insert space](https://mckayreedmoore.github.io/mini-moonboard/?model=round-structural-development) | `round-structural-development` |
| [Historical 2×6 with shoes · four bolts per leg · assessed / unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=round-reinforcement-development) | `round-reinforcement-development` |
| [Historical 2×8 with shoes · six bolts per leg · assessed / unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=wider-leg-development) | `wider-leg-development` |
| [2×6 legs · standard base angles · no custom shoes · unassessed](https://mckayreedmoore.github.io/mini-moonboard/?model=no-shoes-development) | `no-shoes-development` |
| [4×6 legs / rims · centered ⅝-inch pivot · development](https://mckayreedmoore.github.io/mini-moonboard/?model=thick-leg-centered-pivot-development) | `thick-leg-centered-pivot-development` |
| [Historical 4×6 compact frame · three bolts per leg · unqualified](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-thick-development) | `compact-thick-development` |
| [Previous 4×6 frame · inboard spliced knees · conditional package](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-spliced-knee-development) | `compact-spliced-knee-development` |
| [Bought 4×4 plywood · official Mini faces](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-floor-flush-development) | `compact-floor-flush-development` |
| [Cut from 4×8 · kerf on the right](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-floor-flush-kerf-right) | `compact-floor-flush-kerf-right` |
| [Historical 4×6 frame · spliced knees · flush leg tops](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-spliced-flush-top-development) | `compact-spliced-flush-top-development` |
| [Previous 2×6 floor rails · conditional no-slip package](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-floor-rail-development) | `compact-floor-rail-development` |
| [Previous exterior knees · conditional μ=0.4 package](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-exterior-brace-development) | `compact-exterior-brace-development` |
| [2×4 floor rails · numerical response rejected · NOT ACCEPTED](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-floor-rail-2x4-development) | `compact-floor-rail-2x4-development` |
| [Outboard floor rails · recessed leg ends · development / unaccepted](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-floor-recess-development) | `compact-floor-recess-development` |
| [Tapered leg recess · 2×6 floor rails · development](https://mckayreedmoore.github.io/mini-moonboard/?model=compact-floor-taper-development) | `compact-floor-taper-development` |
| [DEVELOPMENT V4 · PB02/PB04 center + PB05 outer scene](https://mckayreedmoore.github.io/mini-moonboard/?model=bolted-v4-development) | `bolted-v4-development` |
| [Corner-block layout · complete concept · NOT build-ready](https://mckayreedmoore.github.io/mini-moonboard/?model=owner-corner-layout) | `owner-corner-layout` |
| [Barrel-nut layout · 24 duties · NOT build-ready](https://mckayreedmoore.github.io/mini-moonboard/?model=owner-barrel-layout) | `owner-barrel-layout` |
