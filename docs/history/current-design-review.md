# Current design review and finite verification plan

The selected candidate is **`compact-floor-flush-development`**: compact 4×6
legs/rims, compact 2×6 base members, two outboard floor runners, whole kickers,
the 1:12 rear recess, twelve complete bolt stacks and 66 panel/kicker axes.
Six fresh no-slip cases meet all 36 frozen adopted checks. The
[authenticated aggregate](floor-runner-mvp-evidence.json), [MVP master
plan](floor-runner-mvp-master-plan.md) and [criteria
ledger](floor-runner-mvp-criteria.md) are current authority. Commercial-angle
separation and independent flange-couple capacities remain unqualified; this
is not a fabrication release.

## Preserved spliced flush-top review

The following paragraphs describe the preceding selected candidate and remain
historical. Their six-case results do not transfer to the floor-runner design.

Six fresh assembled no-slip cases meet the listed conditional criteria. The
maximum adopted nominal lateral ratio is 0.746; the tightest directional
placement margin is 0.361 mm and minimum group-spacing margin is 1.9 mm.
Full-root lateral sensitivity exceeds 1.0 in four cases (maximum 1.081), so it
is recorded but not adopted and does not qualify fully threaded substitutes.

This is a finite engineer-unreviewed DIY assessment under the stated loads,
materials, hardware and installation assumptions. No-slip floor support is
assumed; local floor pressure is not converged or measured. Commercial-angle
unlisted separation and independent flange couples remain unqualified even
where rated force-component comparisons pass. These limitations remain in
the selected package; this selection creates no new general panel, floor-test
or external-review campaign.
The [current six-case angle ledger](compact-spliced-flush-top-angle-ledger.md)
records the exact affected connections and envelope demands without new solves.

The prior [spliced-knee result](compact-splice-study.md), floor-flush/taper
studies and compact-spliced-kicker result remain preserved references, not this
assembly's force evidence. The
[completion record](current-diy-completion-record.md) identifies the current
finite deliverables. The separate 2×4 rail exploration is not selected and
has no acceptance assigned here.

## Preserved September 12 review of the shoe-free baseline

The following work plan and software observations describe
`no-shoes-development` at that stage. They are retained as historical context;
references below to “current,” remaining work, commands and test coverage do
not override the selected flush-top authority above.

This review concerns `no-shoes-development`: single 2×6 legs and outer rims, four bolts per leg,
commercial base angles and a 277 mm kicker datum. It is an engineering work
plan, not a completed structural assessment. The objective is to establish
whether this assembly meets a stated load basis without speculative reinforcement.

### Engineering judgment

The project has accumulated useful geometry and evidence, but too much effort
has been directed at variations of uncertain historical response models.
The assembled response report below now supplies an auditable internal-force
calculation for the published current assembly. Whole-frame behavior matters; that does not require a highly detailed
nonlinear solid model of every screw and T-nut. The analysis should begin with equilibrium and a suitably simple frame model.
Additional detail is warranted when it changes a design decision.
Component resistance checks remain necessary after whole-frame forces are known.

### What is unnecessary as a current design prerequisite

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

### Completed internal-response deliverable

The [assembled-frame response report](current-frame-response.md) now supplies
member and connection forces, joint moments, deflections, and numerical audits
for nine selected cases including mesh and stiffness comparisons. It uses the
published 277 mm shoe-free geometry, independent panels, explicit fasteners,
and compression-only contacts under the agreed no-sliding assumption.

The demanding upper-left 150 lb doubled-load case produces approximately
1.816 kN at the governing leg bolt against a conditional nominal-diameter
reference of 0.917 kN. The leg's gross-section ratio is 0.462. The result therefore
supports prioritizing the connection rather than automatically enlarging the
leg stock. The [resistance audit](current-response-resistance-basis.md) explains
why using a stronger bolt steel alone does not resolve governing Mode II.

This is a selected-case response study, not an exhaustive internal-force envelope
or a construction release. Its [pinned source evidence](../fea/results/current-frame-response.json)
remains separate from the concurrent dependency refactor and rebuild check.

### Work that follows the force calculation

1. **Resolve the governing member and connection comparisons.** Use the calculated demands for the legs, their
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
3. **Keep the construction package consistent with the selected detail.** The
   [current package](current-construction-package.md) supplies cutting, drilling,
   hardware and assembly schedules for the 277 mm candidate, including pad-height
   adaptation. Leg drilling remains provisional until the connection decision.
   The agreed endpoint is engineer-unreviewed DIY documentation; independent
   engineering review is not a completion requirement. See the
   [completion record](current-diy-completion-record.md) for the finite checklist.

The assessment is complete when the current load basis, load path, governing
strength and serviceability comparisons, and matching drawings have been recorded
with a supported connection decision and explicit remaining limitations.
It does not require every historical experiment to pass or every material
property to be measured again.

CWA's [design specification](https://www.cwapro.org/file/secure/cwadesignpecfinal2022.pdf),
sections 4.1–4.2 and 4.5–4.7, addresses design loads, complete load paths and
stability; section 8.2 addresses qualified review. The simple-model-first approach
above is this project's engineering recommendation, not a mandated analysis
method quoted from that specification. The owner-selected engineer-unreviewed
endpoint does not claim compliance with that specification.

### Repository architecture and test policy recommendation

The repository is currently an experimental design history with a current
candidate assembled from earlier Python modules. That preserves traceability,
but makes current work depend on historical code and makes old documents look
more authoritative than they are. The README now presents the current design,
and the viewer opens that candidate by default. The [historical archive](history/README.md) collects previous
candidates and their evidence.

The archive organizes documentation and navigation while retaining the original
locations of Python modules and authenticated assets. Superseded entry points
carry dated banners directing readers to the current basis and this review.
Shared geometry can be extracted when a specific change requires it; completing
this design does not require a wholesale rewrite of the codebase.

The current model now exposes named face/header datums and explicit ownership of
floor-member extensions. Its exporter generates all current meshes and STEP
directly from CAD, without reading predecessor meshes, inventories or manifests.
The source manifest follows local Python imports and records the geometry data
and locked toolchain; historical geometry factories still remain source
dependencies. `uv run python -m mini_moonboard.no_shoes_exports --check` performs
a clean temporary rebuild and compares every current artifact and the manifest.
CI runs this check alongside current/shared tests by default. This reduces export coupling
without claiming the current geometry has been fully extracted from its history.

Recommended future test separation:

- Documentation and navigation changes should receive link checks and checks of the affected browser behavior.
- Geometry changes should receive inventory, fit and affected-member checks, together with verification of export provenance.
- Changes to material calculations or solvers should receive numerical correctness checks and regression checks for affected dependencies and published variants.
- Comprehensive historical CAD regression should run on a schedule, on request, or when changes to shared dependencies require it.

The current candidate tests and browser checks are useful. The complete
historical suite is useful regression evidence, but it is not a structural
qualification. Historical model tests are now opt-in through
`uv run pytest --include-historical`. The explicit inventory preserves shared
geometry, hardware and numerical checks in the default suite, and newly added
tests run by default. The manual CI workflow can also include historical tests
and reference/V1 export verification. See [test scope and known historical
failures](../CONTRIBUTING.md#checks).

Evidence: [current tests](../tests/test_no_shoes_frame.py),
[older response-model audit](reinforced-assumption-review.md),
[fastener applicability](reinforced-fastener-applicability.md),
[material basis](leg-material-basis.md), and [CI](../.github/workflows/ci.yml).
