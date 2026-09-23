# Barrel-nut candidate completion ledger

This ledger records progress toward a conditional DIY package for the
`compact-floor-flush-bolted-development` integrated kerf-right barrel-nut
candidate. It is governed by the [validation plan](barrel-nut-validation-plan.md)
and [candidate criteria](barrel-nut-criteria.md).

Current disposition: **EVIDENCE_BLOCKED**. Geometry and preparation work
exist, but no complete barrel joint has an accepted resistance, no signed
candidate case has been solved, and no adopted structural criterion set has
passed. The selected `compact-floor-flush-development` angle frame and its 36
saved criteria remain separate authority. This ledger transfers none of those
passes.

## Candidate snapshot

| Item | Current record |
| --- | --- |
| Development candidate | `compact-floor-flush-bolted-development` |
| Geometry source | `scripts.export_owner_barrel_scene.build_integrated_viewer_assembly()` |
| Framing and face | 20 framing timbers; six fixed plywood panels |
| New structural connectors | 46 selected qualification bolt/barrel pairs at 24 former-angle duties; not structurally qualified |
| Selected qualification hardware | 46 STAFAST `JCD14201606NL ZN` barrels; CDE Grade 5 `1456BHT5` / `1472BHT5` / `1480BHT5` / `14104BHT5` bolts at 3 1/2 / 4 1/2 / 5 / 6 1/2 in; 46 Fastenal `33857` hardened washers |
| Retained connectors | Twelve frame bolts; 66 panel/kicker screw axes |
| Removed from candidate | 24 ML24Z angles and 144 structural SDS25112 attachments |
| Required cases | A12 left, A12 rear, A12 forward, K12 right, K12 rear, A1 rear |
| Floor condition | Explicit no-slip analytical assumption; floor not verified or anchored |
| Candidate contract | [`barrel-nut-candidate.json`](../barrel-nut-candidate.json); source/data hashes and dirty-snapshot identity recorded, worktree uncommitted |
| Station register | [`barrel-nut-stations.json`](barrel-nut-stations.json); 24 duties, 46 pairs, 132 exact barrel-face cells, 72 retained-face cells, and six complete prepared load records |
| Release state | No drilling, fabrication, structural, climbing, or selected-candidate release |

The owner has authorized and the working candidate integrates two first-row
changes at the left lower/upper center rail stations to N = 42 mm and four
2 mm top-outer machine-bore extensions. They remain subject to a frozen source,
affected section and tolerance checks, and the full criteria. Authorization
and nominal integration are not acceptance. The selected 5 in stack needs a
further blind-bore correction, and the selected CDE 6 1/2 in outer-rail stack
needs new deeper bores; neither correction is yet frozen or released.

## BN task status

