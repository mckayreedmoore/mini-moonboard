# Connection-design completion goal

## Target

Produce one coherent, auditable timber-frame connection candidate, not a climbing
approval. Preserve published predecessor models and their source-bound analysis.
No broad frame redesign unless the connection evidence requires one.

## Work sequence

1. Select and model removable-panel inserts and machine screws. Preserve existing
   through-bolts and manufacturer-specified bracket screws. Record purchased
   dimensions separately from modeling envelopes and unverified resistance.
2. Recover six-component aggregate leg/base forces from authenticated current
   results; extend the load cases to asymmetric single-hold loading. Distinguish
   fixed-floor/bonded-frame conditional forces from actual unanchored demands.
3. Resolve the lower-backing bolt edge-distance issue with a checked purchased
   connector or another evidence-supported detail; assess other actual joints
   against their applicable resistance data without equal-share assumptions.
4. Publish a consistent model, metric/imperial hardware and cut schedules,
   drilling/access information, assembly sequence and qualification ledger.
5. Independently review geometry, evidence and documentation; retain explicit
   human material, installation, floor-contact and physical validation gates.

## Completion boundary

An auditable candidate can contain clearly identified unresolved qualification
items, but must not silently substitute assumptions for supplier ratings or
claim that an optimistic model validates the physical joints. Missing structural
evidence remains visible and prevents construction/climbing approval.

Local work and commits continue during Denver quiet hours. Publication follows
the repository Git agreement. Another agent's untracked design notes are outside
this task's edit/staging scope.

## Current implementation status

- Panel-insert geometry and inspection package implemented as
  `panel-insert-development`; 56 replacements, existing transport/bracket
  fasteners retained. Geometry/export checks pass; resistance remains open.
- Supplier research identifies usable nominal dimensions but not a qualified
  insert engagement/withdrawal rating in the actual stock.
- Current leg-resultant recovery identifies an ideal-bonded panel-edge path as
  well as rim contact. [Aggregate leg-to-board actions](timber-joint-demand.md)
  are recovered; isolated bolt-group demand remains unresolved.
- The A21 backing-angle trial is not selected: available rating/installation
  restrictions do not establish suitability. The original narrow receiver's
  edge-distance concern remains open in its preserved variant.
- Nine asymmetric basis cases and 216 linear-combination scenarios are complete
  on the preserved timber mesh; [results and limitations](timber-asymmetric-results.md)
  include aggregate leg actions. These are not actual isolated bolt demands.
- Wider solid-lumber principals and matched short base blocks are implemented as
  `wide-principal-development`. Geometry/export checks resolve the backing-bolt
  edge-distance screen without relying on an unsuitable angle rating.
- The wider variant has completed its own 60/40 mm bonded stiffness diagnostics.
  Its approximately 23.68 kg mass increase is a tradeoff, not a proven necessity.
- The [connection qualification ledger](connection-qualification-ledger.md)
  separates actual modeled fit from missing joint demand, resistance and human
  inputs. In particular, no supplier-rated capacity is assigned to the inserts.
- A [panel-edge release transformation](panel-edge-release-diagnostic.md) now
  passes against the actual archived timber mesh. It removes the finite-area
  ideal panel-edge bond while retaining the rim and common edge; no released
  structural solution or bolt capacity is claimed.
- Independent correctness, testing/evidence and module-boundary reviews found
  no substantial remaining defects in this diagnostic increment. The reviews
  do not constitute professional structural approval.
- Final focused regression run: 88 tests passed, covering both insert/wider
  geometry and exports, new and preserved structural evidence, asymmetric
  recovery, the release proof and prior floor-screen behavior. Ruff and Git
  whitespace checks passed. Real browser checks previously loaded all 275/291
  selectable entries and exercised front/rear, selection and grid views.
- Final joint resistance checks and human/physical validation remain outstanding.
  The overall goal is not complete.

