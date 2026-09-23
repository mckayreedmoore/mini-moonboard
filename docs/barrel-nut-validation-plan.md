# Barrel-nut validation and conditional DIY completion plan

Prepared 22 September 2026 against freshly fetched `master` / `origin/master`
at `ca203ae94a10f9470c3b6fd567fe199db7e824ae`.

This is an execution plan, not a joint approval. The requested endpoint is a
complete, reproducible, conditional DIY packet **if the complete joints can be
shown adequate**. Otherwise, the endpoint is an exact failed or unresolved
criterion and the smallest concrete next action. More viewer polish, another
nominal-fit probe, or passing software tests alone does not finish this work.

## 1. Correct scope and starting point

The subject is the **integrated kerf-right barrel-nut frame** built by
[`build_integrated_viewer_assembly()`](../scripts/export_owner_barrel_scene.py),
not the selected angle frame and not the later screw-in-insert option.

The current proposal has 20 framing timbers, six plywood panels, 46 provisional
bolt/barrel pairs replacing 24 former angle duties, and twelve retained frame
bolts. All 66 panel/kicker screw axes remain unchanged. Two seam-side
88.9 × 139.7 mm center posts receive the four fixed center kicker screws;
there are no separate kicker backers, corner blocks, ML24Z angles, or structural
SDS screws in this proposal. The climbing surface, panel outlines, screw layout,
hold layout, and individual-member transport requirement remain fixed.

| Joint family | Duties | Current barrel pairs |
| --- | ---: | ---: |
| Bottom/lower/upper outer rail connections | 6 | 12 |
| Bottom/lower/upper center rail connections | 6 | 12 |
| Top rail to outer and center posts | 4 | 8 |
| Outer base to side members | 2 | 4 |
| Outer header to outer posts | 2 | 4 |
| Center posts to header | 2 | 4 |
| Center principals to header | 2 | 2 |
| Total | 24 | 46 |

The selected authority in `current-candidate.json` remains
`compact-floor-flush-development`. Its six-case pass belongs to the angle
frame. Neither that pass nor its listed ML24Z resistance transfers here.
Hidden-frame changes are permitted in the separate development lane by
`AGENTS.md`; panel fastener changes, custom steel, half-laps, housed/interlocking
joinery, and routine structural wood-thread removal remain outside scope.

Start with these current sources:

- [Integrated owner review](bolted-candidate-prototypes/owner-barrel-integrated-owner-review.md): configuration, exact blockers, and pending geometry decisions.
- [Integrated stack audit](bolted-candidate-prototypes/owner-barrel-integrated-stack-audit.md): reach, engagement, insertion bores, and comparator limits.
- [Kinematics](bolted-candidate-prototypes/owner-barrel-integrated-kinematics.md) and [preliminary component checks](bolted-candidate-prototypes/owner-barrel-integrated-preliminary.md): mechanics already explored and what remains unproved.
- [NDS applicability](bolted-candidate-prototypes/owner-barrel-nds-applicability.md): complete barrel-joint checks versus ordinary lateral-bolt subchecks.
- [Load-test readiness](bolted-candidate-prototypes/owner-barrel-load-test-readiness.md): exploratory coupons, qualification evidence, and full-frame proof are different endpoints.
- [`owner_barrel_native_preparation.py`](../scripts/owner_barrel_native_preparation.py): existing preparation for the integrated topology; do not start again from the angle producer.

### Revision reconciliation completed

The owner-approved N = 42 mm first rows at the two left center-rail stations
and 2 mm machine-bore extensions at the four top-outer rows are integrated in
the maintained source-built scene. The former two service-bore intersections
are absent, and the four top-outer rows have 2 mm nominal tip clearance.
[`owner_barrel_combined_owner_trial.py`](../scripts/owner_barrel_combined_owner_trial.py)
now guards that maintained pose. Timber sections, controlled hardware,
tolerances and resistance remain open. Preserve unrelated PB07/PB08 work in
the neighboring worktree and do not apply either revision twice.

Reconcile stale status descriptions too: the load-test readiness note still
calls the connector inventory an older pose and describes sampled-only rim
clearance. The current inventory defaults to the integrated assembly, all six
cases already prepare unsolved, and continuous nominal rim sweeps now exist.
Preserve those completed results while retaining their physical limits.

