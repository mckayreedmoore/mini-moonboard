# Current design review and finite verification plan

This review concerns `no-shoes-development`: 2×6 legs/rims, four bolts per leg,
commercial base angles and a 277 mm kicker datum. It is an engineering work
plan, not a completed structural assessment. The objective is to establish
whether this assembly meets a stated load basis without speculative reinforcement.

## Engineering judgment

The project has accumulated useful geometry and evidence, but too much effort
has been directed at variations of uncertain historical response models.
The missing deliverable is a concise, auditable calculation for the current
assembly. Whole-frame behavior matters; that does not require a highly detailed
nonlinear solid model of every screw and T-nut. Start with equilibrium and a
suitably simple frame model, increasing detail only where it changes a decision.
Component resistance checks remain necessary after whole-frame forces are known.

## What is unnecessary as a current design prerequisite

| Work | Disposition |
| --- | --- |
| Recalculate rejected steel shoes/welds, insert conversions and all earlier frame designs | Preserve in the archive; revisit only if reused or affected by a shared change. |
| New plywood or T-nut testing solely because generic product uncertainty was mentioned | Retain accepted construction and published material basis. Reopen only for a specific incompatible product, layout or governing demand. |
| Physical floor-friction testing | Outside the agreed scope. Retain an explicit no-sliding assumption; still check uplift and overturning. |
| Destructive searches for a climber's “failure weight” | Not needed to demonstrate a specified design load. Reference-limit crossings are not physical breaking weights. |
| Repeated arbitrary joint-spring/prying-factor trials | Not acceptance evidence without a justified range. Study sensitivity only where it can change the design decision. |
| Rebuilding historical STEP/STL files for text or navigation edits | Software regression work unrelated to structural acceptance of the current design. |

Extreme foot-contact cases may remain sensitivities. They should not be described
as demonstrated normal operating conditions or automatically trigger larger stock.
Published material variability and timber grade adjustments belong in the design
values; they are not reasons to request a new materials-testing campaign.

## Required engineering deliverables

1. **One design basis.** Fix the exact current geometry, species/grade and hardware,
   self-weight/equipment allowance, one-climber load cases, directions and load
   combinations, and strength/serviceability criteria. Reconcile the earlier
   150 lb inquiry with the preserved 250 lb design request rather than silently
   treating either as an approved rating. Separate code/reference loads from
   additional sensitivity cases; do not stack arbitrary multipliers.
2. **A complete load-path calculation.** Include centered and asymmetric hold
   loading, lateral racking, foot uplift/overturning and wood bearing. Retain
   no-sliding feet and exclude the pad as structural support. Use published
   properties and justified connection behavior. Verify force/moment equilibrium;
   if numerical modeling is needed, verify its governing results are stable as
   discretization is refined. Do not constrain independent panel seams together
   or assume equal leg sharing without justification.
3. **Checks of the governing members and joints.** Use those calculated demands
   for the legs/four-bolt joints, rim-to-header bearing, restored ML24Z connections
   and any other governing frame member or attachment. For the angles, verify
   catalog load directions, fastener installation and moment-transfer applicability.
   Generic steel strength alone does not establish a rated connection. Keep the
   accepted panel/T-nut basis while accounting for its role in distributing load.
4. **One coherent construction package and independent review.** Produce matching
   cut/drilling/hardware schedules and assembly details for the 277 mm candidate;
   review the calculation and specify installation checks. Older plans are not
   the current schedule. A targeted joint or assembly test is conditional on a
   decision-critical uncertainty remaining after calculation, not an automatic
   requirement. Any such test needs defined loading and acceptance criteria.

Completion means a reviewed current load basis, justified load path, acceptable
governing checks, and matching drawings. It does not mean every historical
experiment passes or every unknown has been physically measured.

CWA's [design specification](https://www.cwapro.org/file/secure/cwadesignpecfinal2022.pdf),
sections 4.1–4.2 and 4.5–4.7, addresses design loads, complete load paths and
stability; section 8.2 addresses qualified review. The simple-model-first approach
above is this project's engineering recommendation, not a mandated analysis
method quoted from that specification.

## Repository architecture and test policy recommendation

The repository is currently an experimental design history with a current
candidate assembled from earlier Python modules. That preserves traceability,
but makes current work depend on historical code and makes old documents look
more authoritative than they are. The README should be the current-design entry
point, the viewer should default to it, and [history](history/README.md) should
collect previous candidates and evidence.

Archive navigation and documents, not working Python modules or authenticated
assets. Moving them would break imports and source hashes. Longer term, extract
shared geometry only when a concrete change needs it; a wholesale rewrite is not
required to complete this design.

Recommended future test separation:

- Documentation/navigation: link checks and affected browser behavior.
- Current geometry: current inventory, fit, changed-member checks and export provenance.
- Material or solver changes: numerical correctness plus affected shared dependencies
  and retained published variants.
- Comprehensive historical CAD regression: scheduled/manual, and whenever affected
  dependencies require it.

The current four candidate tests and browser checks are useful. The complete
historical suite is useful regression evidence, but it is not a structural
qualification. CI has not been narrowed by this review: its existing full suite
remains enabled. Implement dependency-aware selection before removing any coverage;
add timing data before claiming a speedup.

Evidence: [current tests](../tests/test_no_shoes_frame.py),
[older response-model audit](reinforced-assumption-review.md),
[fastener applicability](reinforced-fastener-applicability.md),
[material basis](leg-material-basis.md), and [CI](../.github/workflows/ci.yml).
