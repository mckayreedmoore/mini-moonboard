# Eoere bolted-frame development

This is the main development entry for `compact-floor-flush-eoere-bolted-development`.
The current geometry is **`eoere-base-side-edge-cleats-v1`**, with the optional
extra grid **off**. It uses 22 timbers, six panels, 22 angles, 100 through-bolt
stacks and 66 purchased Hillman panel/kicker screws. The retained folder name
also covers earlier wood-joint studies. The selected screw-and-bracket
[baseline authority](../../current-candidate.json) stays separate.

## Active builder reading path

| Need | Start here | Boundary |
| --- | --- | --- |
| Current geometry | [Extended-cleat viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-extended-cleat-frame-development&view=rear) · [geometry receipt](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-extended-cleats-v1.json) | Extends both full-thickness cleats to the sloping side edge; retains the adjusted v3 axes. Geometry evidence only. |
| Current nominal shop records | [Extended-cleat shop packet](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/README.md) | Current profiles, hole/screw datums, stock nesting, hardware and assembly dependencies; four cleat/post stations remain **HOLD**. |
| Preserved fixture concepts | [Aligned-wire builder-support guide](eoere-builder-drilling-guide.md) | Frozen to `eoere-grid-aligned-wire-cutouts-v1`. Later v3 moved 22 shafts and ten screws; use the current shop packet for current datums. Actual tools, reach, fixtures and tolerances remain unresolved. |
| Current numerical evidence | [Six fresh cases](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/current-cases-v1/result-v1.json) · [parent verification](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/current-cases-v1/parent-verification-v1.json) | Current extended-cleat geometry, extra grid off; passing equilibrium/recovery audits, retained reference exceedances and unknown complete-joint resistance. |
| Current component comparisons | [Six-case summary](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/current-component-results-v1/summary.json) | Own-case panel, screw, gross timber, steel, shaft and washer references; complete-joint resistance remains null. |
| Current tasks and detailed evidence | [Completion ledger](completion-ledger.md#build-package-completion) · [qualification status](completion-ledger.md#current-model-completion-scope-and-qualification-status) | Detailed scope, source bindings, reviews and open inputs; earlier “current” sections retain their historical meaning. |

## Revision map

Geometry, response and shop coverage have different revision boundaries:

| Role | Exact revision / record | Viewer or operations |
| --- | --- | --- |
| **Main development geometry** | `eoere-base-side-edge-cleats-v1` · [receipt](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-extended-cleats-v1.json) | [Extended-cleat base, extra grid off](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-extended-cleat-frame-development&view=rear); published at `bca5f988`. |
| Unadopted lower-corner proposal | `eoere-lower-cleat-z180-proposal-v1` · [four-axis patch and eight receiver datums](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/viewer-revision-v1/runs-v1/export01/layout.json) · [own six-case roster](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/z180-mechanics-execution-v1/cases-v1/result-v1.json) | [Z180 preview](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-lower-cleat-z180-development&view=rear); four stacks lower 20 mm, with eight replacement holes and a [matching nominal shop packet](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/z180-proposal-v1/README.md). Its fresh numerical evidence remains separate from current Z200 results and instructions. |
| Optional unofficial preview | Extended cleats plus `eoere-2026-horizontal-midpoint-grid-v3` | [Extra grid on](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-extended-cleat-2026-development&view=rear); 120 added T-nuts/lights and 119 cable links. Exact midpoints are provisional assumptions. |
| Current shop coverage | `eoere-base-side-edge-cleats-v1`, extra grid off | [Current shop packet](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/README.md), published at `845e2e0c`; nominal records, held stations and unresolved tolerances. |
| **Current six-case response** | `eoere-base-side-edge-cleats-v1` · [case roster](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/current-cases-v1/result-v1.json) | Six genuine independent admissions and twelve component reports; first-order fixed-rear-leg support scenario, without a resistance or physical-applicability pass. |
| Preserved adjusted base | `eoere-midpoint-ready-frame-v3` · [receipt](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-adjusted-base-v3.json) | [Pre-extension base](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-adjusted-frame-development&view=rear); 39.2-mm principal shift, 22 moved shafts and ten moved screws. |
| Preserved aligned-wire geometry | `eoere-grid-aligned-wire-cutouts-v1` · [receipt](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-aligned-wire-v1.json) | [Aligned-wire viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-bolted-aligned-wire-development&view=rear); 30 rail passages aligned to the original grid. |
| Preserved trimmed cleats | `eoere-rear-trimmed-cleats-v1` · [receipt](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-cleat-trim-v1.json) | [Trimmed-cleat viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-bolted-trimmed-cleats-development&view=rear); distinct geometry evidence. |
| Preserved raised-rail response | `eoere-bottom-rail-tnut-clearance-v1` · [numerical receipt](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/fixed-floor-numerical-mvp-v1.json) | [Raised-rail viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-bolted-bottom-rail-development&view=rear) and [preserved shop guide](eoere-shop-assembly-guide.md); current results use fresh own-case fields. |
| Original Eoere proposal | `eoere-far-pairs-cleat-corners-v1` · [frozen contract](../../eoere-bolted-candidate.json) | [Earlier A12 viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-bolted-development&view=rear); the contract preserves this proposal, rather than selecting a later revision. |

## Current disposition

The current nominal shop packet covers 28 wood/panel profiles, 120 receiver-hole
occurrences for 100 shafts, 66 screw datums, 100 hardware sets, 200 access sides
and nine drawings. The revised blanks fit the same 13-stick / 150-board-foot
purchase scenario. Its nominal mass is 219.115940 kg, including the retained
25-kg allowance and excluding pads; actual weight is unmeasured.

**Four dedicated cleat/post stations remain HOLD.** The 0.340625-mm nominal
bore/screw gap becomes **−0.05625 mm** in the maximum wood-hole scenario.
The close pairs are `cleat_post_bolt_left_2` / `round_kicker_left_rim_2`
and their right-side counterparts, inside the outer posts at the kicker
attachments. Their axes are at Z200 and Z192 mm. This comparison concerns
the drilled-hole envelope and modeled 5-mm screw body; the nominal bolt
shaft itself retains a 0.7375-mm gap to that screw envelope. The four-station
hold covers both paired cleat/post layouts.
The [current-source Z180 proposal](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/result.json)
would increase the analytic maximum-bore gap to 3.94375 mm, but remains
unadopted. The separate [receiver and washer-seat study](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/receiver-seats-v1/result.json)
supports all eight proposed bore occurrences and nominal washer rings within
the recorded profiles and cut inventory. The subsequent [four-receiver finished-solid query](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/finished-receivers-v1/runs-v1/candidate01/result.json)
observes complete 38.1-mm own bore walls and full nominal washer-ring backing
in both proposed hole-size scenarios, including the eight retained receiver
occurrences. The separate [Z180 preview](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-lower-cleat-z180-development&view=rear)
uses those four saved nominal receiver solids and translates all twenty bolt-stack
components. It reuses the other 997 visible parts; the extra grid stays off.
Its proposed lower centers are 44.45/95.25 mm from the common Y-minimum edge,
40.3 mm above each cleat bottom and 58.9 mm below each post top.
These are proposal datums, with actual observations blank.
A separate [matching nominal shop packet](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/z180-proposal-v1/README.md)
provides the proposed hole, stack and access tables and three changed drawings;
the unchanged tables and six other drawings retain their original source links.
Actual tool access, placement tolerances and complete end/edge
and joint resistance remain open. The [signed-end inventory](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/end-geometry-v1/result.json)
reuses current bearing forces separately: many reverse through the holes, so
net-force direction and square-end distance alone cannot establish joint strength.
No cutting, drilling, complete-joint
acceptance or climbing release follows from the current geometry or shop packet.
All actual observations remain blank; all 200 access sides remain unverified.
The recorded **$109.93** hardware comparison retains its dated
[purchase scope](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/README.md).

The [four-station hardware followup](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/receiver-seats-v1/hardware-followup-v1/result-v3.json)
retains 4-inch bolts as the first dimensional proposal. Their catalog body
minimum does not guarantee smooth shank through both timbers. Published
shank limits are available: the [full-body hex-cap-screw table](https://www.nickel-systems.com/wp-content/uploads/2025/04/Hex-Head-Cap-Screws-Min-Body-and-Max-Grip-Gaging-Lengths-table-1.pdf)
confirms the saved ASME B18.2.1-2012 bounds of **68.326 mm** minimum body for
3/8-16 × 4 inches and **81.026 mm** for 4½ inches. The latter exceeds the
78.8416-mm far-wood target by **2.1844 mm** in the recorded nominal-timber /
catalog-washer scenario. Its maximum grip-gaging length is 88.9 mm, while
the nut face without a spacer is only 79.4512–81.4832 mm from the head.
This is a known bolt-selection and stack-up issue; nut seating is not
guaranteed for the longer bolt alone. A proposed
single [nut-side catalog spacer](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/receiver-seats-v1/hardware-followup-v1/spacer-window-result-v1.json)
has a feasible length interval of 9.4488–18.542 mm in the same dimension box.
The nominal 12.7-mm comparison gives positive seating/projection margins;
four spacers and the longer-bolt increment total $10.64 before shipping/tax.
Spacer tolerances, contact resistance and installed tool/removal clearance
remain unqualified. This is an unadopted hardware scenario.

A proposed flush 19.05-mm guide and 6.35-mm backer give the earlier 101.6-mm reach
comparison. The separate [paired-bench fixture](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/receiver-seats-v1/fixture-design-v1/result.svg)
now dimensions supports, stops, guide retention and four clamp lanes for the
unadopted Z180 holes. Its generic flange/cap arrangement needs **113.825 mm**
of usable bit projection at the declared tolerance corner. A 1.50-mm relative
positioning budget leaves **2.44375 mm** to the modeled screw body if achieved.
These are fixture requirements, with actual observations blank.
The [catalog comparison](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/receiver-seats-v1/hardware-followup-v1/guide-bit-sources-v1.json)
identifies a wood bit with documented dimensions and a standard guide whose
taller flange requires a different mounting arrangement. The separate
[catalog adaptation](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/receiver-seats-v1/fixture-design-v1/catalog-adapter-v1/result-v3.json)
requires 122.98725 mm of usable bit projection at its declared tolerance corner.
Its derived positioning allowance is 1.522541 mm against the unchanged 1.50-mm
target, retaining that exceedance and a conditional 2.421209-mm screw-body gap.
Actual guides, clamps, drill/chuck, chip clearing and socket wells remain
unverified.

The separate [factory-guide comparison](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/receiver-seats-v1/hardware-followup-v1/factory-guide-sources-v1.json)
identifies the manufacturer-listed Milescraft 1307 at $24.99 with a 13/32-inch
guide hole. This could avoid the custom press-fit receiving plate and cap.
Its hole position, effective guidance, supported footprint and tool fit remain
unestablished; no product dimensions or machining pass are inferred from the
hole-size listing. The smaller Big Gator STD1000DGNP stops at 3/8 inch and is
excluded from this final-bore comparison.

The current six-case calculation retains 250 lb ×2 downward, 300 N horizontal,
the recorded 100-mm hold arm and gravity. All 32 floor points are compression-only;
only the two rear-leg centroids receive XY restraint under the unverified no-slip
assumption. Each fresh case has its own saved-field/operator audit, with no retries
or historical forces. The largest full-gradient residual is **6.128662e-6 N**
against the unchanged 1e-5-N limit. Both credited legs bear in every case; their
minimum normal force is 592.629345 N. The separate seven-case global statics
check has a minimum support-edge margin of 330.28499148 mm.

All six coarse and six detailed component reports are complete. The largest
comparisons below select one own-case witness each; they do not combine cases.

| Current comparison | Largest result | Meaning |
| --- | ---: | --- |
| Generic 9-mm screw-head reference, CD=1 | 2.572553 | Reference exceedance; actual Hillman pull-through resistance remains unknown. |
| Sampled panel bending / rolling shear, CD=1 | 4.613408 / 2.451803 | Reference exceedances retained; panel/screw remedies remain stopped. |
| Heel scenario t6/Ri6 | 1.107192 | Seven exceeded heel rows across six cases. |
| Owner nominal heel scenario t6.35/Ri6.35 | 0.992649 | Zero exceeded heel rows; only 0.7351% reference margin, with actual formed-product resistance unknown. |
| Unadjusted timber-bolt component reference | 0.699372 | 92 compatible shafts per case; eight mixed stacks and all 24 complete joints remain unqualified. |
| Gross timber normal / shear references | 0.513049 / 0.973080 | Fully braced raw rectangles; finished sections and actual restraint remain unqualified. |
| Bolt-shaft material first-yield scenario | 0.513451 | Catalog/root/Fy scenarios; delivered shank, root notch and complete bolt resistance remain unqualified. |
| Catalog-corner axial-only washer required Fy | 156.014671 MPa | Required material scenario, not verified washer Fy or combined washer resistance. |

The first-order model reaches 56.618189 mm of sampled interaction-point motion
and 0.107755 rad of relative strip rotation. Physical applicability, finite contact
pressure and demand bounds remain unestablished. Distributed panel RHS remains
source-authenticated capture rather than an independent regeneration. See the
[detailed record](completion-ledger.md#current-extended-cleat-numerical-completion)
for source/review bindings, retained sensitivity exceedances and exact gaps.

## Proposed Z180 evaluation

The four lowered cleat/post bolts now have [six fresh admitted cases](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/z180-mechanics-execution-v1/cases-v1/result-v1.json)
and [six combined component reports](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/z180-mechanics-execution-v1/component-results-v1/result-roster-v1.json).
The original loads, 32 compression-only floor points and two rear-leg XY
restraints stay fixed. Each case uses its own new operators, forces and admission;
there were no force or component retries. Maximum full-gradient residual is
**4.585086e-6 N**, below the unchanged 1e-5-N limit, and minimum credited-leg
bearing is **592.726899 N**.

The [proposal summary](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/cleat-remedy-v1/current-source-followup-v1/z180-mechanics-execution-v1/summary-v1/runs-v1/attempt02/summary.json)
selects complete own-case witnesses with the unchanged comparison methods:

| Proposed Z180 comparison | Maximum | Limit |
| --- | ---: | --- |
| Generic 9-mm screw-head reference, CD=1 | 2.572731 | Actual Hillman resistance unknown; panel/screw remedies remain stopped. |
| Sampled panel bending / rolling shear, CD=1 | 4.613881 / 2.451843 | Retained reference exceedances. |
| Heel t6/Ri6 | 1.110021 | Seven exceeded rows among 528. |
| Owner nominal heel t6.35/Ri6.35 | 0.995184 | Zero exceeded heel rows; only 0.4816% reference margin, with actual formed-product resistance unknown. |
| Unadjusted timber-bolt component | 0.699181 | 92 compatible shafts per case; eight mixed stacks and all 24 complete joints remain unqualified. |
| Gross timber normal / shear | 0.514427 / 0.974374 | Raw rectangles and assumed restraint; finished net sections remain unqualified. |
| Shaft material first-yield scenario | 0.512707 | Delivered shank/root geometry and complete bolt resistance remain unqualified. |
| Catalog-corner axial-only washer required Fy | 157.133109 MPa | Required material scenario; actual washer strength and combined resistance unknown. |

The maximum sampled first-order interaction-point motion is **57.232675 mm**;
maximum relative strip rotation is **0.109314 rad**. Physical applicability and
demand bounds remain unestablished. The same total applied wrenches and floor
footprint allow reuse of the current global-statics feasibility check, whose
minimum support-edge margin is 330.28499148 mm; its old elastic reactions are
not reused. The unchanged panel bank retains its source-captured distributed-RHS
proof limitation. These are conditional numerical results for an **unadopted**
proposal, with all complete-joint resistances and physical release flags unchanged.
See the [detailed ledger](completion-ledger.md#lowered-cleat-bolt-proposal-conditional-numerical-completion)
for exact inputs, reviews, output checks and active evidence retention.

## Remaining work and next actions

1. Review the separate Z180 preview for the four held cleat/post
   stations before adopting changed axes or revised drilling instructions. The
   current Z200 and separate Z180 numerical packets retain their own bindings;
   neither establishes complete proposed-joint resistance.
2. Use the completed current numerical packet within its declared scope. Complete
   joint resistance, finished net sections, restraint and first-order physical
   applicability remain open; no old response or capacity transfers by relabeling.
3. Identify actual saw/drill/bit and finishing-tool envelopes, then resolve
   supported reach, recess finishing, fixture dimensions and interface tolerances
   against current shop datums. The preserved guide's axis-continuity statement
   belongs to its earlier aligned-wire scope; it does not cover the later 22/10 moves.
4. Retain the current screw count and purchase policy. Panel/screw remedies stay
   stopped; the optional extra grid remains unofficial and separately scoped.

## Engineering reading order

Use the current geometry and shop packet above, then the bounded evidence:

- [Four bounded studies](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/README.md) and [component resistance followup](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/resistance-followup-v1/README.md): old admitted actions and preserved local geometry; complete joint resistance remains open.
- [Adjusted-base audit](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/README.md): 112 nominal washer-seat supports for v3, extra grid off; no extension response or restraint qualification.
- [Connected-stack followup](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/README.md): 48 old shaft/case combinations; trial bearing parameters supply no allowable-pressure or complete-joint pass.
- [Guarded reproduction guide](hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/reproduction-guard-v1/README.md): authenticated inputs, fresh outputs and exact provenance; use its guarded entrypoints for future reproductions.

## Conditional operations and purchasing

Use the current shop tables for changed members/stations. Earlier leg-corner
layout sheets cover only their source-bound unchanged members and four axes.
Model occupancy and CSV lengths are analysis envelopes, not released bit sizes
or delivered shank lengths. Actual parts, tool access and tolerances remain
unobserved. Partially threaded bolts remain the basis; receiving and full
nut seating remain per-stack checks. No insert pilots or physical testing
are added by this reading path.

## History and evidence recovery

The [design-history catalog](../history/design-history.md#eoere-development-sequence)
explains earlier Eoere, thin-frame and WJ alternatives. The
[full pre-compaction summary](../history/eoere-development-summary-before-compaction.md)
preserves every original byte from `845e2e0c`; its old status and next actions
are historical. [Browse that commit's original summary](https://github.com/mckayreedmoore/mini-moonboard/blob/845e2e0cf2bf1514398e115c382865579fd77141/docs/wood-joints-mvp/README.md)
to follow its relative links. The detailed ledger and frozen packets stay at
their source paths.

<a id="current-working-model"></a>
<a id="preserved-earlier-eoere-a12-packet"></a>
<a id="preserved-thin-b103b104-predecessor"></a>

Earlier [wood-joint working-model records](../history/wood-joint-development-summary-before-navigation-cleanup.md#current-working-model),
[Eoere A12 discussion](../history/eoere-development-summary-before-compaction.md#preserved-earlier-eoere-a12-packet)
and [thin-frame discussion](../history/eoere-development-summary-before-compaction.md#preserved-thin-b103b104-predecessor)
retain their own loads, geometry and unresolved criteria.

Required cached solids, source banks, fields, operators and reviews remain
**active inputs**, including files under ignored `fea/generated/`. Use the
[cleanup and recovery record](../repository-cleanup-evaluation-2026-09-28.md)
and [contributor recovery workflow](../../CONTRIBUTING.md) before moving files.
Historical viewer choices and shared mesh aliases remain available. Candidate
selection, native authorization and physical acceptance remain separate decisions.