## 2. What currently prevents a strength conclusion

| Finding in current evidence | Work needed to close it |
| --- | --- |
| No complete barrel joint has an accepted resistance or same-topology demand. | Establish the entire steel/thread/wood path, then assess signed candidate forces and moments. |
| Both single-bolt principal/header joints have a local face-normal twist mode even with all face cells closed. Connected framing rank is 114/114 with all faces closed but 112/114 with all faces open. | Resolve actual signed contact states and connected restraint; full rank with assumed contact is not stability or strength. |
| Principal/header head pocket leaves 2.092 mm nominal edge stock. Only 588.180 mm² of cut contact face lies behind its bolt line. | Check exact local wood, contact pressure and moment path; revise the hidden connection if the path cannot be justified. |
| Outer-header pockets leave 6.35 mm nominal side stock; installed rims obstruct the driver. | Prove pocket resistance and tolerances, plus an achievable rim-first assembly/service sequence. |
| Revised N = 42 mm left center-rail rows give 6.641 mm nominal clearance from the former service-cut conflicts. | Check changed net sections, all interacting cuts, and tolerances. |
| Six-inch rail bolts extend only 1.849 mm past the assumed barrel thread axis. Four top-outer tips now have 2 mm nominal bore-cap clearance. | Establish actual usable engagement and delivered tip reserve using controlled or delivered dimensions; nominal bolt length is insufficient. |
| All 46 modeled barrel insertion bores have zero diameter allowance. | Select a justified fit and drilling tolerance, then recalculate removed wood and interference. |
| Hillman 880543 lacks the required controlled thread/material/resistance evidence in the completed retail research. | Close exact product/lot evidence or use a defensible complete-joint qualification route; no inferred barrel grade. |
| Six-duty preliminary results are constituent scales; eighteen duties are not assessed there. | Check all 24 duties, including both sides and new left-side cuts. Do not add constituent scales into a joint rating. |
| Native preparation exists with conditional 1000 N/mm axial and 500 N/mm lateral barrel springs. | Justify or bound joint behavior; prepare a verified response/assessment pipeline. Those defaults are not measured stiffnesses. |
| Smaller F1–G1 LED passage and owned plywood yield remain unverified. | Check real strand/connector passage and measured sheet dimensions without changing fixed panel outlines or screw axes. |

These are findings to resolve, not proof that the entire concept is impossible.
Conversely, a missing capacity is not a zero utilization or a passing caveat.

## 3. Finite execution sequence

### BN-0 — Freeze the actual candidate and acceptance contract

1. Reconcile revisions as above. Record commit, dirty diff hash where relevant,
   assembly/source hashes, units, and all 24 station identities.
2. Make one machine-readable station register: connected members, grain axes,
   bolts/barrels, entry/access faces, contact faces, all bores/pockets, fixed
   features, and source identifiers. Derive counts from the source assembly.
3. Freeze the six load cases from `scripts.clear_space_batch.CASES`: A12
   left/rear/forward, K12 right/rear, and A1 rear. Record full signed vectors,
   application points, gravity/equipment, dynamic assumptions and stand-off
   from the producer. The headline 250 lb inquiry alone is not the load basis.
4. Write candidate-specific criteria before assessing results. Retain applicable
   member, retained-bolt, support and numerical checks; replace obsolete
   angle/SDS checks with complete barrel-joint checks. Preserve the baseline's
   original frozen ledger unchanged.
5. Define each criterion's method, applicability, source, factors, numerical
   limit and failure disposition. Ratios require compatible demand/resistance
   bases; characteristic, ultimate and allowable values are not interchangeable.
   Set serviceability and numerical tolerance limits before using results to
   choose them. Unsupported checks remain `UNRESOLVED`, not `PASS`.

Deliverables: `barrel-nut-stations.json`, `barrel-nut-criteria.md`, and a finite
`barrel-nut-completion-ledger.md`. These are proposed new artifacts.

### BN-1 — Close hardware and material inputs

1. Start with the exact Hillman 880543 research already completed. Extract
   missing fields into one evidence table rather than repeating broad retail
   searches. Bound any follow-up to a specific missing datum or compatible SKU.
