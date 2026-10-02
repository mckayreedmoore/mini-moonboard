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
with modeled radial clearance on all 88 independent two-receiver candidate bolts.
The current force reference is `two-receiver-frame-attempt03/`: all twelve
zero/nominal states meet equilibrium, connector and floor laws across six cases.
Each nominal state has finite fixed-force seating bounds, with rank296/297;
unique pose and strict tangent stability are not established. Four continuous
candidate bolts and twelve retained bolts remain at zero modeled clearance.
These working calculations retain conditional Hillman stiffness and no-slip support; they do
not replace the native authentication statuses above or alter reviewed geometry.

The [retained bolt-pair calculation](hypotheses/mvp-resume-2026-10-01/retained-group-checks.md)
adds 36 signed pair records and four declared row-factor area scenarios. Its governing
front-left individual ratio becomes 0.9613 under the smallest of those scenarios, compared
with the 0.9521 unadjusted reference below. The actual group carries oblique forces and
a couple, so this is a sensitivity rather than an adopted complete-group factor.

The [retained-washer comparison](hypotheses/mvp-resume-2026-10-01/retained-washer-checks.md)
binds the separate 3/8-inch and 1/2-inch catalog envelopes and saved bores
across 144 seat states. The subsequent
[current saved-STEP support check](hypotheses/mvp-resume-2026-10-01/retained-washer-support.md)
confirms all 24 nominal concentric annuli across 72 shallow probes, using the
corrected side-member copies. Uniform-pressure wood indices remain
0.2083/0.2878; loaded shift/tilt and washer metal acceptance remain open.

| Current six-case result | Conditional working result |
| --- | --- |
| Top outer corners | Conditional 92 ksi component ratios 0.7268 left / 0.8138 right; concurrent steel scenarios 0.7356 / 0.8253 |
| Bottom outer corners | Left component ratio 0.2819, concurrent steel scenario 0.2839; right below 0.00569 |
| Left lower outer service | Individual 92 ksi reference ratio 0.00704; governing same-state shear/tie 6.677 / 7.286 N |
| Member arithmetic | 264 balances, 54,888 signed cut traces; elementary normal/shear references 0.5746 / 0.3700 |
| Member torsion/stability | Braced normal interaction 0.6144; top-rail face shear/torsion proxy 1.0392 exceeds declared 180 psi reference |
| End-grain lateral route | 12 axes / 72 states; NDS perpendicular bearing and Ceg=0.67, individual 92 ksi ratio 0.04648 before group/detailing adjustments |
| Six block/header joints | Adjusted component sensitivity 0.04692, washer wood bearing 0.2627; 36 interfaces and 42 body balances close |
| Continuous knee bolts | 24 asymmetric cases; endpoint sum 0.9192 at 92 ksi / 1.3125 at 45 ksi; recovered nominal bearing/steel indices 0.3596 / 0.5926, with contact/clearance and full joint transfer open |
| Remaining eligible individual bolts | No eligible ratio above one at 45/92/106 ksi; retained front-left second bolt governs at 0.9521 |

Different peaks are not simultaneous. The [bottom-corner calculation](hypotheses/mvp-resume-2026-10-01/bottom-corner-checks.md),
[top-corner worksheet](hypotheses/mvp-resume-2026-10-01/top-corner-component-checks.md),
[member screen](hypotheses/mvp-resume-2026-10-01/member-checks.md),
[torsion/stability calculation](hypotheses/mvp-resume-2026-10-01/member-stability.md) and
[end-grain applicability](hypotheses/mvp-resume-2026-10-01/end-grain-route.md) and
[three-member screen](hypotheses/mvp-resume-2026-10-01/three-member-checks.md) and
[header worksheet](hypotheses/mvp-resume-2026-10-01/header-joint-checks.md) bind current
same-state inputs. The existing service worker's
[upper/lower assessments and earlier Hillman evidence](hypotheses/mvp-resume-2026-10-01/service-and-hillman-integration.md)
remain preserved and ingested without regenerating their historical force records.

The [continuous-bolt bearing construction](hypotheses/mvp-resume-2026-10-01/knee-bearing-checks.md)
recovers shear and bending through all three receivers while preserving 72 saved
receiver wrenches. Its 96 normalized endpoint fields fit the declared nominal
bearing/bending bounds; actual bore-wall contact compatibility and common-bolt
clearance remain open. This does not supply an adjusted asymmetric joint capacity.