| Task | Finite deliverable | Status | Remaining exit work |
| --- | --- | --- | --- |
| BN-0 | Frozen candidate, station register, six-case load contract, criteria, and finite ledger | **In progress: artifacts exist, commit freeze open** | Candidate contract, station register, complete six-case load fields, source/data hashes, criteria, and ledger now exist. Commit the coherent candidate source and regenerate clean bindings; finish each criterion's method, applicability, factors, limit, and failure disposition. |
| BN-1 | Controlled hardware/material evidence and complete tolerance stacks | **In progress: qualification stack selected; evidence gap remains** | [Selected qualification hardware](barrel-nut-selected-hardware.md) now fixes exact STAFAST barrels, the CDE fully threaded Grade 5 bolt family at all four lengths, and Fastenal hardened washers. CDE IFI-199 dimensional limits and bolt/washer constituent standards are recorded. CDE certificates and Class 2A confirmations, the Fastenal washer MTR, STAFAST controlled tolerances/material/thread/resistance evidence, lumber inputs, complete stacks, and delivered measurements remain unresolved. |
| BN-2 | One feasible nominal geometry with tolerances, complete force paths, access, and service | **Incomplete** | Prior nominal machining inventory covers all 20 framing timbers and 268 host/cutter applications. Nominal screens clear the 2.0066 mm STAFAST shift at all 46 barrels and the corrected 12.4408 mm provisional-reserve outer-rail extension at all twelve rows, including selected maximum-washer envelopes. Final 5 in blind-bore cuts, accepted machining clearances, adverse-tolerance combined cuts, and complete section coverage remain open. Resolve principal/header twist and 2.092 mm pocket stock, outer-header 6.35 mm pocket stock, barrel bore fit, thread reach, tool/service sequence, LED passage, and plywood yield. |
| BN-3 | Complete-joint resistance and stiffness basis for every family and critical variant | **In progress: routes inventoried, bases unresolved** | Resistance ledger, stiffness audit, and qualification plan exist. They correctly retain zero passes: no complete bolt/thread/barrel/wood resistance or justified response bounds exist. |
| BN-4 | Verified candidate response model and mechanics tests | **In progress: mechanics preflight supported, model acceptance open** | All six cases prepare with 58 bolts, 66 fixed screws, 132 exact barrel-face cells, and 72 retained-face cells. Four former bevel surrogates now use mapped uncut C3D20 prisms; affected cut-solid sections remain unresolved. Coupled tension-only, compression-only, 0.575 mm radial-clearance, retry, and checkpoint mechanics tests pass. Stiffness/contact evidence, sensitivity closure, and an accepted native result remain absent. |
| BN-5 | Six solved cases and station × case × failure-mode acceptance ledger | **Prepared, not executed** | Fail-closed case runner, six-case orchestrator, signed-demand extractor, schema, case log, and 3,216-row resistance ledger exist. No candidate native case is accepted; no qualified signed demand, utilization, or candidate-wide member/retained-bolt/floor result exists. |
| BN-6 | Matching conditional DIY packet | **Templates started** | A blank receiving/offcut checklist exists. No accepted BOM, shop drill/pocket sheets, cut list, tolerance/jig instructions, assembly sequence, maintenance scope, or matching released viewer exists. |
| BN-7 | Independent mechanics/shop reviews and final verification archive | **In progress; focused software reviews complete** | Independent reviews of criteria, exact contacts, clearance, orchestration, hardware evidence, qualification planning, and complete nominal machining inventory are closed. Focused affected regressions and lint pass; the full 61-file barrel set has not been rerun after four corrected expectations. Final mechanics/shop acceptance and a released archive cannot close without the missing evidence and accepted cases. |

## Current criterion summary

| Class | Supported now | Unresolved now | Meaning |
| --- | ---: | ---: | --- |
| Candidate/load/inventory inputs | 3 | 4 | Complete load identity, connector inventory, and fixed-surface identity are supported. Committed source freeze, complete criteria contract, and controlled materials/hardware remain open. |
| Geometry, machining, and service | 1 | 12 | Exact contact-cell geometry is supported. Prior all-20-timber machining inventory and separate selected-hardware probes do not yet represent frozen final bore depths and adverse tolerances; local sections, access, LED, and panel yield remain open. |
| Response and numerical | 1 | 8 | Uncut bevel-member response-geometry mapping passes. Cut-solid section equivalence and an accepted signed response remain unresolved. |
| Complete-joint resistance | 0 | 20 | Constituent scales are not complete-joint capacities. |
| Applicable selected-baseline reruns | 0 | 34 | Exact candidate rows exist for member, taper, contact, and retained-bolt methods; no saved baseline pass transfers. |
| Documentation and reviews | 0 | 3 | Candidate packet and independent reviews do not exist. |

These counts summarize the rows in `barrel-nut-criteria.md`; they are not a
substitute for the exact identifiers or their evidence. Recount them when
criteria are added, removed, or reclassified.

## Supported preparatory evidence

The following work narrows the remaining problem but does not establish
strength or release:

- Candidate contract and station register bind the working source, scene,
  geometry fingerprint, units, exact station inventory, and dirty-snapshot
  identity. They remain uncommitted and explicitly unreleased.
- The integrated source inventory contains 46 barrel pairs at 24 duties,
  twelve retained bolts, 66 fixed panel/kicker screws, 132 exact barrel-face
  cells, and 72 exact retained-face cells.
- All six required cases have complete authenticated load records and prepare
  without importing legacy ML24Z/SDS connectors or running a native solve.