2. For every length family, identify bolt standard/grade, actual thread start,
   runout, usable male threads, head geometry and length tolerance; barrel OD,
   length, thread-axis offset, through-thread opening, usable female threads,
   material minimum and evidence of thread/barrel resistance; washer dimensions,
   material and bending basis. Record source and uncertainty per field.
3. Compute minimum usable thread overlap across the entire tolerance stack,
   required engagement from the resistance method, tip clearance, installation
   access and replaceability. Exclude incomplete threads and chamfers. Check
   the short-reaching rail stacks and far-projecting principal/header tip.
4. Freeze dry/green, incised/unincised, species/grade, actual sections and
   moisture assumptions. Use the candidate's 2024 material basis and applicable
   adjustments consistently. A different retail wood basket is not equivalent.
5. Separate documentary input closure from receiving inspection. The agent can
   compute required minimums and prepare measurement forms, but cannot mark
   delivered hardware, lumber, plywood or LED assemblies observed.

Exit: a traceable, calculable stack by family, or an exact evidence blocker.
If the retail barrel's minimum properties cannot be established, continue only
with explicitly conditional calculations while specifying the qualification
route. Do not buy a full hardware set on the strength of geometry alone.

### BN-2 — Settle joint geometry, access and load paths

Run this alongside BN-1; stop expensive downstream work on infeasible details.

1. Address principal/header first: draw its free body, identify what resists
   face-normal twist and reversed opening, and evaluate the thin head-pocket
   ligament. The connected frame may provide restraint, but it must be proved.
   Do not add fictitious moment springs, floor anchorage or clamp friction.
2. If this detail needs revision, make the smallest permitted hidden-frame
   correction and assess a complete joint. The documented two-barrel alternative
   is not a ready fix: its 2.796 mm side wood and 1.501 mm inter-pocket stock
   also need justification. Avoid an unbounded alternative-design search.
3. Resolve outer-header pockets and both center post/header connections,
   including transfer from the four unchanged kicker screws into the new posts.
   Preserve the actual limitations of Hillman panel-screw strength data.
4. Integrate the authorized left-row/top-bore changes, or use their landed
   equivalent. Check all 46 pairs against service cuts, other drill paths,
   retained bolts, panel screws, hold hardware, edges and ends. Include barrel
   insertion paths and machine/head pockets, not only shaft cylinders.
5. Recompute actual cut sections at critical planes and ligament transitions.
   Account for intersecting and neighboring holes together. Nominal bounding
   boxes or a full-slot sensitivity are insufficient local section evidence.
6. Establish assembly and individual-member removal with real tool envelopes,
   supported panels, access to buried barrels, retention/orientation, and a
   stuck-fastener recovery route. Reuse the existing nominal rim sweep result;
   add tolerances and support/tool checks rather than repeating it as new proof.
7. Resolve the 25.4 mm LED passage against the actual strand/connector envelope
   and panel cutting against measured stock. Keep observations pending when
   unavailable; do not shrink fixed panels to make a retail sheet fit.

Exit: one complete nominal design with explicit tolerances and a physical
force path at every duty. Local geometry and hardware changes require their
affected checks again, not automatic rework of unrelated history.

### BN-3 — Establish complete-joint resistance and stiffness

Use the [2024 NDS applicability review](bolted-candidate-prototypes/owner-barrel-nds-applicability.md)
as the starting methods map. Verify the cited primary provisions and errata
when implementing; do not substitute another NDS edition's values.

For each distinct family and all geometry-critical variants, cover:

- Bolt tension, shear, bending and interaction using the actual threaded/body
  portions; male and female thread stripping and required engagement.
- Barrel wall/net section, bending and local thread loading.
- Head/washer bending, seating and timber compression/pull-through or breakout.
- Barrel-to-wood bearing in the actual grain direction, splitting, end/edge
  breakout, net-section tension/shear and interactions with nearby cuts.
- Lateral bolt/wood behavior only where the ordinary dowel submodel applies;
  its resistance must not be relabeled as axial barrel anchorage.
- Group load sharing, eccentricity, contact opening, unequal stiffness and
  reversed actions. A two-bolt joint is not automatically twice one bolt.