The [shared-shaft placement check](hypotheses/mvp-resume-2026-10-01/knee-bore-fit.md)
finds 96 straight-shaft witnesses through the three saved bores. Total-motion
fits retain at least 0.435309 mm conservative radial margin; complete bore
deformation and loaded contact are not reconstructed. This geometry result
does not require bore enlargement or change the frame's zero-clearance laws.

The original [zero-withdrawal calculation](hypotheses/mvp-resume-2026-10-01/no-withdrawal-frame-checks.md)
stops in all six cases: upper panels need outward restraint. The
[panel attachment worksheet](hypotheses/mvp-resume-2026-10-01/panel-attachment/README.md)
now finds a concrete reference deficit: 1837 N current modeled-gap withdrawal exceeds the declared
277–629 N unadjusted head references and 711–1073 N generic timber withdrawal references.
Preserved six-joint softer withdrawal-law scenarios reduce the peak to 1240 or 916 N; both still exceed
those head references and increase opening. A separate
[100 N/mm replay on the current all-88-clearance frame](hypotheses/mvp-resume-2026-10-01/panel-attachment/README.md#all-two-receiver-100-nmm-sensitivity-attempt09)
gives 907 N modeled-gap withdrawal and 9.066 mm representative opening;
its favorable generic combined index reaches 3.0068. That hypothesis still
exceeds every declared head reference. These are conditional reference comparisons,
not measured Hillman resistance or a physical failure claim. No changed screw law is selected.

The parent has completed same-state component replays at all 88 two-receiver candidate bolts.
Their rank296/297 nominal modes are reported as
[bounded nonunique seating](hypotheses/mvp-resume-2026-10-01/bounded-clearance.md), with strict
rank300/stability flags retained false. Four continuous bolts still need common-bolt clearance
treatment. This variant's peak panel withdrawal is 1837 N, so the head-reference deficit
persists. The specific top-rail reference exceedance also remains unresolved;
its governing cut lies 52.189 mm beyond a cleat contact footprint in a short
transfer run, so the developed pointwise stress-field assumption is unproved.
No physical wood failure, material factor or geometry change is adopted. The preceding table now uses
one coherent current force source. Earlier six-joint results, terminal packets
and exact producer snapshots remain preserved. All complete-joint flags stay false.

The [assembly package](hypotheses/mvp-resume-2026-10-01/assembly-package/README.md) reconciles
50 transport bodies, 104 bolts/nuts, 208 washers and 66 separate Hillman screws. Larger stock
scenarios place all 44 timber blanks; the 8-foot-only scenario misses five. The recorded priced
hardware terms total $158.46 plus explicit missing terms, rather than a complete purchase total.
The [dated catalog update](hypotheses/mvp-resume-2026-10-01/assembly-package/catalog-costs.md)
adds $31.12 of retained hardware at displayed piece prices. Combining that increment once
with the historical partial sum gives $189.58 before freight/tax, still incomplete.
The [hardware engagement worksheet](hypotheses/mvp-resume-2026-10-01/assembly-package/hardware-engagement.md)
now supplies fourteen family specifications for all 104 stacks, including
body/thread and nut coverage. The [conditional shop guide](hypotheses/mvp-resume-2026-10-01/assembly-package/shop-guide.md)
joins those parts, stock, assembly/removal and transport instructions; Actual/Disposition
cells remain blank. The [longer-bolt occupancy screen](hypotheses/mvp-resume-2026-10-01/assembly-package/hardware-length-fit.md)
finds no clash in twelve proposed added tips and headward-travel increments: 48,190 source pairs
separate by conservative bounds, and two saved STEP pairs have zero intersection and
18.158 mm minimum distance. Full nut/thread/tool operations are outside that finite screen.
Supplier profile guarantees, complete order cost, actual tools and harness staging remain open.
The parent retains integrated mechanics, shared staging and commits; the panel, member and
clearance helpers have delivered their finite results, and the fit worker owns its leaf packet.
No recurring review loop is used.

The [central bearing scenario](hypotheses/mvp-resume-2026-10-01/partial-seat-bearing.md)
provides supported geometry at the center-principal partial washer seat. Its current all-two-receiver
wood-bore-only pressure ratio is 0.1425. Including the catalog washer's maximum
8.3058 mm opening raises the conditional uniform-pressure ratio to 0.2146;
the preserved six-joint wood-bore-only value is 0.5147.
Actual washer/nut transfer remains unqualified. The
[lower-left service comparison](hypotheses/mvp-resume-2026-10-01/service-joint-current-checks.md)
now supplies all 24 current signed bolt states and a peak conditional Grade 5 lateral ratio
0.00704 for the all-two-receiver replay (preserved six-joint value 0.00568);
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

Complete the remaining requirements across all 24 replacement duties and affected members:
common-bolt clearance at the four continuous knee bolts, compatible slip/rotation, full
head/nut/washer transfer, local splitting and applicable group interaction. The partial seat
at `center_principal_right_2` has a supported central-ring pressure comparison; actual
nut/washer transfer remains open. The
[current header-action replay](hypotheses/mvp-resume-2026-10-01/header-joint-checks.md#current-bounded-replay--attempt02final)
has no first-ray normal distance below 4D and no adopted actual detailing failure. The old
BG045 edge exception remains historical evidence; current complete placement and local
splitting are still unproved. It does not presently justify moving those axes.

The [conditional assembly package](hypotheses/mvp-resume-2026-10-01/assembly-package/README.md)
already reconciles 50 transport bodies, 44 timber blanks, 104 bolt/nut stacks, 208 washers
and 66 separate Hillman screws, with stock and assembly/removal scenarios. Full tool/harness
operations, compatible delivered axial profiles and the complete purchase cost remain
unresolved. Priced hardware terms total $189.58 when the $31.12 retained increment is
counted once; wood and other explicitly missing terms remain separate. The earlier
[stock-price observations](hypotheses/current-stock-package-cost-2026-10-01/README.md) retain
their source scope and do not replace this current reconciliation.

1. Resolve the upper-panel attachment reference deficits. The owner constraint decision for
   the next proposal remains pending: an edge restraint occupying a narrow panel margin, or
   permission to revise the panel-fastener specification. Neither change is selected. Retain
   the purchased Hillman policy and reviewed climbing face in the current model. Evaluate a
   proposed correction in the integrated frame, including changed floor-contact branches.
2. Recalculate the top rail with the corrected panel load path. Retain the current 1.0392
   face shear/torsion exception and its short-transfer applicability limit until that result
   is resolved. Do not increase a material factor or infer a physical failure from the proxy.
3. Use the completed twelve-bolt added-occupancy screen when reconciling the conditional shop
   package; its clear additions do not select the proposed lengths or prove full operations.
   Preserve the four captured-nut
   paths and retained leg-bolt harness dependency. Hardware profiles, actual operation fit and
   the complete compatible purchase total remain explicit conditions.

Use the current all-two-receiver force source for subsequent component calculations. Earlier
six-joint sources, native failures and parked method work remain preserved evidence. Complete
joint qualification and all physical-release flags stay unchanged; no recurring review round
is scheduled.

## Detailed coordination and evidence

Local `NEXT-AGENT-HANDOFF-2026-10-01.md` gives exact restart points;
`hypotheses/mvp-integration-2026-10-01/` holds the current integration, exact-47 audit and validation receipts.
The published [endpoint](luna-max-completion-handoff.md#1-endpoint-and-authority) and [criteria register](current-criteria-coverage.md)
retain full requirements. Long [coordinator](hypotheses/mvp-acceleration-2026-09-28/LUNA-MAX-COORDINATOR-CURRENT-CHECKPOINT-2026-09-29.md)
and [four-gate](hypotheses/mvp-acceleration-2026-09-28/four-gate-closure-matrix-2026-09-29.md) chronologies preserve earlier snapshots; later dispositions govern continuation.
The parent owns readiness, frozen inputs, serialized heavy runs and final validation under [AGENTS.md](../../AGENTS.md).
Reuse evidence within its limits; numerical stops, missing evidence and strength failures remain distinct.
Preserve other owners' work, source snapshots and [historical models](../history/design-history.md); check references before pruning outputs.
