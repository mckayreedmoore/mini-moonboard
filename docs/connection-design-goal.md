# Connection-design completion goal

## Target

The application goal was restarted on September 8, 2026. Its active scope is
to bring the current candidate as close as defensibly possible to ready-to-use
plans, including connection resistance and unanchored stability work, while
retaining explicit construction/use validation gates. A complete-looking viewer
or machining package alone does not meet this goal.

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

September 8 continuation: the [current-wide frictional floor screen](wide-floor-screen.md)
and [conditional backing retention ceiling](backing-retention-envelope.md) are
complete within their stated assumptions. Three independent reviews of the
increment (correctness, testing, architecture/package consistency) found no
substantial defects. A linked predecessor page's obsolete flush-installation
instruction was corrected without altering its historical CAD. The combined
floor, retention, bearing and leverage regression passed 65 tests. These results
do not settle actual connection resistance, panel load transfer or floor friction;
the overall goal remains incomplete.

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
  ideal panel-edge bond while retaining the rim and common edge. The subsequent
  released linear solution is archived below; no bolt capacity is claimed.
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

## Current-candidate completion audit

The advertised candidate is `wide-principal-development`. The current-wide
conditional asymmetric work is complete, with
[results](wide-asymmetric-results.md), nineteen replay archives and all 216
independently checked aggregate action cases. Eighteen focused tests passed.
The [hardware BOM](wide-purchase-bom.md) and
[current assembly/access sequence](wide-principal-assembly.md) are also present.
These are candidate deliverables, not complete joint resistance or use approval.

The subsequent [part-local machining package](wide-machining.md) now closes the
dimensional handoff gap: 29 datum/profile references, 276 member-specific
connection-axis rows and 422 other feature records. It includes actual lower
bearing-plane definitions, full metric/imperial vertex coordinates and explicit
drill-versus-reservation semantics. Twenty-eight tests pass, including full CAD
replay and all CSV fields; independent reviews and representative browser-rendered
SVG inspections are complete. Actual installation dimensions where marked
unresolved, contact/load sharing and complete joint resistance are still open.

The [current bracket-axis audit](wide-bracket-axes.md) now distinguishes all
eighteen installed angles from the historical twenty-angle candidate. Its
per-member schedule accounts for all 108 screws, intended grain and mirrored
local axes; three tests pass. The manufacturer letter was re-downloaded with
the same recorded hash and its installation figures inspected. Actual joint
demands, loaded-member classification and mixed-direction resistance remain open.

Completed current-wide evidence includes authentication of the accepted 40 mm
mesh, CAD-derived leg and eleven-body base ownership, nine A12/K12/F6 Cartesian
basis solves, and independent replay of all 216 aggregate action cases. The
earlier narrower timber results remain separate historical evidence; do not
transfer their node identities or forces to this candidate. The incomplete
panel/leg contact attempt also belongs to the preserved timber model.

| Goal requirement | Current evidence | Status and remaining boundary |
| --- | --- | --- |
| Model panel inserts/machine screws while retaining bolts and bracket screws | Current CAD/export, insert selection, 56 pairs, 24 bolts, 108 SDS screws | Nominal geometry complete; effective engagement and application resistance need physical/supplier evidence |
| Conditional asymmetric leg/base demands | Current-wide nine bases, 216 scenarios, independent aggregate wrench replay | Complete within fixed-floor/ideal-bond assumptions; not individual bolt forces |
| Resolve known connection defects and assess actual joints | Wider principals clear the backing edge-distance screen; all 48 washer seats and 24 stacks checked; conditional wood-bearing envelope | Edge-distance geometry corrected; complete joint assessment remains analytically unfinished |
| Consistent manufacturing/audit package | 29 part drawings, local machining schedules, BOM, current assembly sequence | Candidate handoff present; marked installation/tooling details remain unresolved, not production instructions |
| Independent review and explicit human gates | Geometry, testing and package reviews; qualification ledger | Reviews do not confer structural approval; goal remains active |