- Slip, seating, clearance, reassembly damage and loss of engagement; identify
  the supported service/reassembly scope without inventing a cycle-life rating.

For every mode choose one defensible route: applicable published evidence;
geometry-specific mechanics with controlled inputs and justified adjustments;
or relevant complete-joint test evidence. A generic steel label or furniture
test for another joint closes none of these automatically.

Create a resistance ledger and a justified stiffness/clearance range. Steel
`EA/L` is only one constituent: wood, threads, barrel deformation, seating and
hole play must be considered. If a useful bound cannot be established, mark
the resulting response and demands conditional until measurement closes it.

Testing is necessary where these methods leave a governing path unresolved;
it is not an arbitrary blanket prerequisite for every unchanged member.
Define complete-joint coupon geometry, critical variants, lot/specimen
sampling, conditioning, action combinations, instrument requirements,
statistics, design-value derivation, and acceptance limits before tests.
Use the existing readiness note for guarded execution. No climber testing,
invented load multiplier, or single peak force promoted to allowable capacity.

### BN-4 — Finish and verify the candidate response model

Build on `IntegratedBarrelNative` and `prepare_case()`. They already prepare
58 bolts, 66 panel screws, 132 barrel-face cells and 72 retained-face cells;
they explicitly do not solve or claim acceptance.

1. Verify exact current wood, cuts, connectors, mass and grain/material mapping.
   Check whether all native elements and local section calculations represent
   each critical opening; a visual cut alone does not prove this.
2. Eliminate reliance on diagnostic-only geometry substitutions unless their
   equivalence is demonstrated. This preflight is now implemented: the four
   affected bevel members use actual constant-X CAD-prism C3D20 meshes with
   checked volume, centroid, attachment, and connector/contact containment.
3. Confirm no legacy SDS/angle springs or implicit header support survive.
   Verify the corrected kerf-right retained rim/leg interface, all intended
   floor/member contacts, and every load application point.
4. Reuse the existing tension-only handling in `fea/current_response_run.py`.
   Prove that tension-only fastener and compression-only face rules are enforced
   by the actual solver, not merely metadata flags. The 46 barrel pairs now use
   a coupled circular 0.575 mm radial-clearance active set with tested opening,
   engagement, reversal, force recovery, and authenticated checkpoints; the
   twelve retained bolts remain unchanged. Justified complete-joint stiffness
   bounds remain open. No hidden rotational restraints or panel diaphragm credit
   without an applicable connection basis.
5. Improve or bound contact quadrature. This geometry step is now implemented:
   all 24 barrel faces use 132 exact cut-cell areas and first moments, and the
   six retained faces use 72 exact locally bored cells. Mesh, penalty, pressure,
   partial-opening, and stiffness sensitivity remain acceptance work.
6. Add small mechanics verification cases: action/reaction and moment balance,
   opening/reclosure, tension-only engagement, free mechanisms, direction
   reversal and asymmetric row sharing. These test physics, not just flags.

Exit: a source-bound model with validated mechanics and explicit input limits.
A numerically stable solution obtained by restraining a real mechanism is a
failed model, not a passing joint.

### BN-5 — Produce signed demands and close all structural checks

**Authorization boundary:** the execution goal that followed this plan
explicitly authorizes candidate-only native solves after the geometry and
mechanics preflight. It does not authorize selected-baseline reruns, purchases,
supplier contact, physical testing, candidate promotion, or invented inputs.
Do not reuse the angle frame's demands as final evidence.

1. With candidate-only solve authorization, run one governing center/opening
   pilot case selected from the frozen load vectors. Freeze physical
   assumptions and acceptance criteria before running it.
2. Check equilibrium, residuals, convergence, contact signs, source identity
   and complete inventories. Inspect center twist and actual contact restraint.
   A source-preparation test or converged linear solve is not this acceptance.
3. Complete all six cases on the same frozen candidate. Serialize heavy runs.
   Record failed searches and any numerical strategy changes without moving
   physical goalposts or erasing failures.
4. Extract signed forces and moments at all 24 interfaces and all 46 fasteners,
   with common datums and individual row sharing. Assess each complete
   same-case action tuple; do not combine unrelated scalar maxima into a
   fictitious load case unless explicitly used as a justified conservative bound.
