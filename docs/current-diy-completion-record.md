# Current DIY completion record

The selected candidate is **`compact-spliced-knee-development`**, September 13,
2026. Its [study](compact-splice-study.md) and [build package](compact-spliced-build-package.md)
are the current authorities. The agreed endpoint is a documented
**engineer-unreviewed DIY design**, not professional certification, physical
inspection or an unconditional climber weight rating.

## Selected detail and scope

The frame uses solid 4×6 legs and flush outer rims, a compact 2×6 header/posts,
and two centered ½-inch upper bolts per leg at 56 mm pitch. Four independent
unnotched diagonal 2×6 pieces form the knees. Each side has four ⅜-inch splice
bolts and two ⅜-inch bolts at each endpoint, giving 20 complete bolt stacks.
The paired pieces have an explicit lap connection; composite action is not
assumed. Earlier notched braces and failed upper-joint layouts are historical.

Retain the 277 mm main-face datum (150 mm exposed kicker plus a 127 mm pad
allowance), accepted panel/T-nut construction and 66 panel/kicker screws.
Timber supports bear on the floor under the stated no-slip assumption; padding
is not a structural support. Specified lumber is dry, unincised Douglas
Fir–Larch No. 2. Catalog hardware, dimensional bounds and conditional material
properties are documented in the study and matching hardware assessments.

The selected load cases include the 250 lb design inquiry with stated downward
multipliers and 300 N horizontal scenarios. The study defines their exact
positions, directions and equipment assumptions. These finite scenarios are
not a measured impact spectrum or every possible climbing action.

## Finite completion gates

| Deliverable | Evidence and disposition |
| --- | --- |
| Current assembled response | Final case ledger and numerical acceptance in the [study](compact-splice-study.md). All six current cases converged and passed all 21 listed conditional criteria; the highest adopted bolt ratio is 0.674. |
| Connections, members and hardware | Current forces, finite-contact assumptions, spacing, local sections and catalog-dimension resistance comparisons are reported together in the study and pass their listed gates. No acceptance transfers from predecessor models. |
| Matching instructions | The [build package](compact-spliced-build-package.md) identifies this exact geometry, cuts, fresh drilling, complete hardware and assembly sequence. |
| Final consistency | The clean CAD rebuild matches all 769 viewer/STEP artifacts; all 17 construction artifacts and source hashes match. Default tests: 441 passed, 15 historical tests deselected; lint and CadQuery smoke check passed. The functional browser check also passes: 767 meshes, all 20 complete bolt stacks, current selection, documents and floor datums. The rear view and representative leg/knee drilling sheets were visually inspected. |

The owner does not require external engineer review, floor-friction testing,
a general panel qualification campaign or a destructive failure-weight search.
Those are not added completion gates. Explicit analytical/material/installation
assumptions remain limitations of the DIY package; owner acceptance does not
turn a failed calculation into a passing one.

## Historical evidence

The [original response](current-frame-response.md), [compact three-bolt study](compact-thick-study.md),
[solid-4×6 pivot study](thick-leg-pivot-study.md) and intervening knee trials
remain preserved. Their reported shortcomings explain the revisions; they are
not the current joint's result. Do not repeat an earlier three-bolt failure as
the current authority, and do not transfer a historical pivot pass.

The finite task ends when this selected detail has its supported recorded
result, matching instructions and explicit scope limits. Speculative further
improvements are not unfinished requirements.

## Completion

Completed September 13, 2026. The selected detail meets the finite analytical
gates and has matching CAD, viewer, dimensional sheets, stock and hardware
schedules, assembly instructions and CI freshness checks. No design alternative
or additional planning task remains open within the agreed scope. The documented
material, hardware-fit and installation conditions still apply to fabrication.

Browser validation used `CAD_VIEWER_SCREENSHOTS=0` for its final functional
run after screenshot capture stalled during viewport changes in the local
headless renderer. The current rear image was inspected separately; leg and
knee SVG sheets were rendered independently for visual inspection. No browser
JavaScript errors occurred during the passing functional run.

## End-finish and bolt-installation update

The current viewer and drawings use `compact_spliced_trimmed`, wrapping the
outward-bolt installation and the frozen `compact_spliced_knee_frame` analysis
definition. Sixteen inward-facing stacks were reversed; four already-outward
endpoint stacks were retained. All 40 actual receivers/washer seats pass after
the end cuts. Knee tips are flush; leg tops retain 18 mm projection.

[Current trim checks](compact-spliced-construction/end-trim-check.json) reapply
the six saved force cases to current end geometry and hardware. The highest
bolt ratio remains 0.674; updated local parallel ratio is 0.276. Cuts remove
1.410 kg of modeled wood and remain beyond every bolt bore's full-section span.
Original native stiffness and gravity placement are retained as an explicit
small exterior-tail approximation. These are not six newly solved trimmed
assemblies. See the matching build package for tighter rim-end bolt shank
acceptance, cutting datums and the retained geometric tolerances.

Validation for this update: 445 default tests passed, 15 historical tests
deselected; lint and clean current CAD regeneration passed. Functional browser
checks confirmed all 767 meshes and every outward-facing head/nut pair. Updated
leg and knee drawings were independently rendered and visually inspected.

## Lower kicker row update

The current export adapter is `compact_spliced_kicker`. Four lower kicker screws
move from Z112 to Z60 mm; all other axes, stock sizes and hardware counts remain
fixed. Fresh-stock drilling and schedules reflect the relocation. Local receiver
and interference checks apply; the accepted panel basis is retained. The frozen
six native cases still contain the preceding screw locations. This update does
not claim a new assembled response or new panel qualification. See the
[kicker placement review](kicker-screw-placement-review.md).

Validation: 448 default tests passed, 15 historical checks deselected; Ruff and
the clean current export rebuild passed. Browser checks loaded all 767 parts
and confirmed the four lower screw meshes at Z60. The construction packet and
current mass record were regenerated; historical model outputs remain unchanged.
