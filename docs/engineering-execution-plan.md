# Historical engineering execution plan

> Superseded September 15, 2026 by the owner-selected
> [floor-runner MVP master plan](floor-runner-mvp-master-plan.md). Preserve this
> document as the execution history for the earlier floor-runner, uncut and
> spliced-knee investigations; do not use its former selected direction as the
> current work queue.

Created September 14, 2026 following the owner's request to divide the remaining
work into manageable tasks and coordinate less expensive models.

## Authority and scope

This is the execution index for the remaining work. The detailed release gates
remain in [tapered-runner-completion-plan.md](tapered-runner-completion-plan.md).
The selected development authority is now
`compact-spliced-flush-top-development`: the preserved spliced-knee arrangement
with its 7 mm rim reserve, a flush rear-leg top and a relocated upper bolt pair.
The preceding `compact_spliced_kicker`, floor-flush and floor-uncut candidates
remain preserved evidence; none of their numerical acceptance transfers.
This plan does not release construction, change the selected design, authorize
procurement, or authorize a push. Preserve earlier designs and source witnesses.
Retain the accepted panel/T-nut scope and explicit support assumptions; add no
floor test or external engineering sign-off prerequisite.

## Work breakdown and status

Each task ends with a reproducible result or a specific supported rejection.
A completed investigation may leave a design gate open. Do not equate those
two kinds of completion.

| ID | Task and finite deliverable | Dependencies | Worker | Status |
| --- | --- | --- | --- | --- |
| 1 | Verify the existing named panel-offset adapter: rigid translation/rotation, force/moment transfer, rejection of invalid outside points, and complete assembly preparation. Repair only confirmed defects. | None | Sol (`offset_verification`) | Complete: 13 focused tests and guarded full preparation passed; [evidence](floor-uncut-first-case.md) |
| 2 | Establish one front bolt/washer feasibility envelope: placement, bore/washer seating, body/thread coverage, material/resistance basis, and receiving limits; or document the exact rejection. | Stable uncut geometry | Sol (`front_preflight`) | Investigation complete: diagnostic assumptions defined; registration/material gates remain; [preflight](floor-uncut-front-preflight.md) |
| 3 | Resolve one representative commercial-angle connection route using its complete forces and moments. Establish a supported route or identify one concrete replacement investigation. Expand to other affected stations only after the representative route works. | Existing authenticated A12 evidence | Sol (`angle_route`); coordinator reviews interpretation | Investigation complete: existing route unsupported; release gate open; [decision](floor-angle-route-decision.md) |
| 4 | Run the first uncut A12-left case and save authenticated sources, numerical checks, member/connection demands, and rim-bevel face interpretation. | 1; viable explicit hardware assumptions from 2 | Coordinator serializes native run | Complete under controlling no-slip scope: 11-cycle convergence and 25 listed criteria met; bevel/angle/hardware gates remain; [record](floor-uncut-first-case.md) |
| 4a | Diagnose the preserved uncut Coulomb convergence history only if finite-friction behavior is later put back in scope. Do not consume rejected-iterate demands as accepted results. | New owner direction | Sol or coordinator | Superseded by no-slip scope; historical only |
| 5a | Record the branch decision from tasks 2–4. Keep flush selected; decide whether uncut earns one more bounded investigation. | 2–4 and existing rim/taper reviews | Astra coordinator | Complete: uncut earns only task 5b before further investment; [decision](engineering-branch-decision.md) |
| 5b | Pass or reject one material-compatible resistance route for the uncut full horizontal rim bevel under the accepted no-slip A12-left demands. Do not run more global cases or redesign connections. | 5a and accepted task 4 report | Sol (`uncut_rim_method`) | Complete: route rejected; current uncut branch stops; [decision](uncut-rim-bevel-decision.md) |
| 5c | Pass or reject one geometry/load-path concept using a square-ended rim, fitted 6x6 timber bearing block and positive thrust/uplift restraint. Freeze one practical connection route before CAD or solving. This is a new unselected concept, not continuation acceptance. | 5b rejection and existing square-seat studies | Sol (`uncut_rim_method` follow-up) | Complete: examined SDWS route rejected before CAD; head/post-bearing collision and absent applicable three-member resistance method; [decision](fitted-block-restraint-decision.md) |
| 5d | Select the next physical direction: return to the accepted braced/trimmed candidate, relax the flush-detail constraints enough to define a new finite timber/commercial-hardware detail, or authorize a different engineered connection family. Do not silently change selection. | 5b and 5c rejections; owner direction | Owner; Astra records decision | Complete: owner selected the spliced-knee hybrid with 7 mm rim reserve, flush leg tops and relocated upper bolts |
| 6a | On selected flush authority, resolve or finitely reject rim cut, leg taper and complete connection load-path methods, including omitted runner/leg contact and existing notch/torsion assumptions. | 5d selects a finite changed detail while retaining flush authority | Sol; Astra adjudicates disputed methods | Superseded: owner left the tapered-runner direction |
| 6b | Establish contact sampling and timber-mesh adequacy on stable selected flush geometry, with explicit comparison thresholds and interface-motion checks. Distinguish penalty sensitivity from spatial refinement. | 6a methods and geometry stable | Sol | Conditional |
| 7a | Run first two remaining selected flush cases with authenticated inputs; stop at first adopted-criterion failure. | 6a and 6b pass; supported connection route | Sol preparation; coordinator serializes | Conditional |
| 7b | Run last three selected flush cases and consolidate governing demands and criteria. | 7a passes | Sol preparation; coordinator serializes | Conditional |
| 8a | Freeze selected geometry/fabrication datums, cut and drilling tolerances, inspection and rejection rules. | Selected authority geometry stable | Luna assembly; Sol verification | Conditional |
| 8b | Establish force-dependent hardware and receiving limits: washer seats, shank and usable threads, bearing and resistance. | Valid selected flush demand envelope | Sol | Conditional |
| 9a | Assemble package entry point and link existing stock, drawing, hardware and guide material without claiming release. | Selected authority frozen | Luna | Conditional |
| 9b | Finalize matching viewer, manifests, drawings, guide and CAD consistency. | 7 and 8 complete | Luna assembly; Sol verification | Conditional |
| 10 | Independently review every applicable completion gate, resolve confirmed defects, and record the exact conditional completion decision or unresolved blockers. | 7–9 | Independent Sol; Astra adjudication | Superseded by third-wave tasks below |