5. Apply BN-3 resistance checks and all applicable member, twelve-retained-bolt,
   panel/backing and support checks. Keep no-slip floor support explicitly
   assumed; do not add a friction test or claim an anchor or verified floor.
6. Run justified stiffness/clearance and local numerical sensitivities. Close
   the feedback loop: changed joint behavior can change governing forces.
   If measured coupon behavior invalidates assumed bounds, rerun affected
   response/assessment work before acceptance.
7. Produce a station × case × failure-mode ledger with inputs, demand,
   resistance, utilization/margin, method applicability and provenance.
   Report the governing joint/mode and actual reserve. Never infer a climber
   weight rating from these six cases.

Exit: every required check passes on the frozen geometry and supported input
basis, or the failing/missing path is recorded precisely. An unresolved
barrel/thread/wood capacity prevents a “joints strong enough” conclusion.

### BN-6 — Produce the matching conditional DIY packet

Start document templates earlier; finish dimensions and construction
instructions only for the accepted design.

Deliver one internally consistent package containing:

- Exact hardware BOM by SKU/standard/grade and quantity, per-family bolt length,
  engagement requirement, washer and barrel specification, substitution limits,
  purchase-source evidence and refreshed costs for compatible materials.
- Stock/cut list with actual sections, grade/moisture assumptions, panel yield,
  left/right identification, grain direction and waste/kerf allowances.
- Member-local dimensioned drill/pocket sheets: reference faces, both bore axes,
  drill entry side, actual bit/fit limits, depth stops, datum registration,
  counterbore seat, barrel thread-axis depth and minimum remaining wood.
- Practical jigs and drill sequence for intersecting bores, offcut fit setup,
  inspection tolerances, forbidden field elongation/reaming and rejection rules.
- Assembly and disassembly sequence with barrel orientation/retention, real tool
  access, temporary support and rim removal, LED routing and repeatable setup.
  Specify tightening from a justified installation basis; do not invent torque.
- Receiving/fabrication/installation checklist with Actual/Disposition cells
  blank until observed, including delivered threads, fit, splits and damage.
- Matching viewer, cut solids, schedules and evidence links. Clearly distinguish
  occupied CAD envelopes from drill sizes and measured delivered dimensions.
- A scoped inspection/maintenance and reassembly checklist consistent with
  the evidence; no unsupported fatigue or indefinite-reuse claim.

Do not silently select this candidate in `current-candidate.json` or replace
the baseline shop packet. Prepare a reviewable candidate packet first;
promotion is a separate owner selection after completion criteria are met.

### BN-7 — Independent review and finite handoff

Have an independent mechanics reviewer check the weakest joint, signed action
mapping, contact assumptions, thread/barrel evidence and cut-section methods.
Have a separate shop review trace a representative joint from BOM through
drilling, assembly, inspection and removal, plus every exceptional family.
Fix supported findings and repeat only affected checks.

Run focused tests for changed behavior, then the normal non-historical suite,
Ruff and candidate export/viewer checks. Confirm the selected baseline's export
authority remains consistent. Archive commands, source hashes, results and
limitations. Do not copy old test counts into the new completion ledger.

## 4. Completion and stopping rules

There are three distinct outcomes:

| Outcome | Required evidence | Permitted conclusion |
| --- | --- | --- |
| Conditional DIY documentation complete | All adopted candidate joint/member/load-path criteria supported and passed; exact matching machining and assembly packet; remaining physical inspections explicitly stated. | The documented design is adequate within its stated analytical/material/installation assumptions. It remains engineer-unreviewed and is not an unconditional rating. |
| Geometry or strength rejection | An applicable criterion fails, a required load path is absent, or compatible hardware cannot fit within allowed constraints. | This revision cannot proceed at the affected operation. State exact station, mode, value/limit and smallest supported correction. |
| Evidence blocked | Governing hardware properties, justified joint model, required physical results or solve authority are unavailable. | Adequacy is undetermined. Deliver completed independent work, exact missing evidence, prepared measurement/test/request packet, and how to resume. |

