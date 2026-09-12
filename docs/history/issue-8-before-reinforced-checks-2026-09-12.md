# Historical issue #8 handoff, preserved 2026-09-12

This is the issue text before the assembled reinforced-frame checks. It contains
superseded candidates and unresolved reference questions that have since been
answered. Use [the current release decision](../reinforced-release-checks.md)
for present status.

## Context

Resume the current **round-structural-development** candidate after an account/session handoff. Latest pushed calculation commit: `f2af79f9564fc9897bb33763d900d8fe494d2028`; geometry/export revision: `3ddbce505586534da38556c66a70fba476bdb012`. Working tree was clean. **Not released for construction or climbing.**

Related historical tracking: #2, #4, #5, #6, #7. Those issues describe an older insert candidate; do not transfer its qualification or restart insert development for this build. This issue tracks the remaining current-candidate release work, not speculative improvements.

Owner wants an efficient finish, has limited Codex budget, and may continue from another account. Estimated next agent calculation/software-check pass: roughly 2–4 hours, highly uncertain; this is not a build-release deadline. Redesign or manufacturer/designer input can extend elapsed time.

## Current decisions and completed work

- 56 SPAX XFT08P-2000 #8 × 2-inch panel/kicker screws; 24 ML24Z angles with 144 specified SDS25112 screws; eight complete 3/8 × 3.75-inch leg bolt stacks.
- 32 nominal 2x6 LED passages enlarged to 1.5 inches and centered at local N=69.85 mm. Nominal front/rear wood ligaments are each 50.8 mm, with zero tolerance margin against a 2-inch edge-clearance basis.
- Preserve symmetry and current screw axes: service rows S=1134.2/1278.25 mm, interior |X|=435.075/835.075 mm, kicker rows 60/140 mm; fixed upper center #4 remains fixed.
- Current source-authenticated geometry/product audit passes: all 200 screw tips contained, all 56 future insert reserves clear, no tested hardware/electrical collisions. Minimum nominal tip margins: SPAX107.156 mm, SDS2.555 mm. All131 cable paths fit nominal304.8 mm spacing, minimum modeled margin23.206 mm.
- CAD, viewer, cutlist, connection schedule, 48-page drilling PDF and tool/assembly instructions are published. These are draft construction documents, not strength approval.
- Retain owned Roseburg AC exterior PS1 23/32-category fir plywood, Lowe's item12235/model119055. Model thickness18.25625 mm. Proposed lumber specification is dry DF-L No2 or better; actual stock must match.
- Structural screws now; future inserts reserve space only. No insert pilots or insert purchases. No physical floor measurement/testing. Retain explicit analytical support/stability assumptions; no universal floor rating.
- Preserve unrelated contributors' work. Follow AGENTS.md, including commit/push hours and real author/committer timestamp checks.

## Start here

1. [Current analysis and release checklist](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/round-structural-analysis.md)
2. [Panel-fastener review](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/round-structural-fastener-review.md)
3. [Base-connection review and unsent manufacturer question](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/round-structural-base-review.md)
4. [Timber/leg review](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/round-structural-timber-review.md)
5. [Bolted-gusset alternative feasibility](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/round-base-gusset-feasibility.md)
6. [Build plan and tools](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/round-structural-build-plan.md) / [drilling PDF](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/round-structural-drilling/drilling.pdf)

## Remaining acceptance criteria