- The 20-timber idealized graph is full rank with all faces closed, while the
  all-open graph has two free relative modes. Both single-bolt
  principal/header joints retain a local face-normal twist mode even with
  their local faces closed.
- Exact trial-cut cell areas and first moments exist at all 24 barrel faces.
  The two principal/header faces retain 588.180 mm2 behind each bolt line.
- All four former analysis-only bevel members now use source-bound uncut CAD
  prism geometry mapped through C3D20 elements. Volume, centroid, connection,
  and contact-point tests pass. This does not establish the worst remaining
  ligament or local section after bores, pockets, and service cuts.
- The conditional response model now couples the nominal 0.575 mm radial
  dead zone to all 46 barrel bolts. Tension-only, compression-only, radial
  engagement/reversal, retry, and checkpoint mechanics tests pass. Their
  success validates implementation behavior, not stiffness or joint strength.
- Fail-closed runner, orchestrator, demand extractor, and resistance ledger
  exist. They reject absent or unaccepted reports and currently supply no
  accepted demand or resistance pass.
- Nominal straight-line rim removal clears modeled timber and retained
  hardware. It does not prove delivered tool access, temporary support, or
  repeatable service.
- Prior complete-frame nominal cut construction produces one valid connected
  solid for every one of the 20 framing timbers and records all 268
  host/cutter applications, including both leg recesses and both hosts of all
  twelve retained frame bolts. A separate source-built screen shifts every
  STAFAST body and insertion-bore tail 2.0066 mm without a nominal unrelated
  collision. A corrected nominal probe contains the 12.4408 mm provisional-
  reserve outer-rail extensions and selected maximum-washer envelopes in all
  twelve receivers without unrelated, protected, peer-path, or peer-stack
  collisions. Final accepted machining clearances, the 5 in correction, fit,
  and adverse tolerances are not frozen, so this remains preparatory inventory
  evidence.
- Preliminary calculations provide conditional washer/wood, full-slot, and
  steel-only stiffness scales for six duties. They are not demands,
  resistances, or additive joint ratings.

## Exact blockers to a strength conclusion

| Blocker | Criterion affected | Required closure |
| --- | --- | --- |
| Candidate contract and station register bind a dirty, uncommitted working tree. | `bn_candidate_identity` | Commit one coherent source revision, regenerate the contract/register, and verify all bound hashes without changing geometry or evidence. |
| Selected STAFAST `JCD14201606NL ZN` barrels have nominal geometry but no controlled tolerances, internal-thread class/usable interval, material minimums, resistance, or lot conformity in current evidence. | `bn_controlled_hardware_inputs`; thread/barrel criteria | Obtain controlled evidence or measure and qualify the exact lot through the complete-joint route. |
| The former 6 in outer-rail comparator is rejected. Selected CDE 6 1/2 in bolts cover the modeled barrel body but need 10.4408 mm added blind-bore depth for zero clearance or 12.4408 mm for the provisional 2 mm reserve. Selected 5 in rows retain only 0.1204 mm adverse clearance before machining error. Usable STAFAST female engagement remains unknown. | `bn_stack_engagement_and_tip_clearance`; `bn_all_machining_represented` | Freeze lot dimensions, female-thread interval, required engagement, bore depths, and tip clearance; rebuild and check the complete adverse-tolerance cuts. |
| All 46 modeled insertion bores have zero nominal diameter allowance. | `bn_barrel_bore_fit` | Select justified drill/finished fit and tolerances; recompute remaining wood. |
| Principal/header joints have an unresolved twist path, 2.092 mm nominal pocket-edge stock, and only 588.180 mm2 behind each bolt line. | `bn_joint_kinematic_stability`; wood breakout/contact rows | Establish signed connected restraint and complete local resistance, or revise within scope and recheck. |
| Outer-header pockets leave 6.35 mm nominal side stock and require a rim-first service sequence. | `bn_wood_splitting_breakout`; `bn_tool_access`; `bn_member_removal` | Close local resistance, tolerances, real access, and supported service sequence. |
| Nominal combined-cut solids are now source-bound for the governing joints, but event-directed sample-set stability does not establish a continuous minimum, controlled adverse tolerance case, or local resistance check. | `bn_cut_sections_sampled`; `bn_local_net_section_interaction` | Freeze realizable stock, hardware, and machining tolerances; complete continuous section/ligament coverage and local resistance checks under signed demands. |
| The coupled 0.575 mm radial law has passing mechanics tests, but actual clearance and axial/lateral/contact stiffness bounds remain unsupported. | `bn_stiffness_clearance_basis`; response sensitivities | Establish defensible lower and upper behavior bounds or measured qualification inputs, then run required sensitivities. |
| No native case has an accepted source-bound result. The runner, orchestrator, and extractor therefore fail closed with no qualified signed demand. | All response, demand, resistance, retained-bolt, member, and stability rows | Run and accept all six cases only after remaining BN-4 entry inputs close; extract balanced signed actions and populate the resistance ledger. |
| Actual LED strand, owned plywood, delivered hardware, and delivered lumber have not been measured. | Shop-fit and observation rows | Preserve blank shop observations; prepare exact measurement and rejection rules. |

