# Floor-runner MVP master plan

Created September 15, 2026 after the owner returned to the floor-runner design.
This plan supersedes the active execution direction in
[engineering-execution-plan.md](engineering-execution-plan.md). That document
remains the historical record of the earlier floor-runner, uncut and
spliced-knee investigations.

## Selected direction

The owner-selected direction is `compact-floor-flush-development`. Task FR-1
promoted it to current repository authority; the spliced-knee branch remains
preserved history.

Freeze this physical configuration for the MVP:

- solid 4x6 rear legs and side rims;
- compact single-2x6 header and posts;
- two outboard 2x6 floor runners with whole kickers;
- runner ends flush to the outer posts and rear-leg faces, lower rim ends flush
  to the post/header plane, and rear-leg tops flush to the side rims;
- the existing 1:12 rear runner recess, twelve complete outward-facing bolt
  stacks, 24 retained ML24Z angles with 144 specified SDS screws, and 66
  panel/kicker attachment axes;
- the purchased Hillman 42605 #10 x 2-1/2-inch ceramic deck screws at the 66
  panel/kicker axes, subject to exact receiver-containment and installation
  checks rather than transfer of SPAX resistance data; and
- two loose 48 x 72 x 5-inch pads, side by side, with the seam running front to
  back. Each pad uses 3 inches of 44 ILD polyurethane foam between two 1-inch
  stacks made from two 1/2-inch 1.7-density polyethylene sheets.

Preserve every previous design and archive as historical evidence. Do not add
new floor tests, panel qualification, whole-frame comparisons, alternative
connector searches, failure-weight studies, custom steel, or external-review
prerequisites.

## MVP completion claim

The endpoint is a consistent, reproducible, engineer-unreviewed conditional DIY
package for this exact floor-runner assembly under the recorded loads, material
assumptions and no-slip floor support assumption. Normal floor contact may open.
The result is not an unconditional safety rating, manufacturer qualification,
inspection of delivered materials, or verification of the actual floor.

An unsupported diagnostic is not converted into a passing resistance check.
Instead, the package must identify it accurately as an analytical limitation and
give practical fabrication or inspection controls. A native run or redesign is
required only when geometry or source inputs change, a physical load path is
missing, the solver fails, or an adopted numerical criterion exceeds its limit.

## Gate decisions

| Topic | MVP disposition | Stop condition |
| --- | --- | --- |
| Rim terminal cut | Retire the historical quarter-depth projected-seat scalar as a release gate. Its mapping to this supported terminal bevel was never established. Replace it with actual retained-section, bearing, contact and gross/net member checks. Preserve the old −4.970 mm result as a non-adopted sensitivity. | Actual bearing/contact path is absent, or an adopted member/bearing criterion fails. |
| Rear-leg 1:12 recess | Keep the geometry. Record the nominal 0.021506 MPa longitudinal cut-face tension and approximately 0.000149 MPa inferred transverse component as an unqualified local-fracture limitation, not a demonstrated physical failure. Require sound, check-free stock at the recess, a smooth transition, no overcut, and rejection of splits or damage. | Gross/net member checks fail, geometry removes a required receiver, or inspection cannot produce sound stock. |
| Runner/leg contact | Audit the exact interface and bolt-mediated load path once. Include active contact or demonstrate from saved/current relative motion that its omission is conservative or inactive. | A required force has no modeled or physical transfer path. |
| Front bolt pitch | Replace the generic independent ±1 mm hole-position assumption with a paired-hole fixture and measured finished pitch/registration rule. Nominal 39.5 mm pitch must not be credited without inspection. | The full tolerance stack cannot maintain the adopted 38.1 mm spacing and boundary limits. |
| Bolts and washers | Retain the catalog stack sizes. Measure delivered full shank, thread/runout, nut engagement, washer size and actual wood grip; reject incompatible parts. | Delivered hardware cannot meet the documented body, seating, engagement or receiver limits. |
| Hillman panel screws | Use only for the accepted panel/kicker scope. Confirm each modeled axis remains inside its supporting member and the 2-1/2-inch screw does not protrude. Do not substitute SPAX capacity claims. | Any axis misses its receiver, violates a required clearance, or protrudes from the supporting member. |
| ML24Z/SDS angles | Require all listed catalog force interactions to pass. Record separation and force-parallel flange couple as unlisted, manufacturer-unqualified actions. The completed catalog search found no drop-in commercial pair covering the full wrench at all 24 stations, so do not repeat product shopping. Under the owner's rush-to-MVP posture, these unlisted actions are a disclosed limitation rather than an automatic redesign trigger; do not call them manufacturer-qualified. | A listed interaction exceeds 1.0, installed geometry differs from the catalog fastening schedule, or an angle station lacks a physical load path. |
| Floor support | Use the owner's explicit no-slip analytical assumption. Do not claim measured friction or an anchor. | The selected calculation itself requires a tie or anchor outside that stated assumption. |

## Finite work plan

Each task ends in a reproducible artifact or one exact supported rejection.
Heavy native cases are serialized and begin only after the cheap geometry and
criteria work passes.