### Next bounded analytical deliverable

The [backing-leverage investigation](wide-backing-leverage.md) now evaluates
all six actual attachment X positions in a projected two-support statics model.
The maximum positive retention coefficient is 7.024, with an opposing compression
reaction; off-axis moments are recorded separately. This rejects equal-share
reasoning for that model but is not actual joint demand, a conservative bound
or connection qualification. Finite housing contact and panel load sharing must
be resolved before using the result to size hardware.

The [relaxed housing-contact bound](wide-backing-contact-bound.md) now balances
both normal-load moments using the full housing envelopes and actual attachment
stations. Certified minimum total retention reaches 5.462 N/N within the isolated
normal-only model. Unlimited pressure and omitted compatibility make this an
optimistic conditional bound, not physical contact FEA or joint qualification.

The [backing-end retention trial](backing-end-retention-trial.md) identifies a
smaller purchased ML23Z angle from official drawings and checks eight proposed
screw axes/shaft envelopes in current wood receivers. It is not installed in the
current model. The subsequent full bracket/fastener check rejects its proposed
placement: both angles and nearby rim screws collide with existing base-gusset
bolts, including bracket clashes at both full-width slide limits. The documented
trial is rejected; no current geometry was changed to conceal the interference.
An alternative arrangement, tool clearance, installation limits, load transfer
and repeated-disassembly behavior must be resolved before selection.

The subsequent [relocated-bolt end trial](backing-end-relocated-trial.md) clears
the nominal hardware collisions by moving one existing gusset bolt per side
45 mm rear-normal. Two focused tests check raw receiver bore envelopes and
complete changed-hardware clearance. Existing stock and bolt lengths are retained;
the trial remains unselected pending spacing, installation, demand/resistance,
tool access and fresh manufacturing geometry checks.

The [end-angle installation gate](end-angle-installation-gate.md) now records
current ER-280 and ESR-2236 evidence. The trial's backing edge/end distances do
not support the generic axial-SDS route; an applicable connector-specific rating
or separately designed alternative is still required. A precise supplier/reviewer
question is prepared but has not been sent. This does not establish physical
failure or close the unresolved panel/joint demand assessment.

The [supplemental SDS envelope check](current-fastener-fit-audit.md) now uses
the published 0.256 inch major diameter instead of relying solely on the
viewer's simplified 0.25 inch shaft. Two tests pass for all 108 current and
116 relocated-trial SDS positions. Tolerance, pilot and resistance claims remain
excluded; historical source-bound geometry is unchanged.

Assess the intended leg/rim or lower-backing load path with explicitly defined
interfaces, then compare the resulting conditional demands to applicable
connection resistance information. Establish the model assumptions and numerical
acceptance gates before a new solve. Reuse existing force-recovery controls, but
do not substitute aggregate floor actions, equal bolt sharing or optimistic
bonded interfaces for isolated connection demand. An unsupported resistance
must remain unknown, not become a pass by choosing an assumed value.

This analytical assessment is outstanding work within this goal. Actual stock
inspection, usable insert engagement, unpublished supplier installation data,
floor friction and a professionally reviewed physical validation procedure are
separate human/supplier gates. Full unanchored contact qualification is not
retroactively required to call the explicitly conditional aggregate package
complete; it is required before using those idealized results as actual support
behavior. No construction or climbing approval is implied.

Completion-audit regression on September 8, 2026: 101 tests passed across current
and inherited insert/wide geometry and exports, washer seating, current structural
and asymmetric evidence replay, machining, bracket axes and hardware BOM. A
second independent correctness, evidence and package-consistency review found
no substantial remaining defects in the handoff corrections. These checks do
not close the outstanding joint assessment above.

## Active goal continuation: gusset load-path evidence

The active goal remains the current wide timber-frame review package, not a
return to earlier variant sweeps. New work has established a conditional
[two-member bolt yield basis](two-member-bolt-yield.md), checked actual thread
intrusion into member bearing lengths, and calculated a
[gusset bolt-pair transfer envelope](gusset-group-envelope.md). These reference
values are not final allowable joint capacities.

