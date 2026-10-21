# Compact bolted frame development

This is the main entry for `compact-bolted-frame-development`. The current geometry is **`eoere-narrow-channel-openings-v1`**,
with 32 base-grid channel openings narrowed to **14 mm**, retaining N14.35 depth
and every cable path. The optional extra grid is **off**: 22 timbers, six panels, 22 angles,
100 bolt stacks and 66 purchased Hillman panel/kicker screws. The selected
[baseline authority](../../current-candidate.json) stays separate.

The owner selected solid **4×6 outer kicker posts**, replacing only
`base_post_outer_left/right`: 238.9 × 139.7 × 88.9 mm. Both grow 50.8 mm
inward; a 9.525-mm full-height inner-corner bevel clears the kicker T-nut
flanges. Cleats, panels and all 100 bolt lines / 66 screw axes stay fixed.
Eight bolt stacks change; four front head datums rebase along their existing
lines. Four 6-in front bolts and four 7-in cleat bolts replace the old lengths.
Each cleat/post nut uses two existing-type 12.7-mm factory spacers: **twelve
spacers overall**. Revised force response and complete joints remain unqualified.

**Plywood is the owner-selected primary cleat approach:** develop the [rectangular bolted plywood gussets](../wood-joints-mvp/completion-ledger.md#plywood-cleat-development-choice) ([sketch](plywood-cleat-study.svg)) using two 1⅛-in leaves per corner and the existing bolt locations. Published APA values support preliminary sizing; nominal timber/panel clearance is checked. Complete bolt-group resistance, leaf sharing, services/access and revised actions before replacing the solid 2×6 cleats in the current model and builder packet.

## Active builder reading path

| Need | Start here | Boundary |
| --- | --- | --- |
| Current geometry | [Narrower-opening viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-narrow-channels-frame-development&view=rear) · [receipt](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-narrow-channels-v1.json) | 32 narrower openings; 4×6 posts and all axes retained. Six notch holds remain. |
| Current nominal shop instructions | [Builder plan](builder-plan.md) · [composed member/receiver layout](builder-layout.md) · [eight hardware overrides](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/front-posts-4x6-v1/hardware-selection.csv) | Override the preserved packet for these members/stacks. Changed installation remains unqualified; observations stay blank. |
| Revision authority | [Checked revision index](development-revisions.json) | Current geometry and overrides; the complete preceding revision remains separately bound. |
| Latest numerical evidence | [Preserved six cases](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/selected-hardware-v1/current-response-v1/result.json) | Applies to the **2×6-post predecessor**, extra grid off; no response/pass transfers to the wider posts. |
| Current checks and next steps | [Post revision](../wood-joints-mvp/completion-ledger.md#current-4x6-front-post-revision) · [changed bolts](../wood-joints-mvp/completion-ledger.md#current-4x6-post-bolt-reference-followup) · [installation geometry](../wood-joints-mvp/completion-ledger.md#current-4x6-post-installation-geometry) | Fixed-original-force post and Cg-only bolt uppers **0.722654 / 0.508716**. All 200 sides retain nominal wrench/removal alternatives and all 120 receivers retain guide/pad support after the restored-channel followup; bolt 081 needs the revised wrench orientation. Revised response, complete joints and actual tools/tolerances remain open. |

## Revision map

| Role | Exact revision / record | Viewer or scope |
| --- | --- | --- |
| **Main geometry** | `eoere-narrow-channel-openings-v1` · [receipt](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-narrow-channels-v1.json) | [Extra grid off](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-narrow-channels-frame-development&view=rear). |
| Optional unofficial preview | Current narrower openings plus retained `eoere-expanded-right-column-v1` | [Extra grid on](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-narrow-channels-grid-development&view=rear); geometry only, 264 main positions. |
| **Current shop plan** | `eoere-narrow-channel-openings-v1` | [Builder plan](builder-plan.md) composes 32 narrower channel openings with the preceding two post, eight stack, sixteen receiver and two screw-datum overrides. |
| Preserved geometry / hardware | `eoere-raised-kicker-screws-v1` / `eoere-selected-purchase-hardware-v1` | [2×6-post viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-selected-hardware-frame-development&view=rear); its matching six-case response stays frozen. |
| Unadopted lower-corner proposal | `eoere-lower-cleat-z180-proposal-v1` | [Z180 preview](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-lower-cleat-z180-development&view=rear); separate geometry, shop packet and response. |
| Earlier revisions and optional grids | [Preserved revision index](development-revisions.json), `preceding_revision` | All earlier viewer choices and frozen source paths remain available. |

## Current disposition

The [conventional post review](../wood-joints-mvp/completion-ledger.md#current-4x6-post-conventional-review) retains 4×6 stock: net axial/bending **0.654785**, conditional compression **0.598883** at K≤2, and near-end shear **0.722654**.
These saved-action comparisons establish no revised response, endpoint restraint or complete joint capacity.
The [geometry receipt](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-front-posts-4x6-v1.json)
records valid solids, retained axes/backing and positive selected hardware windows.
The revised lower cleat/post bolts also pass the existing nominal-placement
comparison at those saved forces, maximum **0.730193**. Current front bolts retain
the smaller thread-root basis; a [four-seat counterbore option](../wood-joints-mvp/completion-ledger.md#front-runner-counterbore-detail-option) has passing same-action component screens but remains unadopted. Complete joint resistance stays open.
Both post blanks fit the existing rear-leg stock offcuts, retaining the nominal
**13 sticks / 150 board feet**. New timber adds **1.666229 kg** at the recorded
500-kg/m³ density. The predecessor's mass/cost results retain their original scope.
The restored-channel followup preserves nominal access/fixture applicability; changed metal strength, actual tools/tolerances and response remain open.

The [narrower channel revision](../wood-joints-mvp/completion-ledger.md#current-narrow-channel-revision) restores material at 32 openings; the [same-action beam normal upper](../wood-joints-mvp/completion-ledger.md#current-narrow-channel-strength-interpretation) remains **0.480823**. Six central cut holds and the [left/right foot coverage issue](../wood-joints-mvp/completion-ledger.md#current-left-right-rear-foot-comparison) remain.
The [fixed-axis 6×6 rear-leg option](../wood-joints-mvp/completion-ledger.md#rear-leg-6x6-fixed-axis-feasibility) has positive bolt-window/stock screens and a [below-pair shear bound](../wood-joints-mvp/completion-ledger.md#rear-foot-global-statics-component-bound) of **0.988366** over the six-face load box and any horizontal direction within 300 N, under its declared support/mass envelopes; it remains unadopted. Panel/screw
engineering assessment is reopened under the full goal; the [calculation audit](../wood-joints-mvp/completion-ledger.md#current-exceedance-calculation-audit)
corrected the predecessor's panel comparisons from 26 to 27 exceeded references. The [panel-corner hand check](../wood-joints-mvp/completion-ledger.md#panel-corner-handcheck) finds two screws carry **83.8%** of that panel's saved tension; compatible load sharing remains unqualified.
The predecessor's working 6.35-mm heel scenario has maximum 0.992604; seven
exceedances belong to its separate 6-mm sensitivity. Complete joint/member,
physical stiffness/contact and no-slip/restraint qualification remain unresolved.
No fabrication or climbing release is established by this geometry revision.

The [remaining-item review](../wood-joints-mvp/completion-ledger.md#remaining-review-after-4x6-posts)
retains the rear-foot proposal; the [rear cable detour](../wood-joints-mvp/completion-ledger.md#central-cable-bypass-and-known-kit) exceeds the known V5 harness budget
and supplies no current notch remedy. Keep the kit and six cut holds. The primary cleat task is
complete plywood-joint transfer; further retained-timber cleat resistance research is inactive.
Five paired-edge holds, clipped groups and justified member restraint also
remain open; the working 6.35-mm heel has no exceeded saved-force references.

## Proposed Z180 evaluation

The **unadopted** Z180 layout has six fresh admitted cases and six combined
component reports under its own inputs. Maximum full-gradient residual is
**4.585086e-6 N**, within the same 1e-5-N gate. Reference exceedances and small
nominal heel margins remain; first-order applicability and complete-joint
resistance are unqualified. Its results do not select the proposal or release
current Z200 operations. The [detailed proposal record](../wood-joints-mvp/completion-ledger.md#lowered-cleat-bolt-proposal-conditional-numerical-completion)
links the full comparisons, fixtures, reviews and retained raw evidence.

The owner-requested optional column adds twelve T-nuts and matching LEDs at
X2300 mm: **264 main positions**, plus ten unchanged kicker positions.
The two right panels include the new bores. Three right rails receive the
existing smaller cable-channel profile; all 100 bolt and 66 screw axes stay fixed.
Exact CAD checks clear the new services and generic rear-bolt envelopes:
**33.625 mm** flange-to-right-4×6 gap and **14.325 mm** cable gap.
The original-grid option and preceding 252-position viewer remain available.
Future official grid/holds, actual hold footprints, cable installation and
changed-section strength remain unresolved. See the
[right-column implementation](../wood-joints-mvp/completion-ledger.md#owner-requested-right-column-preview).

## Remaining work and next actions

The [full engineering completion goal](../wood-joints-mvp/completion-ledger.md#practical-engineering-completion-goal)
is **unachieved**; its retained-timber route was blocked after three turns with essential inputs missing. The owner now selects plywood as the primary cleat route; complete its joint checks first.
Use conventional worksheets and retained evidence; completion requires the
remaining in-scope engineering duties to be resolved. The four gates are a
fixed basis, complete joints, critical members/restraint and one consistent
engineering disposition. The revised frame's force basis is still partial.
The **preceding 2×6-post** [bounded numerical assessment](../wood-joints-mvp/completion-ledger.md#engineering-closure-beyond-the-assessment)
is complete; the table below retains that predecessor's scope. Its passes
do not transfer to the changed posts or bolts. The [current input boundary](../wood-joints-mvp/completion-ledger.md#current-engineering-input-boundary)
records the missing finite cleat resistance and justified force and transfer basis for the revised joints after the completed conventional checks.
Use the [remaining-step decision table](../wood-joints-mvp/completion-ledger.md#remaining-review-after-4x6-posts) for priorities, dependencies and closing conditions, including the reopened panel/attachment assessment.

| Duty | Completed evidence to retain | Required next conclusion |
| --- | --- | --- |
| Primary plywood cleats and complete wood/bolt joints | The [plywood proposals](../wood-joints-mvp/completion-ledger.md#plywood-cleat-development-choice) use published APA inputs. The original two-leaf gross-cut sizing index is **0.742295** under assigned sharing. An unadopted single 8×24-in factory leaf removes that sharing assumption: gross-cut **0.945264**, lower-bolt **0.827096** and local-bore **0.656266** references, with no nominal plywood interference against the 1,033-part enclosed-passage bank. Its conservative upper-shaft comparison remains **1.024083**; these are supplied-action component constructions, not complete-joint acceptance. | Coordinate the owner's two interior under-header brackets and revised leg connections before crediting reduced cleat demand. Complete the actual upper mixed-stack and lower post interfaces: bolt/group/net/edge resistance, common-shaft and axial-seat transfer, runner contact, revised hardware/tool clearance and justified current actions. Retain or revise the plywood detail before replacing the model/shop packet; the single-leaf comparison is not adopted. Complete the other joints on their own basis. |
| Fittings, washers and timber seats | The [132 connected ideal bend/two-neck constructions](../wood-joints-mvp/completion-ledger.md#current-connected-bend-and-unholed-necks) match full root tractions and include neck backing pressures; the bend controls at **0.952732**, with all 264 necks below **0.509262**. [2,640 local loaded-hole constructions](../wood-joints-mvp/completion-ledger.md#current-loaded-steel-hole-transfer) reach **0.267477**, including all eight mixed axes. [264 nominal net-section envelopes](../wood-joints-mvp/completion-ledger.md#current-continuous-flange-net-section-envelope) reach **0.966037**; [1,584 conditional net-bar stability comparisons](../wood-joints-mvp/completion-ledger.md#current-flange-net-bar-stability) reach **0.984262**, assuming held end translations and support twist restraint. The [nominal elastic-torsion followup](../wood-joints-mvp/completion-ledger.md#current-flange-elastic-window-comparison) now has all **528 conditional region bounds** below one, maximum **0.984743**, after matching each centroid substitution to its own interval side. The [gross-strip warping comparison](../wood-joints-mvp/completion-ledger.md#current-distributed-flange-warping) includes distributed torque and axial warping work, maximum **0.993809**, with warping blocked at both ends. The [combined timber-seat normal-bearing check](../wood-joints-mvp/completion-ledger.md#current-seat-normal-bearing-interaction) includes possible washer/fitting-pressure overlap, maximum **0.493195**. [Washer/spacer duties](../wood-joints-mvp/completion-ledger.md#current-axial-washer-and-spacer-transfer), [common-flat backing](../wood-joints-mvp/completion-ledger.md#current-flat-flange-backing-pressure) and [block paths](../wood-joints-mvp/completion-ledger.md#current-principal-block-shear-components) retain their scope. The [selected bolt/nut axial proof comparison](../wood-joints-mvp/completion-ledger.md#current-grade5-axial-proof-reference) covers **1,200 references**, maximum **0.026509**, conditional on standard Grade 5 parts and full-form engagement. | The [local normal-cycle check](../wood-joints-mvp/completion-ledger.md#local-normal-prying-statics-limit) shows that balance and bearing limits alone do not preserve the saved washer reference. Resolve the holed outer plate between matched neck-exit and local-hole tractions, unused near holes, prying and timber-interior transfer with supported restraint/response. The nominal bar comparisons retain ideal end conditions; complete holed-plate transfer, H3.3 and actual warping/restraint remain unqualified. Neither the partial regions nor the conditional bar model qualify the complete fitting or joint. |
| Finished members and floor support | [All 120 wood-bearing occurrences](../wood-joints-mvp/completion-ledger.md#remaining-bore-window-normal-completion) have **372 nominal normal comparisons**, including 84 staggered and 186 same-station comparisons. [48 normal comparisons cover all 32 channels](../wood-joints-mvp/completion-ledger.md#current-service-channel-normal-coverage), upper **0.480823**; the [notch-location gate](../wood-joints-mvp/completion-ledger.md#current-channel-notch-location-gate) separately finds **six prescriptive failures**. [Taper normal references](../wood-joints-mvp/completion-ledger.md#current-retained-leg-taper-normal-completion) reach **0.345938 / 0.743849** under DF-L/C16 hypotheses; [13 nominal shear/torsion references](../wood-joints-mvp/completion-ledger.md#current-retained-taper-shear-and-normal-notch-scope) reach **0.740474** and map the named normal-notch provision. The [full receiver shear census](../wood-joints-mvp/completion-ledger.md#current-mitered-prismatic-connection-shear) covers all **120 wood occurrences / 100 bolts**: 315 component passes, four failures and five paired-edge holds; six clipped groups remain outside the rectangular rule. [Four positive-side bearing/shaft witnesses](../wood-joints-mvp/completion-ledger.md#current-side-positive-bearing) pass the working lateral reference, maximum **0.959309**, without clearing the paired-edge holds; [rear-foot mean-bearing comparisons](../wood-joints-mvp/completion-ledger.md#current-rear-foot-bearing-and-normal-wrench-recovery) stay closed. | The [front-post failures](../wood-joints-mvp/completion-ledger.md#current-front-end-connection-shear), maximum **1.505549**, and left rear-leg foot failure, **1.123212**, hold those connections. The [load-direction/grade audit](../wood-joints-mvp/completion-ledger.md#current-shear-failure-basis-audit) confirms that prescribed seat-pressure spreading and the compared higher DF-L grades cannot clear them at the same reactions/CD1 basis; the [owner-requested frame update proposals](../wood-joints-mvp/completion-ledger.md#current-frame-update-proposals) screen thicker front posts and shifted rear-foot pairs below one at the original scalar shear forces. The front-post geometry is now implemented as described above; rear-foot changes remain unadopted. The upper-cleat P/G allocation leaves the front checks unchanged. The [sharing limits](../wood-joints-mvp/completion-ledger.md#current-floor-and-shear-sharing-limits) keep the same-edge post targets unchanged under moment-only circulation; the [directional force-cycle bound](../wood-joints-mvp/completion-ledger.md#current-front-force-cycle-moment-bound) also excludes clearing the governing post target under the Fe/divisor-5 law (**250.408860 N** relief upper versus approximately **274.341573 N** needed). Rear-foot same-edge relief through vertical support sharing needs **>377.408 N** removed from its source floor reaction. The [400-N construction](../wood-joints-mvp/completion-ledger.md#current-rear-foot-400n-fixed-sharing) now supplies one balanced local allocation: both fully prescribed shaft fields are below **0.984951**, leg/runner bore-window shear is **0.992788 / 0.708047**, and affected nominal normal references remain below one. The [finite six-wrench floor construction](../wood-joints-mvp/completion-ledger.md#current-rear-foot-400n-full-floor-tractions) keeps those wrenches and satisfies the [reaction/centroid envelope](../wood-joints-mvp/completion-ledger.md#current-rear-foot-sharing-envelope) and complete-resultant mean-bearing reference, maximum **0.981850**. The [500-N trial](../wood-joints-mvp/completion-ledger.md#current-rear-foot-vertical-sharing-trial) remains rejected. Resolve these failures, five paired-edge holds and the channel-detail failure. The [36 planar slit references](../wood-joints-mvp/completion-ledger.md#current-central-channel-slit-reference) reach **0.335919**; finite-notch geometry, design format and the four other wrench components remain unqualified. Combined taper/support, end-load introduction and remaining profile coverage stay open. The taper linear normal/shear comparison has same-cut witnesses **1.218477 / 1.206128**, limited to that auxiliary reference. The [changed foot/end comparisons](../wood-joints-mvp/completion-ledger.md#current-rear-foot-400n-full-floor-tractions) pass their nominal references; complete timber-interior/end transfer and a supported no-slip/restraint response remain unqualified. The [outer-core-only shortcut](../wood-joints-mvp/completion-ledger.md#current-rear-leg-outer-core-load-entry) fails its necessary working bearing reference. |
| Restraint and response | The [directional-restraint and retained-core column worksheets](../wood-joints-mvp/completion-ledger.md#current-directional-restraint-and-column-reference) complete 24 conditional column comparisons, maximum **0.668758**, and state the required spring stiffness. The [washer/spacer elastic normal mode](../wood-joints-mvp/completion-ledger.md#current-washer-axial-compliance-bound) has partial metal compliance **≤0.000287961434 mm/N** across 1,000 profiles. The [cleat return worksheet](../wood-joints-mvp/completion-ledger.md#current-cleat-normal-return-wrench) retains all twelve normal-pressure couples, largest component **8202.246726 Nmm**; matching compression columns alone cannot replace that source partition. | Justify the coupled axial capture/seat return paths, bearing-roll restraint and applicable response. In the prescribed scalar series reference, **C_remaining≤0.000712038566 mm/N** is sufficient for the original 1,000-N/mm captures; the actual wood/head/thread/contact contribution remains unqualified. The original remaining loads balance the normal-pressure couples; no physical failure is inferred. Current priors and unbalanced finite poses supply no physical demand bound; the 56.6-mm motion has no adopted failure threshold. |
| Panels, screws and actual fit | The 66 Hillman policy and current geometry remain fixed. The [insert work evaluation](../wood-joints-mvp/completion-ledger.md#evaluation-of-insert-work-to-date) retains nominally fitting candidates; no complete replacement is qualified. | The [reopened conventional assessment](../wood-joints-mvp/completion-ledger.md#current-panel-hillman-conventional-disposition) retains the failed head/thread references and identifies the required complete path. Resolve flush head, anchorage/combined loading and panel support before selecting a remedy. Actual fit is excluded and observations stay blank. Credit no unsupported panel restraint; retain the analytical no-slip assumption. |

The retained solid-timber cleat route is preserved in the [strength/design-basis review](../wood-joints-mvp/completion-ledger.md#current-cleat-strength-calibration-evidence), [actual group-wrench record](../wood-joints-mvp/completion-ledger.md#current-cleat-centric-group-scope) and [eccentric-dowel assessment](../wood-joints-mvp/completion-ledger.md#current-cleat-dowel-eccentricity). Further resistance searches and rejected tie/force-cycle trials are inactive. Their frozen actions, source data and failed results remain active references for the plywood connection worksheet; nothing is archived or pruned. Preserve both corners, all 100 bolt lines, 66 Hillman axes and the selected-baseline distinction. No native/frame solve or generic contact/fracture campaign is scheduled.

## Engineering reading order

Use the geometry and shop paths above, then the [bounded studies](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/README.md), [resistance followup](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/resistance-followup-v1/README.md), [adjusted-base audit](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/README.md) and [connected-stack followup](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/README.md).
Their older actions, local geometry and trial bearing parameters keep their limits; use the [guarded reproduction entrypoints](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/reproduction-guard-v1/README.md).

## Conditional operations and purchasing

Shop tables apply only to their named revision and explicit overrides. Model
occupancy and CSV lengths are analysis envelopes. Partially threaded bolts
remain the basis; delivered shank and full nut seating require per-stack checks.
No insert pilots, physical testing, cutting or drilling release is supplied here. Amazon angles remain primary; the owner selects [SendCutSend as the planned sourcing fallback](builder-plan.md#sendcutsend-sourcing-fallback), pending its final drawing and joint assessment.

## History and evidence recovery

Use the [history catalog](../history/design-history.md#eoere-development-sequence)
for preceding Eoere, thin-frame and wood-joint options. The
[frozen pre-compaction summary](../history/eoere-development-summary-before-compaction.md)
preserves the `845e2e0c` payload; [browse its original commit](https://github.com/mckayreedmoore/mini-moonboard/blob/845e2e0cf2bf1514398e115c382865579fd77141/docs/wood-joints-mvp/README.md)
for working historical relative links. The ledger and frozen packets stay in place.

<a id="current-working-model"></a>
<a id="preserved-earlier-eoere-a12-packet"></a>
<a id="preserved-thin-b103b104-predecessor"></a>

Earlier [wood-joint records](../history/wood-joint-development-summary-before-navigation-cleanup.md#current-working-model),
[Eoere A12 discussion](../history/eoere-development-summary-before-compaction.md#preserved-earlier-eoere-a12-packet)
and [thin-frame discussion](../history/eoere-development-summary-before-compaction.md#preserved-thin-b103b104-predecessor)
retain their own geometry, loads and unresolved criteria.

Required cached solids, current and historical fields, operators, source banks
and reviews remain **active inputs**, including ignored `fea/generated/`. Use the
[cleanup/recovery record](../repository-cleanup-evaluation-2026-09-28.md) and
[contributor workflow](../../CONTRIBUTING.md) before moving files. Historical
viewers and mesh aliases stay available. The persistent kit restored all 1,219 recorded inputs; no raw inputs are pruned.
Pages publication requires successful CI for the exact master revision; see the [CI repair record](../wood-joints-mvp/completion-ledger.md#ci-repair-and-current-structural-assessment).