## First wave and ownership

Tasks 1–3 can run independently. Workers own only their assigned files and may
not overwrite other contributors' tracked or untracked work.

- Task 1: `fea/floor_uncut_mesh.py`, `tests/test_floor_uncut_mesh.py`, and
  `docs/floor-uncut-first-case.md`. Request coordination before changing shared
  response code, material inputs, or the candidate geometry.
- Task 2: a new `docs/floor-uncut-front-preflight.md`, with a narrowly scoped
  reproducible check if needed. Existing geometry and hardware remain unchanged.
- Task 3: a new `docs/floor-angle-route-decision.md`, with a narrowly scoped
  calculation if needed. No connector removal or new geometry selection.
- Coordinator: this index, shared-document integration, source freezes, heavy
  checks, native solves, and final interpretation of conflicting evidence.

Workers report changed files, commands/results, source references, assumptions,
remaining blockers, and a clear stop condition. The coordinator reviews results
before scheduling dependent work.

## Cost and verification rules

- The owner subsequently reported 33% weekly usage remaining and requested
  efficient coordination. Finish the existing first-wave workers and stop this
  batch at its saved checkpoint. Do not launch more workers or native solves in
  this batch. Keep future updates and task briefs brief and milestone-based.
- Use short, task-specific briefs and exact references instead of full-history
  agent forks. Use Sol for bounded technical work and Luna for clerical assembly.
- Reserve Astra for coordination, disputed engineering interpretations, the
  branch decision, and final adjudication. Do not duplicate every worker's work.
- Serialize native solves, heavy export builds, full suites and commit hooks.
  Lightweight independent checks may overlap. Freeze hashed source inputs before
  starting a native case and preserve its snapshot.
- Stop a batch when a confirmed failure requires design change. Additional load
  cases cannot supply a missing local resistance method or catalog applicability.
- Use focused checks first. Repeat completed full checks only when subsequent
  changes affect them. Record provenance separately from mechanical acceptance.
- Local commits must meet repository time rules with real author and committer
  timestamps. No push is authorized.

## Second-wave ownership

The owner's new instruction begins a separate, usage-limited batch and explicitly
requests delegation under this plan. It supersedes the earlier first-wave stop,
without widening mechanical scope.

- `uncut_rim_method` owns a new `docs/uncut-rim-bevel-decision.md` and, only if
  needed for reproducibility, one dedicated calculation script and focused test.
  It may not change candidate geometry, shared solver code, design selection or
  archived evidence.
- `plan_gap_audit` is read-only. It checks whether tasks 6–10 still follow the
  actual blockers and recommends deletions, splits or reordered dependencies.
- Coordinator owns this plan, branch integration and any later selection choice.
  No native solve starts during this wave.

Plan-audit disposition: tasks 6–9 are no longer one unconditional chain. Uncut
mesh refinement and remaining-case runs are deferred; task 5b decides whether
that branch merits any later plan. Selected flush methods and connection route
must pass task 6a before its mesh study or remaining cases consume solver time.
Fabrication and package work is split into geometry-only and force-dependent
pieces so useful clerical work cannot be mistaken for engineering closure.

