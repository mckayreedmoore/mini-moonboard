# Compact bolted frame development

This is the main entry for `compact-bolted-frame-development`. The current geometry is **`eoere-single-leg-bolts-header-angles-v3`**,
with one bolt at each long-leg/frame and long-leg/runner joint, **24 angles, 96 bolt stacks and two single plywood cleats**.
The 32 enclosed Ø38.1-mm passages, solid 4×6 outer posts, climbing panels and **66 Hillman axes** are retained. Extra grid is off.
The selected [screw-and-bracket baseline](../../current-candidate.json) keeps its separate authority.

Each new angle beneath the header shares two existing header shafts and the
lower cleat/post pair. Those lower axes move from Z200 to the factory far row
**Z173.8125**; their heads sit at the inner flange and nuts face outward.
Each plywood leaf has four holes. The four `*_2` long-leg axes are omitted;
retain the four `*_1` axes. No timber length or section is enlarged by this revision.

## Active builder reading path

| Need | Start here | Boundary |
| --- | --- | --- |
| Current geometry | [Combined viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-leg-header-frame-development&view=rear) · [receipt][combined] | 20 sawn members, two plywood cleats, six climbing panels, 24 angles, 96 bolt stacks and 66 screws. Nominal geometry clears 1,027 occupied parts. |
| Current nominal shop instructions | [Builder plan](builder-plan.md) · [member/receiver layout](builder-layout.md) · [96 selected stacks][hardware] | 112 receiver occurrences; 24 factory spacers. All observations stay blank. Installation and strength remain unqualified. |
| Machine revision authority | [Checked index](development-revisions.json) | The complete enclosed-passage predecessor remains bound under `preceding_revision`; all earlier viewer choices remain available. |
| Current calculations | [Integrated leg/header work](../wood-joints-mvp/completion-ledger.md#single-bolt-leg-joint-review) | [Six corrected cases](leg-header-current-results-v1.json) converge and pass separate raw-operator/force replay; maximum residual 3.724025e-6 N. These are conditional fields, without production admission or physical acceptance. |
| Material and retained service datums | [Plywood basis](plywood-cleat-material-basis-v1.json) · [32 passage rows][passages] | Plywood stamp/thickness and physical cable feeding remain unobserved. Enclosed holes need hole-specific strength checks. |

The plywood proposal is now represented geometrically: one factory
**609.6 × 203.2 × 28.575-mm** leaf per corner, strength axis along world Z,
with a proposed minimum actual thickness of 27 mm. It requires APA Rated
Sturd-I-Floor 48 oc PS 1 plywood with at least five plies and the recorded
Group 1 bearing basis. It is distinct from the 18.25625-mm climbing panels.
Neither modeled occupancy nor a catalog description verifies delivered material.

The enclosed passages remain centred at N69.85 in eight 2×6 members. F1–G1
stays shifted 40 mm along its receiver to avoid bolt 073. All LED endpoints
and the intact harness remain fixed. The six former notch-location failures
belong to the preserved notched model; they do not qualify or disqualify these holes.

## Current disposition

| Concern | Integrated change or usable result | Remaining conclusion |
| --- | --- | --- |
| Long-leg joints and floor feet | One retained `*_1` bolt at each of the four joints removes the two-hole pattern. The 1:12 recess and sole section stay fixed. | **Left foot still exceeds the CD1 near-end shear reference: 826.180 / 733.460 N = 1.126415**, in A12-forward. Right-foot maximum is 0.881455; upper-leg member-shear maximum is 0.084921. The corrected [own-size Grade5/F606 yield references](leg-single-pin-product-references-v2.json) are below one in all 24 rows, maxima **0.847716 left / 0.836991 right** at the upper bolts. This reuses the existing qualified 92-ksi specification. The earlier generic45-ksi report is superseded: its upper rows retain four exceeded sensitivity references, while its foot rows used the wrong diameter. Complete bolt/wood, recess and restraint checks remain. The leg is not a two-force member while its foot bears on the floor. |
| Primary plywood cleats | Two single 8×24-in leaves and their four-hole connections are modeled; new under-header angles share their lower shafts. Published directional APA properties are recorded. | The fuller [net/load-station construction](../wood-joints-mvp/completion-ledger.md#current-shared-header-plywood-results) reaches **1.843983**. Separate [paired-leaf pilots](plywood-cleat-paired-pilot-results-v1.json), each using its own four leaf operators and recovered actions, reach **1.032486 at 8-in width / 1.113541 at 10-in width** in A12-left. These are conditional engineering constructions, not whole-joint capacity ratings. The wider pair redistributes contact unfavorably. Integrate the bilateral upper return before more width trials; neither pilot changes the current model. |
| Outer front posts | Solid 4×6 posts and their 9.525-mm longitudinal T-nut-clearance bevel are retained. The old fixed-force shear comparison was 0.722654. | The fresh 24 post connection-shear comparisons are below one, maximum **0.730989** using the retained full-depth core. Other normal, bearing, end/group and complete-joint checks remain. |
| Enclosed service holes | All 32 holes and their routes are geometrically integrated with the leg/header/plywood revision. | Complete hole-specific shear/splitting, net section, connection ligaments and changed installation/access. No old notch pass transfers. |
| Panel and screw-head references | The separate [98-screw trial](panel98-trial-results-v1.json) retains all 66 original axes and adds 32 on its enclosed-passage parent. It improves panel references but worsens the governing screw-head concentration. | Keep 66 screws in this combined model. The trial alone is not a remedy; its forces do not transfer to the changed header/cleats/legs. Hillman qualification and panel/attachment resolution remain separate duties. |
| Angles, other bolts and member restraint | The two requested under-header angles bring the installed count to 24; six existing four-packs supply that count. Conventional predecessor fitting, washer, bolt and member worksheets remain available in the ledger. | Check the fresh simultaneous fitting/common-shaft/seat actions and actual restraint on the changed basis. Conditional component references do not qualify whole joints or physical response. |

The [combined successor study](coherent-return-paired-foot-results-v1.json)
integrates the other reviewed proposals: four separate plywood leaves,
both upper outboard returns and a 6-mm transverse move of each single foot
bolt. All six original load cases independently replay. Its maximum leaf
section reference is **0.982705**, signed-foot reference **0.894231** and
other named leg/post reference **0.672762**; all 48 named comparisons are
below one. The proposal has **26 angles, 108 bolts and 40 factory spacers**,
retaining 66 screw axes. It remains unadopted: complete joints, changed
members/restraint and the revised shop packet still need their own checks.
The generic screw-head maximum increases to **3.005974**, while panel
bending/rolling remain **3.503559 / 2.087697** at CD1. It does not resolve the
deferred panel/attachment issue. Published v3 remains the 24-angle/96-bolt
geometry described above.

The single-leaf material review corrected the perpendicular-axis rolling-shear
reference from 500 to **385 lbf/ft**; the original saved gross-cut maximum
stays 0.945264 under its assigned scope. The [material record](plywood-cleat-material-basis-v1.json)
also distinguishes the strip factors for Y-normal and Z-normal cuts. Preserve
those corrections when checking the current lower row and new angle sharing.
The [operator scenario](plywood-cleat-operator-scenario-v1.json) uses independent
published EA/EI and identifies the unresolved local shear and torsion approximations.

The rejected six-hole layout and the later right-hand attachment-label error
remain recoverable in the existing integration packet. V3 fixes the labels and
requires **all 96 factory attachments to lie on their own shaft lines** before
preparing or running mechanics. Balanced forces alone did not catch that mapping error.
No rejected force result is a current result or an accepted design basis.

## Revision map

| Role | Exact revision / record | Viewer or scope |
| --- | --- | --- |
| **Current geometry and shop layout** | `eoere-single-leg-bolts-header-angles-v3` · [receipt][combined] | [Current combined model](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-leg-header-frame-development&view=rear); 96 bolts / 24 angles / 66 screws. |
| Unadopted combined successor | `unadopted-bilateral-return-paired-cleats-signed-foot-v1` · [six-case study](coherent-return-paired-foot-results-v1.json) | 108 bolts / 26 angles / 66 screws; independent fields and bounded component references, without complete-joint or structural acceptance. |
| Preserved enclosed-passage parent | `eoere-centred-enclosed-passages-v1` | [100-bolt solid-cleat parent](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-enclosed-passages-frame-development&view=rear). |
| Preserved notched geometry and optional grid | `eoere-narrow-channel-openings-v1` | [Original grid](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-narrow-channels-frame-development&view=rear) · [unofficial extra grid](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-narrow-channels-grid-development&view=rear). Neither is a current combined-grid variant. |
| Preserved matched six-case evidence | `eoere-raised-kicker-screws-v1` / `eoere-selected-purchase-hardware-v1` | [2×6-post response](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/selected-hardware-v1/current-response-v1/result.json); its own geometry, assumptions and acceptance limits. |
| Unadopted lower-corner alternative | `eoere-lower-cleat-z180-proposal-v1` | [Z180 preview](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-lower-cleat-z180-development&view=rear); independent geometry and conditional cases. |

## Remaining work and retention

The [full engineering completion goal](../wood-joints-mvp/completion-ledger.md#practical-engineering-completion-goal)
remains active and unachieved. The six current force/recovery replays are complete; **47 of 48** named leg/post
connection-shear comparisons are below one. Resolve the left-foot component and plywood-cleat construction; finish
upper-bolt geometry/end/edge and complete joints, critical finished
members and restraint, then give one consistent engineering
disposition. The [completion ledger](../wood-joints-mvp/completion-ledger.md#current-concern-update)
retains the detailed predecessor checks and current followups. A failed adopted
criterion or missing load path stops the affected operation; no new blanket
external sign-off or native-solve requirement is introduced.

The [duration worksheet](load-duration-assessment-v1.json) and
[short-term reference disposition](short-term-strength-disposition-v1.json)
retain their own frozen predecessor forces. Their duration credit is unadopted;
the current leg/post and ordinary-bolt comparisons above retain CD1.

The selected screw/ML24Z baseline, earlier block/solid-cleat options, failed
notches, rejected mapping results and all historical viewer choices remain
preserved. The current nominal shop packet and compact viewer patch total
**about 1.0 MB** including the current numerical summaries, before mesh sharing; the complete 96-axis/112-receiver tables make
this combined geometry reviewable without reconstructing the old override chain.
The separately retained enclosed-passage parent adds about 1.48 MB of compressed
scene and three datum/receipt files, preserving its viewer and replay inputs.
Bulky CAD, operators and case fields stay in the ignored integration packet.
Nothing is archived or pruned. No actual material, tool, floor or build inspection,
fabrication release or climbing release is established.

[combined]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/leg-header-v3/geometry.json
[hardware]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/leg-header-v3/hardware-selection.csv
[passages]: ../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/enclosed-passages-v1/passage-datums.csv