## Candidate artifact chain

| Purpose | Artifact | Current boundary |
| --- | --- | --- |
| Candidate-only authority | [`barrel-nut-candidate.json`](../barrel-nut-candidate.json) | Hash-bound dirty working state; unreleased and not selected authority |
| Station, connector, contact, and load register | [`barrel-nut-stations.json`](barrel-nut-stations.json) | BN-0 development input; no solved demand or resistance |
| Selected qualification hardware | [Decision](barrel-nut-selected-hardware.md) and [machine record](barrel-nut-selected-hardware.json) | Exact test articles selected; `EVIDENCE_BLOCKED`, not a purchase list or structural release |
| Hardware evidence | [Ledger](barrel-nut-hardware-evidence.md) and [machine record](barrel-nut-hardware-evidence.json) | Documentary gate remains unresolved |
| Response-property audit | [Stiffness basis](barrel-nut-stiffness-basis.md) | Diagnostic sensitivities only; no accepted bounds |
| Governing combined-cut geometry | [`barrel-nut-combined-cut-sections.json`](barrel-nut-combined-cut-sections.json) | Eight stations, fourteen pairs, and eleven full-cut members; `EVIDENCE_BLOCKED`, with no tolerance, resistance, or release credit |
| Complete-joint evidence route | [Qualification plan](barrel-nut-complete-joint-qualification-plan.md) | Plan only; no test authorized or completed |
| Resistance inventory | [`barrel-nut-resistance-ledger.json`](barrel-nut-resistance-ledger.json) | 3,216 case results, zero passes, zero failures, all unresolved |
| Physical input forms | [Receiving and offcut checklist](barrel-nut-receiving-and-offcut-checklist.md) | Actual and Disposition fields remain blank |
| Bounded feasibility decision | [Go/no-go packet](barrel-nut-go-no-go-packet.md) | Four governing gates, exact owner/shop inputs, correction order, and finite stop rule; current result remains `EVIDENCE_BLOCKED` |
| Native attempt history | [Case log](barrel-nut-case-log.md) | One rejected historical smoke attempt; no accepted case |
| Response execution | [`owner_barrel_native_run.py`](../scripts/owner_barrel_native_run.py) and [`owner_barrel_six_case_run.py`](../scripts/owner_barrel_six_case_run.py) | Conditional diagnostic tooling; fail-closed release flags |
| Demand extraction | [`owner_barrel_signed_demand_extract.py`](../scripts/owner_barrel_signed_demand_extract.py) and [schema](owner-barrel-signed-demands.schema.json) | Rejects missing or unaccepted source reports |

## Verification record

- Focused selected-hardware checks pass 8/8. They verify the recorded
  qualification selection and fail-closed disposition, not joint strength or
  release.
- The integrated affected set passed 128 tests after regenerating the
  criteria-bound resistance ledger.
- The complete 61-file barrel regression set produced 258 passes and four
  stale expectation failures. The four failures were limited to the approved
  2 mm top-outer bore-cap gap and the current 16-row provisional viewer
  head/washer inventory; their corrected focused tests pass 4/4. The full
  61-file set has not been rerun after those corrections.
