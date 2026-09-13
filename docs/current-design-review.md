# Current design review and finite verification plan

This review concerns `no-shoes-development`: single 2×6 legs and outer rims, four bolts per leg,
commercial base angles and a 277 mm kicker datum. It is an engineering work
plan, not a completed structural assessment. The objective is to establish
whether this assembly meets a stated load basis without speculative reinforcement.

## Engineering judgment

The project has accumulated useful geometry and evidence, but too much effort
has been directed at variations of uncertain historical response models.
The missing deliverable is a concise, auditable calculation for the current
assembly. Whole-frame behavior matters; that does not require a highly detailed
nonlinear solid model of every screw and T-nut. The analysis should begin with equilibrium and a suitably simple frame model.
Additional detail is warranted when it changes a design decision.
Component resistance checks remain necessary after whole-frame forces are known.

## What is unnecessary as a current design prerequisite

| Work | Disposition |
| --- | --- |
| Recalculating rejected steel shoes, welds, insert conversions and earlier frames | These studies should remain in the archive and be revisited only when they are reused or affected by a change to shared code. |
| Testing plywood or T-nuts solely because a previous report mentioned uncertainty | The accepted construction and published material basis remain applicable unless a specific product, layout or calculated demand identifies a problem. |
| Physical floor-friction testing | This is outside the agreed scope. Uplift and overturning still require evaluation under the stated assumption that the feet do not slide. |
| Destructive searches for a climber's “failure weight” | These are not required to demonstrate resistance to a specified design load. Exceeding an analytical reference limit does not predict physical collapse. |
| Repeated trials with arbitrary joint stiffness or prying factors | These trials do not establish acceptance without a justified range of properties. Sensitivity studies should answer a specific design question. |
| Rebuilding historical STEP and STL files after text or navigation edits | This is software regression work and does not establish structural acceptance of the current design. |

Extreme foot-contact cases may remain sensitivities. They should not be described
as demonstrated normal operating conditions or automatically trigger larger stock.
Published material variability and timber grade adjustments belong in the design
values; they are not reasons to request a new materials-testing campaign.

## Next engineering deliverable

The next task is to calculate the **internal member and connection forces in the
current assembly**. The completed [equilibrium screen](current-frame-equilibrium.md)
establishes that the evaluated loads can be balanced by compressive foot
reactions. It does not determine the actual distribution of those reactions,
the moments at the joints, or frame deflection.

The calculation should use the [current design basis](current-design-basis.md)
and the simplest model that represents the load path adequately. It should
include asymmetric climbing loads, sideways movement, possible foot uplift,
and compression between the rims and header. Published material properties
should be used, while assumptions about joint restraint should be supported by
the connection detail. Equal sharing between the legs must not be imposed: the
equilibrium results already show that it is incompatible with the governing
off-center case.

The deliverable should identify the governing load case and the force and
moment at each critical connection. It should also report the frame's
calculated deflection and demonstrate that the model balances forces and
moments. A numerical model should include appropriate verification of its
formulation and resolution.

## Work that follows the force calculation

1. **Check the governing members and connections.** Evaluate the legs, their
   four-bolt joints, bearing between the rims and header, the restored ML24Z
   angles, and any other member or attachment that carries a governing demand.
   The angle checks must address the manufacturer's applicable load directions
   and installation details. The accepted panel and T-nut construction remains
   the basis for distributing climbing loads into the frame.
2. **Resolve any identified shortfall.** Change only the member or connection
   that requires it. A targeted physical test is appropriate when a remaining
   uncertainty affects acceptance and cannot be resolved adequately by
   calculation or published evidence. Its loading and acceptance criteria must
   be defined before testing.
3. **Complete and review the construction package.** Prepare consistent cutting,
   drilling and hardware schedules, assembly details, and installation checks
   for the 277 mm candidate. Arrange independent review of the calculations and
   details. The older plans do not provide this current package.

The assessment is complete when the current load basis, load path, governing
strength and serviceability checks, and matching drawings have been reviewed.
It does not require every historical experiment to pass or every material
property to be measured again.

CWA's [design specification](https://www.cwapro.org/file/secure/cwadesignpecfinal2022.pdf),
sections 4.1–4.2 and 4.5–4.7, addresses design loads, complete load paths and
stability; section 8.2 addresses qualified review. The simple-model-first approach
above is this project's engineering recommendation, not a mandated analysis
method quoted from that specification.

## Repository architecture and test policy recommendation

The repository is currently an experimental design history with a current
candidate assembled from earlier Python modules. That preserves traceability,
but makes current work depend on historical code and makes old documents look
more authoritative than they are. The README now presents the current design,
and the viewer opens that candidate by default. The [historical archive](history/README.md) collects previous
candidates and their evidence.

The archive organizes documentation and navigation while retaining the original
locations of Python modules and authenticated assets. Moving those files would
break imports and source hashes. Shared geometry can be extracted when a
specific change requires it; completing this design does not require a wholesale
rewrite of the codebase.

Recommended future test separation:

- Documentation and navigation changes should receive link checks and checks of the affected browser behavior.
- Geometry changes should receive inventory, fit and affected-member checks, together with verification of export provenance.
- Changes to material calculations or solvers should receive numerical correctness checks and regression checks for affected dependencies and published variants.
- Comprehensive historical CAD regression should run on a schedule, on request, or when changes to shared dependencies require it.

The current four candidate tests and browser checks are useful. The complete
historical suite is useful regression evidence, but it is not a structural
qualification. CI has not been narrowed by this review: its existing full suite
remains enabled. Any reduction in routine coverage should follow an
implementation of test selection that accounts for dependencies. Timing measurements are needed before
claiming a speed improvement.

Evidence: [current tests](../tests/test_no_shoes_frame.py),
[older response-model audit](reinforced-assumption-review.md),
[fastener applicability](reinforced-fastener-applicability.md),
[material basis](leg-material-basis.md), and [CI](../.github/workflows/ci.yml).