Task 5b rejected the current uncut rim-bevel method. Therefore that exact
candidate receives no mesh study or additional load cases. Task 5c is a new
geometry feasibility gate based on the already documented square rim end and
independent fitted block. It must identify a positive restraint route before
any CAD or solver investment. Task 5c rejected the examined vertical-SDWS route:
the screw heads conflict with the post/header bearing and the reviewed primary
sources do not qualify its three-member, two-shear-plane connection. That option
also stops before CAD. Task 5d is now the only active checkpoint. Do not delegate
tasks 6--10 or consume solver time until the owner chooses a physical direction.

## Task 5d direction checkpoint

The evidence now supports three materially different choices. This is a design
selection, so the coordinator must not infer it from permission to continue:

1. Restore `compact_spliced_kicker` as the selected direction. Its preserved
   braced/trimmed package is the nearest completed conditional DIY candidate and
   is the recommended low-cost path. This gives up the later floor-runner/flush
   finish preference.
2. Keep the flush-floor direction but relax at least the conflicting flush-face
   geometry. Define one new finite timber/commercial-hardware detail before
   reopening task 6a. Existing flush, uncut-bevel and vertical-SDWS studies do
   not qualify that changed detail.
3. Keep every flush-face constraint and authorize a different engineered
   connection family. This may conflict with the preference against custom
   fabricated steel and requires a separately bounded concept before analysis.

No cheaper-model delegation is useful at this checkpoint: another method audit
or solve cannot choose which physical constraint the owner values least. After
the selection, delegate only the newly applicable downstream tasks in dependency
order; delete inapplicable tasks rather than carrying them as speculative work.

## Third wave: selected spliced flush-top candidate

The owner selected a narrow hybrid: retain the completed spliced-knee topology
and 7 mm rim reserve, remove only the 18 mm rear-leg-top projection, and relocate
the two upper bolts per leg. The 1:12 side taper and floor runners are not part
of this candidate.

| ID | Finite deliverable | Dependencies | Worker | Status |
| --- | --- | --- | --- | --- |
| 11 | Add the exact CAD adapter and public geometry tests. Require zero leg-top projection, retained 7 mm rim reserve, 56 mm upper pitch, fresh drilling, complete outward bolt stacks and receiver/washer fit. | 5d | Sol (`flush_top_geometry`) | Complete: 15 parent-run related tests and focused Ruff passed; generated geometry has all 20 bolt receivers fitting and 7.000 mm rim overhang |
| 12 | Add candidate-specific no-slip FEA launch and resistance/archive adapters. Run A12-left first with candidate-authenticated sources. Stop at numerical, member, connection, contact or placement failure. | 11 | Sol (`flush_top_fea_adapter`); coordinator serializes native run | Complete: exact-profile A12-left archive and splice checks pass; first square-end preparation failure is preserved as diagnostic |
| 13 | If A12-left passes, run A12 rear/forward, K12 right/rear and A1 rear in two bounded batches. Stop at first adopted-criterion failure. | 12 passes | Coordinator serializes | Complete: six fresh archives pass all 21 listed conditional splice criteria |
| 14 | Consolidate six-case governing demands, current end-detail checks and explicit conditional limits. Do not reuse old trimmed forces as current results. | 13 passes | Sol; Astra adjudicates | Complete: maximum first-stage nominal lateral ratio 0.746 and actual-angle ratio 0.712; directional placement margin 0.361 mm; group-spacing margin 1.9 mm; full-root sensitivity up to 1.081 is non-adopted |
| 15 | Generate candidate-specific viewer export, construction packet and build package. Preserve old package and archives unchanged. | 11; force-dependent content waits for 14 | Luna assembly; Sol verification | Complete: candidate export, construction packet and [build package](compact-spliced-flush-top-build-package.md) generated with six-archive evidence |
| 16 | Update README, current-authority documents, viewer default, manifests and `AGENTS.md`; verify no current reference conflicts. | 14–15 | Luna audit; coordinator edits | Complete: selected authority, local viewer/default manifests and current documentation aligned; historical packages retained |
| 17 | Run focused tests, export checks, full suite, Ruff, CAD smoke and independent gate review. Record completion or exact blocker. | 14–16 | Independent Sol; coordinator serializes heavy checks | Complete: 640 tests pass (16 deselected), full Ruff/CAD smoke/rebuild checks pass; independent review identified the retained ML24Z/SDS separation and flange-couple gate, so no fabrication release |
| 18 | Freeze a deterministic six-case commercial-angle demand ledger from the current archives. No new native solves. | 17 | Sol (`angle_ledger`) | Complete: [ledger](compact-spliced-flush-top-angle-ledger.md) records 24 ML24Z/144 SDS per case, 0.615 listed interaction, 240.815 N unlisted separation and 16.340 N·m force-parallel couple; gate OPEN |
| 19 | Obtain manufacturer/connection-designer applicability covering both installation families, bearing F2, application lines and residual couples; otherwise select a targeted replacement topology. | 18 | Owner/external technical source, then coordinator | External answer pending: [public product search](compact-spliced-flush-top-angle-options.md) completed and found no catalog-only larger ML angle/screw closure; ready-to-send exact technical question recorded |
| 20 | If task 19 changes connection geometry or stiffness, run only the affected fresh cases, regenerate evidence/package and repeat independent review. | 19 | Coordinator serializes solves; independent Sol review | Conditional future work; not needed if authoritative applicability closes the exact ledger demands |
| 21 | Update the current viewer and owner-material record for two portable 48 × 72 × 5-inch pads with a front-to-back center seam. | Owner decision | Coordinator | Complete: exact side-by-side bounds, reported five-inch foam stack, current links and browser regression updated; pads remain outside structural scope |