- Ruff passes on every barrel/response Python file changed by this work, and
  `git diff --check` passes.
- Candidate contract source/data hashes, geometry fingerprint, selected-
  authority hash, and dirty-snapshot identity reproduce. All release flags are
  false.
- Selected official and kerf-right viewer/construction artifacts were
  deterministically regenerated after their assessment-scope wording was
  reconciled. The viewer current-design group check now accepts the maintained
  grouped-array syntax. `scripts.current_candidate --check-exports` still
  fails closed with two messages from one real selected-authority mismatch:
  the frozen geometry and six native cases bind the pre-`7cdd2e37` model
  source, while the current model includes that commit's 19.05 mm center-header
  clip shift. The geometry therefore has a stale
  `mini_moonboard/compact_floor_flush_frame.py` source snapshot and does not
  identify the current model revision. No fresh native cases were run; project
  rules prohibit native solves. No selected geometry, six-case result, or
  candidate authority was promoted by this barrel work.

## Selected-baseline checks requiring candidate rerun

Applicable member, retained-bolt, contact, floor, taper, and numerical checks
are listed in `barrel-nut-criteria.md`. Their current candidate status is
`UNRESOLVED` unless the candidate ledger explicitly supplies new source-bound
evidence. In particular:

- the angle frame's six saved cases are not barrel-frame demands;
- the twelve physical frame-bolt axes staying in place does not preserve their
  forces, group action, or utilization;
- unchanged taper or floor geometry still needs source identity and the new
  case response before its force-dependent checks can pass; and
- `angle_rated_force_components` and `ml24z_unlisted_actions` do not apply to
  a candidate without ML24Z angles.

## Physical observation register

No actual wood, cuts, holes, hardware, panels, LED assembly, pads, or floor
have been inspected for this candidate. Keep these cells blank until observed.

| Item | Required record | Actual | Disposition |
| --- | --- | --- | --- |
| Delivered bolt/barrel/washer stacks | Marking, dimensions, tolerance extremes, thread engagement, tip reserve, seating, material evidence |  |  |
| Delivered lumber | Species/grade, moisture, actual sections, grain, checks, splits, knots, and defects at cuts |  |  |
| Owned plywood | Actual dimensions, face condition, fixed-outline yield, kerf and trim allowance |  |  |
| Finished bores and pockets | Location, diameter, depth, angular error, remaining wood, breakout, tear-out, overcut, and fit |  |  |
| Installed joints | Barrel orientation and retention, washer support, engagement, damage, contact, access, removal, and reassembly |  |  |
| LED path | Complete strand and connector feed through documented route |  |  |
| Floor/support | Surface, placement, and bearing condition; this observation does not verify the no-slip assumption |  |  |

## Completion outcomes

| Outcome | Required evidence | Current disposition |
| --- | --- | --- |
| Conditional DIY documentation complete | Every adopted candidate geometry, load-path, response, joint, member, retained-bolt, floor, numerical, documentation, and review criterion passes on one frozen design. Matching machining and assembly documents exist. Physical receiving/installation observations remain explicit conditions. | **Not achieved.** |
| Geometry or strength rejection | An applicable criterion fails, a required physical path is absent, or compatible hardware cannot fit within allowed constraints. Record station, mode, demand/value, limit, and smallest supported correction. | **Not concluded.** Existing thin-stock and twist findings are unresolved, not yet quantified adopted failures. |
| Evidence blocked | Governing controlled properties, mechanics basis, required physical qualification, or authorized solve cannot be obtained after independent work is exhausted. Deliver exact missing evidence and a prepared test, measurement, or decision packet. | **Current disposition under this goal.** Exact qualification articles and controlled bolt/washer constituent bases are selected, but required lot certificates, STAFAST tolerances/material/usable female-thread/resistance evidence, final bore/fit bounds, response bounds, delivered measurements, and complete-joint qualification remain unavailable under the no-contact/no-purchase/no-physical-test boundary. No strength or DIY-ready conclusion is possible until those inputs close. |

Do not promote the candidate in `current-candidate.json` or replace the selected
shop packet when BN-0 through BN-7 are merely planned or prepared. Promotion
requires the conditional-complete outcome and a separate owner selection.