| ID | Finite deliverable | Dependencies | Status |
| --- | --- | --- | --- |
| FR-0 | Create this master plan, freeze scope, classify the old diagnostics, and define hard stop conditions. | Owner direction | Complete |
| FR-1 | Promote `compact-floor-flush-development` to selected authority in `current-candidate.json`, `AGENTS.md`, README, current-authority documents and viewer default. Preserve the spliced-knee branch and its six cases as historical. | FR-0 | Complete |
| FR-2 | Freeze one floor-runner criteria ledger implementing the gate decisions above. Remove the projected-seat scalar from adopted acceptance without deleting its history. State exact member, bolt, contact, commercial-angle and numerical criteria before more solves. | FR-0 | Complete |
| FR-3 | Close exact CAD and shop geometry: all 24 bolt receivers and washer seats, paired-hole fixture limits, delivered-bolt inspection rules, runner/leg interface, Hillman screw containment, pad dimensions and full left/right fabrication datums. | FR-1; may overlap FR-2 | Complete: reproducible nominal CAD and fixture checks; delivered-item inspection remains an installation condition, not a claim of measurement |
| FR-4 | Run a fresh exact A12-left case using the current no-slip producer and frozen criteria. Preserve the old finite-friction archive as history; do not relabel or promote it. Record the new authenticated sources and assessment. | FR-2–FR-3 | Complete: 14-cycle convergence; all 36 adopted checks pass in [fresh case log](floor-runner-mvp-case-log.md) |
| FR-5 | Run the five other exact floor-flush cases in two bounded batches. Stop only for non-convergence, an adopted ratio above 1.0, failed exact geometry, or a missing physical load path. Save authenticated sources and case assessments. | FR-4 passes | Complete: all six cases converge and pass 36/36 frozen checks; A12-forward required 69 one-contact-pivot cycles after three rejected bulk-search attempts |
| FR-6 | Consolidate the six-case governing ledger, including member/bolt/contact results and all 24 ML24Z listed interactions plus unlisted separation/couple demands. Record the limitations; do not restart catalog replacement research. | FR-5 | Complete: [aggregate](floor-runner-mvp-evidence.json) and [144-station-case angle demands](floor-runner-mvp-angle-demands.json); no unlisted capacity claim |
| FR-7 | Rebuild the matching viewer, manifests, construction sheets, stock/hardware schedule and assembly guide. Show the two 4x6 pads with front-to-back seam and list the owned Hillman panel screws. Remove obsolete 3x8 pad and SPAX purchase instructions from current floor-runner artifacts. | FR-3; force-dependent content waits for FR-6 | Complete: nominal viewer and construction artifacts rebuilt and authenticated; six-case force evidence and limits linked, with no fabrication release |
| FR-8 | Run focused tests, full non-historical suite, Ruff, CAD/export rebuilds, browser/viewer checks and one independent gate review. Publish a local completion ledger naming every passed criterion, installation inspection and disclosed limitation. | FR-6–FR-7 | In progress: 805 tests pass (16 historical deselected), Ruff and export rebuild pass; independent review findings addressed. Browser interaction and final completion ledger remain pending. |

## Evidence already earned

- Exact floor-flush CAD and a viewer export already exist.
- All 24 nominal bolt receivers fit in the saved geometry.
- The historical exact A12-left finite-friction case converged and met 37 of 38 then-implemented checks.
  Its governing adopted bolt lateral ratio was 0.8792 and sampled net-member
  ratio was 0.7488; the sole failed item was the now-disputed projected-seat
  diagnostic. It is useful comparison evidence, but it does not replace the
  fresh no-slip case required by FR-4.
- Six cases for the preceding tapered-runner model passed their historical
  checks. They are comparison evidence only and do not replace FR-5.
- The front, rear and upper nominal bolt stacks have documented shank/thread
  budgets. Delivered pieces still require inspection.
- Current commercial-angle listed interactions are below 1.0 in the saved first
  floor-flush case. The catalog does not rate the complete separation/couple
  wrench, and the commercial replacement search found no drop-in solution for
  all 24 stations.
- All six fresh selected no-slip cases converge and meet all 36 frozen adopted
  criteria. The first three A12-forward contact searches were rejected; a
  fourth search converged under unchanged physical assumptions and acceptance
  rules. See the [six-case record](floor-runner-mvp-case-log.md).

## Execution rules

- Rush to the selected MVP. Do not reopen spliced-knee, floor-uncut, fitted-block,
  2x12, shoe, insert, pad-material or alternate-connector branches.
- Prefer authenticated archived results over rerunning unchanged native models,
  but do not transfer the old finite-friction A12 response to the current
  no-slip support scope.
- Run cheap geometry and criteria checks before native solves. Serialize native
  solves, export builds, full suites and commit hooks.
- A failed adopted criterion pauses downstream work and produces one exact
  failure record. A caveat or unsupported method does not become a numerical
  pass; it is either replaced by an applicable check or disclosed as a limit.
- Keep documentation and viewer language precise: selected development,
  conditional DIY package, no manufacturer qualification, no unconditional
  fabrication or climber rating.

## Completion checklist

- [x] Floor-runner authority is consistent across code, documents and viewer.
- [x] One frozen criteria ledger governs all six exact cases.
- [x] Exact CAD geometry and hardware/fabrication inspection rules are recorded; actual delivered-item inspections remain pending installation.
- [x] Six exact cases converge and meet every adopted numerical criterion.
- [x] Commercial-angle listed interactions pass and unlisted actions are plainly
  disclosed without a false catalog qualification.
- [ ] Viewer shows the exact frame, Hillman panel screws and two 4x6 pads.
- [ ] Construction package and assembly guide match the selected model.
- [ ] Tests, lint, CAD/export, browser checks and independent review pass.
- [ ] Final ledger states the conditional claim and every owner/shop inspection.