## Completed evidence to reuse

The [configuration handoff](../.agents/configuration-review-status.md) records
selected export/construction refresh, fresh-export checking, 584 passing tests
(16 deselected), Ruff and smoke checks. CAD asset bytes and archived witnesses
were unchanged at that checkpoint. This is a saved verification result, not a
claim that later edits have been checked.

Reuse the six candidate-authenticated archives under
`fea/results/compact-spliced-flush-top/` and their matching source manifests.
The earlier flush A12-left assessment, contact-penalty study and tapered-runner
cases remain historical references only; their forces do not qualify this
relocated joint. Do not repeat completed source-method audits without a new
question.

The uncut preparation failure is documented in
[floor-uncut-first-case.md](floor-uncut-first-case.md). At planning time, working
code already contains a named offset implementation; task 1 verifies that work
rather than assuming it must be written again.

## Execution log

- September 14, 2026: Owner authorized saving this plan and beginning execution.
  First wave is tasks 1–3; subsequent work follows the dependencies above.
- First wave: task 1 verified the existing offset matrix and repaired malformed
  registration handling. Thirteen focused tests and focused Ruff passed. Fresh
  full preparation passed in 42.87 seconds with 217 source hashes stable,
  25,388 nodes, 5,062 elements, 20 members, and 1,344 springs. No native solve
  was performed by this verification.
- Task 3 ended with a supported negative route disposition for the representative
  ML24Z joint. Its catalog and available mechanics evidence do not establish
  complete resistance. A single flush-only rim/post gusset is defined as a
  possible later local study; no gusset or revised geometry is selected.
- Task 2 completed the single front-hardware preflight and reproducible arithmetic.
  The combined independent bore-error envelope does not guarantee registration;
  catalog bolt body length does not guarantee the receiving limit; and the
  proposed washer lacks a published through-thickness yield basis. Current CAD
  still contains provisional earlier hardware. A first run remains useful for
  member/contact/bevel demand under that explicit representation, not as an
  authenticated assessment of the proposed replacement stack.
- First wave is complete. Task 4 is the next pending execution step; no native
  solve has started. Tasks 2 and 3 completed their bounded investigations, not
  connection qualification. This batch stops here to limit usage. No commit or
  push was made.
- Task 4 first native attempt ran September 14, 2026. It exhausted 100 cycles
  in 698.88 seconds. Final normal contact, equilibrium and MPC checks passed,
  but the floor-friction residual was 23.2533 N against 0.01 N. The archived
  state is numerically rejected. No branch decision or remaining cases follow
  until task 4a diagnoses convergence and a bounded retry succeeds.
- Owner then confirmed floor attributes are outside scope. Runner inheritance
  was corrected to the controlling no-slip assumption while retaining unilateral
  normal contact. Fresh A12-left converged in 11 cycles. Its portable assessment
  meets all 25 listed conditional criteria, but does not close the rim-bevel,
  unlisted commercial-angle or provisional-hardware gates. Historical Coulomb
  archive remains preserved; its convergence diagnosis is no longer a current
  dependency. Task 5 is next.
- Task 5a kept flush selected and allowed one further uncut method investigation.
  Task 5b rejected the full-bevel resistance route because the right q+ face is
  in tension and no reviewed solid-sawn method covers the local combined-action
  detail. Current uncut geometry stops. Task 5c now tests one separate square-end
  and fitted-block load path before any further modeling.
- Task 5c rejected the examined fitted-block restraint before CAD. One screw
  column occupies the post/header bearing, and no reviewed primary method covers
  the proposed three-member, two-interface SDWS action without assuming excluded
  composite behavior. Both uncut experimental routes are closed. Task 5d now
  requires an explicit physical-direction choice; unchanged flush analysis and
  tasks 6--10 remain paused.