The agent can finish a conditional documentation package without pretending it
has fabricated or inspected anything. It cannot finish a validation route
that depends on unavailable physical tests by writing their procedure alone.
Exploratory coupons, qualification coupons and a non-climbing full-frame proof
must retain their separate purposes. Follow the existing readiness gates if
physical testing is used; software completion is not proof-test completion.

Do not add external sign-off, a new floor-friction test, or arbitrary load
testing as blanket requirements. Do not downgrade a failed or missing new
barrel-joint criterion into a disclaimer merely to finish. Exhaust applicable
documentary and analytical routes; preserve real physical-evidence blockers.

## 5. Work allocation and first executable checkpoint

After source reconciliation, independent bounded work can proceed in parallel:
one agent owns hardware/material evidence, one owns geometry/service checks,
and one reviews resistance-method applicability. The parent owns shared
criteria, configuration, response integration, heavy checks and the final
ledger. Delegate independent review after implementation. Coordinate file
ownership; serialize native solves, large CAD exports and full test suites.

Honor the clone's local Git quiet-hours instructions in
`$(git rev-parse --git-common-dir)/QUIET_HOURS.md`: Monday–Thursday
07:30–18:00 America/Denver. Edits/tests can continue; commit creation and
publication wait until allowed time. Retiming instructions apply only to the
owner's unpublished commits, never published history. These hooks and their
instructions are local files, not part of the tracked candidate packet.

The first checkpoint should finish BN-0 plus the principal/header feasibility
and hardware-gap records. It should answer whether the current joint has a
defensible qualification route, rather than producing more nominal viewer
variants. Proceed through the complete plan when feasible; a checkpoint is
not a substitute for the requested final outcome.

Existing useful verification targets include:

```sh
uv run pytest -q tests/test_owner_barrel_combined_owner_trial.py tests/test_owner_barrel_installed_stack_audit.py tests/test_owner_barrel_visual_wood.py
uv run pytest -q tests/test_owner_barrel_integrated_kinematics.py tests/test_owner_barrel_native_face_contacts.py tests/test_owner_barrel_native_preparation.py
uv run pytest -q tests/test_owner_barrel_integrated_backing.py tests/test_owner_barrel_post_header_preliminary.py tests/test_owner_barrel_scene.py
uv run python -m scripts.current_candidate --check-exports
git diff --check
```

These existing tests cover geometry/preparation boundaries, not structural
acceptance. Add new mechanics/assessment tests where BN-3 through BN-5 introduce
actual behavior. No existing unconditional native-run command is prescribed.

## 6. Suggested goal for the next model

The following is a proposed instruction to give after switching models. It is
not activated by this planning turn. It deliberately supplies the narrow
authority needed to avoid stopping later at the existing native-solve rule.

> Execute `docs/barrel-nut-validation-plan.md` as a goal. Bring the integrated
> kerf-right barrel-nut candidate to a complete conditional DIY documentation
> package if its complete joints and frame checks can be shown adequate.
> Start from latest master and reconcile existing worktree changes and recorded
> approvals. Preserve the selected angle-frame package and historical evidence.
> Keep the climbing surface, panel outlines, 66 panel/kicker screw axes and
> individual-member transport requirement fixed. Use the existing hidden-frame
> design authority; do not introduce custom steel, inserts, half-laps or
> housed/interlocking joinery. I authorize the candidate's two N = 42 mm
> left-center first-row changes and four 2 mm top-outer bore extensions if not
> already integrated, subject to all validation gates. I authorize necessary
> local candidate joint corrections within these constraints and candidate-only
> native solves after geometry and mechanics preflight; this overrides the
> general no-native-solves rule for this goal only. Do not rerun the selected
> baseline merely for comparison. Use bounded parallel agents and serialize
> heavy runs. Follow the local Git quiet-hours instructions. Do not purchase
> hardware, contact suppliers, conduct physical
> testing, promote the selected candidate, or claim observed measurements.
> Finish all independent computational and documentation work. If an adopted
> criterion fails, correct it within scope and recheck; if completion requires
> missing physical/material evidence or a design change outside scope, deliver
> the exact blocker and a concrete measurement/test or design-decision packet.
> Do not invent capacities, borrow another topology's passes, or call an
> unvalidated joint DIY-ready.