Further progress: [aggregate base actions](timber-base-demand.md) are recovered
for all six original and 216 asymmetric cases on the preserved timber mesh.
Actual floor-node ownership includes the kicker bottom, an explicit fixed-floor
model assumption. This does not yet isolate the gusset/backing joint actions.
The [conditional washer/wood bearing envelope](backing-bearing-envelope.md)
now has a matching 2024 NDS reference basis, separate from unqualified washer
bending, local wood failure and complete connection resistance.

The follow-up release solve and replay archive are complete. Forty-five focused
tests passed across release preparation/audit/publication, physical mesh
reconstruction, base recovery and bearing arithmetic. Independent correctness,
testing and boundary reviews found no substantial remaining defects in these
diagnostic additions. The goal remains active: physical joint qualification is
not substituted by these numerical checks.

## Immediate continuation, without another broad redesign

1. Develop the intended unilateral interface/load path after the completed
   [released-interface sensitivity](timber-release-results.md). Its small
   displacement change and tiny interpenetrations do not isolate real bolt loads.
2. Isolate gusset and backing actions beyond the now-recovered aggregate base
   wrench. Aggregate base and leg actions do not establish individual joint loads.
3. Develop a conditional backing-bolt resistance envelope, beginning with washer
   and local timber bearing. Use it to decide whether the heavier principals
   are justified; do not choose them solely because their bonded FEA is stiffer.
4. Resolve insert engagement and application resistance with actual hardware
   data and supplier/reviewer-supported testing. Keep bracket SDS screws and
   transport through-bolts unchanged unless their own checks require changes.

The [current fastener-fit audit](current-fastener-fit-audit.md) now confirms
full modeled support beneath all 48 washers and nominal dimensional clearance
for all 24 through-bolt stacks. Three focused tests pass. The
[contact-surface preparation](timber-contact-plan.md) also passes two actual-mesh
checks, providing verified paired faces for the next unilateral-contact control.
Neither addition supplies an unverified structural rating.

The [eccentric two-body contact control](panel-contact-control.md) now completes
four nonlinear penalty/increment runs with all 36 endpoints audited. Contact
force and moment agree with independent reactions on both bodies; 37 focused
tests and independent reviews pass. Actual frame contact, opening/recontact and
real fastener load sharing remain unfinished. The goal remains active.

## Current-candidate evidence gap

**Update:** the four conditional asymmetric-evidence steps below are now
complete, with [current-wide results](wide-asymmetric-results.md), nineteen
replay archives and all 216 independently checked aggregate action cases.
Eighteen focused tests pass. The [hardware BOM](wide-purchase-bom.md) and
[current assembly/access sequence](wide-principal-assembly.md) are also present.
Part-local machining dimensions, actual contact/load sharing and complete joint
resistance remain unfinished; the overall goal is not complete.

The advertised candidate is `wide-principal-development`. The 216 asymmetric
scenarios and aggregate leg/base actions from the earlier section belong to the
preserved narrower timber model, not this candidate. Their values cannot be transferred
to changed principals, posts and connector positions. Completing the current
candidate's conditional demand package therefore requires:

1. Authenticate the existing wider 40 mm mesh and its archived solver inputs.
2. Recover leg and base ownership against the actual wider CAD and mesh. The
   leg shapes remain unchanged, but remeshing changes node and element IDs.
   The wider base has eleven bodies: header, six posts, two kicker panels and
   two gussets. Recompute unique floor nodes and moment references.
3. Solve the nine A12/K12/F6 Cartesian basis cases and reconstruct the 216
   prescribed linear scenarios. Reuse numerical helpers, not historical
   geometry identities or old result labels.
4. Independently replay aggregate force/moment and displacement results with
   source-derived ownership. Retain fixed-floor/ideal-bonding limitations;
   these results still do not establish real fastener sharing or resistance.

The panel/leg contact diagnostic remains a separate same-mesh investigation of
the preserved timber model. Its completion does not close this wider-candidate
gap. The purchasing and part-local assembly/machining handoff also needs to
identify the current candidate consistently; historical inspection packets
must not silently act as its manufacturing instructions.
