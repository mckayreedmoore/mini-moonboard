# Wood-joint development

**Current summary: October 2, 2026.** Candidate `compact-floor-flush-wood-joints-development`,
reviewed revision `led-clearance-2x6-runner-seated-blocks-v1`, has its own
[contract](../../wood-joints-candidate.json). The selected screw-and-bracket
[baseline](../../current-candidate.json) and its passes remain separate.

Maintained sources and readable summaries are published. Generated arrays, CAD copies and
raw receipts remain local and ignored; complete replay needs the preserved workspace inputs.

The [reviewed WJ24 viewer](https://mckayreedmoore.github.io/mini-moonboard/wood-joints-wj24-viewer.html)
and [scene](../../site/owner-wood-joints-wj24-scene.json) preserve 24 blocks, 92 candidate bolt axes,
twelve starting frame-bolt arrangements and 66 Hillman panel/kicker axes: 58 unchanged and eight
recorded moves. Report required changes before altering that geometry.

**The conditional engineering MVP is incomplete: all 47 criteria are pending and all physical
release flags are false.** Three authenticated rear diagnostic exports are usable within their
recorded scope: **A1-rear, A12-rear and K12-rear**. **A12-forward, A12-left and K12-right remain
unresolved.** The separate A12 reduced-operator comparison retains **27 force-interval failures
and STOP**; later two-body recovery did not clear the discrepancy or supply accepted forces.
No complete joint, physical inspection, floor qualification or fabrication, drilling or climbing
release is established.

## Current working model

The owner selected a simple MVP model and stopped recurring agent reviews. The parent has
integrated an [isolated top-corner correction](hypotheses/mvp-resume-2026-10-01/top-corner-correction.md)
with bolt clearance at both top/bottom outer corners and both left outer service cleats.
All twelve zero-gap/modeled-gap states satisfy the declared mechanics laws across six cases.
These working calculations retain conditional Hillman stiffness and no-slip support; they do
not replace the native authentication statuses above or alter reviewed geometry.

| Current six-case result | Conditional working result |
| --- | --- |
| Top outer corners | Grade 5 component ratios 0.7077 left / 0.8037 right; concurrent steel scenarios 0.7164 / 0.8150 |
| Bottom outer corners | Left component ratio 0.2920, concurrent steel scenario 0.2942; right below 0.00570 |
| Bottom-left movement | 2.4501 mm / 0.2522°; motion compatibility remains open |
| Left lower outer service | 0.7561 mm / 0.1564°, 4.968 N bolt shear / 13.942 N separate tie |
| Member arithmetic | 264 balances, 54,888 signed cut traces; applicable normal/shear references 0.5415 / 0.3736 |
| End-grain lateral route | 12 axes / 72 states; NDS perpendicular bearing and Ceg=0.67, peak conditional 92 ksi ratio 0.2577 before remaining adjustments |
| Six block/header joints | Adjusted component sensitivity 0.2599, washer wood bearing 0.3984; 36 interfaces and 42 body balances close |
| Continuous knee bolts | 24 asymmetric bolt cases; declared conservative sum 0.9040 at 92 ksi / 1.2898 at 45 ksi, with endpoint embedding and full joint transfer unvalidated |
| Remaining eligible individual bolts | No ratio above one even at 45 ksi; retained upper leg bolt governs at 0.7555 |

Different peaks are not simultaneous. The [bottom-corner calculation](hypotheses/mvp-resume-2026-10-01/bottom-corner-checks.md),
[top-corner worksheet](hypotheses/mvp-resume-2026-10-01/top-corner-component-checks.md),
[member screen](hypotheses/mvp-resume-2026-10-01/member-checks.md) and
[end-grain applicability](hypotheses/mvp-resume-2026-10-01/end-grain-route.md) and
[three-member screen](hypotheses/mvp-resume-2026-10-01/three-member-checks.md) and
[header worksheet](hypotheses/mvp-resume-2026-10-01/header-joint-checks.md) bind current
same-state inputs. The existing service worker's
[upper/lower assessments and earlier Hillman evidence](hypotheses/mvp-resume-2026-10-01/service-and-hillman-integration.md)
remain preserved and ingested without regenerating their historical force records.

The original [zero-withdrawal calculation](hypotheses/mvp-resume-2026-10-01/no-withdrawal-frame-checks.md)
stops in all six cases: upper panels need outward restraint. The
[panel attachment worksheet](hypotheses/mvp-resume-2026-10-01/panel-attachment/README.md)
now finds a concrete reference deficit: 1812 N modeled-gap withdrawal exceeds the declared
277–629 N unadjusted head references and 711–1073 N generic timber withdrawal references.
Completed softer withdrawal-law scenarios reduce the peak to 1240 or 916 N; both still exceed
those head references and increase opening. These are conditional reference comparisons,
not measured Hillman resistance or a physical failure claim. No changed screw law is selected.

The parent has also completed saved bore clearance at all 88 two-receiver candidate bolts.
All twelve zero/nominal states satisfy equilibrium, spring and floor laws; the six nominal
states have finite fixed-force seating bounds. Their rank296/297 modes are reported as
[bounded nonunique seating](hypotheses/mvp-resume-2026-10-01/bounded-clearance.md), with strict
rank300/stability flags retained false. Four continuous bolts still need common-bolt clearance
treatment. This variant's peak panel withdrawal is 1837 N, so the head-reference deficit
persists. Fresh same-state component replays now give top-corner ratios
0.7268/0.8138 (concurrent steel 0.7356/0.8253), bottom-left 0.2819
(concurrent steel 0.2839), lower-left service 0.00704, end-grain 0.04648,
continuous-knee conditional sum 0.9192 and remaining eligible individual bolts
0.9521. The 44-member elementary normal/shear references are 0.5746/0.3700;
header and torsion/restraint updates remain in progress. These saved-force
comparisons preserve nonunique seating and all complete-joint flags false.
The preceding table remains the preserved six-joint reference; earlier terminal
packets and exact producer snapshots are preserved.

The [assembly package](hypotheses/mvp-resume-2026-10-01/assembly-package/README.md) reconciles
50 transport bodies, 104 bolts/nuts, 208 washers and 66 separate Hillman screws. Larger stock
scenarios place all 44 timber blanks; the 8-foot-only scenario misses five. The recorded priced
hardware terms total $158.46 plus explicit missing terms, rather than a complete purchase total.
The [hardware engagement worksheet](hypotheses/mvp-resume-2026-10-01/assembly-package/hardware-engagement.md)
now supplies fourteen family specifications for all 104 stacks, including
body/thread and nut coverage. The [conditional shop guide](hypotheses/mvp-resume-2026-10-01/assembly-package/shop-guide.md)
joins those parts, stock, assembly/removal and transport instructions; Actual/Disposition
cells remain blank. Supplier profile guarantees, complete order cost, actual tools
and harness staging remain open. Proposed longer shaft occupancy is the next finite fit check.
The parent retains integrated mechanics, shared staging and commits; pane workers own panel
references and hardware fit, and bounded helpers handle member restraint and finite free play.
No recurring review loop is used.

The [central bearing scenario](hypotheses/mvp-resume-2026-10-01/partial-seat-bearing.md)
provides supported geometry at the center-principal partial washer seat. Its current all-two-receiver
wood-pressure ratio is 0.1425; the preserved six-joint value is 0.5147.
Actual washer/nut transfer remains unqualified. The
[lower-left service comparison](hypotheses/mvp-resume-2026-10-01/service-joint-current-checks.md)
now supplies all 24 current signed bolt states and a peak conditional Grade 5 lateral ratio
0.00704 for the all-two-receiver replay (preserved six-joint value0.00568);
zero-lateral directions remain null and complete-joint acceptance stays false.
Complete wood/group/washer resistance, finished member sections, restraint and operation checks
remain unfinished. Detailed washer meshes, stiffness-output builds and provenance tooling remain
parked method work. No stronger bottom hardware or stock change is selected by the current screen.

## Useful results

- The [October 1 evidence summary](parallel-owner-handoff-2026-10-01.md) records source-action work;
  local center-boundary and retained-bolt validations preserve signed three-case actions and modeled
  equilibrium. Direct-seat and cleat routes remain distinct; physical sharing, stiffness and resistance are unqualified.
- [Finished geometry](hypotheses/current-finished-feature-register-2026-10-01/README.md),
  [stock scenarios](hypotheses/current-stock-envelope-reconciliation-2026-10-01/README.md) supply 44-piece
  geometry bindings. Local retained-edge samples do not establish full-depth minima, observed grade or approved cuts.
- Local annulus/contact fixtures qualify their frozen software/output scopes. The
  [washer-method note](hypotheses/corner-washer-method-investigation-2026-10-01/source-note.md) explains the
  remaining transfer gap; candidate pressure, washer metal, wood resistance and partial-seat capacity are unqualified.

## Remaining work and next actions

Complete all 24 replacement duties and affected-member checks: coupled contact, clearance and
slip/rotation; simultaneous bolt tension/shear/bending; head/nut/washer transfer; finished sections,
bearing, splitting and group interaction. Resolve the partial washer seat at `center_principal_right_2`
and the BG045 conditional edge exception. Hardware profile/functional fit, materials, installed tools,
reversible removal, transport, a coherent conditional shop package and integrated validation
remain open. [Stock-price observations](hypotheses/current-stock-package-cost-2026-10-01/README.md)
still lack a complete compatible material/quantity/cost reconciliation.

1. Complete the current joint calculations using the six-joint source. Retain both bottom
   outer cleats from their favorable conditional references; finish their movement/operation
   and complete wood/washer transfer checks. Use the supported NDS end-grain route before
   considering its unapplied stock/grain alternative; finish continuous three-receiver bolts.
2. Resolve the upper-panel Hillman resistance/load-sharing task with purchased screw policy
   unchanged. Apply any changed laws in the integrated frame with floor branches free to change.
3. Finish conditional assembly/removal, member transport, stock/hardware quantities and cost,
   then reconcile the shop package to the working model. Preserve historical native failures,
   parked method work and all physical-release flags; add no recurring review rounds.

## Detailed coordination and evidence

Local `NEXT-AGENT-HANDOFF-2026-10-01.md` gives exact restart points;
`hypotheses/mvp-integration-2026-10-01/` holds the current integration, exact-47 audit and validation receipts.
The published [endpoint](luna-max-completion-handoff.md#1-endpoint-and-authority) and [criteria register](current-criteria-coverage.md)
retain full requirements. Long [coordinator](hypotheses/mvp-acceleration-2026-09-28/LUNA-MAX-COORDINATOR-CURRENT-CHECKPOINT-2026-09-29.md)
and [four-gate](hypotheses/mvp-acceleration-2026-09-28/four-gate-closure-matrix-2026-09-29.md) chronologies preserve earlier snapshots; later dispositions govern continuation.
The parent owns readiness, frozen inputs, serialized heavy runs and final validation under [AGENTS.md](../../AGENTS.md).
Reuse evidence within its limits; numerical stops, missing evidence and strength failures remain distinct.
Preserve other owners' work, source snapshots and [historical models](../history/design-history.md); check references before pruning outputs.