- [ ] Establish defensible current load demands and force distribution, including contact, eccentricity, bracing/support assumptions and governing face/kicker locations. Prefer conservative conventional calculations where sufficient. Do not automatically launch a broad FEA sweep.
- [ ] Check all panel/kicker attachments for withdrawal, lateral load, head pull-through and applicable combined-action/adjustment rules. SPAX TER2010-02 provides unadjusted DF-L withdrawal133lbf/in; current1.24-inch embedded thread gives733.601N. Head reference943.023N requires the applicable23/32 plywood SG>=0.50 condition. The SPF lateral table is not automatically a DF-L assignment. Matching actual panel properties remains necessary.
- [ ] Check current timber members, enlarged passages, beam/column stability, bearing and concentrated connection zones with applicable material values and dimensional tolerances. Centered-bore geometry alone is insufficient.
- [ ] Resolve base and leg connections with current simultaneous demands: applicable ML24Z installation/rating or a specifically calculated replacement, including uplift, moments, steel/wood/fastener modes, bearing, washers, splitting and group effects. The ML bearing table has no F2 allowable; the separate end-mount450lbf value cannot simply transfer. A34 is not a verified drop-in replacement. Historical gusset upper bolt leaves only10.57mm rim-edge distance; do not restore it unchanged.
- [ ] Confirm actual received stock/hardware and intact harness fit/feed. Update machining/installation details for any necessary changes. No physical floor testing added.
- [ ] Complete applicable validation for the release commit, regenerate source-matched artifacts if producers change, and verify deployment. Publish a final requirement-by-requirement release decision. Close this issue as completed only when these requirements are satisfied; do not equate software/geometry passes with structural approval.

## Analysis implementation caveats

`fea/round_structural_frame.py` is a new current-screw diagnostic runner. Five focused adapter/provenance tests passed, but **full mesh preparation and native solves remain unrun**. Its inherited uniform rear-prism surrogate keeps only50.8mm depth behind centered holes, discarding the intact front ligament. This is artificial stiffness, not a conservative response bound; do not use an arbitrary-stiffness run as qualification.

`fea/round_member_connection_assessment.py --structural-screws --native-run ... --output ...` supports authenticated current-run assessment. Historical insert/ordinary-screw demands do not qualify this revision. `fea/shell_surface_recovery.py` now accounts for binary32 conversion plus decimal output rounding; historical reports retain older recovery metadata and need appropriate reprocessing/authentication before comparison with revised code.

## Progress after handoff: conditional screw calculation

