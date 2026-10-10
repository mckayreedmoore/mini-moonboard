# Compact bolted frame development

This is the main entry for `compact-bolted-frame-development`.
The current geometry is **`eoere-raised-kicker-screws-v1`**,
with the optional extra grid **off**: 22 timbers, six panels, 22 angles,
100 bolt stacks and 66 purchased Hillman panel/kicker screws. The retained
evidence folder keeps earlier wood-joint studies at their frozen paths. The selected
[baseline authority](../../current-candidate.json) stays separate.

The [checked revision index](development-revisions.json) binds geometry,
optional preview, applied hardware and response separately. The current geometry
raises two upper outer kicker screws/holes from Z192 to **Z212 mm**, retaining
all 100 bolt axes. The modeled maximum-bore/screw gap is **3.94375 mm**;
post-top axis distance is 26.9 mm and end-distance strength remains unqualified.
The preceding smaller channels and eleven filled principal arc cuts remain.
The viewer applies `eoere-selected-purchase-hardware-v1`: 32 longer bolts and eight spacers, with all axes retained.

## Active builder reading path

| Need | Start here | Boundary |
| --- | --- | --- |
| Current geometry | [Selected-hardware viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-selected-hardware-frame-development&view=rear) · [receipt](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-kicker-clearance-v1.json) | Geometry evidence only; 100 bolts fixed, two screws raised. |
| Current shop records and hardware choice | [Matching shop packet](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/README.md) · [100 selected stacks](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/hardware-selection.csv) | Current screw/channel datums; selected bolt lengths and eight spacers are now applied in the viewer. Actual fit and strength remain open. |
| Preserved fixture concepts | [Builder drilling guide](../wood-joints-mvp/eoere-builder-drilling-guide.md) | Frozen aligned-wire geometry; later v3 moved 22 shafts and ten screws. Actual reach, fixtures and tools remain unresolved. |
| Latest numerical evidence | [Six fresh cases](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/current-cases-v1/result-v1.json) · [parent verification](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/current-cases-v1/parent-verification-v1.json) | Preceding extended-cleat geometry, extra grid off. Passing numerical audits do not transfer to the channel or raised-screw revisions. |
| Component comparisons | [Six-case summary](../../fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/adjusted-base-mechanics-v1/current-component-results-v1/summary.json) | Own-case references retain exceedances; complete-joint resistance remains null. |
| Detailed tasks and holds | [Completion ledger](../wood-joints-mvp/completion-ledger.md#build-package-completion) · [qualification status](../wood-joints-mvp/completion-ledger.md#current-model-completion-scope-and-qualification-status) | Source bindings, reviews and missing inputs; earlier “current” sections keep their historical meaning. |

## Revision map

Geometry, response and shop coverage have different boundaries:

| Role | Exact revision / record | Viewer or scope |
| --- | --- | --- |
| **Main geometry** | `eoere-raised-kicker-screws-v1` · [receipt](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-kicker-clearance-v1.json) | [Extra grid off](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-selected-hardware-frame-development&view=rear); two holes/screws raised, bolts fixed. |
| Optional unofficial preview | Current geometry plus `eoere-expanded-right-column-v1` · [receipt](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-right-column-v1.json) | [Extra grid on](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-selected-hardware-grid-development&view=rear); 264 main positions, with a new column 100 mm right of K. |
| Preserved 252-position preview | `eoere-2026-horizontal-midpoint-grid-v3` | [Earlier extra grid](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-kicker-clearance-2026-development&view=rear); 120 added T-nuts/lights and 119 links. |
| Smaller-channel predecessor | `eoere-uniform-small-service-channels-v1` · [receipt](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-uniform-channels-v1.json) | [Preserved viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-uniform-channels-frame-development&view=rear); preceding kicker positions. |
| Applied hardware geometry | `eoere-selected-purchase-hardware-v1` · [receipt](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-selected-hardware-v1.json) | [Nominal installation followup](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/selected-hardware-v1/README.md); 100 bolt axes retained, 32 shafts extended, eight spacers added. |
| **Current shop plan** | `eoere-raised-kicker-screws-v1` | [Current packet](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/current-model-followup-v1/README.md), composing current channels/screws with unchanged raw cuts, nesting, recesses and receiver axes. The separately bound hardware overlay applies the purchase override. |
| **Latest six-case response** | `eoere-base-side-edge-cleats-v1` · [receipt](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/occupied-extended-cleats-v1.json) | [Preserved viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-extended-cleat-frame-development&view=rear); six own-case admissions and twelve component reports, fixed-rear-leg support scenario. |
| Unadopted lower-corner proposal | `eoere-lower-cleat-z180-proposal-v1` | [Z180 preview](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-lower-cleat-z180-development&view=rear) · [separate shop packet](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/shop-assembly-v1/extended-cleat-followup-v1/z180-proposal-v1/README.md); four stacks lowered 20 mm and eight replacement holes, with its own six-case response. |
| Original Eoere proposal | `eoere-far-pairs-cleat-corners-v1` · [frozen contract](../../eoere-bolted-candidate.json) | [Earlier viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=eoere-bolted-development&view=rear); retained proposal identity. |

## Current disposition

The current shop packet covers 28 profiles, 120 receiver-hole occurrences,
66 screw axes, 340 panel datums, 32 base channel occurrences, 100 selected
hardware sets and 200 access sides. It keeps the 13-stick / 150-board-foot
stock scenario. The combined nominal mass estimate is 219.517834 kg,
including selected hardware increments; actual weight is unmeasured.

Selected Grade 5 full-body partial-thread lengths clear the catalog seating
and two-tip-pitch comparisons. Forty-eight added hardware envelopes clear
nominal parts. The dated fastener basket is $148.51 before angles/tax/shipping.
**Cleat/post holds concern end strength, actual tolerances/contact and
tool qualification.** The modeled screw conflict and nominal stack choice are
resolved. Nominal box-wrench insertion, a 60° handle sweep, counterhold and
removal clear all 200 sides; twelve need raised/reoriented support and up to 93.222 mm below-frame clearance.
The assumed long socket fails at 24 nut sides.
Guide rings and two clamp pads have nominal finished-face support at all
120 receivers. The proposed alignment budget has only 0.011771 mm remaining
at the longest path; actual tooling and observations stay unresolved/blank.
See the [installation study](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/selected-hardware-v1/README.md) and [current followup](../wood-joints-mvp/completion-ledger.md#current-shop-and-hardware-selection).

The preceding extended-cleat numerical packet retains six genuine own-case
admissions under the original loads, 32 compression-only floor points and two
rear-leg XY restraints under the unverified no-slip assumption. Its largest
full-gradient residual is **6.128662e-6 N**, within the unchanged 1e-5-N gate.
Reference exceedances remain for generic screw heads, panel bending/rolling
shear and the t6/Ri6 heel scenario. The owner nominal t6.35/Ri6.35 heel reference
has a small margin; actual formed-product resistance remains unknown.
Physical applicability, finished sections, restraint, demand bounds and all
complete-joint resistances remain open. See the
[detailed numerical record](../wood-joints-mvp/completion-ledger.md#current-extended-cleat-numerical-completion)
for comparisons, sensitivity exceedances and the source-captured panel-RHS limit.

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

1. Resolve current screw/end and complete-joint resistance, net sections,
   restraint and physical applicability; bind any new response to current inputs.
2. Check delivered hardware against the selected rows, including shank/runout,
   full nut seating, spacer/washer contact and threaded wood bearing.
3. Apply the documented generic tool requirements to actual equipment,
   fixtures and placement tolerances; the completed nominal paths do not inspect actual tools.
4. Retain the 66-screw count and purchase policy. Other panel/screw strength
   remedies remain stopped; the extra grid and Z180 layout remain unadopted.

## Engineering reading order

Use the geometry and shop paths above, then the
[bounded studies](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/README.md),
[resistance followup](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/resistance-followup-v1/README.md),
[adjusted-base audit](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/README.md)
and [connected-stack followup](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/README.md).
Their older actions, local geometry and trial bearing parameters keep their limits.
Use the [guarded reproduction entrypoints](../wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/revised-base-audit-v1/reproduction-guard-v1/README.md).

## Conditional operations and purchasing

Shop tables apply only to their named revision and explicit overrides. Model
occupancy and CSV lengths are analysis envelopes. Partially threaded bolts
remain the basis; delivered shank and full nut seating require per-stack checks.
No insert pilots, physical testing, cutting or drilling release is supplied here.

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

Required cached solids, fields, operators, source banks and reviews remain
**active inputs**, including ignored `fea/generated/`. The 1,446 hardware-geometry and 1,535 access-study pins remain active. Use the
[cleanup/recovery record](../repository-cleanup-evaluation-2026-09-28.md) and
[contributor workflow](../../CONTRIBUTING.md) before moving files. Historical
viewers and mesh aliases stay available. The persistent kit restored all 1,219 recorded inputs; no raw inputs are pruned.
Pages remains held by the [diagnosed CI failures](../repository-cleanup-evaluation-2026-09-28.md#observed-ci-publication-hold).