The [gusset load-path audit](gusset-load-path-audit.md) now maps actual shared
faces and recovers all nine archived basis displacement fields with native
CalculiX. Original and reduced-precision recoveries pass the preset numerical
checks. Header/rim/post edge forces remain separate to avoid double counting
or inventing individual bolt demands. The bonded header path prevents a direct
demand/resistance qualification of the intended bolted splice.

Immediate work remains narrowly focused: replace idealized connection transfers
with defensible fastener/bearing behavior, then compare demands and applicable
resistances. In parallel with that engineering decision, obtain the already
prepared supplier/reviewer answers for the end-angle installation and panel
insert engagement. Do not change lumber sizes based on the bonded recovery or
label the current machining package ready for construction.

The subsequent [released-gusset connector trial](gusset-connector-trial.md)
successfully replaces full-surface ties with force transfer at actual bolt-axis
points in an isolated, frozen-parent-motion model. Three assumed stiffnesses
and six rigid-motion controls establish the numerical formulation, not actual
bolt stiffness or demand. The original direct prescribed-anchor attempt failed
and remains archived. Next, connect this formulation to freely redistributing
parent members in the whole-frame model; do not size the connection from the
small one-way trial forces.

The [coupled whole-frame gusset assessment](coupled-gussets.md) now completes
that specific redistribution step: 830 shared nodes are released, with no
geometric change, and eight point connectors join independently moving gusset
and parent interfaces. All 27 native bases and 648 derived scenarios pass the
declared numerical checks for the three assumed stiffnesses. Peak tested
connector resultant is 50.3075 N in the 300 lb sensitivity combinations, not
an actual demand bound or a basis for a safety factor. Remaining ideal bonds,
uncalibrated axial/lateral stiffness, bearing/contact and connection resistance
still prevent qualification of the physical splice or frame.

The [coupled leg/rim release](coupled-leg-release.md) now removes the additional
rim and upper-panel bonds from both legs while preserving their glued-ply
idealization and original floor supports. All 27 bases and 648 combinations
pass the declared numerical gates. Depending on the assumed spring stiffness,
peak leg-connector resultant ranges from 364.97 to 903.48 N and peak loaded-hold
displacement from 7.8143 to 2.7803 mm. These are conditional sensitivity results,
not physical bounds. The next comparison needs a resistance/slip basis for the
actual rim plus two-ply leg stack; the prior gusset reference cannot substitute.

The [leg-bolt resistance checkpoint](leg-bolt-resistance.md) now verifies all
eight actual three-member stacks. A conditional perfectly bonded laminate
reference is 797.62 N per bolt, below the stiffest trial's 903.13 N lateral
maximum. This is not an adjusted allowable or proof of physical failure.
Laminate behavior, purchased bolt properties, calibrated slip and combined
axial/lateral resistance remain the next connection decision; the design is
not released for construction.

A steel-strength-only sensitivity reaches a mode-II reference ceiling of
840.79 N under the same inputs, still below the stiffest trial's lateral
maximum. Do not pursue a stronger bolt grade alone as the fix. The procurement
basis retains no laminate credit, so the next substantive connection model
must resolve individual-ply transfer or explicitly qualify composite behavior.

The [individual-ply map](leg-ply-load-path.md) now verifies that the existing
mesh can separate both pairs of leg plies without remeshing. All four ply
volumes/centroids and six stitch axes are checked against current CAD. The
next step is a defensible three-bearing-member bolt formulation and released
ply equilibrium checks, not another bonded-leg stiffness sweep.

The [mass-specific demand checkpoint](leg-bolt-resistance.md) now separates
the requested 250 lb maximum from the 300 lb sensitivity and retains same-case
force vectors. Their stiffest-trial lateral peaks are 770.90 and 903.13 N,
respectively. Neither comparison qualifies the joint; do not conflate the
300 lb numerical shortfall with proof of failure at the requested maximum.
