# Wood-joint MVP completion ledger

The [refined execution plan](next-mvp-plan.md#refined-execution-plan-september-24-evening)
is the current work sequence. Its immediate milestone is to finish the selected
direct ordinary-joint method/sensitivity gate while current-frame demand
preparation proceeds in parallel. Current geometry and numerical-method
preparation do not close structural criteria; all 47 entries in the current
coverage register remain pending.

## September 26 MVP review disposition

For the reviewed 92-axis revision, retain the direct contact model for the
first ordinary-joint method demonstration. The current load path includes
bolt/bore clearance and transfer, finite timber contacts that can open, and an
explicitly assumed bolt/nut axial-engagement route. No reduced representation
has qualified current bounds for these mechanisms. The latest diagnostic
located the first reported cleat-bore contact and a complete following
accepted state. That demonstrates an interpretable contact event, not an
accepted joint response.

| Progress state | Current status | Evidence still needed to advance |
| --- | --- | --- |
| `inputs_ready` | Partial for the representative patch; current geometry, mesh ownership, contact mapping and source pins are recorded. Delivered engagement remains unobserved and must stay a named scenario. | Freeze the exact response assumptions and comparison inputs for the chosen run. |
| `method_demonstrated` | Partial; event output and state framing are authenticated. | Adopt a justified force/moment tolerance and complete timestep, mesh/contact, and assumption sensitivity on the same named patch. |
| `current_demands_available` | Not reached for the reviewed full frame. | Fresh signed reactions/actions from the current six source-bound cases. |
| `criterion_resolved` | 0 of 47 formally accepted; this is a criterion disposition count, not a measure of completed preparation. | Apply complete, applicable resistance and limit-state methods to fresh demands; preserve method gaps as unresolved. |

The next checkpoint must advance one of those state transitions. Before another
solver or instrumentation branch, its record must name the decision, the
settling observation, and the next executable step. Full-frame demand
preparation and non-native input work may continue alongside the local method
gate.

For practical integration, the September 26 forward/reverse sequence hypothesis
is recorded in [transport operations](transport-operations.md#current-reviewed-revision-sequence-hypothesis-to-validate)
for the same 24-block/92-bolt revision. It makes no assembly or removal pass:
support, service handling, complete tool paths, and tolerance-aware motion must
still be established operation by operation. The earlier 104-axis sequence is
retained as history and does not transfer.

### Source/geometry integration status, September 26

[`scripts/wood_joint_development_candidate_check.py`](../../scripts/wood_joint_development_candidate_check.py)
passes the owner-reviewed revision fingerprint/count check, rebuilds all 24
candidate blocks, reconciles 92 candidate bolt axes, 66 panel/kicker axes, and
12 starting frame bolts, and round-trips all 24 block solids through temporary
STEP files. This validates the source-bound geometry and file exchange only;
it does not establish joint mechanics, capacity, assembly, or release.

The selected-baseline
[`current_candidate --check-exports`](../../scripts/current_candidate.py)
still fails its source-identity gate: the current
`mini_moonboard/compact_floor_flush_frame.py` fingerprint differs from the
stored analyzed geometry fingerprint. Do not repair that mismatch by changing
the stored hash alone; the selected candidate's old case passes do not transfer
to a changed model. The selected geometry/evidence relationship needs its own
authenticated review before that check can pass.
CI now runs each validation gate independently and reports all results before
returning failure, so this selected-baseline finding does not skip the separate
wood-joint candidate integration result.

Focused local validation passes: maintained-code Ruff, the CadQuery smoke test,
56 tests across the changed resistance/contact/current-geometry screens, and
the separate current-gauge test. One historical every-increment producer test
skips because its source solver bundle is not stored in the repository. A
local all-repository pytest run reached roughly 67% and showed failures/errors
in older owner-barrel/PB04 suites before I stopped the long native/geometry
run; it did not produce a final test summary. CI retains the full suite and
will report that gate alongside both candidate checks.

Current checkpoint, September 26: the
[third corrected trajectory](hypotheses/evaluation-resume-2026-09-24/dependent-residual-contact-trajectory-run-attempt03/execution.json)
is terminal after the parent-requested stop at its bounded observation goal
(5,227 seconds, no OOM, solver exit 137 following Docker stop). Its preserved
[resultant-monitor observation](hypotheses/evaluation-resume-2026-09-24/dependent-cleat-bore-event-monitor-attempt01/parent-poll06-report.json)
covers 40 accepted states. All four monitored cleat bores first report nonzero
normal-force resultants at state 39, 0.0195 s; the preceding 38 accepted
states have complete target CF/CFN records and zero reported resultants.
The [bounded pointwise observation](hypotheses/evaluation-resume-2026-09-24/parent-bore-pressure-prefix-attempt01/README.md)
also finds the first emitted positive local pressure at state 39 on each pair,
with complete empty point lists in the preceding 38 accepted states. The
parent joined those times to accepted STA identities and matched all 936 CFN
components against the independent resultant monitor. This locates the first
reported event among recorded states, not continuous-time physical onset.
The following accepted state is 40 at 0.01975 s. Its initial angular capture
had 312 of 315 records. After increment 41 was accepted on its second attempt,
the [monotonic extension and parent framing audit](hypotheses/evaluation-resume-2026-09-24/parent-event-state-prefix-attempt01/framing-audit.json)
verified the original DAT prefix unchanged and appended the three buffered
records. States 39 and 40 each have all 315 angular records with passing
vector identities, all 116,162 physical ACC nodes, 24 MPC rows and 337
matching support ACC rows. Their complete map blocks contain 72,045 and
79,174 points. This justified stopping the bounded diagnostic, not accepting
the joint or its entire planned horizon.
The final terminal STA also records accepted state 42 at 0.0203 s; that
later state's DAT tail is incomplete and is outside the two-state stop goal.
The parent then completed serialized full-mass reconstructions for states 39
and 40 with the pinned Gmsh 4.12.1 image. The
[global-wrench diagnostic](hypotheses/evaluation-resume-2026-09-24/event-state-global-wrench-audit-attempt01/README.md)
has an independent result review that recomputes both moment residual vectors
within JSON serialization precision and verifies the source pins. Every
component falls below its conditional output-token bound (largest ratio
1.25%); the bounds omit mass/operator and multiplier uncertainty and are not
an equilibrium tolerance. Force tolerance, whole-horizon completion, time
accuracy, physical engagement, capacity, and mechanical acceptance remain
open. The reused state reports carry legacy `first_state` labels; their
increment/time scopes and the parent record identify the selected states and
completed reconstructions.

The [first-state output checks](hypotheses/evaluation-resume-2026-09-24/repaired-first-state-prefix-attempt01/README.md)
pass their scoped independent reviews and parent replays: corrected energy
accounting, physical acceleration coverage, and contact-vector identities.
The [mass-operator source review](hypotheses/evaluation-resume-2026-09-24/first-state-global-angular-diagnostic-attempt03/mass-operator-applicability-note.md)
confirms the untransformed element operator for the pinned F2F configuration,
while keeping physical-space mass and MPC-reduced generalized forces distinct.
The integrated adapter's [parent preflight](hypotheses/evaluation-resume-2026-09-24/first-state-global-angular-diagnostic-attempt03/parent-preflight.json)
reproduces the author's output byte-for-byte: 116,162 physical acceleration
and displacement nodes, 57,643 elements, 35 pairs with 315 contact records,
337 support acceleration nodes, and 662 load rows. It does not perform mass
integration. The corrected full mass/moment adapter passed its independent
review, including the added displacement-token bound on inertial moment.
Its first parent mass execution stopped before integration because the local
Python environment lacks Gmsh. The preserved
[retry](hypotheses/evaluation-resume-2026-09-24/first-state-global-angular-diagnostic-attempt03/parent-mass-run-attempt02/execution.json)
uses the existing pinned Gmsh 4.12.1 image with the project's NumPy 2.5.2
mounted read-only. It completed in 34.46 seconds with unchanged source and
inputs. The [actual first-state result](hypotheses/evaluation-resume-2026-09-24/first-state-global-angular-diagnostic-attempt03/parent-mass-run-attempt02/README.md)
has force residual components below 1e-12 N and moment residuals up to
4.86e-10 N mm. The moment components exceed the narrow conditional
output-token bounds; their interpretation and independent review remain open.
Small absolute residuals do not establish an equilibrium pass. Physical thread engagement and numerical sensitivity
remain unresolved. No complete joint or fresh full-frame case is accepted.

The first terminal-mode contact-event reconstruction exposed a reader defect:
the angular selector rejects a truncated record in the later, unselected
state 42, although selected state 39 is independently complete. Its
[failed execution](hypotheses/evaluation-resume-2026-09-24/first-state-global-angular-diagnostic-attempt03/parent-event39-mass-attempt02/execution.json)
is preserved. The separate [streaming selector correction](hypotheses/evaluation-resume-2026-09-24/first-state-global-angular-diagnostic-attempt04/README.md)
was source-reviewed and passed the parent no-mass selection preflight for both
event states; the original producer and terminal trajectory remain unchanged.
The earlier event invocation's CLI-option error is also preserved and did not
run integration. Corrected event-state energy accounting is complete on
bounded authenticated slices and has an independent review
([result](hypotheses/evaluation-resume-2026-09-24/contact-energy-corrected-event-states-attempt01/README.md),
[review](hypotheses/evaluation-resume-2026-09-24/contact-energy-corrected-event-states-review-attempt01/independent-review.md)).
The review found a join-key wording defect in the reviewed README snapshot. A
read-only [follow-up review](hypotheses/evaluation-resume-2026-09-24/contact-energy-corrected-event-states-review-attempt01/post-correction-review.md)
confirmed the corrected current README against the producer and parser:
`(element_fortran_number, igauss, jfaces)`. The original review remains intact;
the correction changes no calculations or reported values.

The [conditional Unified thread-tooth field](hypotheses/evaluation-resume-2026-09-24/current-unified-thread-tooth-field-attempt01/README.md)
now has a frozen executable local transfer law and completed independent
review (nine focused tests). The reviewed `k_u` is a distributed local
tooth/root stiffness density; its slice stiffness is `k_u` times active slice
length. The auxiliary bar-informed `K_c` is not a whole bolt/nut tangent and
is not used as a scalar gap spring. This closes the bounded source/formula
review only: actual engagement, fit phase, rotation restraint, hardware
selection and physical predictive error remain unresolved.

The dated records below preserve the method-development sequence; later
repairs and actual-run observations supersede their earlier readiness limits.

Method checkpoint, September 25 at 17:53 UTC: the parent built the
[isolated multithreaded SPOOLES derivative](hypotheses/evaluation-resume-2026-09-24/mt-factorization-build-review-attempt01/parent-verification.json).
The exact rebuilt object set is `spooles.o`, `results.o` and `printoutcontact.o`;
the binary links both expected MT entry points. A source-bound thread-count
benchmark remains required before using this speed change in a joint run.
The energy-reader correction also passed the parent
[production printout fixture](hypotheses/evaluation-resume-2026-09-24/contact-energy-reader-repair-attempt01/parent-printout-fixture-attempt01/execution.json):
eight assertions cover sparse F2F point slots, legacy compact reads, ordinary
springs and contact-range boundaries, with runtime bounds checks enabled.
The previously passed `calcenergy` fixture still matches the proposed source.
These are build and focused method checks, not a corrected native trajectory
or a complete-joint result. Parent inspection also found that the separate
`frd.c` CELS branch still reads compact energy slots; the proposed repair does
not change it. Corrected energy validation must use the repaired `calcenergy`
solver/controller totals, `printoutelem` DAT values and exact point-map writer
values. FRD CELS is excluded from that validation until separately corrected.
All 47 formal criteria remain pending.

The parent then executed the two unchanged contact benchmark decks with the
preserved serial point-map binary and the MT derivative at one and four
requested solver threads. All six runs returned zero and passed the strict
[existing contact/reaction/completion audit](hypotheses/evaluation-resume-2026-09-24/mt-factorization-benchmark-attempt01/parent-strict-audit-summary.json);
each scenario's audit JSON is byte-identical across the three arms. The
[pre-run contract](hypotheses/evaluation-resume-2026-09-24/mt-factorization-benchmark-attempt01/parent-input-contract.json)
also requires actual multiworker execution. That gate is not met: both
four-thread arms log four requested CPUs but only one actual SPOOLES worker,
consistent with this tiny fixture's elimination graph. Preserve this limit;
a larger source-bound fixture is required before claiming parallel coverage.
The subsequent [complete pairwise comparison](hypotheses/evaluation-resume-2026-09-24/mt-factorization-benchmark-attempt01/README.md)
matches the numerical outputs across all six arms; the actual-worker limit
of this tiny fixture remains. These are numerical method diagnostics, not
joint or frame cases.

The [combined corrected solver build](hypotheses/evaluation-resume-2026-09-24/reader-acc-mt-build-attempt01/parent-build-verification.json)
is now complete: binary SHA-256
`4e794cae6d0495a5a543e5bd962f5dde2a3539f0cb850432e230ee23494654e9`,
with exactly eight intended objects rebuilt. The first attempt stopped before
compilation because the image lacked `patch`; the preserved retry mounted a
hash-verified host `patch` read-only and completed with the unchanged recipe.
The full production ELSE-then-CELS printout fixture also passed bounds-checked
execution and [independent review](hypotheses/evaluation-resume-2026-09-24/contact-energy-reader-repair-attempt01/independent-review-addendum.md).
Both original static contact decks passed under this combined binary, with
[DAT output identical to the serial reference](hypotheses/evaluation-resume-2026-09-24/combined-reader-static-smoke-attempt01/result.json).

A [sixteen-copy contact fixture](hypotheses/evaluation-resume-2026-09-24/mt-multiworker-contact-fixture-attempt01/fixture-contract.json)
then ran in four serialized arms. All returned zero; both four-thread arms
(the plain MT and combined corrected binary) logged four actual workers for
both factorizations. The [parent all-pair audit](hypotheses/evaluation-resume-2026-09-24/mt-multiworker-contact-fixture-attempt01/parent-independent-audit.json)
and independent fixture audit agree: all 48 ordered contact reports, complete
top/bottom displacement and reaction rows, per-copy force and moment checks,
and completion checks pass. All four DAT files are byte-identical. This
establishes numerical agreement for this static fixture with four actual
workers; it does not establish dynamic joint response or a speedup factor.

Current native checkpoint, September 25 at 18:26 UTC: the parent launched the
[corrected joint trajectory](hypotheses/evaluation-resume-2026-09-24/dependent-residual-contact-trajectory-run-attempt02/execution.json)
after verifying the eight unchanged inputs, binary/source index, immutable
launcher snapshots, and [parent readiness](hypotheses/evaluation-resume-2026-09-24/dependent-residual-contact-trajectory-parent-readiness-attempt02.json).
The container used the reviewed binary with four actual SPOOLES workers,
a four-CPU limit, and 10 GiB memory limit. The planned observation was the first
cleat-bore contact transition plus one following complete accepted state,
subject to earlier stop for a numerical defect. Corrected LOG/DAT energy and
full-mesh acceleration outputs must be checked before interpreting the
response; FRD CELS remains excluded. The run is now
[terminal after an instrumentation failure](hypotheses/evaluation-resume-2026-09-24/dependent-residual-contact-trajectory-parent-terminal-attempt02.json):
at 18:33 UTC it exited with code 1 after 438.427 seconds and one accepted
0.0005 s increment (23 iterations). The new full-acceleration writer rejected
the native node-count guard. The earlier local writer passed its original
element-count check, but the assumed total node count does not match runtime.
All eight input and ten output pins verify; there was no OOM. Full-mesh ACC
and point-map outputs are absent, so the printed corrected LOG energy alone
does not complete the paired energy audit. Repair the instrumentation against
native node semantics before the next trajectory. No complete joint is accepted.

The [reviewed attempt02 reader adapter](hypotheses/evaluation-resume-2026-09-24/contact-energy-reader-corrected-first-state-attempt01/independent-review-v2.md)
now authenticates that failed run against its v2 terminal record, exact
executable/source index and runtime image. Eighteen focused tests pass,
including contradictory missing/output-hash inventories and mismatched image
rejection; the real report reproduces byte-for-byte. Missing point-map and
DAT energy evidence remains unavailable, not zero. This adapter explicitly
rejects the later attempt03 source lineage.

The [source-derived repair](hypotheses/evaluation-resume-2026-09-24/all-physical-acc-output-proposal-attempt02/README.md)
accounts for 4,524 generated rigid-constraint nodes from the four frozen nut
sets. It requires at least 120,694 runtime nodes while continuing to derive
the exact 116,162 physical nodes from the original C3D10 connectivity. The
parent [compiled helper fixture](hypotheses/evaluation-resume-2026-09-24/all-physical-acc-parent-fixture-attempt02/execution.json)
passed eleven cases with undefined-behavior and bounds sanitizers. Three valid
runtime node counts produce identical complete physical-node output; eight
invalid count, connectivity, type, or value cases fail as intended. This
repairs the exercised output boundary only. The [fresh combined build](hypotheses/evaluation-resume-2026-09-24/reader-acc-mt-build-attempt02/parent-build-verification.json)
is now complete with binary `3b63e1590b143be79c4c869c218286fc83c081fd89802a63658cd13776b60ab0`
and source index `b55323a611704378ad84f1e688075e284859bdbd09b75d853c0bb8ef0b9ef19f`.
All fifty source artifact hashes and generated artifact hashes verify. Exactly
eight objects were rebuilt; only `results.o` differs from the preceding build.
The initial invocation refused a copied prior Makefile in a reserved output
path before compilation; the parent preserved that file separately and the
unchanged recipe then succeeded. Independent review confirms the build
lineage and retained reader correction.

The [third trajectory attempt](hypotheses/evaluation-resume-2026-09-24/dependent-residual-contact-trajectory-run-attempt03/execution.json)
launched at 19:05 UTC on September 25. The parent rechecked all eight unchanged
inputs, the new binary and source index, live bind mounts and limits, and
immutable launcher/helper/test snapshots. The launcher now requires the
repaired fixture and source lineage; 37 focused tests pass. Its historical
container-name literal still contains `attempt02`, while the actual run
directory, preparation, binary and execution identify attempt03. The first
accepted-state gate is complete physical-node acceleration and corrected
LOG/DAT energy agreement with the point-map writer. The planned endpoint
remains the first bore-contact transition plus a following accepted state;
an earlier numerical or source defect stops interpretation.

The third attempt has now produced the required first-state energy and acceleration output. The
[authenticated live prefix](hypotheses/evaluation-resume-2026-09-24/repaired-first-state-prefix-attempt01/README.md)
records all 116,162 finite physical-node acceleration triples and runtime
`nk=120694`, matching the source-derived count. All 104,245 writer points join
uniquely to the Fortran records. Corrected DAT CELS and LOG energy agree with
the writer sum, approximately `3.4786029443e-11 N mm`, within printed-token
bounds. The largest pointwise native-law difference is `6.31e-30 N mm`;
printed C/Fortran pressure, area and clearance differences are zero. This
closes the observed first-state output fault, not complete response or joint
acceptance. Independent prefix review reproduces those results. The initial
DAT tail lacks its last angular rows; a separately authenticated 363-byte
extension completes all 315 first-state angular records, with 1,575 finite
values, while preserving the initial capture. Angular output coverage is
established, but angular equilibrium is not yet evaluated. Independent
extension review and parent replay also confirm all 1,155 contact-vector
identity checks under the printer-bound policy. These cover force
decomposition, action/reaction and pair-couple accounting, not whole-joint
equilibrium. The native run subsequently reached the first reported bore
contact event and one following accepted state; see the current checkpoint
above for the terminal record and completed state-39/40 diagnostics.

A [bounded live observation](hypotheses/evaluation-resume-2026-09-24/parent-bore-force-peek-attempt01/README.md)
records 76 complete normal-force resultant records for the four cleat bores
through increment 19 (0.0095 s); all printed force components are zero.
This does not prove absence of local contact, since point forces may cancel.
Pointwise pressure evidence remains required to identify the first local
contact state. The observation preserves source-prefix hashes and record
offsets and makes no complete-state framing or stop-readiness claim.

The [finite incremental monitor](hypotheses/evaluation-resume-2026-09-24/dependent-cleat-bore-event-monitor-attempt01/parent-observations.md)
has now run on the actual trajectory after its bounded-read fix and eleven
focused tests. The first parent poll finds complete target CF/CFN records
for 29 accepted states through 0.0145 s, all with zero reported resultants.
Its first 19 states match the separate finite reader exactly in 228 force
component tokens. Pointwise contact and full output framing remain separate
requirements; the monitor does not authorize stopping or establish mechanics
acceptance. Independent monitor review is complete and records the limited
print-only action/reaction diagnostic and missing dedicated negative STA
regression test. A second parent poll reads only the appended output and
extends complete target records to increment 31 (0.0155 s), still with zero
reported resultants.

The [orderable washer follow-up](washer-property-options/ordinary-washer-orderable-options-2026-09-25.md)
adds priced 316 stainless options and documents their limits. No checked
offer yet jointly establishes the pinned dimensional envelope and a
product-bound yield minimum. The 254 SMO family remains a conditional
material scenario; no washer selection or bending resistance is adopted.

The parent also completed both central kicker-post removal screens using the
unchanged STEP export. The
[right post](hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-center-post-right-attempt02/parent-run-attempt02/report.json)
and independently derived
[left post](hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-center-post-left-attempt02/parent-run-attempt02/report.json)
both have clear conservative continuous envelopes for a 140.7 mm translation
toward the removed kicker panels. Each retains all 210 stationary obstacles
in the collision scene; only endpoint-distance calculation excludes obstacles
with invariant transverse separation. Both final bounding boxes are disjoint
from all obstacles, with a 1 mm axial gap to the header. This is nominal route
evidence under the recorded prior removals, not a support, staging, tool,
tolerance or complete transport result. Independent reviews of
[right attempt02](hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-center-post-right-attempt02/independent-review.md)
and [left attempt02](hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-center-post-left-attempt02/independent-review.md)
are complete. Left attempt01's stale right-side prose labels remain preserved;
the corrected left report passed a separate parent rerun with the same geometry
and 140.7 mm route.

The parent then completed the [paired floor-runner screens](hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-base-floor-rails-attempt01/parent-run-attempt01/report.json).
Each 1 mm outward translation has a clear conservative continuous envelope
against 17 other timbers and all 131 modeled wires, with disjoint endpoint
bounds. Both legs, all twelve retained stacks, all candidate stacks and all
candidate corner-cleats are assumed already removed. The export contains no
candidate cleats, so these results do not verify their removal. This is local
separation evidence, not a complete removal, support, handling, or transport
sequence. The [independent review](hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-base-floor-rails-attempt01/independent-review.md)
confirms the source pins and bounded geometry result. Its explicit limitations
include the unverified prior-removal statement for the 92 candidate axes and
the absent cleats; neither is promoted to sequence evidence.

Earlier native checkpoint, September 25: the finite-actuator diagnostic is
[terminal after an explicit parent stop](hypotheses/evaluation-resume-2026-09-24/ordinary-finite-actuator-k1e4-attempt02/terminal-outcome.md),
with nine accepted increments through 0.003875 s. The fresh [force-driven
derivative](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-seating-100n-every-increment-k1e4-attempt01/README.md)
passed parent and independent input reviews and is now
[terminal after a parent-directed stop](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-seating-100n-every-increment-k1e4-attempt01/terminal-outcome.md).
Its [execution record](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-seating-100n-every-increment-k1e4-attempt01/execution.json)
records 7948.409 seconds before the explicit stop. There are 38 accepted
increments through 0.02171185 s and seven rejected attempts. Session 34273
has terminated; native return code 137 follows the parent stop, not an OOM
or runtime-limit event. All 27 frozen inputs and 15 output hashes verify.
The 0.025 s target was not reached. Contact-onset accounting supports moving
to a matched-binary timestep refinement after the queued diagnostics.
The [first-state monitor comparison](hypotheses/evaluation-resume-2026-09-24/every-increment-first-state-comparison-attempt01/comparison.json)
records q = 2.4127149e-5 mm, 0.13370% below the earlier force-driven result
at that time; maximum loaded displacement differs by +0.03620% and nut
rotation by -0.31606%. These scalar comparisons do not establish equivalent
iteration paths, time accuracy or joint acceptance. It used four solver
threads, a 10 GiB limit and a 10800 s
runtime bound, with output requested at every accepted increment. The
completed [five-state work audit](hypotheses/evaluation-resume-2026-09-24/current-finite-actuator-work-audit-attempt03/README.md)
and [contact coverage audit](hypotheses/evaluation-resume-2026-09-24/finite-actuator-progress-contact-audit-attempt02/README.md)
preserve their bounded findings; no current joint or whole-frame acceptance
follows from them.

The [half-timestep derivative](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-seating-100n-every-increment-k1e4-halfdt-attempt01/input-freeze.json)
is [terminal after an explicit parent stop](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-seating-100n-every-increment-k1e4-halfdt-attempt01/terminal-outcome.md).
It ran with four solver threads, a 10 GiB limit and a 10800-second runtime
bound. Session 17654 ended after 5560.122 seconds, with 43 accepted increments
through 0.0206025 s and one rejected attempt. Return code 137 follows the
parent stop, not an OOM or timeout. All 34 frozen inputs and 12 output hashes
verify; the 0.025 s target was not reached. Parent and
[independent input reviews](hypotheses/evaluation-resume-2026-09-24/halfdt-launch-gate-review-attempt01.md)
verify all 34 child artifacts and all 27 inherited parent inputs. Exactly one
pilot line changes: initial and maximum increments are 0.0005 s instead of
0.001 s. The packaged binary, 0.025 s horizon, minimum timestep, loads,
contacts, materials and every-increment output requests are preserved.
Its [execution record](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-seating-100n-every-increment-k1e4-halfdt-attempt01/execution.json)
governs current run status; launch readiness is not time-accuracy evidence.
The immutable [early output prefix](hypotheses/evaluation-resume-2026-09-24/halfdt-early-prefix-attempt01/README.md)
records four accepted increments through 0.002 s with 23, 5, 7 and 8
iterations and no rejected attempts. All 34 input artifacts were verified
before capture. Its 0.001 and 0.002 s states support exact-time comparisons
with the coarse run. The completed work and momentum audits below remain
limited to this fixed prefix.
The [early common-time comparison](hypotheses/evaluation-resume-2026-09-24/halfdt-early-comparison-attempt01/README.md)
has been reproduced exactly by the parent and independently reviewed.
At 0.001 and 0.002 s, half-step q is 17.43% and 9.15% lower, respectively,
with absolute q below 0.0002 mm. Reconstructed cumulative work is 8.25% and
2.57% higher; each reconstruction agrees with its own native work print
within the reported output bounds. These are observed early-state differences,
not a time-accuracy result. The separate
[early momentum postprocess](hypotheses/evaluation-resume-2026-09-24/halfdt-early-momentum-audit-attempt01/momentum-audit.json)
completed in 32.302 seconds and passed its bounded independent review. Over
0.001–0.002 s, all global and cleat XYZ components are within propagated
print bounds under both mass formulations. The largest absolute global and
cleat residuals are 1.5441e-11 and 1.2666e-11 N s, respectively. The local
contact impulse uses two 0.5 ms intervals and complete cleat-incident
reports; incomplete unrelated contacts remain unavailable. These bounds do
not include between-output force variation or time-discretization error.
The [expanded work comparison](hypotheses/evaluation-resume-2026-09-24/halfdt-precontact-comparison-attempt01/README.md)
now covers all 13 common accepted times through 0.013 s. A separately pinned
log extension completes the final native summary without replacing the
original snapshot or admitting later states. The parent reproduced the report
exactly, and its independent review passed. At 0.013 s, q differs by -0.416%
and reconstructed cumulative work by -0.0119%. Those times precede the
coarse run's reported bolt-hole contact onset and do not resolve its energy
discrepancy.
The immutable [first contact-transition prefix](hypotheses/evaluation-resume-2026-09-24/halfdt-contact-firsttransition-prefix-attempt01/README.md)
now records 39 accepted half-step increments through 0.0195 s, with no
rejected attempts. The parent copied and verified all 34 frozen inputs along
with the output prefix. The last accepted increment required 15 iterations;
its native energy discrepancy remains substantial. The parent exactly
reproduced the [first-transition work comparison](hypotheses/evaluation-resume-2026-09-24/halfdt-contact-onset-comparison-attempt01/README.md),
and its independent review passed.
At the exact 0.019 s shared state, q differs by -0.1865% and reconstructed
work by +0.00696%; native work matches within the reported print bounds.
At the standalone half-step 0.0195 s state, reconstructed work also matches
the native print. Its [complete contact-storage bound](hypotheses/evaluation-resume-2026-09-24/halfdt-contact-storage-bound-attempt01/README.md)
was reproduced exactly and independently reviewed: all 35 pairs and 72,043
rows are accounted for, and at least 0.142278623 N mm remains outside the
represented storage envelope after print margins. This identifies no cause
and establishes neither time accuracy nor joint acceptance. The 0.0195 s
state has no exact accepted coarse counterpart, and the terminal half-step
run has no accepted 0.020 s state. The requested same-time contact comparison
therefore remains unavailable. The parent stopped this diagnostic to obtain
the missing constraint-force and contact-moment outputs next.
The reviewed [convergence-source note](hypotheses/evaluation-resume-2026-09-24/current-lowload-convergence-readiness-attempt01/README.md)
identifies the upstream mechanical residual clamp and distinguishes that
Newton gate from later contact-stiffness restoration and impact checks.
It describes pinned source semantics, not packaged-binary equivalence or
the cause of a particular accepted or rejected increment. No convergence
tolerance has been changed.

The separate [angular-output diagnostic executable](hypotheses/evaluation-resume-2026-09-24/finite-actuator-angular-momentum-audit-attempt01/angular-output-build-attempt01/README.md)
has linked successfully after verifying 1176 upstream source-file hashes and
recompiling the two modified output routines. The contact printer passed five
native fixtures and independent review; the MPC/acceleration hook passed its
source review, algebraic sign fixture and syntax check. This built executable
and its unmodified upstream counterpart remain distinct from the packaged
binary used for timestep refinement. The first arm of the paired native
hook/output check has terminated with native exit code 201 after one accepted
increment; the paired check has not passed.
The [paired input fixture](hypotheses/evaluation-resume-2026-09-24/dependent-residual-native-check-attempt01/README.md)
is frozen for that check. Parent comparison confirms identical eight-file
arms, unchanged model includes and amplitude table, and only the shortened
0.0005 s horizon plus pivot-force and stress output requests. Its native
accepted-first-increment output comparison and dependent-residual reconstruction
are now complete within the bounded scopes below.
The parent prepared separate fresh upstream and instrumented run folders
with the same eight pinned inputs. Parent review caught and corrected a
stdout-log naming mismatch before execution; all eight focused tests pass.
The [readiness record](hypotheses/evaluation-resume-2026-09-24/dependent-native-parent-readiness-attempt01.json)
binds the corrected launcher, tests, inputs and both binaries. The
[unmodified upstream arm](hypotheses/evaluation-resume-2026-09-24/dependent-native-upstream-attempt01/execution.json)
launched first, with four-CPU/thread controls, 10 GiB and an 1800-second bound.
The source-built executable reports one CPU for SPOOLES factorization;
the configured controls do not imply four-thread factorization. The
instrumented arm was prepared with the identical inputs. The
[independent launcher review](hypotheses/evaluation-resume-2026-09-24/dependent-native-launch-review-attempt01/independent-review.md)
passed within its stated scope; the parent also observed both actual mounts
as bind mounts. The [parent terminal validation](hypotheses/evaluation-resume-2026-09-24/dependent-native-upstream-parent-review-attempt01/parent-terminal-validation.json)
verified both terminal bind mounts and all eight input and nine output hashes.
The run lasted 649.653 seconds without a timeout or memory exhaustion. After
accepting increment 1 in 23 iterations, it attempted a remaining 5e-10 s
increment below the 1e-6 s minimum and failed. Parent source inspection finds
the end-of-step negative-pressure cleanup scheduled that increment after
acceptance: the reported pressure ratio is -0.2665078, below the -0.05 trigger.
This is not an initial timestep clamp. Accepted and rejected fields share the
rounded 0.0005 s timestamp; extraction must distinguish their step/increment
identities. Under a separate [diagnostic readiness decision](hypotheses/evaluation-resume-2026-09-24/dependent-native-instrumented-parent-readiness-attempt01.json),
the unchanged instrumented arm terminated with code 201 after 650.025 seconds,
following the same accepted first state and failed cleanup attempt. Parent
[terminal validation](hypotheses/evaluation-resume-2026-09-24/dependent-native-instrumented-parent-review-attempt01/parent-terminal-validation.json)
verified all eight input and ten output hashes and both actual bind mounts.
Its LOG, STA, CVG and CEL files exactly match the upstream files; all six
accepted FRD field blocks are also byte-identical. Removing only the 350
source-defined diagnostic headers and their numeric rows leaves the full
legacy DAT byte-identical as well. The source-bound
[endpoint review](hypotheses/evaluation-resume-2026-09-24/dependent-native-endpoint-review-attempt01/source-bound-review.md)
finds no barrier to the bounded accepted-state comparison. The original
whole-run success gate remains failed. The
[accepted-increment comparator](hypotheses/evaluation-resume-2026-09-24/dependent-residual-native-check-attempt01/comparison-adapter-attempt01/accepted-inc1-comparison.json)
now verifies all six FRD fields, 105 legacy contact reports, 315 angular
records, 35 energy records and the exact hook identities for increment 1.
Parent replay and [independent review](hypotheses/evaluation-resume-2026-09-24/dependent-residual-native-check-attempt01/comparison-adapter-attempt01/independent-review.md)
reproduce its parsed report; all six focused tests pass. JSON key ordering
varies, and the review separately records the imported parser hash. Coverage
does not establish the added energy records' equivalence to global contact
energy; that accounting remains under investigation. Runtime, full-step,
trajectory and mechanics gates stay false. Native
input parsing warns that the `ELSET` selector on `*EL FILE` is unrecognized;
the accepted stress field contains 116162 nodal records, and the selector
must not be claimed as honored. The frozen fixture remains unchanged.
The [dependent-node mass-row extraction](hypotheses/evaluation-resume-2026-09-24/dependent-residual-mass-rows-attempt01/README.md)
completed in 1.619 seconds using one CPU. It prepares 21 scalar rows from
60 bolt elements with the native-reference four-point rule. Five synthetic
postprocessor tests pass; its independent review found no sign or
support-coverage blocker. The first measured hook has 24 MPC rows and 337
exact acceleration-node identities at step 1/increment 1, time and timestep
0.0005 s. Parent authenticated its native provenance separately, then ran the
[residual reconstruction](hypotheses/evaluation-resume-2026-09-24/dependent-residual-first-state-attempt01/README.md)
in 1.519 seconds using one CPU. All 24 components were computed and the
reconstructed mass rows match the earlier reviewed extraction. The independent
arithmetic review recomputed all 24 components exactly; full body/wrench
accounting remains pending. These
constraint components are not convergence-error measures or joint acceptance.
The [first-state contact-output audit](hypotheses/evaluation-resume-2026-09-24/first-state-contact-output-audit-attempt01/README.md)
now binds all 315 angular records and 35 per-pair energy records. Parent replay
reproduces the final report exactly. Its force decomposition, action/reaction
and pair-moment identities pass the stated output-arithmetic bounds. The
per-pair energy sum is 3.478603645e-11 N mm, while the native total is
1.091530e-9 N mm; their disagreement exceeds the print bounds. The displayed
CELS-row sum agrees with the native total at its printed precision. These
terms must not be added together. Source review identifies two distinctions
requiring actual point-level evidence: geometric initial-contact offsets and
compact-element versus integration-point energy-array indexing. The separate
[point-map output derivative](hypotheses/evaluation-resume-2026-09-24/contact-energy-point-map-attempt01/README.md)
has passed independent source review, the actual compiled C emitter fixture,
and the actual Fortran printer fixture. Removing only its new printer tags
reproduces the prior fixture output byte for byte. The full diagnostic binary
has built successfully; no solver mechanics or reviewed geometry has changed. The independent audit review
reproduces the raw-record arithmetic, including closure using formatted-field
rounding bounds alone. The parent launched the
[point-map trajectory](hypotheses/evaluation-resume-2026-09-24/dependent-residual-contact-trajectory-run-attempt01/preparation.json)
at 17:08 UTC on September 25 after freezing all eight inputs, the executable,
and its source index. The live container uses four CPUs, a 10 GiB limit, no
network and a verified read-only executable bind. Its target is the first
cleat-bolt/bore contact transition plus one complete following accepted state;
a numerical defect established by the point evidence may stop it earlier.
The parent stopped the run after its first accepted state at 0.0005 s,
following 23 iterations. Its 104,244 point rows show a native-law/writer energy
sum of 3.478603644582e-11 N mm, versus 1.091529615022e-9 N mm in the compact
reader slots; all point writer and reader addresses differ. This supports a
reader-addressing defect. The [point-map audit](hypotheses/evaluation-resume-2026-09-24/contact-energy-point-map-analysis-attempt01/README.md)
now joins all 104,244 C and Fortran points uniquely, with no missing records.
Native and printer clearances, pressures and areas agree at printed precision;
initial-clearance offsets do not explain this state's energy discrepancy.
The compact report and parser are frozen, four focused tests pass, and final
independent audit review is underway. The energy totals also enter native timestep checks, so this
requires a separately reviewed source correction before interpreting further
response. The [terminal verification](hypotheses/evaluation-resume-2026-09-24/dependent-residual-contact-trajectory-parent-terminal-verification-attempt01.json)
confirms all eight input hashes, all eleven output hashes and the executable
are unchanged. Native code 137 reflects the recorded parent stop after
674.106 seconds, not OOM. The cleat-bore-transition target was not reached;
the early-stop numerical-defect clause was used. No joint is accepted.
A separate build review also found that the custom source Makefile omitted
`-DUSE_MT=1`, compiling out multithreaded SPOOLES factorization despite the
four-thread environment. The installed backend has the MT symbols; a clean,
separately pinned threaded build and matched numerical comparison are being
prepared without changing the preserved serial run.
The [full physical-node acceleration proposal](hypotheses/evaluation-resume-2026-09-24/all-physical-acc-output-proposal-attempt01/README.md)
is separate from the reader correction. Its actual compiled C emitter passes
a fixture using the pinned 57,643-element connectivity: all 116,162 physical
node triples are emitted correctly in two states, duplicate calls are
suppressed, invalid node maps and non-finite physical accelerations are
rejected, and source arrays remain unchanged. The precise output is needed
because the [first-state angular reconstruction](hypotheses/evaluation-resume-2026-09-24/first-state-global-angular-diagnostic-attempt01/README.md)
from rounded FRD fields has an uncertainty bound much wider than the measured
residual. That reconstruction is weak consistency evidence, not an accepted
angular-balance check. Full binary integration and native validation of the
new acceleration output remain pending.

The [static-q rank disposition](hypotheses/evaluation-resume-2026-09-24/static-q-rank-disposition-attempt01/README.md)
and independent review rule out using the prescribed internal cleat movement
as a static response shortcut. Its optimistic closed-contact rigid screen
still has 51 null directions with that control, at the stated 1e-10 relative
threshold; nearby-threshold sensitivity preserves the no-go conclusion. This
is not a count of the current native tangent's complete nullspace. The
[reduced lateral-stiffness source disposition](hypotheses/evaluation-resume-2026-09-24/reduced-lateral-stiffness-source-disposition-attempt01/README.md)
has also passed independent review. It supports an explicitly conditional,
historical-EC5 post-seating service-slip sensitivity at each physical bolt
axis, with density and modeled clearance kept explicit. It supplies neither
a physical stiffness bound nor axial engagement, strength, or a complete
current-joint response, and is not added to the existing solid contact model.

## Current evaluation checkpoint, September 24 evening

The owner has reviewed `led-clearance-2x6-runner-seated-blocks-v1` and explicitly
resumed evaluation with Luna/max agents. This supersedes the viewer-phase pause
and the historical layout counts below. The current model has 24 blocks in
seven designs, 92 candidate bolt axes, 66 panel/kicker axes (58 fixed and eight
recorded moves), and twelve starting frame-bolt arrangements. Geometry review
is permission to evaluate, not structural acceptance. The parent owns frozen
inputs and serialized native execution. Current evidence is collected in the
[evaluation-resume packet](hypotheses/evaluation-resume-2026-09-24/README.md).
The selected angle-frame and historical evidence remain preserved.

Current preparation now includes the complete 50-member timber/panel contact
graph, an independently audited ordinary-joint mesh, its contact classification
and material mapping, and all 92 candidate axial hardware-operation screens.
The four nut-slide and two nut-washer-slide overlaps now have bounded local
captured-nut alternatives recorded in the current access screen. Actual tools,
capture, reverse assembly, and thread compatibility remain separate. The
[corrected retained-bolt screen](current-retained-access.md) separates temporary
tool and hold-projection envelopes from installed obstacles. Eight bolt
withdrawal paths clear their modeled obstacles; all four lumber-leg paths
intersect modeled LED wires. The [staging review](current-retained-wire-sequence.md)
shows why the existing pack-2/3 hypothesis clears only the right-side blocker.
Its completed lower-bound screen removes only the two implicated wire spans
from the exhaustive hit maps: all 24 component/direction checks then clear.
This establishes which modeled obstacles must move, not a physical service
sequence. Connectors, attachments, slack, real tools and handling remain open.
The parent has now exported and hash-verified the [D6 geometry bundle](hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/parent-export-attempt04/brep-export/manifest.json):
20 current timber members, 60 physical retained-bolt roles and 131 modeled
wires, totaling 211 STEP files. This preserves the reviewed model and only
supplies inputs for individual-member motion checks; no transport path or
staging/support operation is accepted by the export. Independent export review
confirms the frozen summaries for all 16 finished members and the source
identity complement for the other four. Parent STEP readback also verifies
all 211 shapes are valid and preserve solid counts, volume, bounds and center
of mass within declared serialization tolerances; this is not Boolean
shape-equivalence or member-motion evidence. Earlier export failures
remain preserved, including the unstable floating-point shape-fingerprint
comparison that was replaced with a single source extraction under frozen
source, inventory and runtime-module bindings.
The first individual-member check now has an
[exact left-leg translation result](hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-attempt02/parent-run-attempt02/report.json).
The original convex hull intersected the base-floor member because it filled
the leg recess. A guarded source-plus-leading-face sweep preserves that
recess and reports no modeled intersection above 1e-6 mm³ over the full
62.468 mm outward translation. It is contained in the original hull, transferring the other
189 obstacle clears. This assumes the stated prior removals, establishes no
positive clearance margin, and leaves support, handling and the complete
sequence open. The [independent motion review](hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-attempt02/independent-review.md)
now supports that bounded result. A separate parent record adds the observed
post-run package versions without claiming a pre-execution environment freeze.
The separate [right-leg screen](hypotheses/evaluation-resume-2026-09-24/current-retained-bolt-access-attempt01/member-motion-right-attempt01/README.md)
and independent review also pass the same bounded overlap check for its own
62.468 mm +X path. Its dependencies and all boundary faces were checked
independently; no mirror equivalence was assumed. Both leg results leave
positive margins, temporary supports and a complete removal sequence open.

The [current midpoint CAD screen](hypotheses/evaluation-resume-2026-09-24/current-midpoint-clearance-attempt03/report.json)
has completed on the unchanged live model. It retains the historical 491
hypothetical neighboring hold/LED sites and includes the current G2 LED datum
shift. Its obstacle scope
is 904 physical or axis-envelope shapes: 44 timber solids, 520 candidate and
retained hardware components, 66 screw envelopes, 142 T-nuts and 132 LED
bodies. Temporary tool/withdrawal and hold-projection envelopes are excluded;
wires and plywood remain outside this historical-comparison scope. Timber
intersects 14 of 120 horizontal LED midpoints, 21 of 121 vertical LED
midpoints, 15 of 120 horizontal T-nut midpoints and one of 121 vertical
T-nut midpoints. None of the nine horizontal kicker midpoints has a modeled
obstacle hit. No tested site intersects structural hardware. All 121 vertical
sites in each main-panel family overlap existing hold or LED geometry, a
separate issue from timber clearance. The
[independent review](hypotheses/evaluation-resume-2026-09-24/current-midpoint-clearance-attempt03/independent-review.md)
confirms source pins, all site/group counts and the declared screen limits.
The [reviewed static map](hypotheses/evaluation-resume-2026-09-24/current-midpoint-clearance-map-attempt01/README.md)
visualizes all 491 sites without rebuilding CAD. Its mutually exclusive
categories are 44 timber-flange hits, seven timber rear-projection-only hits,
220 existing-body-only overlaps and 220 sites with no screened hit. The
exported image includes its provisional-probe and excluded-scope limits.

Attempt01 stopped before intersections because the panel-axis helper received
the snapshot instead of its required revision report; an actual-artifact
regression now covers that boundary. Attempt02 completed; attempt03 corrects
only report-location metadata, and all geometry findings match exactly.
This is a bounded hypothetical-placement screen, not compatibility with a
future manufacturer's layout or approval to change panel holes.

The published [ordinary-patch resistance preflight](hypotheses/evaluation-resume-2026-09-24/ordinary-patch-resistance-preflight-attempt01/README.md)
records eight conditional washer-to-wood bearing references and both 33 mm
bolt-group pitches. Its six focused tests pass, and the parent reproduced the
reviewed result exactly. The references are not joint capacities and are not
summed. The separate
[finished-member query](hypotheses/evaluation-resume-2026-09-24/ordinary-finished-end-edge-query-attempt01/query.json)
completed 96 exact finite-face and solid-interval rays across three axial
stations per bolt receiver in 2.371 seconds. It confirms 43.35 mm as the
shortest sampled square-cut grain-direction end distance for the cleat's
rail-bolt group and records internal bore interruptions separately. The
[summary](hypotheses/evaluation-resume-2026-09-24/ordinary-finished-end-edge-query-attempt01/README.md)
separates the angled principal-foot boundary from square-cut end distances.
Only under the stated softwood, nominal-bolt and pure parallel-tension case
does the shortest end give the preliminary per-axis ratio 0.9753; no
connection factor, failure or required geometry change is assigned. The
smallest sampled cross-grain edge is 27.9 mm. The
[independent review](hypotheses/evaluation-resume-2026-09-24/ordinary-finished-end-edge-query-attempt01/independent-review.md)
passed after correcting the conditional NDS wording. Fresh signed actions,
tolerance and continuous through-thickness extrema remain outside this
discrete geometry check. The exact seven-file query/review bundle is published
as `81268185ed3e37200f5db02a8ae55dc26156bdb9`; its tracked dependency closure
and all 68 upstream geometry-source hashes were verified before publication.

The [native reference-tangent preflight](hypotheses/evaluation-resume-2026-09-24/ordinary-native-preflight-attempt04/README.md)
completed in 38.126 seconds after an algebraically equivalent MPC dependency
change avoided an earlier 10 GiB memory failure. It produced 334,908 equations.
A source-bound matrix witness supports one specific cleat slip direction at
the reference state, consistent with the earlier rigid-motion preflight. Six
assembled mass checks pass, including exclusion of nut display-volume mass.
This does not establish total nullity, every contact active state, a unique
initial stiffness, or a loaded joint response. The initial static
force-controlled sweep remains stopped. The immediate task is a separately
bounded clearance-seating response with explicit engagement, inertia, and
output-accounting assumptions. All 47 structural/layout/hardware criteria
remain pending; no current complete-frame load case has run.

The first [executed gauge-free motion pilot](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-pilot-attempt02/README.md)
reached its 600 s runtime bound without a converged increment. Twenty trial
iterations are recorded; the contact count continued changing while the
maximum displacement increment was approximately 1.7e-8 mm. The launcher
stopped the run, giving return code 137 after its stop grace; this was not an
out-of-memory termination. All frozen inputs remained unchanged. A separate
[larger-initial-increment pilot](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-pilot-attempt03/README.md)
retains the same physical/load inputs and adaptive cutbacks, with four solver
threads. Its execution record governs its status. Neither trial iterations nor
successful matrix factorization establish a loaded-joint response or capacity.

The larger-initial-increment pilot has produced its first converged increment
at 0.0025 s after thirteen iterations. An
[immutable live-output snapshot](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-first-increment-snapshot-attempt01/snapshot.json)
preserves that result separately from later trial iterations. The monitored
relative displacement is 6.989744e-6 mm; the native energy-balance discrepancy
is 0.032926%. Work, momentum, source/ownership and time-discretization checks
remain necessary. This first increment does not close the requested 0.025 s
pilot, take up the bolt-hole clearance, establish quasistatic stiffness, or
resolve any of the 47 structural/layout/hardware obligations.
The [terminal record](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-pilot-attempt03/terminal-outcome.md)
now confirms the runtime stop during the second increment, with only that one
complete sample. The [independent first-point accounting audit](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-first-increment-audit-attempt01/README.md)
now reproduces the serialized-load work and all energy terms within printed
precision. Its reconstructed discrepancy is 0.0329271%; this is discrete
Newmark endpoint work, not continuous-ramp path work or time-accuracy evidence.
The [cleat momentum audit](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-first-momentum-audit-attempt01/README.md)
also reconstructs the first point from the frozen displacement/velocity fields.
Its native four-point C3D10 mass gives N momentum 2.39374998e-6 N·s,
consistent with the discrete applied impulse 2.39375e-6 N·s to printed
precision. The exact piecewise-linear ramp integral is only 1.66475e-6 N·s:
the coarse first increment overestimates that impulse by approximately 43.8%.
This separates correct discrete accounting from unresolved time accuracy.
Individual contact impulses, later response and clearance seating remain open.

The [whole-patch momentum audit](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-global-momentum-audit-attempt01/README.md)
now integrates all fifteen positive-density owners (11.775601 kg), with
zero-density nut carriers kept separate. Its kinetic energy agrees with the
native printed value to 1.7e-8 relative. Linear and angular momentum residuals
fall within propagated FRD print-resolution bounds; this does not prove
exact solver or constraint closure. An independent origin-shift identity
check closes to 3e-20 N·mm·s after correction of a generator-consumption bug
in the audit's vector summation. The regression covers all three components.

A separately frozen [first-point checkpoint](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-checkpoint-attempt01/native-readiness-review.md)
retains all twelve physical/load artifacts and requests iteration diagnostics
and a step-end restart. Its execution record governs run status. The shorter
step and total-time amplitude require endpoint comparison before reuse; this
checkpoint does not replace the 0.025 s pilot or establish clearance seating.
Its [terminal outcome](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-checkpoint-attempt01/terminal-outcome.md)
is a runtime stop after 34 recorded trial iterations, with no converged sample
and no restart file. Frozen inputs and terminal outputs retain their recorded
hashes. The saved iteration/contact files now support diagnosis before another
run; trial displacement corrections alone are not convergence evidence.

The [contact-iteration audit](hypotheses/evaluation-resume-2026-09-24/ordinary-contact-iteration-audit-attempt01/ordinary-contact-iteration-audit.md)
maps generated contacts to the original owner pairs. All 34 convergence-file
counts match their contact-file groups; an extra group without a convergence
row remains unconfirmed. Confirmed switching occurs on the three timber-face
and sixteen bolt-seat pairs. All sixteen bolt-bore/washer-bore pairs remain
open in these records. These are generated contact identities, not measured
pressures or physical chatter.
The [trial-motion audit](hypotheses/evaluation-resume-2026-09-24/ordinary-iteration-motion-audit-attempt01/README.md)
finds 34 complete displacement fields: q drifts on both loaded members and
finishes 11.921% above pilot03's first accepted point. The last five trials
increase monotonically, so their smaller local range does not show settling.
Neither audit supports relaxing convergence merely to accept a trial field.

A [longer bounded pilot](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-pilot-attempt04/README.md)
keeps attempt03's physical inputs, time parameters and convergence controls,
adds iteration diagnostics, and permits 2,400 seconds of serialized execution.
The [native recovery review](hypotheses/evaluation-resume-2026-09-24/native-contact-recovery-review.md)
identifies a default retry at iteration 60, which earlier runtime limits did
not reach. It temporarily reduces contact stiffness but requires reconvergence
at the original stiffness. Whether that path occurs or succeeds must be read
from the actual execution; it is not presumed from the longer allowance.
The live run has accepted its first increment after eight iterations, with
q = 6.94490490e-6 mm (approximately 0.64% below pilot03). During the second
increment, contact-impact checks caused a retry after 28 iterations and the
log records a factor-100 contact-stiffness reduction. This occurred before
the iteration-60 slow-convergence fallback. It remains a trial recovery.
An [immutable recovery prefix](hypotheses/evaluation-resume-2026-09-24/native-contact-recovery-observation-attempt01/README.md)
now records restoration after iteration 10 of the second attempt, followed by
another impact rejection at iteration 11. The third attempt applies a
quarter-sized time increment. Restoration is observed; accepted convergence
at original stiffness is not established by that prefix.
The [subsequent accepted-increment prefix](hypotheses/evaluation-resume-2026-09-24/native-contact-recovery-observation-attempt02/README.md)
does establish recovery: attempt 3 restores original stiffness at iteration
7 and converges at iteration 20. Two later increments converge in 12 and 7
iterations, reaching 0.002733122 s with q = 8.42013648e-6 mm. These four
accepted increments remain an early motion diagnostic, not clearance seating
or a completed response. The execution record governs terminal status.
The [terminal record](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-pilot-attempt04/terminal-outcome.md)
now confirms a runtime stop after 2,408.048 seconds, with eight accepted
increments ending at 0.003129826 s and q = 1.19207456e-5 mm. Increment 9
remained a trial. All fourteen frozen inputs and twelve recorded outputs
match their hashes. Native recovery succeeded; the requested 0.025 s response
and clearance seating did not complete.

A [separate scaled seating input](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-seating-100n-attempt01/README.md)
is frozen but unexecuted. It multiplies all 662 existing CLOAD components
exactly by 100 and preserves all other cards, with the original unit weights
still defining q. The short pilot reaches 15.625 N per side, not its 100 N
full-ramp reference. This is preparation for a bounded clearance-onset
diagnostic; execution remains serialized and time accuracy, transfer and
engagement evidence are required before quantitative interpretation.
A [ramp-knot-aligned derivative](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-seating-100n-aligned-attempt01/README.md)
now adds 25 time points and applies their schedule to all 41 output requests.
All physical inputs, scaled forces and q weights are preserved. Three focused
tests pass. After terminal disposition of pilot04 and independent input and
timing review, the parent launched this case with four threads and a
7,200-second runtime bound; its execution record governs status. Native
integration will land on ramp knots, but output/stop monitoring covers requested points rather than
every adaptive substep. Exact forcing impulse does not imply time-accurate
motion or a complete substep work history.
Its [immutable first-knot snapshot](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-aligned-first-knot-snapshot-attempt01/README.md)
records convergence at 0.001 s after 25 iterations, with q = 2.31868671e-5 mm.
The actual applied force is 0.0298 N per side, and the prescribed first-knot
impulse is 1.49e-5 N·s under both exact linear-ramp and endpoint-trapezoid
integration. The native energy discrepancy is 1.230541%; correct prescribed
impulse does not close that discrepancy or establish time-accurate response.
The [cleat momentum audit](hypotheses/evaluation-resume-2026-09-24/aligned-first-knot-momentum-audit-attempt01/README.md)
now gives 1.4900000213e-5 N·s along the applied direction, within
2.13e-13 N·s of the prescribed impulse. Its mass-weighted COM displacement
is 1.33467773e-5 mm, distinct from q. The optional equal-node rigid-fit split
is a kinematic diagnostic, with a principal fit condition estimate of 8.8e4; it does
not establish whole-patch equilibrium or a physical contact-force split.
The [accepted-history audit](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-history-audit-attempt01/README.md)
independently reconstructs discrete work at all eight accepted pilot04 states
and the aligned first knot. Each agrees with native external work within the
combined print bound. The parent separately checked cumulative work and exact
piecewise-linear ramp integrals; seven focused tests and Ruff checks pass.
Missing accepted displacement samples make work unavailable rather than being
bridged. These accounting checks do not close the energy discrepancy.
The [first-knot contact audit](hypotheses/evaluation-resume-2026-09-24/aligned-first-knot-contact-audit-attempt01/README.md)
finds 33 complete CF/CFN/CFS triplets, part of pair 034's CF report, and no
pair 035 report. Fifteen observed bore CF vectors are zero; fourteen complete
bore triplets also report zero area. The snapshot cannot establish all sixteen
bore states. Missing fields remain missing, distinct from present NaN
centroid/normal values at zero force. No complete body reaction or contact
impulse is inferred from these single-state slave-side force reports.
The [aligned baseline terminal record](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-seating-100n-aligned-attempt01/terminal-outcome.md)
now records a parent-directed early stop at 2333.59 seconds, before the
7200-second maximum. Seven increments reached 0.00103451 s, with four rejected
attempts. The launcher reports `process_failed`/137 because the parent stopped
the container; this was not the configured timeout or evidence of an OOM.
All eighteen inputs and thirteen recorded outputs retain their hashes.
Only the first output knot has monitor fields, so the terminal history audit
correctly withholds full work reconstruction for the six unsampled accepted
substeps. The terminal DAT did not recover the missing contact tail.
The [penalty companion input review](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-seating-100n-aligned-k1e4-attempt01/parent-input-review.md)
verifies a frozen K=10000 N/mm³ child against that K=100000
aligned baseline. Exactly one native scalar changes; all 35 contact-pair
records, geometry, forces and timing are preserved. Four focused tests pass,
and the parent independently checked all 23 artifact hashes. This is a
numerical sensitivity input, not an accepted contact law or a changed frame.
After terminal hash verification of the original branch, the parent launched
the child with a 2400-second maximum, four threads and the same 10 GiB limit.
Its [readiness review](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-seating-100n-aligned-k1e4-attempt01/native-readiness-review.md)
limits the intended result to matched-state numerical comparison. The child's
execution record governs status; the original branch remains its reference.
The child has now accepted its first 0.001 s increment after 26 iterations.
Its [immutable snapshot](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-aligned-k1e4-first-knot-snapshot-attempt01/README.md)
supports a [matched motion/energy comparison](hypotheses/evaluation-resume-2026-09-24/aligned-first-knot-penalty-motion-comparison-attempt01/README.md).
Although q changes only 4.19%, the complete loaded-node displacement and
controller-rotation field differences are 14.90% and 23.85% of their baseline
infinity norms, exceeding the pre-interpretation numerical screens. Native
energy discrepancy increases from 1.230541% to 3.905511%. The lower penalty
therefore cannot be treated as an interchangeable convergence shortcut.
These are numerical sensitivity findings, not failures of adopted structural
criteria. The comparison now derives the work coefficient from the hash-checked
actual CLOAD and ramp cards; its independent review confirms unchanged results.
The separate [cleat momentum comparison](hypotheses/evaluation-resume-2026-09-24/aligned-first-knot-penalty-momentum-comparison-attempt01/README.md)
uses one shared C3D10 mass operator for both first-knot states. Its full XYZ
momentum difference is 5.2348% of the baseline infinity norm, below the declared
10% screen. The parent verified snapshot hashes and comparison arithmetic.
This is one owner's momentum comparison, not complete-joint equilibrium;
contact and other-owner comparisons remain separate.

The K=10000 companion is now [terminal at its runtime bound](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-seating-100n-aligned-k1e4-attempt01/terminal-outcome.md):
17 accepted 0.001 s increments reach 0.017 s, with no rejected attempts.
All 23 frozen inputs and 14 outputs match their recorded hashes. Final q is
0.4670346 mm. The [terminal work audit](hypotheses/evaluation-resume-2026-09-24/ordinary-transient-history-audit-attempt03/README.md)
has every accepted monitor and reconstructs 2.4060944693 N·mm; all 17
cumulative work comparisons match native output within the declared print
bounds. This closes recorded work accounting for that interval only, not
time accuracy, the requested endpoint, contact equilibrium, or a joint gate.

The independently reviewed [first-knot contact comparison](hypotheses/evaluation-resume-2026-09-24/aligned-first-knot-penalty-contact-comparison-attempt01/README.md)
flags 18 matched CF vectors and the corresponding separate CFN vectors under
the numerical 10% change screen. CFN is not added to CF. Partial pair records
remain explicit. This reinforces the local sensitivity finding; it is not a
failure of an adopted structural criterion.

The parent's small [static prescribed-q fixture](hypotheses/evaluation-resume-2026-09-24/prescribed-q-native-static-attempt02/terminal-outcome.md)
verifies the displacement mapping and confirms zero raw RF at the non-element
control node. The [implicit dynamic fixture](hypotheses/evaluation-resume-2026-09-24/prescribed-q-native-dynamic-attempt01/terminal-outcome.md)
reproduces expected U/V but reports zero native kinetic energy and external
work on its SPRING2/MASS model. Source review must resolve that output scope
and exercise inertial equilibrium before a large prescribed-q derivative.
These are implementation findings, not current-joint response acceptance.

The subsequent [finite-actuator validation](hypotheses/evaluation-resume-2026-09-24/spring-actuator-validation-attempt01/README.md)
resolves the scalar dynamic implementation path. Both physical mass
coordinates remain independent; only a massless q proxy is eliminated, and
a separate spring joins it to the prescribed target. The coarse three-step
case matches discrete Newmark but has severe continuous-time error. Refining
to 300 steps at 0.0001 s reduces maximum sampled q and controller-force errors
to 0.01171% and 0.04579% of their exact continuous response infinity norms.
Physical momentum and reconstructed controller work versus physical kinetic,
joint spring and actuator spring energy close within output precision in all
states. The [source/readiness review](hypotheses/evaluation-resume-2026-09-24/prescribed-q-inertial-fixture-readiness.md)
confirms this bounded scalar method and its limitations. The target's RF is
observable actuator force; actual q, target q and actuator energy remain
distinct. Current-joint actuator scale, timestep, contact response and work
accuracy still require their own frozen case and evidence.

Independent fixture review identified the prescribed massless target velocity
as a separate output interpretation. Its native V follows the Newmark
displacement recurrence, not the continuous ramp slope. The corrected audit
checks that recurrence with propagated printed-displacement bounds at all
303 states. Physical motion, momentum and target-displacement work results
are unchanged; target V contributes neither mass energy nor work.

The [terminal contact audit](hypotheses/evaluation-resume-2026-09-24/aligned-k1e4-terminal-contact-audit-attempt01/README.md)
now covers the completed K1e4 run. The first sixteen accepted states have all
35 force-report triplets; the last accepted state has 33 complete triplets,
one partial CFS record and one absent pair. All 271 available bore CF reports
have zero area and force. The missing final bore report remains unknown.
No sampled bore bearing has been observed, and displacement alone does not
establish whether clearance was taken up between output states.

The [current actuator scale estimate](hypotheses/evaluation-resume-2026-09-24/current-finite-actuator-scale-attempt01/current-finite-actuator-scale.md)
uses the current cleat/principal masses to propose a numerical 200 N/mm drive,
1.15 mm target over 0.1 s and 0.0005 s increment. Its 0.521082 kg reduced mass
is a two-member translation-only estimate, omitting rotations and other joint
parts. It supports selecting a diagnostic scale, not a physical frequency
bound, contact stiffness, accepted timestep or joint capacity. The native
target will use piecewise-linear samples of the underlying quintic ramp.

The [first current finite-actuator diagnostic](hypotheses/evaluation-resume-2026-09-24/ordinary-finite-actuator-input-audit-attempt02/README.md)
has now started after 29 focused tests and the independent actual-input audit
passed. Attempt02 preserves the reviewed physical mesh, materials and contact
inputs, replaces the 662 CLOAD components with one finite spring and a
massless dependent proxy, and records every accepted increment with a single
physical/driver node-file union. The source and child retain 23 and 12 verified
input pins respectively. Its [execution record](hypotheses/evaluation-resume-2026-09-24/ordinary-finite-actuator-k1e4-attempt02/execution.json)
governs current status. Five increments through 0.0025 s have been accepted
at this checkpoint, with iteration counts 22, 7, 6, 6 and 8 and no rejected
attempts. An
[immutable first-state snapshot](hypotheses/evaluation-resume-2026-09-24/ordinary-finite-actuator-first-knot-snapshot-attempt01/snapshot.json)
preserves the initial accepted result. Its proxy displacement is
6.862260e-8 mm, target displacement 1.426740e-6 mm and target RF
2.716235e-4 N, consistent with the serialized 200 N/mm spring relation.
The [first-state work audit](hypotheses/evaluation-resume-2026-09-24/current-finite-actuator-work-audit-attempt01/README.md)
reproduces the emitted-MPC coordinate, target reaction and discrete
target/spring/proxy work split within propagated output-rounding bounds.
It does not assign an initial physical/contact energy, and the native global
external-work field is not the prescribed-target work oracle. A
[five-state immutable prefix](hypotheses/evaluation-resume-2026-09-24/ordinary-finite-actuator-progress-snapshot-attempt02/README.md)
supports the completed five-state work and contact audits without reading
changing native files. The corrected [work audit and independent review](hypotheses/evaluation-resume-2026-09-24/current-finite-actuator-work-audit-attempt03/independent-review.md)
reproduce all five work identities within output-rounding bounds and reject
gaps in accepted increment numbers. The [independent contact review](hypotheses/evaluation-resume-2026-09-24/finite-actuator-progress-contact-audit-attempt02/independent-review.md)
verifies all 521 observed headers against the frozen pair/request order.
All 35 pair triplets are complete through 0.002 s; the 0.0025 s tail is
partial and remains unknown. All reported bore CF vectors and areas are
zero in this prefix; that does not establish physical gap closure or seating.
This is not bore seating or joint acceptance. Parent execution uses four
solver threads, a 10 GiB memory limit and a 10,800 s bound. Geometry and all
47 criterion statuses are unchanged.

A later [log observation](hypotheses/evaluation-resume-2026-09-24/native-stiffness-adaptation-observation-attempt01/snapshot.json)
records seven accepted increments through 0.0035 s. Increment seven required
a retry: the native solver temporarily reduced constant contact stiffnesses
and logged their restoration before accepting its second attempt. The same
capture ends with an unsuccessful first attempt at increment eight; subsequent
status belongs to the live execution record. Trial contact softening must not
be mistaken for an accepted change to the prescribed material/input penalty.
The [rounding-metadata erratum](hypotheses/evaluation-resume-2026-09-24/ordinary-finite-actuator-input-audit-attempt02/metadata-erratum.md)
also records a sign error in one diagnostic metadata field. The emitted
equation and running input are unchanged; the actual-input and work audits
independently recover the signed weights. Future producer metadata is fixed
in commit `3463fa513ccd00a480ef7a00d8eacbdbb3f1299c`.

The finite-actuator case subsequently ended by explicit parent stop after
2863.35 s, before its runtime bound, with nine accepted increments and seven
unsuccessful attempts. Its [terminal disposition](hypotheses/evaluation-resume-2026-09-24/ordinary-finite-actuator-k1e4-attempt02/parent-terminal-disposition.json)
binds all terminal output hashes and verifies all twelve input pins unchanged.
The [source addendum](hypotheses/evaluation-resume-2026-09-24/current-native-stiffness-adaptation-energy-addendum.md)
confirms that native `allwk` omits prescribed-target reaction work while the
contact-control path uses that term. This can bias energy-based decisions;
specific retry causality remains unproven. The fresh force-driven derivative
preserves the previous CLOADs and physical inputs, requests initial/maximum
1 ms increments and records every accepted state. Native implicit dynamics
may choose its initial increment automatically; actual accepted times govern
the audit. Removing the output time
points also removes guaranteed ramp-knot alignment after adaptive cutbacks;
actual load impulse and time accuracy must be checked rather than inherited.

An [immutable two-increment force-driven history audit](hypotheses/evaluation-resume-2026-09-24/force-every-increment-first-history-audit-attempt01/README.md)
now reproduces the native applied-work values through 0.002 s. Cumulative
reconstructed work is 1.1834758553e-5 N mm versus native 1.183476e-5 N mm;
both accepted states agree within reported output-print bounds. The scalar
force-pattern impulse is 8.9e-5 N s. The first two 1 ms intervals end at ramp
knots, so their exact piecewise-linear and endpoint-trapezoid impulses agree;
later cutbacks still need their own check. This establishes early applied-work
accounting, not a complete energy balance or accepted joint response.
The [independent review](hypotheses/evaluation-resume-2026-09-24/force-every-increment-first-history-audit-attempt01/independent-review.md)
reproduces the frozen input checks, both work comparisons and the impulse
arithmetic without discrepancies.

The [first-iteration source review](hypotheses/evaluation-resume-2026-09-24/current-every-increment-first-iteration-review-attempt01/iteration-1-review.md)
preserves an important reproducibility limit: both force-driven runs started
at 0.001 s with matching matrix/contact counts and maximum correction, but
their first residuals and subsequent contact counts differ. The old printed
zero is a residual thresholded below 1e-6; the new residual is 0.388662.
Neither an output-control effect nor parallel-order variation is established
as the cause. Close first-state monitor scalars do not establish identical
contact states or numerical paths.

The corrected [finite-actuator momentum reconstruction](hypotheses/evaluation-resume-2026-09-24/finite-actuator-momentum-audit-attempt02/report.json)
now evaluates four global intervals and three cleat intervals from the frozen
five-state prefix. All vector components lie within the [corrected output
precision bounds](hypotheses/evaluation-resume-2026-09-24/finite-actuator-momentum-audit-attempt02/rounding-bound-addendum.json)
under both distinct mass operators. The original impulse-bound formulas
omitted the time/force uncertainty product; the addendum supplies that term,
at most 2.20165e-14 N s for contact impulse. The parent independently checked
the added terms and all 42 unchanged component comparisons. The largest absolute
cleat residual is 1.92336e-11 N s; its approximately 1e-9 N s bound includes
contact-force printing and FRD binary32/decimal quantization. Ten incident
cleat interfaces enter each available balance, using CF once with the
owner-dependent sign. The final 0.002–0.0025 s cleat interval remains
unavailable because its contact tail is incomplete. The [first attempt's
parent review](hypotheses/evaluation-resume-2026-09-24/finite-actuator-momentum-audit-attempt01/parent-review.md)
records the corrected exact-time selection bug; its omitted cleat balances
are not evidence of missing physical contact reports. These are early-time
linear momentum checks, not angular balance, time accuracy, bore seating,
or joint acceptance. The [independent review](hypotheses/evaluation-resume-2026-09-24/finite-actuator-momentum-audit-attempt02/independent-review.md)
is complete and confirms the result with the separate rounding-bound addendum.

The [angular-momentum source review](hypotheses/evaluation-resume-2026-09-24/finite-actuator-angular-momentum-audit-attempt01/source-bound-readiness.md)
identifies the next missing observable. Native CF moments use the slave
integration-point positions; the master moment also needs the force-line
offset correction. The saved frictionless contact outputs do not establish
that correction or a useful bound. A compact, output-only master-wrench
instrumentation is being prepared separately from the live solver. Native
RIGID BODY equations do update with motion; the 24 authored nut-fit equations
are a distinct fixed-coefficient approximation whose current-position reaction
couple remains unquantified. Neither issue changes the earlier linear-momentum
result or establishes a structural failure. No live input or geometry was
changed to address these output gaps.

The parent captured a [twenty-state force-driven prefix](hypotheses/evaluation-resume-2026-09-24/force-every-increment-seating-prefix-attempt01/README.md)
at 12:06 UTC on September 25 while the run continued. Its status file records
20 accepted increments through 0.020 s without rejected attempts; all 27
input pins were verified before copying. The final monitor coordinate is
0.851846561 mm and maximum controller rotation is 0.000919007 rad. The changed
rotation trend motivates a direct contact audit rather than a seating claim.
The fixed DAT, log and FRD prefix supports separate work, contact and energy
reviews; non-atomic capture and partial-tail limits remain explicit. Native
contact-energy output is not yet a qualified storage-energy observable.

The resulting [contact audit](hypotheses/evaluation-resume-2026-09-24/force-every-increment-seating-contact-audit-attempt01/README.md)
finds the first nonzero bore CF vectors and positive reported areas at 0.020 s
on four cleat interfaces, WJCP_020/022/024/026. Each has complete CF/CFN/CFS;
the preceding 19 states have complete reports and zero reported bore forces
and areas. All 2,095 observed headers match their pair/request slots, and all
20 global CDIS groups match CNUM. The final nonincident washer-bore reports
034/035 remain partial/missing; they are not zero-filled. This establishes
observed contact onset in the diagnostic, not full seating or resistance.
The separate [applied-work reconstruction](hypotheses/evaluation-resume-2026-09-24/force-every-increment-seating-work-audit-attempt01/README.md)
reproduces all 20 accepted increments: cumulative work is 5.8916216504 N mm
versus native 5.891622 N mm, within its 1.32318e-5 N mm print bound. The scalar
pattern impulse is 0.07208 N s, with no skipped ramp knots in this prefix.
The [independent work review](hypotheses/evaluation-resume-2026-09-24/force-every-increment-seating-work-audit-attempt01/independent-review.md)
reproduces the source pins, all 20 projections and print bounds, cumulative
work and impulse. The [independent contact review](hypotheses/evaluation-resume-2026-09-24/force-every-increment-seating-contact-audit-attempt01/independent-review.md)
also confirms the four first bore-contact observations, complete preceding
reported zeros, exact deck/pair/request mapping, and preserved partial tail.

The [energy-prefix audit](hypotheses/evaluation-resume-2026-09-24/current-force-energy-readiness-attempt01/independent-review.md)
now matches full-set DAT internal and kinetic energies to their LOG totals
within printed precision at all 20 accepted states. A parent rerun reproduced
the complete JSON exactly. At 0.020 s the native LOG reports a −0.4650846 N mm
energy residual and 44.068010% relative balance diagnostic. Contact energy
remains unqualified: the source review identifies a conditional difference
between surface-point storage indices and compact generated-element read
indices, but the captured outputs do not prove an actual index mismatch or
explain this residual. Prepared printer diagnostics remain unapplied; they do
not change the live solver, validate its energy controller, or establish
numerical dissipation. Global and local momentum accounting across the
0.019–0.020 s contact-onset interval has now completed its first calculation.

The parent executed the [contact-onset momentum audit](hypotheses/evaluation-resume-2026-09-24/force-every-increment-seating-momentum-audit-attempt01/momentum-audit.json)
on the frozen DAT/FRD prefix with both the physical Gauss8 and reconstructed
native four-point C3D10 mass operators. All twelve global/cleat vector
components lie within their propagated print bounds. The largest global
residual is 1.35579e-8 N s; the largest cleat residual is 2.24591e-9 N s.
The ten incident cleat interfaces are complete at both endpoints. Partial
nonincident pair 034 and absent pair 035 remain unknown and are not used as
zeros. Applied impulse comes from the actual 662-term CLOAD/RAMP_N input;
there is no actuator RF in this case. The corrected bounds include the
time/force second-order product. The [independent review](hypotheses/evaluation-resume-2026-09-24/force-every-increment-seating-momentum-audit-attempt01/independent-review.md)
reproduces the actual load resultant and ramp integral, ten signed raw CF
pairs, both mass-operator results and all twelve component bounds. This does
not establish angular momentum, energy closure, time accuracy, physical
engagement, stiffness or resistance.

A later [supplemental DAT/STA/log prefix](hypotheses/evaluation-resume-2026-09-24/force-seating-contact-energy-prefix-attempt01/README.md)
preserves 26 accepted status rows and verifies that every byte covered by the
earlier twenty-state capture is unchanged. All 27 input pins still match.
It supplies the complete contact tail for the
[contact-storage upper bound](hypotheses/evaluation-resume-2026-09-24/current-force-energy-readiness-attempt01/contact-storage-bound-attempt01/contact-storage-bound.json).
All 35 pair reports are complete at 0.019 and 0.020 s. Both CDIS and CSTR have
108,297 rows at 0.019 s and 72,155 at 0.020 s, matching CNUM and mapping every row to
exactly one frozen slave surface. The pairwise bound includes half-last-digit
pressure, clearance and area margins, including the small tensile/open rows.
At 0.020 s it is 0.287187282 N mm, below the 0.46642955 N mm lower printed
bound on external work minus internal and kinetic energy. At least
0.179242268 N mm therefore remains outside that contact-storage envelope.
The original native contact term is replaced, not subtracted twice.

The parent reproduced the full result exactly and independently recomputed
the 35 pair products and energy difference; see
[parent validation](hypotheses/evaluation-resume-2026-09-24/current-force-energy-readiness-attempt01/contact-storage-bound-attempt01/parent-validation.json).
The [independent review](hypotheses/evaluation-resume-2026-09-24/current-force-energy-readiness-attempt01/contact-storage-bound-attempt01/independent-review.md)
confirms the current bound, including all 35 master/slave report identities
and the positive-area source path. The positive-area and storage interpretation
is conditional on the pinned upstream CalculiX 2.21 source semantics; that
source is not bitwise provenance for the packaged solver binary. The actual
printed fields satisfy the declared pressure/clearance law. Within this
scope, missing contact storage alone cannot close the discrepancy. This does
not identify its cause, prove numerical dissipation or establish time
accuracy. No FRD or CEL was copied, and the earlier momentum snapshot remains
its own authority. All 47 criterion statuses remain unchanged.

The independently checked [first-knot overlap screen](hypotheses/evaluation-resume-2026-09-24/aligned-first-knot-penalty-overlap-comparison-attempt01/README.md)
finds complete global CDIS blocks matching CNUM in both branches. Maximum
positive normal overlap is 2.616841e-8 mm and 2.273343e-8 mm, below the
declared numerical screen. Different active-row counts prevent pointwise
matching; this does not repair the partial pair-force coverage or cancel
the force/motion sensitivity findings.

The [engagement evidence-route clarification](current-engagement-evidence-routes.md)
separates adopted obligations from earlier method proposals. An applicable
validated analytical/numerical model can support a conditional engagement
scenario without a new per-product stiffness coupon. Existing rigid fits and
arbitrary spring-ratio sweeps are not validated physical bounds. Thread/shank
strength, complete-joint response and delivered-fit conditions remain separate.

The parent monitor now reads only each requested displacement block instead
of splitting the entire remaining contact-output history for every sample.
Seven focused tests pass, including bounded allocation with a large unrelated
contact tail. On one captured 40.3 MB live DAT string, the old and new parsers
return exactly the same seven complete observations; parsing took about
0.43 s and 0.013 s respectively. This improves monitoring overhead only.
Pilot04 retained its original loaded launcher and frozen snapshot. The later
aligned-case launch records the updated source separately.

A subsequent [incremental-monitor check](hypotheses/evaluation-resume-2026-09-24/incremental-monitor-validation-attempt02/report.json)
removes the remaining repeated whole-file reads. The launcher reads appended
bytes once, retains partial lines and monitor blocks between polls, and
detects output disappearance, replacement and size regression. Independent
review found no motion-stop regression and prompted a finite sample-time
check, now covered by tests. All 26 focused transient/history tests pass.
The 305,519,240-byte terminal DAT reproduces all seventeen recorded motion
observations exactly; the first scan took about 1.0 s and an unchanged-file
poll about 0.000093 s on this run. These are monitoring measurements, not a
solver speed claim. Earlier native executions and their launcher snapshots
remain unchanged.


The September 25 [dead-load map](current-frame-dead-load-map.md) and its
[independent review](hypotheses/current-frame-dead-load-map-review-2026-09-25.md)
reconcile the modeled inventory separately from the six climber-force cases.
The parent then extracted [778 current mass centers](hypotheses/evaluation-resume-2026-09-24/current-mass-centroids-attempt01/README.md)
from existing CAD objects without rebuilding or changing the geometry. Every
volume and mass matches the frozen weight inventory. The modeled mass is
224.420776668 kg with center (−1.644537, 697.857581, 1033.609057) mm in global
coordinates; the additional 25 kg equipment allowance has separate placement
scenarios. All 66 screw rows retain the original axis-envelope mass estimate,
and the eight moved screw centers were checked without double translation.
This is gravity-placement preparation, not support reactions or frame
acceptance. The [independent centroid review](hypotheses/evaluation-resume-2026-09-24/current-mass-centroids-attempt01/independent-review.md)
reproduces every row's mass, gravity force and moment, the aggregate center,
and all eight moved-axis centers. All 40 timber/block centers represented in
the geometry snapshot lie within their corresponding finished bounds. Exact
BRep centers were not independently re-extracted; the recorded parent CAD
read remains their geometric provenance. Reduced-model load ownership remains
open at this checkpoint.

The [mass source-to-topology map](current-frame-mass-source-topology-map.md)
now joins all 778 inventory rows to current geometry and receiver identities.
Its independent review reconciles source coverage, mass, center, gravity force
and first moments, including all 66 current screw-envelope centers. The
current 63.5 mm envelopes remain distinct from the inventory's historical
50.8 mm analysis field. Per-role mass carriers are one possible route;
documented aggregation or condensation is allowed when it preserves the
behavior required by the intended analysis. The map implements no solver
attachment or response. Its six-file reviewed chunk is published as
`9079befdf333d8089d016c81ac52a9860520c715`.

Source commit: `df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb`

Candidate: `compact-floor-flush-wood-joints-development`

Selected authority remains `current-candidate.json`. Preserved barrel authority
remains `barrel-nut-candidate.json`.

## September 24 execution follow-up

The corrected [access-relief study](hypotheses/wj24-access-relief/README.md)
now records nine connector-only variants with retained local contact and
washer-seat support. It exposes local section losses and separates nominal
LED movement from enlarged clearance envelopes. Wire handling, manufacturing
tolerances, and strength remain unresolved; no relief is selected for cutting.

The current WJ24 [representative STEP export](hypotheses/wj24-patch-reconciliation/README.md)
has completed. Its new five-body mesh contains 89,743 nodes and 46,629 C3D10
elements; independent audits are in progress. The earlier WJ16 mesh and its
surface classification remain historical inputs, pending explicit current
geometry and hardware reconciliation. No native structural response has run.

The complete-layout tool diagnostic screened 100 ordinary stacks and retained
four backer stacks as an unmodeled access-state obligation. Its raw results
require separation of retained geometry and temporary operation envelopes,
followed by removal-order and geometry review. The actual WJ24 backer mechanics
extraction now binds two interfaces, four bolts, and four fixed Hillman load
entry axes; it supplies no demands or accepted connection properties.

The [local viewer and browser evidence](hypotheses/wj24-viewer-review/README.md)
are archived and parent-verified; publication waits for quiet hours to end.
The [conditional bolt-length screen](wj24-bolt-length-screen.md),
[stock yield](wj24-timber-stock-yield.md), and
[partial costs](wj24-development-costs.md) exist, while final hardware fit,
SKU selection, and complete costs remain open. These advances do not close
the stage acceptance gates in the table below.

| Chunk | Status | Evidence | Remaining work |
|---|---|---|---|
| WJ-00 | Complete | `wood-joints-candidate.json`, `plan.md`, `decision-log.md`, `criteria.json`; `authority-integrity.json` and `scripts/wood_joint_authority_integrity.py` reproduce exact selected/barrel authority and all 725 kerf-right export bytes from the reviewed handoff commit; all release flags false | None within WJ-00 |
| WJ-01 | Complete | `source-inventory.json`, `source-inventory-summary.md`, `scripts/wood_joint_inventory.py`; 24 duties, 144 SDS axes, 66 fixed screw axes, twelve frame-bolt arrangements, six source contacts, two unresolved receiver obligations, source faces, grain axes, and local transforms | Receiver attachments and replacement interfaces remain unresolved by design |
| WJ-02 | Complete | `mini_moonboard/wood_joint_geometry.py`; typed finished-part, interface, bolt-stack, evidence, bore, contact, clearance, and access records; focused negative tests; source-bound WJ-03 fixture persists face, grip, installed-envelope, and access reports | No connection resistance or strength pass is established by the primitives |
| WJ-03 | Partial; current sampled sequence diagnostic, support, envelope, and tolerance gates open | `mini_moonboard/wood_joint_frame.py`, candidate-only `mini_moonboard/wood_joint_panel_machining.py`, `scripts/wood_joint_wj03_sequence.py`, and final `wj03-sequence-diagnostic.json` (`b547a604…7e0f4`) include WJ-05 diagnostic backers, shifted posts, bolts, stacks, and four center receiver IDs. The corrected candidate service bores clear the 35 right-return LED hits reported at the earlier pre-helper checkpoint `0ebf90eb`; the left return was already clear. Kicker motion with the lower panel retained still overlaps by 1–18 mm; extraction and return pass when the lower panel is staged first. No LED disconnection is needed or inferred. Other paths/tools are unchanged. Both staged poses have 0 mm nominal gap to base-floor wood; permanent rear projection remains +86.018477 mm beyond the ordinary envelope, and the 315.648756 mm bolt-stroke reach remains separate temporary workspace. | Resolve support, continuous motion, tolerance, and permanent-envelope disposition; complete interfaces and stacks before updating acceptance. No sequence, layout, or capacity acceptance. |
| WJ-04 | Diagnostic revise; bound probe, early mechanics, and tool-access reports current | `wj04-probe.json` binds `narrow_x95p25_ordinary_bolt_candidate` at configuration hash `d1c63e1f…206c0e`; the cleat has 0.0 mm nominal excess beyond the ordinary N envelope, modeled stacks/seats clear locally, generic 50 mm rail-tool gap is 0.764 mm, and temporary nut exit extends 21.872532 mm beyond the ordinary limit. `wj04-tool-access.json/.md` reports `diagnostic_overlap_present`; conservative envelopes overlap solids during several counterhold/stroke/reindex/removal operations, but the report neither proves physical access nor impossibility. `wj04-early-mechanics.json/.md` binds six historical angle-demand cases but does not replay them; four source files mismatch per case, so capacity remains unresolved. Mechanics consumes the probe's finite-probe rail contact area (11,401.398713 mm²) and reports the canonical bounding rectangle separately (11,401.425 mm²; −0.026287 mm² delta); principal values reconcile within rounding. The 2×6 rip in `stock-and-cut-basis.md` needs post-rip regrading. | Refine and physically bound tool paths; verify delivered grade, bolt/thread transitions and nut engagement, actual wrench motion, tolerances, signed end/edge treatment, fresh candidate demand, integrated WJ-03 geometry, and complete joint resistance. No capacity or WJ-04 acceptance is established. |
| WJ-05 | Diagnostic partial; fresh nominal reports | `wj05-center-backer-transfer.json/.md` reports `nominal_geometry_clear_diagnostic`; `wj05-receiver-audit.json/.md` reports `blocked_center_receiver_path`. All 66 axes stay fixed: 62 enter frame timber and four enter two separate 4×4 backers with 45.24375 mm nominal receiver length. The repaired right upper socket proxy has 2.959434 mm seated wire clearance and 1.661248 mm along the full approach sweep. | Four center structural duties and two backer/header attachments remain unaccepted; long through-bolt/thread engagement, bearing, splitting, washer/contact, tool fit, ratchet access, service motion, and tolerances remain open. Complete receiver-to-frame paths and joint mechanics; physical observations remain blank. |
| WJ-06 | Complete diagnostic composition; 0 accepted replacements | The [full WJ24 layout](hypotheses/wj24-integrated-static/README.md) contains sixteen rebuilt hosts, twenty-eight connector pieces, 104 proposed bolt axes, 520 CAD roles and all 144 removed SDS axes. No legacy angles/SDS or source-only overlays remain. All 66 fixed axes, four backer redirects, shifted center posts and twelve frame bolts reconcile; the parent independently matched all fourteen retained raw-host records and 68 source-input hashes. | Resolve G1/G12 provisional hold clearance, reduced bottom-center bearing face, tools, tolerances and mechanics for every duty. Publish the complete diagnostic viewer after quiet hours; no joint is accepted. |
| WJ-07 | Diagnostic partial; no MVP-L acceptance | [Full WJ24 static diagnostic](hypotheses/wj24-integrated-static/README.md): all eighteen implemented static/source-tracking gates pass. [Individual LED extraction](hypotheses/wj24-led-extraction/README.md) tests 132 continuous rearward sweeps against 842 stationary shapes; G7 intersects the lower full-stock cleat by 319.657955 mm³. Earlier wired rail hits and unwired zero-gap contacts remain preserved. | Resolve G7 extraction and G1/G12 hold access, supported panel/wiring staging, whole-strand feeding, local tool conflicts, tolerances, assembly and reverse removal. Static fit and 131 clear LED sweeps do not prove transport. |
| WJ-08 | Diagnostic partial; no mechanics acceptance | `criteria.json` contains planning migration only. [Backer unit-wrench witnesses](hypotheses/wj12-backer-unit-statics/README.md) close 24 signed synthetic cases with finite patches checked in both finished members; [sampled sections](hypotheses/wj12-sampled-sections/README.md) quantify named local cuts. [Full-stock input extraction](hypotheses/wj16-full-stock-mechanics-inputs/README.md) binds eight WJ16 bolts and four contact planes with explicit grain and hardware datums. The [full-stock thread-bearing screen](hypotheses/wj04-full-stock-thread-screen/README.md) covers eight bolts and 256 member/corner fractions; the maximum beyond the recorded Lb boundary is 7.8549%, below the conditional one-quarter geometry limit. None supplies actual demand or resistance. | Complete connection mechanics, actual demands, critical sections, bearing/wood/washer resistance, and the evidence-bound criteria contract. |
| WJ-09 | Current joint diagnostic partial; no response or criterion accepted | For the owner-reviewed `led-clearance-2x6-runner-seated-blocks-v1`, the current direct three-member/four-stack/three-contact diagnostic reached the first reported cleat-bore event at accepted state 39 (0.0195 s) and a complete following state 40. Corrected physical acceleration, energy, contact-vector coverage and framing checks are recorded; the state-39/40 global moment residuals fall within conditional printed-token bounds only. These checks do not establish a force tolerance, whole-joint equilibrium, time/mesh sensitivity, delivered engagement, resistance or current full-frame demand. | Define supported acceptance tolerances; complete targeted timestep/mesh/contact and engagement-scenario sensitivity; audit a representative response; then characterize the remaining joint families. Fresh current-revision six-case demands and criteria remain required. |
| WJ-10 | Inventory partial; no shop-package acceptance | [Complete-layout inventory](hypotheses/wj24-hardware-inventory/README.md) reconciles 104 proposed bolts, 104 nuts and 216 washers, 52 ordered receiver pair groups and 28 connector blanks. Retained frame bolts and Hillman screws remain separate. | Assign sixteen remaining bolt lengths; verify all hardware fit and specifications, stock yield, prices, tools and coordinated instructions. Complete independent review and the conditional MVP-E packet. |
| WJ-11 | Owner/shop | None | Physical receiving and observed prototype records; MVP-P |

## WJ-00 acceptance record

- New candidate identity is distinct and does not replace selected authority.
- Selected and preserved barrel authority files were read and left unchanged.
- `authority-integrity.json` reproduces both authority-file SHA-256 values and
  the aggregate SHA-256 of all 725 kerf-right export paths and STL bytes from
  the handoff commit; its source script fails if any byte differs.
- Starting repository commit equals handoff reviewed commit.
- Kerf-right physical surface and 66 screw axes are fixed.
- Ordinary 139.7 mm local-N envelope has an explicit datum/reporting policy.
- No primary-member notch is the default; bounded housed investigation requires
  complete cut and joint evidence.
- Connector construction options and exclusions are explicit.
- Imported legacy criteria remain pending; no pass or capacity is inherited.
- Layout, engineering, prototype, drilling, fabrication, structural, and
  climbing release flags are false.

## Current claim boundary

The narrow WJ04 and original WJ03 entries preserve the active registry's
historical reports. Current development geometry is the complete WJ24
diagnostic in WJ-06, including compact outer nodes and full-stock ordinary
cleats; neither registry promotion nor joint acceptance has occurred.
The [physical hardware export](hypotheses/wj04-mechanics-hardware/README.md)
and [parent seat audit](hypotheses/wj04-mechanics-hardware/seat-and-envelope-audit/README.md)
now establish nominal representative hardware geometry and finite bearing
faces. They do not establish contact response, resistance or native readiness.

WJ-00 through WJ-02 are complete. WJ-03 establishes a source-bound nominal
outer-node topology and returns `revise_named_constraint`; it does not establish
layout acceptance, selected hardware, tolerance feasibility, connection
resistance, a native solve, shop dimensions, observed material, or release.