Commit `df6d1e5` adds [a reproducible lateral and wood-interaction calculation](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/round-structural-screw-calculation.md), its [calculator](https://github.com/mckayreedmoore/mini-moonboard/blob/master/fea/round_structural_screw_reference.py), and [source-bound result](https://github.com/mckayreedmoore/mini-moonboard/blob/master/fea/results/round-structural-screw-reference-v1.json).

- Conditional single-screw lateral reference: **52.983 lbf / 235.680 N**, mode IIIs governs. Uses DF-L bearing and the published other-grade plywood default, root diameter, reduced bearing lengths, and no fastener-count multiplier.
- Withdrawal reference remains **733.601 N**. The **943.023 N** head reference is still conditional on the applicable plywood G>=0.50 basis; the lateral G=0.42 default does not establish that head condition.
- NDS 2018 wood-screw combined-load equation implemented with an explicitly supplied adjusted head reference. Actual current loads, applicable adjustments and combined steel resistance remain open. No assembly qualification is claimed; 2024-edition equivalence was not established by this bounded calculation.
- Six calculation tests pass; independent review agrees with the conditional inputs and result. No CAD or hardware change.

Reproduce to a fresh path:
```sh
uv run python -m fea.round_structural_screw_reference --output /tmp/screw-reference.json
uv run pytest -q tests/test_round_structural_screw_reference.py
```

## Earlier CI fixes: full verification succeeded at df6d1e5

Commits `8a881d6` and `df6d1e5` address the six remaining replay failures. Computed work and local stress transforms use operation-derived binary64 bounds; derived S8 axes and norms permit narrow rounding differences. Raw signed connector forces, global stress witnesses, IDs/coordinates, archive hashes and engineering gates retain exact checks.

All eight archived evidence tests pass under both default and Nehalem OpenBLAS configurations. Four numerical-comparison regression tests and six screw-reference tests pass; repository-wide Ruff passes. The combined focused run passed 18 tests.

**Verified earlier full CI:** [run 34704872331](https://github.com/mckayreedmoore/mini-moonboard/actions/runs/34704872331), commit `df6d1e5`, completed successfully. [Viewer deployment](https://github.com/mckayreedmoore/mini-moonboard/actions/runs/34704872303) succeeded for the same commit. Recheck these exact runs; do not infer full CI success from local tests.

Historical failed baseline: [run 34677705445](https://github.com/mckayreedmoore/mini-moonboard/actions/runs/34677705445) at `3f08e65`: 6 failed, 2550 passed, 19 skipped. Smoke/export steps were skipped. The failures were work summation and transformed-stress comparisons; scalar force-norm fixes alone had not been sufficient.

Check or reproduce:
```sh
gh run view 34704872331
uv run pytest -q tests/test_evidence_assertions.py tests/test_round_frame_evidence.py tests/test_round_load_evidence.py
OPENBLAS_CORETYPE=Nehalem uv run pytest -q tests/test_round_frame_evidence.py tests/test_round_load_evidence.py
```

Next engineering work remains current supported load demands and the unresolved head/base/leg/timber capacity checks above. This issue remains open and the design remains unreleased.


## September 12 continuation: concrete calculation results

Published `cfc2c28` without changing CAD, hardware, screw axes or the preserved designs. Independent calculation review found no blocking formula defects. **60 focused tests pass**, including source/result replay, current load-point mapping, independent edge-moment recovery, screw/head/section equations and current export contracts. Repository-wide Ruff and diff checks pass. All four new saved reports have current source hashes.

1. **[Conditional panel force-equilibrium screen](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/round-structural-panel-equilibrium.md).** Maximizing lateral force over the existing combined-action equation and head cap gives **252.354 N per screw**. Four kicker screws have an optimistic sum of **1009.418 N**, below the 1200 N diagnostic and all retained 250/300 lb downward ×1/×2 cases when no panel-edge bearing or backing friction is credited. This is a necessary-condition failure for the unchanged conditional references, not an upper bound on physical capacity or a verdict on a kicker with justified edge support. Current geometry puts kicker edges at floor level, but the prior support policy does not qualify their bearing. Main-panel nonfailures are not feasible reaction witnesses or acceptance. This identifies a concrete kicker load-path requirement before another full-frame solve.
2. **[Plywood head reference](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/round-structural-head-calculation.md).** Added a reproducible **304.125 N conditional NDS2018 reference** for G=.42 other-grade plywood. Actual countersunk-head applicability remains unresolved: AWC research includes flatheads, while Simpson publishes product-specific flathead reductions in dimensional lumber. Those factors do not transfer to SPAX plywood. A reduced equation thickness does not prove a physical lower resistance bound. Actual seat, adjustments, edition reconciliation and demand checks remain open.
3. **[Timber reference and dimensional acceptance](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/round-structural-timber-calculation.md).** Independently verified **1170 psi** DF-L No.2 normal-duration bending reference via AWC2024 TableW-1. Isolated centered-section products are **979.424 / 198.288 N·m**, not frame allowables. Actual depth must be at least actual bore diameter +101.6mm + twice centering error for the two-inch-edge comparison. Nominal139.7/38.1mm has zero tolerance margin. Current combined actions, restraint, local opening/connection behavior and acceptance of the detailing basis remain open.
4. **[Current global load sensitivity](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/round-structural-global-envelope.md).** Fresh mass integration gives **166.616 kg** under stated densities; all142 hold locations use current panel planes. **46/48 grouped sensitivities meet the moment comparison only; two fall below1.5.** Both use ×2 weight,80% mass,100mm standoff and300N horizontal force: **250lb factor1.489852; 300lb factor1.427370**. Net restoring moment remains positive. No assumptions were altered to erase the small shortfall. This does not produce internal joint demands or a friction/floor rating; no physical floor tests were added.
5. **[Base/leg resolution note](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/round-structural-base-resolution.md).** Current leg joints are **two four-bolt groups**, not independent two-bolt groups; shared timber review corrected. Exact group geometry and simultaneous wrench equations documented. ML24Z mounting/couple applicability still lacks an inspected published basis; nominal CAD thickness plus generic steel properties cannot qualify the purchased angle. **H3** with eight specified SD9112 fasteners is a concrete supplemental uplift candidate to investigate (conditional normal-duration1.112kN comparison), **not selected or checked for fit**. Placement, full moment path and compatible current demands remain necessary. No manufacturer message was sent.

### Next finite engineering decision

Resolve the kicker's credited load path and the base's rated or specifically calculated connection detail, then establish the compatible current demand envelope. Reconcile the two overturning sensitivity shortfalls with the explicit installation/load basis. Do not restart historical insert work, assume equal sharing, or run the known rear-prism surrogate as qualification. Remaining original acceptance criteria above stay open; none is closed merely by publishing these conditional calculations.

### Verification for this commit

- [Full CI at cfc2c28](https://github.com/mckayreedmoore/mini-moonboard/actions/runs/34708590510): in progress at this update.
- [Viewer deployment at cfc2c28](https://github.com/mckayreedmoore/mini-moonboard/actions/runs/34708590534): in progress at this update.
- The previous `df6d1e5` full CI and deployment both succeeded. Recheck the exact new runs above; do not transfer that success to the new commit.

**Issue remains open. Draft build plans are available; construction/climbing release remains blocked.**


## Kicker bearing/prying and H3 placement follow-up

Published `f2af79f`. Current CAD and selected hardware remain unchanged. **82 focused tests passed**, including the earlier60 plus new prying, APA-reference and H3/provenance/output-preservation tests. Repository-wide Ruff, diff whitespace, document links and current-result hashes pass. Independent review found no blocking formula defects. The earlier regional H3 trial is preserved but explicitly superseded; use the US-dimensionv2 result.

### H3 direct add-on rejected

The [US-dimension fit check](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/round-structural-h3-fit.md) uses the embedded H3 graphic in the primary US2026 catalog, page299: each wing **1 9/16in /39.6875mm**. No regional-to-US dimensional equivalence is assumed.

- Rear header face to closest rim: **47.087270mm**; nominal reach shortfall **7.399770mm**. The entire favorable wing envelope misses wood before a hole-pattern check is relevant.
- Front header face: **100% occupied by kicker plywood**, verified by CAD intersection. Moving the flange outside the panel or cutting clearance would be a different mounting detail.
- Standard US vertical-uplift H3 mounting is therefore rejected for the unchanged base. Its conditional uplift number is not assigned to this frame. No replacement was silently selected.

The base now needs an applicable ML24Z mounting/couple basis or a specifically revised receiver/panel/connection detail with complete load transfer; H3 is no longer an unchecked drop-in candidate.

### Kicker bottom-edge support assessed, not adopted

[APA axial reference](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/round-structural-kicker-bearing.md): standing-kicker loading uses panel axial compression **FcA**, not surface-normal Fc-perpendicular bearing. A-A/A-C23/32 Group1 gives **42.3223N/mm** perpendicular to strength axis. One2669N+gross-plywood-weight scenario requires **63.76mm of uniformly compressed width**. This is not an approved contact length: local pressure, load spreading, net hold region, simultaneous bending/buckling and floor/contact support remain separate. Other species-group factors are retained; owned plywood remains selected. No floor measurements/tests were introduced.

[Source-bound prying calculation](https://github.com/mckayreedmoore/mini-moonboard/blob/master/docs/round-structural-kicker-prying.md): credits upward floor reaction anywhere through panel thickness, signed screw shear and frictionless backing. It retains29.411N current modeled panel weight at its actual CAD centroid because that weight can stabilize pitch. No independent screw moment, friction or seam transfer is credited.

- **11 of45 sampled cases per kicker exceed the generous conditional pitch bound** using unchanged screw/head references.
- **22 cases have restricted2D force/pitch witnesses**, using zero vertical screw shear, mid-thickness floor bearing and explicit backing heights. These are not3D equilibrium, pressure, stiffness or strength passes.
- **12 remain inconclusive**; restricted LP failure is not general infeasibility.
- Example:1200N downward,100mm standoff,+300N outward requires top-row tension at least **784.346N**, above the conditional two-screw sum **608.249N**, even under the generous bearing/shear assumptions.

Bottom-edge bearing can change the previous screw-only shear result, but cannot alone qualify the kicker under the current reference/load combination. Actual head applicability remains unresolved. Next kicker decision must establish a defensible resistance/load/support basis or a specifically checked attachment revision that carries prying as well as vertical force.

### Current verification

- [Full CI at f2af79f](https://github.com/mckayreedmoore/mini-moonboard/actions/runs/34709788282): in progress at this update.
- [Viewer deployment at f2af79f](https://github.com/mckayreedmoore/mini-moonboard/actions/runs/34709788284): in progress at this update.
- Previous `cfc2c28` viewer deployment succeeded; its full CI was still running at the latest check. Earlier `df6d1e5` full CI/deployment both succeeded.

**All original remaining release criteria stay open. These targeted checks resolve the two proposed shortcuts, not the entire structure. Draft build package remains unreleased for construction/climbing.**

## September 12 concrete reinforcement development — `1b85ed8`

The separate `round-reinforcement-development` candidate now contains actual CAD changes; the selected `round-structural-development` and its drawings remain preserved. [Combined design/review](https://github.com/mckayreedmoore/mini-moonboard/blob/1b85ed86fead66f19a02349bb76b7e383ecd1675/docs/round-reinforcement-development.md).

- Two provisional fabricated steel shoes replace the outer two ML24Z/12 SDS connections. Sixteen new complete hex bolt stacks and bearing plates accompany explicit 9.525 mm rim-end trims. Eight original leg stacks and 22 ML24Z connections remain. This is not a purchased rated replacement or a released welding/fabrication detail.
- Five added header screws per independent kicker produce nine per kicker and 66 total panel/kicker screws. No additional timber or tied panel seam is introduced.
- All 142 owned-type Escape T-nuts are modeled and individually selectable. Published US kit guidance is documented: wood 3.5-inch countersunk; plastic 2.5-/3.5-inch cap head. Installed hold bolts remain absent because hold-seat geometry and the plastic per-hold mapping are unavailable. T-nut barrel/thread geometry and retention screws remain explicitly unresolved.
- Base v3 nominal fit passes: 16 stacks, 32 assumed socket envelopes, 58 retained screw intervals; no detected interference. Combined checks include the added kicker screws and T-nuts against other hardware and machined bodies and also detect no occupied-volume intersections.
- Revised mass is 181.205809 kg at assumed densities, including 1.530098 kg modeled T-nut envelopes. All 48 retained global moment comparisons meet 1.5; minimum 1.644591. This does not establish floor, friction or structural qualification.
- Final kicker v2 uses revised drilled panels plus their modeled T-nuts: 450/450 restricted six-component equilibrium witnesses, maximum individual tension 272.879773 N against the still-unqualified 304.124547 N head reference. Receiver wrenches are recorded; stiffness compatibility and actual resistance remain open.
- Focused Python checks, repository Ruff, exact evidence hashes, actual T-nut selection/visibility, and the selected predecessor's browser regression passed. Full CI and Pages run separately for this commit.

[Development viewer](https://mckayreedmoore.github.io/mini-moonboard/?model=round-reinforcement-development&view=rear) is live; matching design deployment 34715972593 passed and the public 142-T-nut inventory plus an exported mesh hash were verified. The new candidate is an explicit unqualified development option, not a change to the selected default. All original unfinished strength, installation and release requirements remain open; no closing claim is made.


Historical-audit test follow-up `a73316f` excludes only the four unused successor modules from the preserved round-service source scan; all original source hashes remain exact. Twenty-seven related tests pass. CAD/viewer geometry is unchanged. Latest full CI: https://github.com/mckayreedmoore/mini-moonboard/actions/runs/34716399510 (running at handoff). The superseded known-failing CI run for `1b85ed8` was cancelled after the follow-up run started.

