# Four-gate closure matrix — 2026-09-29

This append-only, read-only synthesis binds the completed Luna Max floor,
panel-withdrawal, receiver-path, and beam self-weight reviews to the source
records below. It identifies current evidence, unresolved assumptions, the
smallest actionable unblocks, and the effect on a six-case response. It does
not establish connection capacity, accept demands, or authorize geometry
changes, meshing, or solver execution.

## Authority and current decision

- [`AGENTS.md`](../../../../AGENTS.md) — SHA-256
  `672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536`.
- [Root continuation note](root-continuation-note-2026-09-29.md) — SHA-256
  `60501849cdfb156c09e74ad6eff5cb9161180af2f0ef93fedeab5b0a312006d3`.
- [Execution brief](LUNA-MAX-COORDINATOR-EXECUTION-BRIEF-2026-09-29.md) —
  SHA-256
  `3b515c613836bce55b0695dc1ccd3a8895d79e23f41bcca1d196fda046faaf36`.
- [Status and work-order addendum](LUNA-MAX-COORDINATOR-STATUS-AND-WORK-ORDER-2026-09-29.md)
  — SHA-256
  `d6129e6debbcfa7e79f692e45f757ab8c4f6e9deaa5c4e3892b5113e7cffd53a`.
- [Closed demand-coverage register](demand-coverage-register-2026-09-29.md) —
  SHA-256
  `d745ca62f2fa66bf671227ed2089da8568d4237ae5e5a6180db773885f231072`.
- [Reviewed A/B method comparison](option-ab-method-selection-2026-09-29.md)
  — SHA-256
  `d73dc9b2583c88b64fab4a8e61b1910dfbdb2881cc6dde629b30911a5425c76a`.

**Readiness: BLOCKED.** The closed register found no path-complete member or
joint demand subset. All four gates below block accepted current-revision
member/joint demands; other full-frame inputs and solver mappings also remain
incomplete. All 47 MVP-E criteria remain pending. The separate T09 mesh-only
track is currently deferred by the parent. This matrix does not prepare or
run a mesh or solver; any restart requires a separate parent decision.

| Gate | Status | Established from pinned records | Missing to close | Six-case effect |
|---|---|---|---|---|
| Conditional floor support | **BLOCKED** | c11 is one solved `a12-rear` linear branch with two floor complementarity failures; its paired tangent springs are a finite-spring scenario. | A defined conditional no-slip-while-bearing law, bearing/re-engagement reference, bounded coupled state-selection method, and passing known-answer fixture. | No accepted floor/support reactions or full-frame response. |
| Panel withdrawal | **BLOCKED** | Six applied panel wrenches have 1,199.82–1,659.44 N positive outward panel-normal resultants. | Applicable Hillman 42605 withdrawal resistance/stiffness and installation/group evidence, plus the receiver-to-frame route and load sharing. | Panel/screw demands cannot be recovered or accepted. |
| Receiver and hardware paths | **BLOCKED** | STEP identities and nominal geometric receiver intersections are mapped; gravity source rows preserve wrenches. | Current attachment/bearing laws, stiffness and force-sharing basis, solver body/DOF mapping, and closed paths through frame to support. | No path-complete internal member/joint demand subset. |
| Member self-weight distribution | **BLOCKED** for exact beam demands; equivalent totals are **CONDITIONAL** | At the 600 kg/m³ scenario, 20 frame timbers total 127.5322 kg / 1,250.6635 N. Mean equivalent loads from descriptor lengths span about 30.04–71.83 N/m. | A justified beam station axis/support span and source-bound local mass/centroid distribution, with force/first-moment and known-answer section-force checks. | Body-level gravity balance cannot supply exact local `N/V/M` demands. |

The four gates are separately tracked but **not mechanically independent**:
panel withdrawal transfers through receivers; receiver forces depend on
attachment and bearing laws; both routes terminate through the frame and
floor; and member self-weight changes the same supported frame response.
Closing one evidence packet does not close the coupled path or establish a
valid partial-demand subset.

## 1. Conditional floor support — BLOCKED

**Evidence and exact pins.** The one-case c11 freeze, model, response, and
independent postrun audit are respectively
[`freeze.json`](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/freeze.json)
`1633e79900afd194ece79c7463a7b383a11bb96920e7449e6a25c528e933b8e2`,
[`model.json`](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/model.json)
`d3417111926c982a07ced393aa1c12f815aa87b5b8eb851b45bc63a1ea10fac0`,
[`response.json`](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1/response.json)
`b8558fbaa986ff251008da629c21d8d9a56e16c965ce09476e94a688f0a9f878`, and
[`independent-postrun-review.json`](reduced-static-a12-rear-ratio1-gap0-attempt02/cycle-11-sign-closure-r1-postrun-review/independent-postrun-review.json)
`0c6c7b8601a8b15cd46901c912934483b5da14babb84380a9301c0730cdb18ed`. The
[method/model reassessment](c11-method-model-reassessment-2026-09-29.md) is
`e80e41c061a37da01b11f34cb00c1a6aefb8b6b6d545956cc4257e44da732a0a`.
The pinned 2.23 contact screen and manual are
[`contact-formulation-method-screen.md`](../evaluation-resume-2026-09-24/ordinary-external-force-transient-attempt04-diagnostic/contact-formulation-method-screen.md)
`6900e09206248de4ef0c318086cc69743dbdada1f1e53862721a40e6de6730f9` and
[`ccx_2.23.pdf`](../../../../fea/generated/ccx_2.23.pdf)
`a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`.

**Established.** c11 is an equilibrated selected branch, not a converged
conditional-support solution: six compression-only checks fail overall
(four active cells separate with tension; two inactive cells penetrate).
For the floor, one active cell separates with `−298.865 N` normal branch
force while its paired tangents carry `328.526 N`; another inactive floor
cell penetrates with no reaction. The independent audit passes its evidence
accounting, while numerical and mechanical acceptance remain false. The
finite tangential spring stiffness is a numerical scenario, not measured
floor friction. The existing CalculiX coupon covers normal contact and
`CF`/`CFN`/`CFS` output, not the desired conditional stick law. Frictionless
contact cannot provide tangent stick; finite Coulomb friction requires an
unsupported coefficient; `TIED`/`*TIE` is not unilateral bearing with
conditional zero slip. Do not substitute a high `μ`, infer an anchor, or
transfer c11 support forces.

**Missing and smallest actionable unblock.** Define a new candidate law that
enforces zero tangential motion only while the same support cell is bearing,
including the first-bearing and re-engagement reference. Specify coupled
normal/tangent state selection, finite termination/failure behavior, and the
scope of any uniqueness claim. Then give a hand-checkable fixture with
open/bear/release and tangent stick/open/re-engage states, expected reactions,
gaps, and tangent motion, plus an independent exact-hash review. This is a
method/evidence packet only; the parent separately decides whether any test
may be run. Until then, floor law and reactions block all six current cases.

## 2. Panel withdrawal — BLOCKED

**Evidence and exact pins.** The
[withdrawal preflight](panel-withdrawal-preflight.md) is
`22e4b14d270a1d7ba8a247562b901ef4998483ca7d70feed6646560a29c6d18f`; the
[six-case load contract](../evaluation-resume-2026-09-24/current-load-cases.json)
is `9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a`,
and [load datums](../evaluation-resume-2026-09-24/current-load-datums.json)
are `c3a561b84eb56472264e92eacabae7c2e06fe33633ebba96f1de9ee974924022`.
The reduced-model source inputs are
[`model-inputs.json`](reduced-static-attempt01/model-inputs.json)
`178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9`;
the full-frame source manifest is
[`current-full-frame-input-manifest.json`](../evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json)
`9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11`.

**Established.** Applying the frozen outward panel normal to each external
case wrench gives these global outward resultants before gravity. These are
panel resultants, not per-screw actions. The frozen normal is
`n_out = (0, 0.7660444431189781, −0.6427876096865394)` and the reported value
is `F_out = F_global · n_out`:

| Case | Loaded panel | Applied global force `(Fx,Fy,Fz)`, N | Outward panel-normal resultant, N |
|---|---|---:|---:|
| `a12-rear` | `main_upper_left` | `(0, 300, −2224.110808)` | 1659.44 |
| `a12-forward` | `main_upper_left` | `(0, −300, −2224.110808)` | 1199.82 |
| `a12-left` | `main_upper_left` | `(−300, 0, −2224.110808)` | 1429.63 |
| `k12-right` | `main_upper_right` | `(300, 0, −2224.110808)` | 1429.63 |
| `k12-rear` | `main_upper_right` | `(0, 300, −2224.110808)` | 1659.44 |
| `a1-rear` | `main_lower_left` | `(0, 300, −2224.110808)` | 1659.44 |

The source record identifies the Hillman 42605 product, but supplies no
applicable structural withdrawal rating or axial stiffness for the installed
wood/screw configuration. No verified installed thread engagement, head or
panel limit, or group-sharing rule closes the load path. The owner-selected
pilot/countersink policy remains the controlling installation instruction;
it does not establish withdrawal resistance.

**Missing and smallest actionable unblock.** Obtain applicable,
source-backed resistance and load-slip/stiffness evidence for the exact screw,
wood, penetration, and group geometry, including the head/panel limit and
installation details; then show the signed transfer from each panel group to
its receiving members and onward frame path. If that evidence is unavailable,
record the product-data or design/test decision required rather than borrowing
another screw's values or dividing each load equally. Until the evidence and
downstream receiver path close, all six panel withdrawal demands are blocked.

## 3. Receiver and hardware paths — BLOCKED

**Evidence and exact pins.** The manifest above binds 50 STEP bodies, 92
candidate bolt axes, 12 retained frame-bolt arrangements, 66 Hillman axes, and
six load cases. The
[receiver screen](../evaluation-resume-2026-09-24/receiver-screen-attempt04.json)
is `851495f2ccc80f286a7eae97fc54bcf602a478bb7d4e13eb28e2ae44cfb87991`; the
[duty-path graph](../evaluation-resume-2026-09-24/current-duty-path-graph-attempt01-2026-09-28/duty-path-graph.json)
is `b3cf2e6b9bc6052e914bbce4ba3052dd3329075ca2043931002ce6fb7a448115`,
with [independent graph review](../evaluation-resume-2026-09-24/current-duty-path-graph-attempt01-independent-review-2026-09-28/review-record.json)
`742b47c45a21d90a159a30050f6d948a64e5af47005abede232577638a10a4db`.
The [mass/topology source map](../evaluation-resume-2026-09-24/current-mass-topology-map-attempt03/source-topology-map.json)
is `308a329a0b40db454d5b0e27c9ec2eca92d66eec96bfb222df5f7b7185bef4d4`,
and its [independent review](../evaluation-resume-2026-09-24/current-mass-topology-map-attempt03/independent-review.md)
is `956a5b63047c7e49c3aedae407f008d5b0d5828aad86382ecf1d26200db196ad`.
The c11 body-wrench audit input
[`body-external-wrenches.csv`](reduced-static-attempt01/body-external-wrenches.csv)
is `6c823add8e29fc2089bff460ce7fa59c300794511214890b638b6c1a6c77a33f`.

**Established.** All 66 modeled screw-axis envelopes intersect their raw
receiver regions and clear the finished receivers; 22 panel/receiver and 52
named block/frame pairs have finite nominal face intersections. These are
geometry results only. The mass map accounts for 778 source rows (50 physical
members, 520 hardware-role rows, 142 T-nuts, and 66 screw-envelope proxies),
but every solver DOF is null and implemented mechanical carrier count is
zero. The separate 25 kg accessory allowance has no observed item split or
center of gravity. c11 maps source gravity wrenches to bodies/panels and
preserves force/first-moment accounting; it does not model hardware as
mechanically connected carriers, establish attachment stiffness, or prove
force sharing. c11 is one failed-contact branch, not an accepted demand set.

The center-kicker chain from two Hillman axes through the center post,
post/cleat bolts, cleat, and header bolts is an identity path only. The
geometric alternatives through bearing/seat surfaces have no demonstrated
action split. The edge-support intervals and other receiver interfaces also
lack a validated active-bearing and attachment law. Source wrenches are not
mechanical carriers.

**Missing and smallest actionable unblock.** Create a current-revision,
source-bound interface ledger with each member/hardware identity, body/element/
DOF ownership, contact or attachment law, source-backed stiffness (or the
explicit missing basis), signed simultaneous interface actions, group-share
rule, equal-and-opposite closure, and downstream route to runners/floor.
Resolve accessory representation/location or keep its placement scenario
explicit. This ledger may show a required design decision; it cannot fill a
missing capacity or stiffness by assumption. Until the interfaces and all
routes are closed, receiver/member demands are blocked.

## 4. Member self-weight distribution — BLOCKED for exact beam demands

**Evidence and exact pins.** The
[source mass/centroid inventory](../evaluation-resume-2026-09-24/current-mass-centroids-attempt01/mass-centroids.json)
is `4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a`;
the [reduced member geometry](reduced-static-attempt01/member-geometry.json)
is `121f1940d0180367f953a1f92443964ded901ca775536750a9b028e37d6c8187`.
The [density scenario](../../board-weight-2026-09-24.json) is
`7425c8100c9bbf0586d8e1732138eb5ec1e6147f8418b5cf3ea95dc6108e035e`; the
[timber material-frame map](../evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/current-frame-timber-material-frame-map.json)
is `f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409`.
The exploratory OBB load-input script is
[`produce.py`](../evaluation-resume-2026-09-24/current-frame-member-beam-selfweight-attempt01/produce.py)
`4195f4f4fb7a7d2cc512cd7073925edb211d8abc575a6958544a2c25c4ff4942`.
The c11 gravity implementation is
[`wood_joint_reduced_body_loads.py`](../../../../fea/wood_joint_reduced_body_loads.py)
`64b7b2ccec107a95f23d749abace7d89346d0a57191ad3746273c496c27ab1f0`;
c11's exact model/response/audit pins are listed in Gate 1.

**Established.** At the assumed density of 600 kg/m³, the 20 frame-timber
source rows give 127.5322 kg and 1,250.6635 N. Spreading each body weight
uniformly over the reduced descriptor length yields *mean equivalent* loads
from about 30.04 to 71.83 N/m; values scale with the assumed density. This
preserves each force resultant but is not an exact local distribution. The
longest OBB axis is a geometry-derived candidate line, not a proven structural
beam reference or support-to-support span. The leg mass centroid lies about
53.8 mm from the descriptor-line midpoint; the reviewed correction couple
(up to about 2,095 N·mm) restores the whole-member force and first moment, not
the true local `q(s)` or its section-force diagram. The script includes an
analytic-box check that has not been executed; even if it passes, it would
validate OBB extraction behavior only, not support axes or beam mechanics.

Keep these three scopes separate:

1. c11's source-audited solid-body gravity and whole-body wrench balance;
2. the conditional uniform-equivalent line-load scenario above; and
3. accepted beam section actions, which are not available.

No c11 support, member, contact, or connector force transfers to a changed
beam/support formulation.

**Missing and smallest actionable unblock.** Bind the selected beam station
axis, reference line, support span, local frame, density scenario, and a
sectioned mass-per-length and centroid profile to the exact member geometry.
Derive `q(s)` and eccentric moment along that axis; integrate to the source
mass and first moment within declared tolerances. Then verify signed section
force recovery on a small known-answer beam fixture and obtain independent
review. If only the uniform-equivalent scenario is defensible, retain it as a
conditional external-wrench approximation and do not report its local section
actions as exact design demands. The current beam demand gate remains blocked.

## Cross-gate dependencies, T09 deferral, and next decision

- Panel resultants require panel fastener/bearing transfer and receiver
  actions; receiver force sharing cannot be inferred from the six external
  wrenches. The panel and receiver records must close together before screw,
  member, or joint demands can be accepted.
- Receiver reactions route through the frame to the floor. The conditional
  floor law affects global support reactions and therefore the frame/member
  response. Do not carry c11 floor or connector reactions into another
  support model.
- Member self-weight is part of the same whole-frame response. c11's
  source-audited solid gravity proves external wrench accounting only; the
  conditional equivalent beam scenario does not substitute for a validated
  section-force recovery path.
- All six externally applied cases are input load wrenches, not complete
  internal joint demands. Materials, panel layups, contact/attachment laws,
  hardware carriers, body/element/DOF maps, and load mappings remain separate
  full-input gates.
- The parent has deferred T09 mesh-only work for this continuation. No mesh
  preparation, smoke test, or all-body mesh is included or authorized here.
  Reopen only after a separate parent go/no-go, exact input freeze, and
  method/readiness decision. A mesh would not close any gate above.

**Recommendation:** keep the six-case model **not ready**. First preserve and
review the four source-bound gate packets; return any design/evidence choice
to the parent. Only after all support, withdrawal, receiver, and beam-demand
paths plus the other complete-input gates close should the parent consider a
frozen full-frame response. The parent retains all readiness, run-budget,
mesh/solver authorization, and final-validation decisions.

## Append-only update — reviewed timber self-weight profile

Date: September 29, 2026. This update supersedes only the earlier status of
the beam self-weight *input evidence* above. It does not close the member
demand gate or change the other three gate dispositions.

The [current frame beam self-weight profile](../evaluation-resume-2026-09-24/current-frame-beam-selfweight-profile-attempt01/README.md)
is now independently reviewed and reproducibly verified. It bins 20 exact
timber STEP bodies into 599 finite slabs along the pinned grain-aligned member
descriptors. At the conditional modeled density of 600 kg/m³, it gives
127.5321817203 kg and 1,250.663469867 N. Aggregate gravity-force closure is
`4.67e-9 N`; first-moment closure is `4.60e-6 N·mm`. The rotated-box
known-answer fixture passes. Parent reran the packet's documented
`uv run --no-sync python3 .../produce.py --verify` command successfully; the
producer printed the pinned content digest
`3d3f11095091609940a3b0525ee4f65cb54bb0afc58772b5084eecbcb928b984`.

The independent Luna Max review found no blocking findings. Its scope check
reconciled the producer, record, source-member hashes, descriptor stations,
axis frames, gravity convention, fixture result, and aggregate closures.
The profile therefore advances the beam gate's source-bound, finite-bin
mass/centroid and whole-wrench accounting evidence to **CONDITIONAL input
evidence**. Its conditional assumptions remain modeled uniform density and
the pinned descriptor axes.

The gate remains **BLOCKED for exact beam/member demands**. The finite bins do
not define continuous `q(s)`, support spans and end conditions, transfer
through the still-open floor and receiver paths, or recovered section forces.
The separate section-force recovery method is deferred until support spans
and connection behavior can be specified; a later model-readiness gate must
include a signed section-force known-answer check. Do not treat bin couples as
an exact continuous eccentric-moment field or as design section actions.

This update leaves the conditional floor-support, panel-withdrawal, and
receiver/hardware-path gates **BLOCKED**, leaves overall six-case readiness
**BLOCKED**, and does not authorize geometry changes, mesh preparation, a
native solve, or physical work. The prior profile-related statement that its
separate source-derived profile packet was still needed is superseded by this
update and the linked reviewed packet. The older exploratory OBB script's
analytic-box check remains unexecuted and non-adopted; it is independent of
the new slab-profile packet's passed rotated-box fixture. The historical
matrix text above remains unchanged for provenance.

## Append-only integrated readiness decision — 2026-09-29

This parent synthesis incorporates the closed demand register, the reviewed
Option A/B comparison, the exact-hash-reviewed receiver/load-path ledger, the
exact-body material crosswalk, the reviewed finite-bin beam profile, and the
existing Hillman withdrawal preflight. It supersedes only stale descriptions
above that say the receiver ledger or beam profile is still to be created. It
does not change the reviewed geometry, loads, acceptance criteria, or native
run controls, and this addition has not had a separate cold review.

The exact-hash inputs used for this synthesis at its original integration are the [demand register](demand-coverage-register-2026-09-29.md)
`d745ca62f2fa66bf671227ed2089da8568d4237ae5e5a6180db773885f231072`,
[Option A/B comparison](option-ab-method-selection-2026-09-29.md)
`d73dc9b2583c88b64fab4a8e61b1910dfbdb2881cc6dde629b30911a5425c76a`,
[receiver/load-path ledger](receiver-load-path-ledger-2026-09-29.md)
`c1181907e211673d746741dcb47e95cf40fe0cb7ba858642e2ea53240c9c2673`,
[conditional material crosswalk README](../evaluation-resume-2026-09-24/current-full-frame-conditional-material-crosswalk-attempt01/README.md)
`2dc502af7061a2e50d3e2ff92ed7aead9e5c93a2e6faa7a57c55c42d255eced8`,
[material crosswalk JSON](../evaluation-resume-2026-09-24/current-full-frame-conditional-material-crosswalk-attempt01/conditional-material-assignment-crosswalk.json)
`540601bdbcc2cd321cdd600971d8eb3cc4b0f4436a19916513ec0d72705cc65b`,
[beam-profile README](../evaluation-resume-2026-09-24/current-frame-beam-selfweight-profile-attempt01/README.md)
`b0b86d8add77ad5b0906de542bbf7ce20634507ef784757d076f795ae2ed6cc0`, and
[Hillman withdrawal preflight](panel-withdrawal-preflight.md)
`22e4b14d270a1d7ba8a247562b901ef4998483ca7d70feed6646560a29c6d18f`.

## Append-only modeled receiver-order reconciliation — 2026-09-29

The candidate bolt-group inventory's read-only verifier confirms 88 unique
two-receiver axes with geometric head-to-nut interval proposals. The reviewed
[three-member supplement](bolt-groups/three-member-stack-order-attempt01/README.md)
verifier confirms the four remaining axes in two stacks. A direct ID-set
comparison finds the sets disjoint and their union equal to all 92 candidate
axes in the inventory. Both documented `--verify` commands pass. The current
[receiver/load-path ledger](receiver-load-path-ledger-2026-09-29.md) records
this integration; its prior exact-hash cold review remains the review of the
unmodified ledger baseline, not this later wording update.

This completes modeled receiver-member order coverage for the 92 candidate
axes and unlocks per-axis member assignment for future contact and connection
method work. Stop if either source pin changes or the axis union ceases to
cover all 92 IDs exactly once. The proposals do not verify delivered bolt
orientation or seating, contact restraint, forces, load sharing, stiffness,
capacity, or receiver-to-support transfer. The 12 retained frame-bolt
arrangements remain separate and unrechecked. The receiver gate and overall
six-case readiness remain **BLOCKED**; no mesh or native run is authorized.

### Bounded NDS applicability exception for 12 candidate axes

The verified geometry inventory identifies 12 candidate axes that are
parallel to one receiver's proposed grain direction: four `wj03_outer`
`knee_outer_*_inner_header_1/2` axes and eight `wj05_center_x190`
`center_post_header_*_1/2` / `center_principal_header_*_1/2` axes. The
existing [conditional NDS bolt screen](nds-screen/README.md) assumes the
bolt axis perpendicular to both member grains and expressly excludes
end-grain-axis connections, so its illustrative individual values do not
apply to these 12 as candidate capacities. Its source discussion identifies
the conditional main-member end-grain route in NDS-2024 §§12.3.3.4 and
12.5.2.2, but the actual main/side role, delivered diameter/orientation,
signed actions, and group interaction remain unknown.

The useful result is a source-bound exception list that prevents using the
perpendicular-grain scenario where its assumptions do not hold. Stop before
assigning resistance until those roles and delivered properties are
established and the NDS geometry/action factors can be checked. This narrows
method preparation; all four demand gates and six-case readiness remain
**BLOCKED**.

A focused Luna Max review returned **PASS** for the 12-axis/member join,
perpendicular-axis screen assumption, and stated limits. It confirmed the
proposed-grain directions are not observed stock and that no end-grain
capacity was applied.

| Gate | Usable result or check gained | Exact remaining input | Engineering result unlocked | Stop condition |
|---|---|---|---|---|
| Conditional floor support | The owner-selected analytical premise is no slip while a floor cell bears. The existing normal-contact and isolated spring fixtures pass only their stated scopes. c11 is one equilibrated `a12-rear` branch, but six compression-only checks fail; it is not a valid support response. | A finite law for initial bearing, open/release, and re-engagement references; coupled normal/tangent state selection and termination; and a reproducible known-answer state check. The existing feasibility plan already specifies the hand-solvable open/bear/release and tangent reset oracle. No physical friction coefficient or floor test is authorized by this assumption. | A bounded candidate floor-state rule validated on the specified local fixture, sufficient to scope a later parent-reviewed Option B implementation. This alone does not provide whole-frame reactions. | Stop if state selection or reset behavior is ambiguous, unbounded, or fails the specified oracle. Keep floor reactions and every support-dependent demand unresolved; do not transfer c11 forces. |
| Panel withdrawal | Six source-bound outward panel resultants are **1,199.82–1,659.44 N** before gravity. The exact purchased Hillman 42605 product is identified. The preflight gives only a conditional NDS reference scale, not a product rating. | Applicable resistance and load-slip/stiffness basis for the exact screw and installation (product eligibility or supported allowance, actual thread penetration/root/steel, pilot and countersink, head/panel limit), defensible group interaction, and the signed transfer from panel axes through receiving members to the frame. | Signed six-case screw-group/per-axis actions and applicable product/NDS withdrawal, lateral, head/panel, and interaction checks. | If the exact installed product has no applicable resistance/stiffness or group basis, mark the path uncheckable. Do not borrow SPAX data, use the illustrative NDS arithmetic as capacity, or divide panel load equally among screws. Missing evidence is not a finding that the screws physically fail. |
| Receiver and hardware paths | Source identity and nominal geometry are reconciled for 24 blocks, 92 candidate axes (88 two-receiver axes and four axes in two three-member stacks), 12 starting frame-bolt arrangements, and 66 Hillman axes. The source gravity map closes bookkeeping; the reviewed material crosswalk covers exact STEP identity and conditional orientations for 44 wood bodies. | For each loaded interface: adopted carrier/member roles, attachment or bearing law, source-backed stiffness or an explicit unresolved basis, solver body/element/DOF mapping, signed simultaneous interface actions, supported sharing/group interaction, and equal/opposite transfer through each receiver to runners/floor. Six panel layups, steel/hardware roles, density assignments, and complete solver mappings remain false/unassigned in the material crosswalk. | A closed receiver-to-frame-to-support action ledger, followed by applicable bolt, wood bearing/splitting, panel, and member checks. | Stop where any loaded route lacks an identified carrier/law or force-sharing basis. Geometry intersections, bolt counts, or source-wrench closure cannot stand in for force transfer; do not accept any c11 connector reaction. |
| Beam/member demand | The reviewed 599-bin profile covers 20 exact timber bodies at the conditional 600 kg/m³ scenario: **127.5321817203 kg**, **1,250.663469867 N**, force closure `4.67e-9 N`, and first-moment closure `4.60e-6 N·mm`. Its rotated-box fixture passes. | Adopted density/material assignment; a source-supported structural station axis and support span/end behavior from the closed receiver paths; continuous or otherwise justified local member load mapping; and signed `N/V/M/T` section-recovery requirements with a known-answer beam fixture. | Per-case signed member actions, deflection/stability outputs, and code-check demands consistent with the actual member support and load model. | Stop if the support span, end behavior, or line-load/section method is unsupported. Keep the profile as conditional mass/wrench evidence; do not report its bins or mean equivalent loads as exact beam demands. |

**Binary readiness: NO.** Keep Option B as the selected route, but do not
freeze the full response model or start a six-case solve. The existing records
still show no path-complete member/joint demand subset, and all 47 MVP-E
criteria remain pending. This is an evidence/readiness disposition, not a
physical failure finding. Even if these four gates close, the full input audit
must still resolve material/body assignments and solver mappings before a
parent-owned freeze or native-run decision. T09 remains deferred; this
synthesis grants no mesh or solver authority.

The bounded next task is to close the missing evidence for the conditional
floor state law against the already-specified fixture, then return to the
panel and receiver paths with exact product/law inputs. Its engineering result
is a finite, unambiguous local state rule for open/bear/release/re-engagement,
which permits a later parent decision on whether to scope a frame
implementation. It does not validate a full-frame solver or produce support
reactions. Stop if the existing fixture cannot be satisfied with that rule;
leave the floor-dependent response blocked and report the exact unresolved
state behavior. Do not add another generic contact coupon or widen the solver
scope.

## Append-only Option B evidence update — 2026-09-29

This update supersedes only the preceding immediate-next-task paragraph and
adds scoped evidence to the four gate rows. It reuses the reviewed Option A/B
comparison, demand register, receiver/load-path ledger, material crosswalk,
and timber self-weight profile; none is recreated here. Option B remains the
selected route. This update changes no geometry, load, criterion, readiness
flag, or native-run control. Missing evidence remains an open engineering
input, not a physical failure finding.

### New usable results

| Gate | New result | What it unlocks | What remains open |
|---|---|---|---|
| Conditional floor support | The [two-cell normal/tangential fixture](conditional-floor-two-cell-coupled-stick-fixture-attempt01/README.md) passes eight hand-checkable stages: each has one normal active set, open contacts carry zero tangent force, re-engagement resets the tangential reference, and the maximum normal residual is `2.274e-13`. The [accessory-aware support resultant check](accessory-support-resultant-attempt01/README.md) reconstructs 54 case/scenario wrenches; every resultant CoP lies inside the modeled hull, with a minimum edge margin of `389.254 mm` and resultant normal force `4,670.093 N`. | A bounded local candidate rule for normal opening/bearing plus one-direction ideal stick/release/reset, and a necessary gross-hull equilibrium screen under all nine existing accessory placements. | Neither artifact gives the eight foot reactions, validates the real floor, proves no-slip capacity, checks the internal path, or produces whole-frame member/joint actions. The floor gate remains **BLOCKED**. |
| Panel withdrawal | The [group-total screen](panel-screw-group-total-withdrawal-attempt01/README.md) finds conditional outward axial-tension lower bounds of `1,199.82–1,659.44 N` for five cases under normal-only contact and zero tangential contact transfer. `a1-rear` remains unbounded because of a finite opposing-normal kicker/panel patch. | A bounded minimum total action for five panel groups, useful for requesting or screening exact product resistance evidence. It does not distribute action among screws. | Exact Hillman 42605 resistance, load-slip stiffness, installed thread engagement, head/panel limit, group sharing, and receiver transfer remain absent. The panel gate remains **BLOCKED**. |
| Receiver/hardware | The [candidate bolt-group inventory](bolt-groups/README.md) provides geometric head-to-nut order proposals for 88 two-receiver axes; the [reviewed three-member-stack supplement](bolt-groups/three-member-stack-order-attempt01/README.md) resolves the remaining four. Their disjoint IDs cover all 92 candidate axes under the pinned attempt04 geometry. | Complete modeled receiver-member order for per-axis assignment and targeted path/law checks. The 12 retained frame-bolt arrangements remain a separate set. | Modeled order does not establish delivered orientation or seating, contact restraint, signed actions, force sharing, stiffness, capacity, or transfer. The candidate receiver gate remains **BLOCKED**. |
| Member demand | No new member section action is gained. Keep the previously reviewed conditional finite-bin mass/centroid profile and its limits. | It remains a source-bound gravity-wrench input for a later supported frame model. | Support spans, end behavior, action transfer, adopted material assignments, and verified section-force recovery remain missing. The member-demand gate remains **BLOCKED**. |

The local contact fixture received a focused exact-hash Luna Max review with
**PASS** and no blocking or nonblocking findings. The reviewer confirmed the
normal and tangent signs, all eight state/reaction answers, re-engagement
references, residuals, source pins, local checksum, and README links. Its
reviewed result supports only the bounded two-cell state-selection case. The
accessory, five-case panel-group, and stack-order packets also have focused
Luna Max passes recorded in their review trail. Their scopes are as limited as
the table states.

### Bounded next work and stop conditions

Do not create another generic contact coupon or repeat completed handoff,
demand-register, A/B, crosswalk, receiver-ledger, or beam-profile reviews.
Continue in this order:

1. **Close the panel-product evidence question.** The engineering result is
   either an applicable resistance/load-slip basis for the purchased Hillman
   42605 installation that permits a five-case group screen to be compared
   with resistance, plus a resolution for `a1-rear`, or a documented finding
   that this product path is not checkable from available evidence. Required
   inputs are exact product qualification/properties, root and head geometry,
   actual thread penetration, installed pilot/countersink basis, plywood/head
   limit, and a defensible group-sharing basis. Stop if any of these are
   unavailable; retain the five conditional group minima and `a1-rear`
   exception without assigning capacity or per-screw actions. An owner-selected
   complete alternate tension path would be a separate design decision.
2. **Close receiver actions only where a carrier and law are supported.** The
   engineering result is a signed, equal-and-opposite action ledger for a
   mechanically complete path from loaded panels and block interfaces through
   the frame to the support, followed by applicable NDS/product resistance
   checks. Reuse the reviewed receiver ledger and the new stack-order result.
   Exact inputs still include selected connector/member roles, delivered
   bolt properties/dimensions, supported attachment or bearing law and
   stiffness where distribution depends on it, member/panel properties,
   and solver body/element/DOF mapping. Stop at the first loaded interface
   without an identified carrier, force-sharing basis, or downstream route;
   do not infer actions from geometry or c11.
3. **Defer beam section checks until those paths close.** The engineering
   result is signed per-case `N/V/M/T` and stability/deflection quantities
   that can be compared with code limits. Required inputs are the resulting
   support span/end behavior, adopted density and material assignment, and a
   source-bound distributed-load/section-recovery method with its known-answer
   check. Stop if the support path or local load mapping is unresolved.

The new floor artifacts permit a later parent decision on whether the full
frame implementation is sufficiently specified; they are not whole-frame
validation and do not authorize a native run. Overall binary readiness remains
**NO**: no path-complete member/joint demand subset exists, the four gates
remain blocked, and all 47 MVP-E criteria remain pending. Parent retains
frozen-input readiness, native-run controls, serialization, and final
validation.

### Exact pins for this update

- [Coupled two-cell fixture README](conditional-floor-two-cell-coupled-stick-fixture-attempt01/README.md):
  `2882f420b8b8bda0db5677aacfae0682407394e6aa13740af7ea6946c96c2c37`;
  [input](conditional-floor-two-cell-coupled-stick-fixture-attempt01/fixture.json):
  `c4fbb8b9c1d87ddba3b848c113bda540945b67a3d0d9435150a5c5e1d195de31`;
  [verifier](conditional-floor-two-cell-coupled-stick-fixture-attempt01/verify_fixture.py):
  `79fd9586306f81d2bf1a6cfc8cb22ca20bd85addd1b2fa8dd546eeb4ab950028`;
  [observed result](conditional-floor-two-cell-coupled-stick-fixture-attempt01/observed.json):
  `5dd5e3ed76ffc3a13e79edeb28731328deb66e5d065fa8cbd83674f5f4340449`.
- [Accessory support README](accessory-support-resultant-attempt01/README.md):
  `2fd59b6f5546034d6986ad63acfeec53dc2ba6a49556b81a363f9ff355e243ae`;
  [result](accessory-support-resultant-attempt01/accessory-support-resultant.json):
  `adc1507a5540c54a701f95b7291b0e765819b502c39e33df164b3f805af5e76d`;
  [checksums](accessory-support-resultant-attempt01/SHA256SUMS):
  `263c32475897368a34133a33256e2fdd19c0303854acf323cde87b7892a11f7d`.
- [Panel group README](panel-screw-group-total-withdrawal-attempt01/README.md):
  `6946b2d4cdc7696d41d397e4b9b167e8f2cf6f32d932d61758cefa2028ecd7ae`;
  [result](panel-screw-group-total-withdrawal-attempt01/panel-group-result.json):
  `11f79aa4e0d4cc1a84c22f95406da59393b1e97a8f536985bdb4ad172e69ef94`;
  [checksums](panel-screw-group-total-withdrawal-attempt01/SHA256SUMS):
  `0e7cc365d611cbd55dfb24bf6187dd827ca40d26397f330ba13955c0461929b3`.
- [Three-member-stack README](bolt-groups/three-member-stack-order-attempt01/README.md):
  `55d5a87d8aaeaf6c2712f73c3ce7fa238f4981f8e33fb57768f66a005216d3d3`;
  [result](bolt-groups/three-member-stack-order-attempt01/receiver-stack-order.json):
  `e6a6d242ae2a62ecefafc4acbe8f3ea78a916aac4f48f53bdff84ec3c773055e`;
  [checksums](bolt-groups/three-member-stack-order-attempt01/SHA256SUMS):
  `3156feb6f3c1c07d4487c2ae223bd5ef570b17cf0ca421d58c47e934cbc26f2c`.
## Append-only Option B continuation — support-reaction envelope and product-source disposition

This update reuses the reviewed accessory resultant, panel group-total screen,
receiver ledger, and current exact-product preflight. It adds a statics-only
vertical reaction envelope and records the outcome of the focused public
source screen for Hillman 42605. Geometry, load cases, acceptance criteria,
and native-run controls are unchanged.

### Usable floor-support result

The [normal foot-reaction bounds packet](normal-foot-reaction-equilibrium-bounds-attempt01/README.md)
is source-pinned to the existing eight support-face polygons and 54
case/accessory wrenches. Its local verifier and checksum pass, and an
independent Luna Max review reproduced all 432 face bounds and 864 extreme
witnesses. The witnesses close vertical force within 9.10e-13 N and CoP
within 2.17e-12 mm.

Every case has at least one nonnegative vertical-reaction distribution over
the eight modeled faces. Each individual face has a zero minimum in every
scenario when optimized independently; the endpoints cannot be combined into
one reaction vector. The largest statically admissible one-face resultant is
3,605.070 N at base_floor_left, for a12-left with
split_12_5_kg_hold_at_kicker_1; total normal resultant is 4,670.093 N.

This unlocks an outer equilibrium envelope for vertical support allocation and
shows that whole-assembly statics alone forces no particular named face to
carry load. It does not predict actual foot reactions or contact states, and
does not supply pressure, floor resistance, friction, internal transfer, or
member/joint demands. The floor gate remains **BLOCKED**. Stop if a source
pin changes, a scenario has no admissible distribution, or a witness misses
the recorded equilibrium tolerance; do not turn this outer envelope into
native reactions.

### Hillman 42605 public-source disposition

The focused exact-product source screen found no applicable published
withdrawal resistance, axial load-slip stiffness, root/head dimensions, or
qualification basis for the purchased 42605 installation. The [Lowe's
product Q&A](https://www.lowes.com/questions/fas-n-tite-42605-deck-screws/999995042/f4fd545e-48c7-5ada-90ea-db1169f463ee)
says Hillman does not list a tensile-strength rating for this product.
The [existing preflight](panel-withdrawal-preflight.md) already separates the
generic NDS #10 reference value from a 42605 capacity, and explains why the
round-head NDS pull-through provision does not establish resistance for this
flat countersunk screw in plywood. An indexed qualification search found no
exact-model 42605 evaluation report; the located [ESR-4839](https://cdn-v2.icc-es.org/wp-content/uploads/report-directory/ESR-4839.pdf)
was for a different Power-Pro stainless product and is not transferable.

The current public-data disposition is **UNCHECKABLE**, not physical failure.
The five conditional group-total minima remain 1,199.82–1,659.44 N;
a1-rear remains unresolved because the opposing-normal kicker/panel patch
has no adopted action law or capacity. Stop public-source re-search unless
new exact-product information appears. Closing the screw-dependent path
requires an exact-model installation/property package or matched testing
covering resistance and load-slip response, actual penetration and head/panel
limit, plus a defensible group-sharing basis and transfer through the
receiving frame. A complete alternate tension path requires a separate
owner-directed design decision.

### Current handoff sequence

1. Keep the panel screw path **BLOCKED / UNCHECKABLE from current public
   sources**. The engineering result that would reopen it is an applicable
   exact-product or matched-test basis that can be compared with the five
   group-total bounds and can address a1-rear; stop if product/install
   applicability, group behavior, or the alternate contact path remains
   unsupported.
2. Continue receiver work only at an interface with an identified carrier and
   a supported force-transfer law. The target result is signed simultaneous
   equal-and-opposite actions through a complete receiver-to-runner/support
   route, with applicable code/product checks. Stop at the first missing
   carrier, law, sharing basis, or downstream route; geometry and c11 branch
   reactions are not substitutes.
3. Recover beam/member actions only after those routes and support behavior
   are specified. Reuse the reviewed finite-bin mass profile and stop if
   adopted material, member spans/end behavior, or section-recovery inputs
   remain unresolved.

The floor-reaction packet is statics evidence only. Overall binary readiness
remains **NO**; all four demand gates remain blocked, no path-complete
member/joint demand subset exists, and all 47 MVP-E criteria remain pending.
This update grants no geometry change, mesh, native solve, fabrication, or
physical-test authority.

## Append-only panel withdrawal threshold update — assigned gravity — 2026-09-29

This update reuses the frozen six-case loads, panel receiver map, reduced-static
body-force rows, and contact geometry. It adds the loaded panel's conditional
self-weight and source-assigned same-panel T-nut gravity to the earlier
climber-only group-total screen. The [attempt02 packet](panel-screw-group-total-withdrawal-attempt02/README.md)
is exact-hash reviewed **PASS**; its verifier and checksum pass.

At the conditional 600 kg/m³ panel-density scenario, five cases have
normal-only compression-contact lower bounds of **1,304.24–1,763.87 N** on
the sum of twelve aligned panel-screw axial tensions. `a12-rear` governs at
1,763.868 N. The bound includes 104.078–104.424 N of assigned panel/T-nut
gravity in addition to the climber-load outward component. For `a1-rear`, the
body outward resultant is 1,763.734 N, but the finite
`kicker_left`/`main_lower_left` patch permits an inward compression reaction;
no group lower bound is established for that case.

This unlocks an updated total-group withdrawal threshold for comparing with
applicable exact-product or matched-test evidence. It does not assign
per-screw actions, a finite upper bound, product resistance, or transfer to the
receiving frame. The Hillman 42605 path remains **BLOCKED / UNCHECKABLE from
current public data**, and the receiver-to-frame path remains open. Do not
repeat the public search or extend this arithmetic unless new product,
installation, or contact-state evidence changes the inputs. Missing evidence
is not a physical failure finding.

Independent Luna Max review confirmed the source hashes, body-force
reconciliation, conditional panel density, twelve axis directions, all six
contact-normal dispositions, and the stated claim limits. No geometry, mesh,
native input, or solver run changed. Overall readiness and all four gate
statuses remain unchanged.

Exact packet pins: [README](panel-screw-group-total-withdrawal-attempt02/README.md)
`d67618407907c4fc1849f4758b3a4eabc589d763cc1b4dc3ed588902e6d86182`;
[result](panel-screw-group-total-withdrawal-attempt02/panel-group-with-gravity-result.json)
`ba6ac176bea3898425b1391aba5897c57170afafb50d0d3915dee048f8bdc225`;
[verifier](panel-screw-group-total-withdrawal-attempt02/verify_panel_group.py)
`7f355d3ed7c5773bec09b8e7ff5e2cd94ee390278b742068bf43939dd50d8f14`;
[SHA256SUMS](panel-screw-group-total-withdrawal-attempt02/SHA256SUMS)
`3bbce99b86465ef2f9a4d0f25b15e706cc6bba2cb10d59487e0a63685e42bf56`.

## Whole-support horizontal and yaw resultant update — 2026-09-29

The existing exact-hash [accessory-aware support packet](accessory-support-resultant-attempt01/README.md)
also records the integrated horizontal force and yaw-moment reactions required
by global equilibrium. Its read-only verifier was rerun; all 54 case/accessory
wrenches reconstruct and all normal center-of-pressure points remain inside
the modeled support hull. Reaggregating the saved rows confirms that each
load case has the same tangential resultant and yaw reaction across all nine
accessory scenarios:

| Load case | Required global floor tangent resultant `(Fx,Fy)` (N) | Magnitude (N) | Required global floor yaw reaction `Mz` (N·mm) |
|---|---:|---:|---:|
| `a1-rear` | `(0, -300)` | 300 | `+305,760` |
| `a12-forward` | `(0, +300)` | 300 | `−305,760` |
| `a12-left` | `(+300, 0)` | 300 | `−464,866.130` |
| `a12-rear` | `(0, -300)` | 300 | `+305,760` |
| `k12-rear` | `(0, -300)` | 300 | `−294,240` |
| `k12-right` | `(−300, 0)` | 300 | `+464,866.130` |

This supplies a whole-support boundary demand for later action closure: the
six cases require a 300 N total horizontal reaction, with absolute yaw
reaction up to `464,866.130 N·mm`. It is global equilibrium bookkeeping, not
the distribution among eight modeled faces, an internal frame reaction, a
floor capacity or friction check, an anchor demand, or proof that the
conditional no-slip assumption is physically satisfied. The floor-support
gate and all support-dependent member/joint demands remain **BLOCKED**.

Stop using this envelope if the pinned load, gravity/accessory, or support
inputs change, or if any of the 54 reconstructions fails its recorded
tolerance. Do not infer local foot reactions from these resultants. The
packet pins are [README](accessory-support-resultant-attempt01/README.md)
`2fd59b6f5546034d6986ad63acfeec53dc2ba6a49556b81a363f9ff355e243ae`,
[result](accessory-support-resultant-attempt01/accessory-support-resultant.json)
`adc1507a5540c54a701f95b7291b0e765819b502c39e33df164b3f805af5e76d`, and
[verifier](accessory-support-resultant-attempt01/verify_accessory_support.py)
`06048ed3f09d4b0e8283bbdc3ba79d3234334204431d8ce7b0cf6c2a21da2efc`.

## Bounded left center-kicker path screen — 2026-09-29

This screen follows only the left center-kicker branch using the already
reviewed receiver ledger, exact-BRep contact graph, center-screw receiver map,
hardware schedule, and NDS exception list. It finds no signed internal action
or applicable capacity check that can be assigned from the current inputs.

For `a1-rear`, the loaded `main_lower_left` panel has a conditional outward
resultant of `1,763.734 N` after assigned panel/T-nut gravity. Its finite
contact with `kicker_left` is `425.577 mm²`, but no active-contact law or
force-share basis is adopted; this is the first stop on this branch. The
existing panel-group screen therefore makes no screw-group lower-bound claim
for this case. For upper-left load cases, `main_upper_left` is separated from
`kicker_left`; a route through `main_lower_left` crosses a `22,229.038 mm²`
panel-to-panel contact and then the same unsupported lower-panel/kicker
interface. Those areas and states are geometric evidence only.

The two moved center-kicker Hillman axes enter `base_post_center_left`. Their
modeled receiver overlap is `45.24375 mm` full-section-equivalent and the
kicker/post face area is `9,075.165 mm²`; neither is installed engagement or
a load-transfer result. The exact-product disposition remains **UNCHECKABLE**
from current public data. Downstream, `center_post_left_1/2` and
`center_post_header_left_1/2` identify post/cleat/header bolt interfaces, but
delivered bolt products, material roles, signed actions, and group checks are
unassigned. The latter two axes are among the proposed-grain NDS end-grain
exceptions; do not assign the perpendicular-grain illustrative bolt values.
A separate `5,322.570 mm²` post/header seat is geometrically present in
parallel with the cleat route, with no adopted seat law or share. No route
continues from these interfaces to runners/floor with signed actions.

The useful result remains at the boundary: each case requires `300 N` net
global tangent and up to `464,866.130 N·mm` absolute global yaw reaction;
the vertical normal resultant is `4,670.093 N`. These whole-support
resultants do not allocate force to the center-kicker branch. The five
conditional panel-group minima in attempt02 likewise remain total actions on
the loaded panel's twelve aligned screws, not forces on the two center-kicker
axes.

The next engineering result that can close this branch is a signed,
equal-and-opposite action path through an interface with an identified
carrier, supported contact/attachment law and sharing basis, followed by
applicable product/NDS checks to the conditional floor support. Stop at the
first loaded interface without that law, basis, assigned product/material, or
downstream route. Current exact missing inputs are the lower-panel/kicker
contact state and transfer law (or a documented alternate tension path),
applicable installed Hillman resistance/stiffness and group evidence if the
screws carry tension, selected bolt/nut/washer properties and member roles,
and the post/cleat/header-to-runner transfer. Missing evidence is not physical
failure. This screen changes no model choices, geometry, criteria, or
native-run controls and authorizes no solver work.

Exact source pins: [contact-map README](../evaluation-resume-2026-09-24/current-geometric-interface-map-attempt02-2026-09-28/README.md)
`00ea09173fa3e15f3a90b5bdc7297de7bf7ac8ef358e7015508bed6c94bfa47e`;
[contact graph](../evaluation-resume-2026-09-24/current-geometric-interface-map-attempt02-2026-09-28/complete-contact-graph.json)
`7806242ac48b198becf5db97b16b6a5605021b8d86b964f0f02adb6806aeec26`;
[receiver map](../evaluation-resume-2026-09-24/current-geometric-interface-map-attempt02-2026-09-28/receiver-screen.json)
`851495f2ccc80f286a7eae97fc54bcf602a478bb7d4e13eb28e2ae44cfb87991`;
[receiver screen](../../current-receiver-screen.md)
`297f557feba46c169ddc046070ac86936aabd2ae589bd8bed301c4d95f0d27c2`;
[hardware schedule](../../current-hardware-schedule.md)
`47a1de21705570cfd23fb493c640d8983945ee410623e15484cf53ed7596bffa`.

## Conditional candidate-bolt pitch screen — 2026-09-29

The verified [candidate bolt inventory](bolt-groups/README.md) contains 92
modeled axes in 46 two-axis geometry groups. All modeled shaft diameters are
6.35 mm; the minimum modeled perpendicular center pitch is 33.0 mm, or
approximately `5.20D` (7.6 mm above `4D`). Multiple groups share the minimum.
These are model centers and a model diameter, not verified installed holes or
delivered bolts. The inventory itself cautions that its geometry groups are
not NDS load-aligned rows and its pitch is not an NDS spacing result.

One limited comparison is possible: **if** installed center pitch is at least
33 mm and delivered bolt diameter is at most 8.25 mm, the pitch exceeds `4D`
for a true parallel-to-grain row. Under that orientation, this clears the
row-spacing threshold for the full NDS geometry factor `CΔ` in Table 12.5.1B.
It does not establish the perpendicular-to-grain attached-member spacing,
oblique-load shear-area check, spacing between rows, or end/edge distances.
Those checks require delivered diameter, actual hole centers/tolerances and
finished member boundaries, actual receiver roles/grain/shear planes, and
signed per-member lateral actions to classify rows and loaded ends/edges.
Apply the [NDS-2024 Chapter 12](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf)
provisions in §§12.1.2–12.1.3 and 12.5.1, Tables 12.5.1A–D, only after those
inputs are established; the repository's [source correction note](../../bolt-dimension-source-correction.md)
records the chapter PDF pin.

This geometry screen does **not** show that bolt ratings act independently.
`CΔ` spacing/end-distance geometry is separate from `Cg` group action and
from the force distribution within an eccentric or multi-member joint. Do
not multiply the individual-bolt reference values by bolt count or infer
equal sharing. The receiver/hardware gate remains **BLOCKED**. Stop before an
NDS detailing or capacity disposition if delivered size, installed geometry,
member roles/grain, load direction/actions, or the downstream transfer path
is still unknown. No geometry, criteria, native input, or run control changed.

Exact inventory pins: [README](bolt-groups/README.md)
`faa50a5f9ca08ca5c40eaff30950b4ed4a56baf5fe9415517f1be8149266b458`;
[JSON](bolt-groups/bolt-groups.json)
`4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4`.

## Source-assigned panel/screw subsystem boundary wrench — 2026-09-29

The new [bounded packet](panel-screw-subsystem-boundary-wrench-attempt01/README.md)
reuses the frozen six-case load contract and mass-centroid record to form one
free body from the six panel bodies, 142 source-assigned T-nuts, and 66
panel/kicker screw-axis mass proxies. Under the conditional modeled mass
scenario, that group is 74.044731 kg with its center at
`(−1.873, 678.050, 1106.366) mm` and gravity resultant `(0, 0, −726.131) N`.
The packet reports the six signed **aggregate** reactions required from the
remaining frame, including moments about that group center; the reaction is
not divided among the 66 axes, panel bearing faces, blocks, or members.

This provides a six-component receiver-family balance target for checking a
future assembled response. Internal panel-panel actions cancel because the
complete panel set is inside the free body. The panel density remains the
conditional `600 kg/m³` scenario; screw masses remain axis-envelope proxies;
the separate 25 kg accessory allowance is excluded. It does not demonstrate
that the interfaces are active, determine individual actions or capacities,
or close a member/joint demand path. Stop before distributing the group
wrench without an adopted transfer law and force-sharing basis. The four
demand gates and overall readiness remain **BLOCKED / NO**; no geometry,
criterion, mesh, or native-run authority changes.

Exact pins: [README](panel-screw-subsystem-boundary-wrench-attempt01/README.md)
`404affb913f27583fb605a7b2c13ac81d31a48e9c54f546244dc56f30d5b6722`;
[producer](panel-screw-subsystem-boundary-wrench-attempt01/produce.py)
`9c02433a8e465bc6ba60f4bfcf771a9c1582a475d6cf00ec6429149665f95952`;
[result](panel-screw-subsystem-boundary-wrench-attempt01/panel-screw-subsystem-boundary-wrench.json)
`75cc10d534f915bf18cc4c6c1fff467cc96ab1c354ca2602674ef13f3d73972b`.

## Derived panel-screw peak-force consistency floors — 2026-09-29

Using the exact-hash-reviewed [gravity-inclusive panel-group result](panel-screw-group-total-withdrawal-attempt02/README.md),
the maximum axial tension among a panel's 12 screws cannot be smaller than
the established total-group lower bound divided by 12. This follows from
nonnegative screw tensions (`max(T_i) ≥ ΣT_i/12`); it does **not** assume equal
sharing or identify which axis is most loaded.

| Case | Total-group lower bound (N) | Necessary minimum on `max(T_i)` (N) |
|---|---:|---:|
| `a12-rear` | 1,763.868 | **146.989** |
| `a12-forward` | 1,304.242 | **108.687** |
| `a12-left` | 1,534.055 | **127.838** |
| `k12-right` | 1,533.709 | **127.809** |
| `k12-rear` | 1,763.522 | **146.960** |
| `a1-rear` | Not established | Not established |

This adds a consistency floor for any later per-axis tension vector: a vector
below the tabulated peak in a listed case would contradict the group-total
bound. It is not a per-screw design demand, does not show that every screw
must resist that force, and supplies no capacity or demand/capacity check.
`a1-rear` remains unresolved because its finite opposing-normal
panel/kicker contact may carry some or all of the normal action. The
receiver-to-frame path, actual Hillman 42605 resistance/load-slip data, and
group distribution remain missing. Stop before assigning per-axis forces or
claiming product acceptance until those inputs and the complete downstream
path are established. The source result JSON is pinned at SHA-256
`ba6ac176bea3898425b1391aba5897c57170afafb50d0d3915dee048f8bdc225`.

## Bounded source check of conditional lateral-slip stiffness — 2026-09-29

The cited [Swedish Wood Volume 2 (2022)](https://www.swedishwood.com/siteassets/5-publikationer/pdfer/sw-design-of-timber-structures-vol2-2022.pdf),
§9.2 / Table 9.2, describes `Kser` per fastener and shear plane. Its table
lists bolts (with or without clearance), screws, and pre-drilled nails under
`Kser = ρm^1.5 d / 23`; it says to add bolt clearance separately. The
conditional lateral-slip expression in
[`wood_joint_reduced_properties.py`](../../../../fea/wood_joint_reduced_properties.py)
matches that comparison and keeps modeled radial clearance separate. The
source also says the volume is for education and is not an official document
for practical structural design; it directs designers to the original
Eurocode documents. This is therefore a conditional EC5 service-slip
comparison, not an adopted U.S. design property, product qualification, or
capacity.

Independent standard-library arithmetic on the source-coded proxies gives
`3,086.746 N/mm` for a modeled 6.35 mm candidate bolt at 500 kg/m³, and
`2,689.679 N/mm` for the nominal #10 Hillman lateral comparison using the
modeled 4.826 mm basic diameter and geometric-mean 547.723 kg/m³ timber/panel
density proxy. These are per-fastener, per-shear-plane scenario values; they
are not measured stiffnesses. The property builder keeps Hillman axial
stiffness null in its no-credit baseline. The response adapter's default
ratio-1.0 axial spring is explicitly a non-qualifying diagnostic that equates
axial withdrawal stiffness to lateral `Kser`; Table 9.2 does not support that
axial equivalence. The 104 through-bolt outer-seat axial springs instead use
a separate conditional steel-plus-wood-seat series model, whose washer-seat
and timber-column assumptions also remain unverified.

This closes only the narrow question of whether the cited formula includes
the general bolt and screw categories. Stop before using it as candidate
stiffness or as an axial law until delivered fastener dimensions, actual wood
density/product applicability, installed clearance and engagement, and the
complete receiver path are evidenced. Exact local inputs: `model-inputs.json`
SHA-256 `178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9`;
property builder SHA-256
`26b6e8bf8800208bfb867439694afa705558ac63ca338778e9210e940a55d9a1`;
connection model SHA-256
`f94b1161b984b7599f6c8d4a131ad49a3f12a0033ec6a0b6b5892a5b9d45e2f7`;
saved assembly record SHA-256
`b474c686355b6fa74dfe158344340ebcb817f128a3c29f32bdb042649e93e02e`.

## Append-only load-boundary disposition — 2026-09-29

The earlier integrated next-step note listed owner resolution of
hold/T-nut inclusion as a remaining boundary input. The frozen [six-case load
contract](../evaluation-resume-2026-09-24/current-load-cases.json), SHA-256
`9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a`, already
defines each climber case as a force on a 20 mm panel patch centered at the
hold-face datum plus its equivalent 100 mm standoff moment at the panel
midplane; it assumes no joint law, connection stiffness, force sharing, or
capacity. The reduced-case builder (`fea/wood_joint_reduced_case.py`, SHA-256
`9b442e85221c383f1ad013dd493d87c9d4a303b6e36f58b2733f5de00316e192`) applies
exactly one case patch to the loaded physical panel. That resolves the
analytical boundary for these six load cases: carry the frozen wrenches
directly into the panel model, and do not add the same climber action at
T-nuts.

The repository's `validate_current_load_contract` accepted the pinned JSON.
An independent standard-library reconstruction checked all six force vectors
and `(force point − panel-midplane point) × force` moments; maximum moment
discrepancy was `0 N·mm`. This validates the applied-wrench inputs and their
case-level mapping, not any structural response.

This is a scope clarification, recorded with its physical limits in the
[receiver/load-path ledger](receiver-load-path-ledger-2026-09-29.md). It does
not establish the physical hold-to-bolt/T-nut-to-panel path or qualify that
hardware. The distinct T-nut weight bookkeeping remains gravity accounting.
The engineering result unlocked is a settled input boundary for panel-to-frame
analysis; it does not provide a panel/screw force distribution or downstream
member actions. Stop using this clarification if the pinned contract or its
panel patch/standoff mapping changes, or if the required result becomes a
physical hold-attachment check.

The next work remains receiver/load-path closure under the existing gates:
source-backed transfer laws and mappings, signed simultaneous actions, and
equal-and-opposite closure through the frame to the conditional floor support.
Exact Hillman withdrawal/load-slip and group evidence, receiver laws/sharing,
and accessory scenario selection or measured placement remain missing as
applicable. This update resolves no gate and authorizes no model, geometry,
mesh, native-run, or physical-work change.

## Append-only upper-panel no-axial force-cone sign check — 2026-09-29

This bounded check addresses the tolerance caveat in the saved
[panel-path LP review](reduced-static-attempt01/panel-path-screen-review.md).
The source inventory pins commit `df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb`;
its recorded 40-degree frame normal is `(0, -cos 40°, sin 40°)`, and the
main-panel screw axes use that direction. In the frozen reduced inputs, each
upper panel has twelve bit-identical screw axes
`a = (0, -0.7660444431189781, 0.6427876096865394)`. Let outward
`u = -a`. The lateral-only screw law permits forces perpendicular to `a`, so
their force projection on `u` is zero by definition.

The [read-only sign auditor](reduced-static-attempt01/panel_direction_cone_audit.py)
pins `model-inputs.json`, `contact-geometry.json`, the saved LP script, and its
saved result by SHA-256. It interprets serialized binary64 source components
as exact rational values for the dot-product sign checks; it does not rerun
the LP. For each upper panel, all seven recorded compression-contact
directions have nonnegative outward projection: four are `+1`, the
lower/upper panel interface is `+3.3886e-13`, and the lumber-leg side and
panel seam are zero. No recorded compression direction projects inward.
Every case also has positive outward force on each upper-panel body after
including assigned panel/T-nut gravity:

| Case | `main_upper_left`, N | `main_upper_right`, N |
|---|---:|---:|
| `a12-rear` | 1763.868 | 104.078 |
| `a12-forward` | 1304.242 | 104.078 |
| `a12-left` | 1534.055 | 104.078 |
| `k12-right` | 104.424 | 1533.709 |
| `k12-rear` | 104.424 | 1763.522 |
| `a1-rear` | 104.424 | 104.078 |

Projecting force equilibrium onto `u` therefore gives a positive external
term, zero from ideal lateral screw forces, and nonnegative compression
contact terms. These terms cannot sum to zero. **The useful result is that
the two upper-panel bodies require an inward axial-restraint path in this
no-axial-credit force-direction model.** This reinforces the panel-withdrawal
gate; it provides no per-screw share, compatible displacement, withdrawal
stiffness, resistance, or demand/capacity ratio. The lower panel is not covered
by this sign argument because its kicker contact can act inward.

The saved LP remains a floating-point tolerance screen: it gives unbounded
lateral variables and a maximum computed outward projection of
`3.5617e-17`. That computed LP status is not an exact-arithmetic infeasibility
proof; the independent force-cone check above rests on the source's ideal
40-degree direction equations and the sign of the recorded contact directions.
Neither result qualifies as-built geometry, installed screws, or omitted
hardware/accessory loads. Recompute if any pinned input, contact direction,
screw axis, or case changes.

Exact pins: model inputs
`178ab4f9352c8b1f11525ffc6680efa5733ba74cedd609874e9a1966624740f9`;
contact geometry
`034067430fff5207cdb40819fa8118a367edeb29a8d83926928cc96a0e87d151`;
LP script
`6d2a6323fa7cfc10fc857be8da1011df65174754d15f12f99bb09c18f7d9cb30`;
saved LP output
`80b7df4762981479c7f5c080d6207773cea1a2d6d4310f35280849b96400ec2c`.
The auditor reports `PASS_RECORDED_DIRECTION_SET_SIGN_AUDIT`; no native solve
or mechanical acceptance occurred. Exact Hillman withdrawal/load-slip and
group evidence, head/panel limit, installed engagement, receiver stiffness
and sharing, and equal/opposite transfer through the frame to support remain
missing. This closes no capacity or response gate.


## Corner-demand dependency: coupled support rule and exact limitation

The [bounded structural-coupling fixture](conditional-floor-structural-coupling-fixture-attempt01/README.md)
now tests normal/tangent coupling, ideal stick only while bearing, release,
and discrete reference reset. Four hand-answer stages each have exactly one
admissible mask. Standard-library KKT and independent constrained-coordinate
elimination agree on all 16 candidate states, with selected force-balance
residual below 3.56e-15 N. This closes that small-fixture coupling question,
not the full-frame support gate or any corner-demand check.

The [exact-rational applicability counterexample](conditional-floor-structural-coupling-fixture-attempt01/parent-reference-counterexample.md)
also proves that this fixed preceding-open-state reference rule does not
ensure existence or uniqueness under arbitrary coupled loads. One cell with
fixture carrier `[[20,5],[5,100]] N/mm`, normal penalty 100 N/mm and reference
x=0 has no admissible static branch under `(Hx,Pz)=(4,+0.5) N`: its open
branch penetrates; its stuck branch requires negative normal force. The
sign-reversed load has two admissible branches. These are method examples,
not source-case loads or physical failure findings. The corner's convex
force-energy argument does not prove uniqueness for this disjunctive floor law.

Parent source-pin extraction finds 100 frozen floor-normal cells, each with
a paired old tangent ownership row: 38 per runner and four per remaining
six supported posts/legs. Exhaustive normal-mask enumeration has up to
`2^100` candidates and is not a practical frame selector. No C11 force or
finite-tangent acceptance transfers.

The precise remaining floor dependency is an applicable reference-capture
and loading-history/state-selection treatment for the coupled frame, with
bounded failure behavior; neither four passing stages nor selecting one
admissible mask supplies it. Do not fix it by accepting negative normal
forces, retaining tangent restraint at zero bearing, or changing stiffness
until a branch passes. No frame/native run, geometry, criterion or original
LEG/FLOOR-RUNNER resistance change occurred. Signed actual-case corner
boundary forces and applicable member/hardware checks remain outstanding.


## SPRINGA native signed-law and reversal method verified

The [straight-line SPRINGA coupon](nonlinear-springa-known-answer-attempt01/README.md)
passed its controlled single native launch with the same pinned 2.23 binary.
All three hand answers, signed endpoint actions, physical/ground equilibrium,
MPC closure and fixed directions pass: +10 N -> +0.1 mm, -20 N -> -0.1 mm,
then +10 N -> +0.1 mm. Parent's additional 18-increment check has maximum
table-law / ground-balance residual 1.78e-15 / 7.11e-15 N. No residual, sign
criterion, stiffness or geometry was relaxed to obtain this result. The
SPRING2 packet remains failed; its source diagnosis is an inference and no
pinned binary was patched.

Engineering result unlocked: a built-in signed unilateral scalar carrier
that opens and recloses across reversal, with verified endpoint RF meaning.
The next task is a bounded two-moving-body nested relative-coordinate MPC
fixture; it stops when complete physical-body transfer and its known answers
are verified or a specific incompatibility is exposed. This method bridge
retains the old physical projection equations and tests the newly introduced
relative layer. It provides no fresh frame run authority. Actual six-case
corner demands, applicable floor support and complete corner resistance
evidence remain pending.


## Exact-stick constraint representation at the frozen floor points

The [floor constraint expressibility audit](current-floor-stick-constraint-audit-attempt01/README.md)
expands all 200 tangential rows onto 800 unconstrained physical solid DOFs.
Their rank is 200. A distinct-pivot representation reconstructs every
original source row within 1.95e-16 coefficient residual and satisfies
the pinned manual's unique dependent-DOF rule. An admissible trial field
closes all original constraints within 2.92e-16. This avoids the illegal
approach of directly fixing an already dependent projection ghost.

Engineering result unlocked: an exact geometric representation for a
conditional all-bearing stick branch, preserving every source floor point.
Existing finite tangential springs are not automatically exact stick. No
frame deck or native solve is produced by the audit. Native constraint
reaction recovery, compatible positive normal bearing and history/recontact
remain unverified; no fixed-reference counterexample is dismissed. A native
method check must settle force transfer/reaction output before frame use.


## Nested moving-body transfer and geometric-linear iteration verified

The [relative-coordinate fixture](current-springa-relative-coordinate-fixture-attempt01/README.md)
passed its single scoped native run. Existing projection ghosts plus
`Q=u_second-u_first` with positive unilateral table law transfer equal and
opposite forces to both moving bodies and close each body. Opening and
reclosing hand answers pass. Parent independently checks all 18 printed
increments: maximum body residual 4.01e-6 N, physical global residual zero.
The numerical SPRINGA ground is explicitly excluded from physical balance.

The verified runtime also uses Newton iterations while geometric effects
are off under the frozen `NLGEOM,NLGEOM=NO` option sequence, preserving the
original small-deformation frame/body-audit assumption. The positive
relative coordinate leaves a closed-side tangent at the zero knot without
changing force law, preload or stiffness. A negative-coordinate/min law
would pick an initially zero tangent in the pinned interval lookup.

Engineering result unlocked: source-owned unilateral carrier assembly with
verified nested-MPC physical transfer and stable initial closed-side tangent.
Luna now prepares a bounded input-only a12-rear frame adapter using these
stock native carriers and the exact floor constraint representation. It
stops at source-bound deck/model/audit; no freeze, force solve or acceptance
is delegated. Exact floor reference RF interpretation remains a separate
small method check. Full-frame readiness remains false pending that mapping
and response-audit integration. No C12 authority or old-bolt resistance
requalification follows.


## Exact-floor reaction recovery verified; corner scope reaffirmed

The left outer corner assembly under evaluation is BG001 (post to exterior
spine), BG003 (spine/side/inner block through two continuous three-member
bolts), and BG045 (inner block to header). Its complete load path includes
member contact/bearing, lateral and axial bolt actions, splitting/net
sections, washer seats and onward transfer. The 92 introduced block axes
replace former ML24Z/SDS duties; they are distinct from the twelve original
LEG/FLOOR-RUNNER arrangements. Reuse unchanged baseline resistance methods
and evidence for those twelve. Reopen only an identified geometry, receiver,
hardware or demand difference; do not transfer historical case acceptance.

The [exact-floor method attempt01](current-exact-floor-mpc-fixture-attempt01/README.md)
ended before mechanics because the linear stiffness token `20` lacked a
real-data decimal point. It remains preserved as failed. The separate
[attempt02](current-exact-floor-mpc-fixture-attempt02/README.md) changes only
real-number formatting and its run identity, preserving numeric inputs and
hand answers. Its one authorized native launch returned zero. Both known
answers, Newton/geometrically-linear runtime, isolated spring forces and
physical body balance pass. Parent independently checked all twelve printed
increments: maximum RF error 5e-6 N and body-balance residual 3.56e-15 N.

Exactly one of the four predeclared reaction interpretations passes both
cases: `RF_REFERENCE_MINUS_DEPENDENT_CLOAD`. Raw reference RF is -0.5/-1 N;
after subtracting the respective applied dependent loads +6/-4 N, actual
floor x reactions are -6.5/+3 N. This is a source-load correction, not a
force fitted to residuals. Numerical SPRINGA grounds are excluded from
physical balance. For the transformed frame constraints, recover the
transferred load from `(S^-1)^T F_pivot` and restore original row ownership.
The adapter must retain raw output and this explicit source correction.

Engineering result unlocked: exact stick reference-force recovery for the
verified small compression-bearing model. Luna's next deliverable remains
an input-only source-bound a12-rear adapter; its stop condition is an
inspectable deck, model and mapping audit. Whole-frame response recovery and
positive-bearing compatibility must still pass before a scoped frame run
can produce usable corner demands. No new frame launch is authorized by
this coupon result. Minimum outstanding mechanical input is the signed
current-frame corner actions with compatible contact states and verified
body/global transfer. Applicable hardware/material and washer/splitting
exceptions remain explicit conditional checks, not accepted capacities.


## Current frame input preparation and bounded response work

Parent source inspection found and returned three draft adapter issues for
correction before native use: material orientation overrides were bypassed;
the relative-coordinate audit did not handle omitted zero components; the
new response needed an explicit schema. Parent's separate
[current serialized-input checker](current-springa-parent-input-audit-attempt01/README.md)
also checks actual emitted floor coefficients and their applied-load
transfer, rather than relying only on full-precision algebra. No input pass
or frame readiness is claimed before outputs exist and that checker runs.

Luna prepares a response auditor using existing physical ownership, force
rounding and body/global wrench methods. Its stop condition is implementation
and verification on passed native method fixtures, with no native launch.
One additional input-only two-reference fixture addresses the specific
nonidentity matrix/permutation force-recovery behavior required by the exact
floor representation; it does not reopen general contact research. All work
is a dependency of current corner demands. No original LEG/FLOOR-RUNNER
resistance qualification or panel study is restarted.


## Nonidentity floor equation reaction map verified natively

The [transformed-reaction method coupon](current-transformed-floor-reaction-fixture-attempt01/README.md)
passed its single scoped stock 2.23 launch, returned zero and reproduced both
predeclared known answers. Its nonidentity matrix and reversed source-row/
physical-pivot orders recover original-row reactions [-11.25,+7.75] and
[+6,-9] N. Those reconstruct physical support forces [-6.5,+3] and
[+2.25,-5.25] N and preserve the source/physical yaw moments -300/+525 Nmm.
The transformed source-load subtraction and row permutation are now observed
native behavior, not an extrapolation solely from the scalar coupon.

Parent independently checked every twelve printed increments: maximum RF
and body residual 5e-6 N; maximum source/physical/global yaw residual
5.69e-13 Nmm. This closes the bounded force-output-method question. It does
not close frame floor-bearing compatibility, stiffness/engagement
applicability, 50-body equilibrium or six-case corner demands. The frame
input adapter and new physical response auditor remain the next bounded
deliverables; no C12 or complete-joint acceptance follows.


## Corrected current frame input and independent serialized check passed

The one source-bound a12-rear [adapter](current-springa-frame-input-adapter-attempt01/README.md)
has emitted its model, deck and audit. The freshly normalized physical loads
match the pinned source input, while raw attachment loads expand to that map
with maximum nodal discrepancy 1.14e-13 N. It retains 1,903 C3D20 solids,
1,292 SPRINGA carriers and 348 unchanged bilateral SPRING2 components.
All 218 material/orientation/section cards match the source deck.

Parent's independent serialized audit passes: 50 bodies and source ownership/
loads preserved; exact floor reconstruction error 7.54e-14; reference-transfer
error 4.76e-14; unit channel force/moment errors 3.61e-13 / 4.45e-10 mm;
emitted-load correction discrepancy zero; all 21,998 pivots distinct and
unfixed. Model and deck digests are respectively
`61f95ec9e670b2bd0e95d426cc14ff381283edfc4f9c87e47c2b344dd4fe50b8` and
`11674a8b50f0c292e7e03288697afa7bbfaebc0f3db5f49b0439c125a5ab9a4c`.

Next engineering gate: the source-bound physical-force auditor must pass its
actual native fixture replays and exact model/deck contract. Parent then owns
a fresh, one-launch diagnostic freeze/review; this input pass itself supplies
no run authority, frame forces or joint acceptance. The complete corner
exporter is being prepared in parallel for verified current results only.
Original LEG/FLOOR-RUNNER resistance evidence remains separate and reused.


## Corner priority confirmed; first current-frame diagnostic launched

BG001/BG003/BG045 are the left outer corner-block path: post/exterior spine,
spine/side/inner block, and inner block/header. The 92 new block-attachment
axes replace former angle/SDS duties. The twelve original LEG/FLOOR-RUNNER
arrangements remain a separate evidence class; their unchanged resistance
calculations are reused. A retained arrangement is reopened only for a named
changed geometry, receiver, hardware or current demand issue.

The final physical-response auditor passed 42 printed method-fixture states
and a near-zero SPRINGA endpoint-length arithmetic witness. Parent froze the
one a12-rear diagnostic and independently rechecked its actual serialized
inputs. Deck SHA remains `11674a8b50f0c292e7e03288697afa7bbfaebc0f3db5f49b0439c125a5ab9a4c`;
frozen model SHA is `58daa4d557c929b83fdffd989ba53ac75b82f6c87f3bc848cb1af28562a0e8fe`.
The standard serializer changes only diagnostic scope and truthful
always-active bilateral metadata. The source geometry, constitutive inputs,
loads and exact-floor reaction mappings are preserved.

[Attempt packet](current-springa-frame-a12-rear-attempt01/README.md) owns exactly
one 240-second/4-GiB serialized launch. Every printed state must pass physical
law, MPC, all-positive floor normal, global and all-50-body balance gates
before any corner force is usable. This remains a zero-gap, zero-accessory,
all-bearing exact-stick diagnostic; it supplies no joint acceptance or
historical pass transfer. The complete corner exporter is being prepared for
source-bound verified outputs. Minimum next dependency is a passing current
response; splitting, washer, bearing/contact and onward-transfer checks still
require their recorded applicable material/hardware and compatibility inputs.


## Current-frame attempt terminal: no accepted increment

The one scoped a12-rear launch ended with return code 201 after 51.43 seconds,
six failed cutbacks and accepted time zero. No usable corner forces were
gained. The same normalized residual/correction pattern persists as the
load increment is quartered, so smaller increments alone are not an evidenced
remedy. Rejected best-iterate FRD results are not promoted to demands.
This does not establish physical failure of the corner blocks.

The native slot is idle, the launch budget is consumed, and there is no
automatic retry. A bounded read-only pinned-manual/source and primary-online
diagnosis will identify at most two mechanics-preserving next methods. The
complete corner exporter remains blocked on precisely a passing current,
source-bound response; no blanket original LEG/FLOOR-RUNNER resistance work
was reopened.


## Native iteration issue resolved; exact remaining floor compatibility issue

The fresh controlled-iteration a12-rear diagnostic returned zero in 45.06
seconds and reached full load in seven accepted increments. The first took
13 iterations; later increments took two. No geometry, material, source load,
connection law, FIELD criterion or physical closure criterion changed. The
documented time controls delayed the premature residual-growth cutoff.

The strict response audit correctly rejected this all-bearing support branch.
A source-bound diagnostic screen of all 100 nonlinear normals at all seven
printed states found 17 strictly positive cells and 83 strictly separating
cells, with the same set throughout. Exact tangent restraint at those 83 open
cells is incompatible with the specified bearing-dependent no-slip law.
No corner demand is usable and no physical corner failure is established.

The next bounded engineering result is one conditional selected-bearing
branch: retain every normal law and physical input, impose exact zero tangent
motion only at the 17 proposed bearing cells, and release the 83 others.
This is a proposed state from a rejected branch, not accepted support evidence.
Fresh input/algebra and physical-response checks must prove normal/tangent
compatibility and all-body/global balance before any BG001/BG003/BG045 action
is recovered. There is no general recontact or uniqueness claim and no
unbounded native mask iteration. The original LEG/FLOOR-RUNNER resistance
work stays separate; any later affected demand is a concrete demand-only
check using unchanged resistance where applicable.


## Selected-bearing subset independently expressible; response not yet evaluated

Parent independently derived the proposed 17-cell / 34-row restraint subset
from the original source equations. Rank is 34; singular ratio is 0.158114;
pivot condition is 11.6773; source/reference reconstruction residuals are
1.11e-16 / 2.78e-16. The independent actual-deck checker is prepared in
`current-springa-selected-floor-parent-input-audit-attempt01/`. These are input
algebra results, not accepted floor reactions or corner demands.

The input adapter and response auditor have agreed the source-row, physical
pivot, reference and active/inactive map contract. Their bounded stop is one
prepared branch and a checked response method; parent still owns fresh frozen
inputs, readiness, one serialized run and final validation. Every normal,
active tangent, released tangent and physical-body/global balance must pass.
No geometry change, original bolt resistance restart or general recontact
solver is authorized by this record. BG001/BG003/BG045 remain the primary
complete corner path, and all six cases and sensitivities remain outstanding.


## Owner corner priority confirmed; two conditional support proposals rejected

BG001 (post/exterior spine), BG003 (spine/side/inner block through two
continuous three-member bolts), and BG045 (inner block/header) are the left
outer corner-block assembly: six physical bolts, eight lateral planes and six
axial ties. The 92 new block-attachment axes replace former ML24Z/SDS duties;
the twelve original LEG/FLOOR-RUNNER arrangements are separate. Their unchanged
resistance evidence is reused. No original resistance work was reopened and
no historical frame-case pass transferred. The complete corner deliverable
includes contact/member bearing, lateral and axial bolt groups, splitting,
washer seats and onward transfer, rather than isolated bolt capacities.

The 17-cell proposal reached full load (native return 0, seven printed states),
but its strict floor audit rejected inactive SPR1185. All 100 normal laws
were independently screened at every state: 23 cells bear and 77 separate,
with the same inventory throughout. A fresh input-only 23-cell proposal
passed the parent actual-deck audit and three replayed method fixtures.
Its 46 exact tangent constraints reproduce the source equations within
7.32e-14; source unit-wrench errors are 1.70e-13 N / 2.08e-10 Nmm.
Geometry, loads, laws, materials and the 92+12+66 axis classes are preserved.

Parent froze and ran that single proposal in
`current-springa-selected-floor-a12-rear-attempt02/`: native return 0,
59.56 seconds, confirmed terminal, full factor 1. Its strict response audit
rejected inactive SPR1215 at time 0.1. Diagnostic screening of all 100 normal
laws at all seven states gives 25 bearing / 75 separated cells, adding
`floor_base_floor_right_26` and `floor_base_floor_right_28`, losing none.
This diagnoses an incompatible prescribed bearing set; it does not establish
physical corner failure or usable corner forces. No response is promoted, no
third native mask run is authorized by this record, and tolerances remain
0.1 N / 2 Nmm. The two terminal assessments and diagnostic screens preserve
the exact rejection and file pins.

Minimum calculation dependency: a compatible source-bound frame support
response, with signed corner/onward interface actions and all-body/global
closure. Then reuse the existing conditional NDS/washer/net-section arithmetic
with those concurrent forces. Accepted corner resistance additionally needs
applicable member design strengths/grain/service assumptions, washer/bolt
compatibility and an applicable splitting treatment for the actual topology
(in particular BG003's oblique middle-member end and orthogonal bore families).
These are explicit conditional limits, not a new inspection or blanket external
sign-off prerequisite. All six cases and stiffness/engagement sensitivities
remain outstanding; solver convergence alone closes none of those gates.


## One current conditional response closes the numerical demand gate

The freshly frozen 25-bearing / 75-separated a12-rear proposal in
`current-springa-selected-floor-a12-rear-attempt03/` completed with native
return 0 in 60.37 seconds, confirmed terminal, seven printed increments and
full load factor 1. All source MPC, 1,292 SPRINGA, 348 bilateral, 100 floor
normal and 50 active / 150 inactive tangent checks pass at every increment.
The prescribed bearing set remains compatible. Raw and rounding-interval
all-body/global equilibrium pass without changed tolerances.

The independent parent sums also pass all 50 physical bodies and the global
frame at all seven increments. Maximum raw force residual is 0.000813895 N;
maximum raw moment residual is 0.877489569 Nmm, within 0.1 N / 2 Nmm. Numerical
ground reactions are excluded. Frozen model/deck/live-source verification
passes after terminal assessment. Response SHA-256 is
`892dadeed0b20d809ce5250d3cd1c3deb31697f69208d8bbefb5f702160e1274`.

The immutable auditor passed its calculation but its CLI could not encode
NumPy Boolean values as JSON. The separately recorded parent writer converts
only NumPy scalars to Python scalar values, uses strict JSON, and reruns the
unchanged pinned audit. No native run, threshold, mechanical computation,
frozen source or response gate was changed for serialization. The independent
parent audit reads the serialized response and passes.

Parent adopts this response only as conditional numerical case forces:
ring A, Hillman axial proxy ratio 1, zero bolt gap, zero accessories and an
unverified no-slip floor assumption on the reviewed geometry. It is not a
joint resistance pass, six-case envelope, sensitivity closure or floor/build
qualification. BG001/BG003/BG045 complete-path export and applicable screens
are the next immediate result. The 92 new axes remain separate from the
twelve original LEG/FLOOR-RUNNER arrangements; unchanged original resistance
evidence is reused. The remaining five cases need their own compatible
support responses, and stiffness/engagement/accessory exceptions stay open.


## Complete left corner numerical path exported for the first conditional case

`current-corner-native-demand-export-attempt03/corner-demand-report.json`
now reports all 338 owned interfaces, including incoming/onward transfer,
232 contact rows and twelve outer head/nut washer-seat records. All five
corner members close independently at each of seven increments; worst local
raw residual is 0.000696 N / 0.4754 Nmm. Parent additionally checked exact
signed exported vectors against the passed native response, complete source
inventory, all six physical bolts / eight planes / six ties, and all four
local released zero-action floor groups at every increment.

At full load in this conditional a12-rear scenario:

| Group | Separate lateral-plane resultant magnitudes (N) | Axial tie magnitudes, one per physical bolt (N) |
|---|---|---|
| BG001 post/spine | 301.657; 335.061 | 64.966; 18.473 |
| BG003 spine/side/inner block | bolt 1: 483.948 / 65.913; bolt 2: 239.230 / 86.983 | 95.967; 43.508 |
| BG045 inner block/header | 90.116; 24.946 | 119.343; 19.882 |

These magnitudes summarize separate signed vectors preserved in the report.
They are not independent capacities, a force envelope or joint acceptance.
BG003's unequal outer-plane actions prevent blindly applying its earlier
equal-outer-action double-shear reference. Maximum modeled full-annulus
washer pressure is approximately 0.536 MPa; this is a geometry conversion,
not a washer steel/pull-through or wood resistance pass. Splitting/net
section work still requires applicable methods and actual section actions,
not the whole-body equilibrium resultants.

The remaining five fresh case inputs and the source load register are in
progress. Each case needs its own compatible support response; no force or
bearing-mask transfer from this first case is allowed. The conditional
resistance comparison reuses reviewed original methods and keeps genuine
applicability exceptions explicit. All original LEG/FLOOR-RUNNER resistance
evidence remains separate and unchanged.


## Six fresh source cases registered; five native inputs in progress

`current-six-case-source-load-register-attempt01/register.json` contains fresh
source assemblies for a12-rear, a12-forward, a12-left, k12-right, k12-rear and
a1-rear, with a common non-load geometry/carrier signature and exact per-case
load/wrench maps. Parent checked all recorded source hashes and independently
recomputed the hold-standoff moments for every case. Register SHA-256 is
`7a638a49fc5086b4d5fed52148286a300b8b271f7d380b1a131ea8e17b094508`.
Only a12-rear has a passed conditional native response. The five remaining
inputs are being prepared in `current-springa-six-case-frame-input-adapter-attempt01/`,
with no native/freeze authority delegated and no bearing-mask transfer.

Final corner report SHA-256 is
`812a62fa3cd96a8983649c84a8c78a8d176d639465c887b11d1827a3f8f1ee17`.
Parent exact signed-force/inventory audit passes for that final report at all
seven increments. A stale washer-source unit-action caveat was corrected
only in the fresh export projection; forces and original source evidence
were unchanged. Applicable component resistance arithmetic is being recorded
separately; it remains conditional and cannot supply a combined joint pass.


## First resistance comparability screen and five audited case inputs

`current-corner-a12-conditional-resistance-screen-attempt01/` is complete and
its pinned producer replay passes. For the passed conditional a12-rear
response, BG001's separate Y/Z component/reference ratios are
0.266/0.328 and 0.375/0.325; BG045's are 0.222/0.0369 and
0.0604/0.0151. These are necessary individual component screens, not
combined-action DCRs, adjusted design capacities or joint passes. BG003 has
no applicable symmetric double-shear comparison: paired plane magnitudes
differ by 7.342 and 2.750, with non-collinear actions. Four eligible
base-post/header washer references have conditional ratios 0.0192–0.1243;
block seats are not given a perpendicular-grain reference. Splitting,
section actions, adjustment/interaction and bolt/washer compatibility stay
explicitly unresolved. No original resistance check was reopened.

All five remaining fresh source-bound frame inputs now pass independent
parent serialized-input audits in
`current-springa-six-case-frame-input-adapter-attempt01/`. Their load maps
match the fresh register; material/orientation/geometry are preserved.
No a12-rear bearing mask or response is transferred.

The separately frozen forward all-bearing diagnostic completed at full
load with native return 0 in 40.85 seconds. Its source-bound normal-law
screen gives 35 bearing / 65 separated cells at each of seven increments,
so all-bearing tangent restraint is rejected and its forces are withheld.
One forward-specific 35-cell/70-row proposal is being prepared. The left
case all-bearing diagnostic is independently frozen/audited and running
under parent serialized control. One conditional six-case response is
usable; the other five response/support pairs and sensitivities remain open.


## September 30: five diagnostic runs complete; forward selected branch underway

All five remaining case-bound all-bearing native diagnostics reached full
load with confirmed terminal execution. The summary is
`current-five-case-native-diagnostic-register-attempt01/register.json`.
Their forces remain withheld because tangent restraints include separated
cells. Stable positive-normal counts are forward 35, left 10, K12-right 10,
K12-rear 16 and A1-rear 44. K12-rear has one first-increment cell whose
printed displacement interval is inconclusive; a bounded zero-SPC evidence
check is in progress, without relaxing physical criteria.

The forward-specific 35-bearing/65-released proposal passed independent
serialized-deck and frozen case-context checks. It is now under one
parent-owned serialized native run in
`current-springa-selected-floor-a12-forward-attempt01/`. Its frozen model
SHA-256 is `50edee6194d3abdb758e8e7eb17f361b10cae7fc839dcedfa9f24f070d25324b`;
the deck is `401930f909d503e388a68f3eade5ebfaa1e228d5bc48712a217e170fe8bef553`.
The stop condition is terminal execution followed by strict support,
carrier-law and all-50-body/global balance checks at every increment.
Until those pass, only the earlier conditional a12-rear corner response is
usable. No mask, force or acceptance is transferred between cases.

BG001/BG003/BG045 are the left outer corner assembly: post to spine,
spine/side/inner block, then inner block to header. The six physical bolts,
eight lateral planes and six axial ties form one complete path. The 92 new
block axes remain separate from the twelve original LEG/FLOOR-RUNNER
arrangements. Their unchanged resistance evidence is reused; none was
reopened by this work. Remaining joint dependencies include the response
envelope, unequal three-member BG003 action compatibility, timber splitting
and section actions, and actual bolt/washer/grain compatibility.


### Forward selected proposal terminal result

The forward 35-bearing proposal reached full load with native return 0 in
43.06 seconds and confirmed terminal execution. Its strict case-bound
response audit rejected inactive normal SPR1026: strict separation with
zero endpoint RF was not established. Forward corner forces are withheld;
this is a support-pattern mismatch, not a demonstrated physical joint
failure. `current-springa-selected-floor-a12-forward-attempt01/parent-terminal-assessment.json`
records the exact rejection. A bounded fresh normal-law screen is identifying
changed support states; no automatic iteration or geometry change is authorized.
The usable conditional case count remains one, and the native slot is idle.


### Exact forward support mismatch localized

Parent read-only diagnosis binds the terminal DAT and confirms SPR1026,
`floor_base_floor_left_1`, is strictly bearing at all seven increments despite
being designated inactive. Its final normal force is 9.570275 N with a
0.0000005 N printed-force radius; projected closing displacement is
0.00005257167 mm with a 0.000000500005 mm printed-displacement radius.
This is not merely an ambiguous zero token. Evidence is
`current-springa-selected-floor-a12-forward-attempt01/parent-offending-cell-diagnosis.json`.
The full normal-only diagnostic screen reports a stable 31 bearing / 69
separated inventory; that remains diagnostic, not a validated replacement
branch. A future proposal must explicitly record support-stage lineage and
pass complete compatibility again. No corner force adoption follows here.


### Forward mask changes and bounded follow-on work

The fresh selected-floor normal-law screen pins terminal output and records
31 strictly bearing / 69 strictly separated / zero ambiguous cells at all
seven increments. Relative to the proposed 35-cell mask, six selected cells
became separated and two released cells became bearing: left runner cell 1
and right runner cell 7. This eight-cell change must be explicitly carried
in any next proposal; a convergence flag cannot replace complementarity.

The source-bound screen is
`current-springa-a12-forward-selected-floor-screen-attempt01/screen.json`.
Parent verified its source pins and separately recovered SPR1026's positive
force at every increment. Fresh work is bounded to a left-case input
proposal from that case's own ten-cell diagnostic, the BG003 asymmetric-action
applicability check, and a representation-only scientific-zero U-token proof.
The zero-token investigation must preserve nonzero-U and all-RF intervals,
source/method guards and physical criteria. It cannot fix the forward mask's
real contact changes or justify accepting its corner forces.


### Independent forward native normal replay

`current-forward-floor-parent-interval-audit-attempt01/check.py` independently
parses the recorded native U/RF tokens, emitted node coordinates, and source
projection/normal bindings without importing any FEA recovery kernel. Its
`audit.json` passes all 700 cell/increment classifications, reproducing the
31 positive / 69 strictly separated / zero ambiguous pattern. It pins the
exact model/deck/DAT/screen and its own source. This strengthens the support
mismatch diagnosis only; it does not promote rejected forces or establish
any joint resistance or floor qualification.


### BG003 unequal-action method boundary and conditional references

`current-bg003-unequal-action-applicability-attempt01/` is complete and its
producer replay and parent independent Mode Is arithmetic pass. Current
NDS-2024 single/symmetric-double yield provisions and unequal-side-length
rules do not supply a complete resistance comparison for the observed
unequal, non-collinear three-member actions. The historical 2018 asymmetric
clause also assumed equivalent side-member loads. The four separate
outer-receiver bearing-mode reference ratios are 0.2754, 0.0313, 0.1533 and
0.0434, under the explicit DF-L G=0.50, full-shank quarter-inch, proposed
grain and conservative effective-length scenario. These are component
reference comparisons, not adjusted complete-joint DCRs or passes; they are
not summed. Coupled middle-member action, dowel bending across both planes,
axial/lateral interaction, group adjustment and splitting remain separate
unresolved checks. The current consolidated AWC errata was considered;
its sub-quarter-inch KD correction does not alter this quarter-inch term.
No original LEG/FLOOR-RUNNER resistance was reopened and geometry is unchanged.


### September 30: left and K12-right selected diagnostics terminal

Parent independently audited and froze the case-specific left and K12-right
10-bearing/90-released proposals. The left native execution is terminal with
return 0 in 51.83 seconds; strict response audit rejects inactive SPR1269,
`floor_base_post_center_right_2`. Parent source-bound diagnosis finds its
positive normal force rises from 0.9737118 N to 9.737118 N; its final closing
coordinate is 0.00007317606 mm ± 0.000000500005 mm. This is a real mask
mismatch, not a printed-zero ambiguity. K12-right similarly reached full
load with confirmed terminal return 0 in 52.33 seconds, but its strict audit
rejects inactive SPR1257. Both native packets contain exact terminal
assessments and withhold corner forces pending complete normal-state screens.
No physical corner failure is inferred and unchanged original bolt
resistance is not reopened.

The A1-rear 44-bearing/56-released input passed source-bound input checks and
is under parent-owned frozen readiness/execution. The forward 31-bearing
proposal is prepared from the explicit selected-stage screen projection,
which preserves both original all-bearing physics authority and its direct
rejected selected35 output lineage. It is not a transferred pass or force
source. Neither prepared input implies support compatibility or joint
acceptance. The six-case response envelope and sensitivities remain open.


### September 30: six-case response register and K12-rear terminal exception

The [current six-case corner response register](current-six-case-corner-response-register-attempt01/README.md)
authenticates all six terminal executions and keeps the usable-demand count
at one conditional rear case. K12-rear's source-bound 16-bearing proposal
completed in 53.19 seconds, return zero; the validated zero-U representation
audit rejects inactive SPR1074. Exact model/deck/DAT and exception pins are
in its parent terminal assessment. No forces from that response are adopted.

The bounded forward31 diagnosis shows selected SPR1026 is strictly separated
at every increment, not interval-ambiguous: its full-load projected q is
about −0.02885715 mm, native table force zero. The observed 37-positive/
63-separated pattern is stable through seven increments and equals none
of the previous 35- or 31-cell patterns. It is not an adopted replacement
mask and does not trigger an automatic retry. A case-local reproducible
diagnosis is being recorded. Geometry, laws, criteria and unchanged original
LEG/FLOOR-RUNNER resistance remain preserved.


### Current actual-direction single-bolt lateral references

The [resultant-direction packet](current-corner-resultant-direction-single-shear-attempt01/README.md)
now evaluates the actual a12-rear lateral direction for both connected
members at each BG001 and BG045 bolt. It replaces the need to infer a
lateral comparison by combining separate coordinate components. Under the
existing smooth full-body quarter-inch, Fyb 45,000 psi, zero-gap, proposed
grain and Fe 5,600/4,450 psi endpoint scenarios, all six yield modes are
retained and Mode IV governs all four bolts. BG001 ratios are 0.42363 and
0.49082 against 712.070 and 682.661 N references. BG045 ratios are 0.22468
and 0.06230 against 401.080 and 400.416 N after the existing conditional
Ceg=0.67 once. They remain individual-bolt lateral reference comparisons,
not adjusted design DCRs, group/axial interaction checks or complete-joint
passes. BG003 remains a coupled unequal, non-collinear three-member problem.

Parent independently recomputed force norms, proposed grain angles,
Hankinson Fe interpolation, reduction angle and Mode IV arithmetic without
importing the yield helpers. The parent audit binds final screen SHA-256
`d3b1ce4448ea90929b6410424f0212d86b4caee5130bca7c93209e06ad5b3c10`.
The producer replay and its final checksum manifest pass. All four actual
axial tie vectors/magnitudes remain separate; no missing field is defaulted
to zero. Twelve original LEG/FLOOR-RUNNER arrangements remain out of scope.


### A1-rear now passes its conditional response and independent body sums

The source-bound A1-rear 46-bearing/54-released proposal ran once and is
terminal, return zero in 40.10 seconds. All seven increments through full
load pass the pinned zero-U response method's support, MPC, spring-law and
physical balance gates. The immutable auditor's CLI failed only while
serializing a NumPy boolean after mechanics checks had completed. The new
parent writer converts NumPy scalar types to native JSON types and reruns
the same unchanged audit; no native rerun, criterion or force change occurs.

Response SHA-256 is `257b5b743369fcc2242537b7ccfe81f2efba0a195ef044624d7b67da6a09678c`.
Parent independently summed all 50 physical bodies and global force/moment
resultants at every increment without importing the recovery balance kernel.
Maximum raw residuals are 0.0002213 N and 0.159621 Nmm, within the frozen
0.1 N/2 Nmm criteria. The exact parent terminal assessment permits this
conditional case's forces, not joint resistance or a historical pass.

There are now two usable conditional physical responses and one completed
signed corner export; A1's complete BG001/BG003/BG045 corner projection is
in progress. Four remaining load cases and whole-frame engagement/stiffness
sensitivity still require compatible audited responses. The twelve original
LEG/FLOOR-RUNNER resistance arrangements remain separately preserved.


### September 30: two complete corner exports and the next bounded exception

A1-rear's source-bound signed corner export is complete, report SHA-256
`2b498383b319aeb31e74c3b329e0758330b8b39d0a8e1b4788437db06453bfce`.
The parent independently checks all 338 interfaces across seven increments,
including native vectors, two active corrected floor-tangent groups and two
released zero groups, six physical bolts/eight planes/six ties, and the
separate twelve retained arrangements. The [two-case comparison](current-corner-two-case-demand-comparison-attempt01/README.md)
records each signed action; maximum lateral-plane resultants for a12-rear / a1-rear
are BG001 335.061 / 146.049 N, BG003 483.948 / 137.900 N and BG045
90.116 / 87.077 N. Some BG003 directions reverse, so resistance checks cannot
inherit the other case's loaded ends or directions. These are demands,
not accepted capacities or the six-case envelope.

The parent froze and ran one K12-rear 21-bearing/79-released proposal, derived
from that case's own complete normal-interval diagnostic. It completed in
53.68 seconds, native return zero, and the unchanged strict 711 response
method rejects inactive SPR1104 as not strictly separated with zero endpoint
RF. The exact assessment in `current-springa-selected-floor-k12-rear-attempt02/`
withholds all corner forces and records no physical failure. No automatic
mask retry follows; a bounded source-bound diagnosis is in progress.
The [six-case register](current-six-case-corner-response-register-attempt01/README.md)
now records two complete usable corner exports and four rejected case responses.

The [independent BG001 reference audit](current-bg001-geometry-wood-parent-audit-attempt01/README.md)
verifies the existing recorded angle/end-distance arithmetic and conditional
parallel-component row/net references. Geometry-scaled lateral comparisons
are 0.60184 and 0.69728, with mixed-direction Cg unapplied. Unadjusted
parallel-component row comparisons are 0.17301 spine / 0.21626 post; the
Chapter 5 glulam Cvr factor has no supported application to this solid-sawn
scenario and is omitted. Mixed-action splitting, adjusted resistance,
complete contact/member path, washers/axial interactions and coupled BG003
continuous-bolt behavior remain open. Each active follow-up is bounded to
these corner dependencies; unchanged original LEG/FLOOR-RUNNER resistance
is not reopened. Geometry, loads, criteria and native controls are preserved.

`current-knee-joint-check-summary.md` is retained at its currently pinned
state because the reproducible A1 projection freezes that legacy context
source. This later checkpoint and the current response register carry the
new results without invalidating the historical evidence pin.


### Corner axial/washer components and bounded K12-rear diagnosis

The [axial tie/seat screen](current-corner-axial-tie-seat-screen-attempt01/README.md)
and fresh parent independent arithmetic/vector audit cover all six full-load
a12-rear ties and twelve end seats. Conditional minimum-annulus DF-L No. 2
perpendicular-bearing comparisons for four base-post/header seats are
0.02007–0.12964. These are unadjusted component references on ideal supported
annuli, not washer plate response or accepted pressure/capacity. Candidate
blocks have a distinct elastic-only material map with no strength grade;
the separate DF-L No. 2 what-if comparison does not assign that grade.
BG045 block seats load parallel to proposed grain, so Fc-perpendicular is
inapplicable. The hypothetical Grade 5 bolt Fy×At reference is 13.014 kN,
component ratios 0.00142–0.00917; bolt interaction, nut/thread engagement,
washer spreading/bending and exact supported areas remain unresolved.
The final screen hash is
`cae5c67d1166205aaa442c8ae889c95245162b7d1569cf264b13bc260d712ac4`.

The [K12-rear attempt02 interval diagnosis](current-springa-k12-rear-selected-floor-normal-interval-diagnostic-attempt01/README.md)
classifies all 100 normals at all seven increments with no ambiguity: stable
23 bearing/77 separated, versus the proposed 21/79. Only inactive SPR1104
and SPR1110 bear, both strictly at every state; no selected cell separates.
Parent rehashed all 19 source pins and exact producer/report pins. This is a
real support-branch mismatch, not a tolerance or printed-zero problem.
Parent selected one fresh 23-cell input proposal for preparation, with no
native authority from the diagnosis itself or automatic further iteration.

The [BG003 continuous-dowel note](current-bg003-continuous-dowel-method-candidate-attempt01/README.md)
records a research method family and the exact unvalidated biaxial/material-law
gap. It is not an implementation queue or accepted resistance method.
Conditional calculations can use clearly specified hypotheses without claiming
inspected material; physical qualification is a separate claim boundary.


### Owner corner-block priority and latest case-specific results, September 30

BG001/BG003/BG045 are the complete left outer corner-block assembly: post to
exterior spine, spine/side/inner block, and inner block to header. Its six
new bolts include eight lateral shear planes, six axial ties and twelve
washer seats. They belong to the 92 new block-attachment axes replacing
ML24Z/SDS duties. The twelve original LEG/FLOOR-RUNNER arrangements retain
their separate baseline resistance evidence. Reopen a retained arrangement
only for an identified changed receiver, geometry, hardware or demand;
unchanged resistance work is reused and historical case passes do not transfer.

Two responses, A12-rear and A1-rear, have independent all-body/global audits
and complete signed corner exports. Their [comparison](current-corner-two-case-demand-comparison-attempt01/README.md)
now includes all sixteen primary contact cells at all seven increments.
At full load A12-rear has resolved post/spine compression while the
inner-block/header forces contain zero; A1-rear reverses those conditions.
A zero-containing force interval alone does not prove finite separation.
Maximum lateral plane demands are 335.061 N for BG001, 483.948 N for BG003,
and 90.116 N for BG045 across these two cases, not a six-case envelope.
The [A1 axial/seat screen](current-corner-a1-rear-axial-seat-screen-attempt01/README.md)
and its parent audit complete six ties/twelve seats. Individual post-2,
side-2 and header-2 ties exceed A12-rear despite smaller group maxima.
These remain conditional component references, not complete joint passes.

Four additional serialized native runs completed to full load with return
zero; all remain rejected and supply no adopted corner forces:

- K12-rear attempt03: its 23/77 floor set is strictly consistent at all seven
  states, but SPR489 fails the strict qghost/source output-interval check at
  factor 0.2 by 1.6344e-11 mm beyond its radius plus guard. Source projections
  pass; no tolerance waiver or geometry failure is inferred. See the
  [source-bound diagnosis](current-springa-selected-floor-k12-rear-qghost-diagnosis-attempt01/README.md).
- K12-right attempt02: inactive SPR1311 bears. The observed stable 11/89 set
  adds only right-leg cell 0 to the latest ten-cell input, without recurrence
  to either earlier ten-cell set. Parent rehashed all 52 diagnostic source
  pins and selected one fresh input preparation; no automatic native retry.
- A12-left attempt03: selected SPR1302 separates. The [700-row diagnosis](current-springa-a12-left-normal-interval-diagnostic-attempt02/README.md)
  confirms the local ten-to-eleven-to-ten set recurrence. Parent rehashed all
  46 sources. Repeating those masks is not a justified next step.
- A12-forward attempt03: selected SPR1050 fails strict bearing compatibility;
  the case-local set comparison is pending. No rejected force is exported.

The [BG003 middle-zone feasibility check](current-bg003-middle-zone-cut-feasibility-attempt01/README.md)
finds that two 44.45 mm geometrical halves do not establish independent bolt
segments or a simultaneous lower-bound resistance. Balancing each plane's
force over finite bearing depth leaves a midpoint moment without a proven
contact couple; axial tension also persists. This excludes that unsupported
shortcut, not the joint itself.

Minimum remaining evaluation dependencies are (1) four usable case responses
and bounded full-frame stiffness/engagement sensitivity, (2) a justified
continuous-bolt resistance treatment for BG003's unequal, non-collinear plane
actions plus axial tie, and (3) explicit block strength/grain hypotheses and
compatible bolt shank/root, washer support/bending and nut/thread engagement
inputs. Mixed-action splitting and the complete onward member-transfer checks
remain necessary. Conditional calculations may use labeled hypotheses;
missing physical/product evidence is not a demonstrated physical failure.
Reviewed geometry, load authority, strict criteria and native controls remain
unchanged. The goal remains active and the corner assembly is not accepted.


### Forward compatibility diagnosis completed

Parent independently rehashed all 170 sources of the
[A12-forward attempt03 diagnosis](current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt02/README.md).
All seven states classify 37 strictly bearing / 63 strictly separated, no
ambiguity. This stationary observed mask matches none of the three tested
forward inputs (35, 31, 37 cells); the latest 37-cell input shares 34 cells
with it. Selected SPR1050 separates throughout. No update-cycle or convergence
claim follows, and the rejected run supplies no adopted demands.
Parent independently audited and froze the source-bound K12-right eleven-cell
proposal for one serialized attempt03 run; terminal compatibility and all-body
balance still determine whether any forces are usable. No original leg/runner
resistance check or reviewed geometry was changed.

K12-right attempt03 completed in 51.48 seconds at full load with native return zero. The unchanged strict 711 response audit rejects selected SPR1311 as not strictly positive. Exact terminal assessment withholds forces. The full-set comparison is pending; no further mask update or native run is selected. Two usable signed corner cases remain.

[A1 BG001 lateral component references](current-bg001-a1-resultant-reference-attempt01/README.md) reuse unchanged reviewed resistance/geometry with A1 signed vectors. At actual grain angles 11.421/44.567 degrees, raw Mode IV references are 767.897/667.352 N and unadjusted comparisons 0.14181/0.21885. Parent independent source/Mode IV arithmetic passes; no loaded-end/group/splitting/axial interaction or joint acceptance follows.

[A1 BG001 signed geometry](current-bg001-a1-signed-geometry-attempt01/README.md) explicitly verifies the same loaded grain ends and changed cross-grain loaded edge at post bolt 2 in both receivers. Sampled listed edge minima are met. Recorded conditional interpolation yields group Cdelta 0.72537 and geometry-scaled comparisons 0.19550/0.30171; actual group row-alignment sine 0.50720 leaves Cg and mixed-direction splitting unresolved. No complete resistance or case-envelope acceptance follows.

The [K12-right attempt03 diagnosis](current-springa-k12-right-attempt03-normal-interval-diagnostic-attempt01/README.md) confirms an exact ten-to-eleven-to-ten recurrence for the two latest inputs, differing only at SPR1311. Parent rehashed all 65 sources and independently checked the 700-row partition and exact prior-set match. SPR1311 at full load has strictly separated gap [-0.0057160855,-0.0057160845] mm; this is not a printed-zero ambiguity. No further fixed-mask update is selected. A bounded current ideal-stick support-method investigation now covers both left and right cycles.
The [conditional BG001 stiffness input](current-a12-rear-bg001-seat-stiffness-variant-attempt01/README.md) changes only two runtime ties from 4670.054 to 2401.714 N/mm, using a documented uncalibrated local compliance scenario. Parent independently checked all eight JSON differences and two deck records. It is not yet native-ready; a dedicated override-aware input/method validator must preserve strict floor and all-body gates before a scoped response sensitivity run.


### Bounded SPR489 representation remedy under preparation

The pinned-source investigator traced SPR489's physical-point interpolation,
projection and qghost equations. The current replay reports tiny independent
coefficient removal by CalculiX 2.23 cascade.c; no selected-floor H/D equation
is in this dependency chain and no dependent-zero coefficient repair occurs.
At factor 0.2, the reported pruned/unpruned scalar difference is -1.2340e-11 mm,
versus a strict scalar interval overrun of 1.6344e-11 mm. This is a credible
partial numerical mechanism, not complete causal proof or a tolerance waiver.
A reproducible source-pinned trace is being prepared for parent verification.
The next candidate is a small known-answer direct scalar/interpolation
projection fixture that bypasses the intermediate projection cascade while
proving the same scalar q and owner action/reaction. Production input remains
unchanged and its response rejected. No native fixture is authorized until
parent reviews exact equations, analytic answer, pins and readiness.

The [independent ideal-stick hand-fixture audit](current-ideal-stick-hand-fixture-parent-audit-attempt01/README.md) exhaustively enumerates two tangent masks and two normal-law sectors in exact rational arithmetic. Both sector-consistent equilibria violate their own stick gate, including the zero-normal boundary in the inactive sector. This demonstrates that a generally convergent positive-normal mask update cannot be assumed. It does not prove that the full frame lacks another admissible branch, verify a new native algorithm, or demonstrate physical joint failure. No further repeats of the confirmed left/right two-mask cycles are selected.

Parent independently executed the exact two-tie sensitivity validator and obtained its sealed source-bound contract. Only SPR1771/SPR1772 runtime constitutive bindings are replaced; all geometry, loads, other carriers and floor equations remain fixed. Native sensitivity is still not ready: the current response API always revalidates the unchanged baseline, so a separate minimal pinned 711 response-core adaptation must explicitly accept the authenticated override contract and retain every physical gate. Baseline response replay and rejection of inherited forces under changed stiffness are required before a run.

BG045 primary-source follow-up finds no end-grain exemption from edge detailing. A conditional rectangular-face loaded-edge comparison is being finalized: A1 inner-block axis 2 points toward a −Y envelope face 20 mm away, versus 25.4 mm under the perpendicular-grain 4D branch. The 5.4 mm difference is a potential detailing requirement under that named interpretation, not an adopted joint failure or a model-change authorization. Header mixed-direction actions require a separate applicability boundary. All inspected/as-built claims remain excluded.

The [left-corner onward-transfer register](current-corner-left-leg-onward-transfer-register-attempt01/README.md) isolates the two retained LEG arrangements directly joining base_side_left to lumber_leg_left. Across both usable cases it records all 56 signed lateral/tie actions with exact action/reaction checks. A12 full-load lateral resultants are 1183.332/1723.082 N and ties 262.707/529.439 N; A1 lateral resultants are 377.513/276.079 N and ties 71.602/178.438 N. No resistance is recomputed and no old pass is transferred. A bounded evidence map will link only these two arrangements to existing checks and identify any concrete demand/receiver/geometry/hardware difference. This closes a demand-register linkage beyond the new corner blocks, not full joint acceptance.


### BG045 two-case component screen finalized

The [BG045 signed wood-mode screen](current-corner-bg045-two-case-wood-mode-screen-attempt01/README.md)
is finalized at report SHA-256
`6b63e59dbbc1e77ad46eb582b97fead1a6d874a0df8e01353f0ff049065d864b`.
Parent replayed its source verifier and independently rehashed project sources
and recomputed all four conditional Mode IV references with Ceg applied once.
The largest single-bolt lateral component comparison is 0.22495. Header washer
seats are cross-grain compression; block seats are parallel-grain compression,
so the header Fc-perpendicular reference does not cover the block seats.

The named rectangular-face interpretation for A1 block axis 2 selects its
−Y envelope face at 20.0 mm versus 25.4 mm under the conditional 4D rule:
a potential 5.4 mm detailing deficit. NDS defines a loaded edge by the action
direction but the reviewed text does not supply a general oblique rectangular
corner selection recipe. The report distinguishes source geometry rays from
normative edge selection. A12 block axis 1's short +Y component face is a
conservative sensitivity; its geometric ray first reaches +X at 44.45 mm.
Header component comparisons also remain sensitivities for the full oblique
actions. No adopted joint failure, geometry change or drilling instruction
follows. Mixed-action splitting, net/row applicability, block parallel-seat
strength and complete resistance remain open.


### Sensitivity response-method review in progress

Parent reviewed the separate 711 response-core adaptation. The physical force
and equilibrium audit body is factored without deliberate tolerance changes;
the added API must authenticate the exact two-tie override contract. The first
diff accepted arbitrary callable builders. The agent added fixed class/seal
checks, and parent independently verified rejection of a fake builder before
invocation, without reading native output. A fixed validator-source pin and
baseline physical replay/stale-force rejection remain required before native
readiness. The [parent review packet](current-sensitivity-response-core-parent-review-attempt01/README.md)
records the exact tested source and the snapshot timing limitation; the
snapshot followed the correction and does not preserve the initial diff.
No sensitivity force or extra usable case is claimed.
### September 30: fresh corner stiffness response and direct-scalar fixture

The exact A12-rear BG001 two-tie stiffness variant was frozen and run once
through the serialized parent runner. Native exit was zero in 53.929 seconds.
The sealed response fork passes all seven increments, every source spring
law/MPC, retained bilateral checks and strict 25-bearing/75-separated floor
compatibility. Parent independently recomputed all 50 bodies and global
balances: maximum printed component residuals are 0.001330 N and 0.570069 Nmm,
within unchanged 0.1 N/2 Nmm criteria. Native slot is now idle. This is one
conditional sensitivity point, not an additional base load case, six-case
sensitivity envelope or calibrated physical stiffness bound.

The postprocessor's original JSON write failed on a NumPy boolean after all
mechanical gates passed. The separate parent writer reran that exact pinned
audit and recovered only its final report at the serialization statement,
converting NumPy scalars via item(). No force, uncertainty, gate or tolerance
was changed; the original writer/source snapshots were preserved.
The native response and independent audit are in
`current-a12-rear-bg001-seat-stiffness-native-attempt01/`.
The reproducible signed comparison is
`current-a12-rear-bg001-seat-stiffness-parent-native-preparation-attempt01/corner-sensitivity-comparison.json`.

At full load, reducing the two BG001 tie stiffnesses from 4670.054 to
2401.714 N/mm changes post ties 64.966/18.473 N to 52.434/11.707 N.
BG003 first tie rises 95.967 to 103.092 N; its largest lateral plane changes
483.948 to 485.775 N. BG045 first lateral plane rises 90.116 to 92.812 N.
All fourteen signed bolt actions are retained at each of seven matched
increments. These are redistribution results, not resistance acceptance.

The SPR489 direct-scalar method coupon also ran once and terminated at zero.
Its original checker rejected an intermediate table comparison because it
used scalar q without the actual SPRINGA dd-dd0 and the established length-
subtraction representation bound. Original rejection and frozen checker remain
preserved. Parent reviewed the separate corrected checker against pinned 711
geometry/16-epsilon span arithmetic and independently replayed the same output:
all 18 printed states pass source-MPC/table/support checks, and all three
full-step endpoints pass analytical displacement and physical owner force/
moment checks. Intermediate applied-load ramps are not inferred.
See `current-k12-rear-direct-scalar-native-attempt01/parent-method-validation.json`.
This validates the bounded coupon method; the K12-rear frame response remains
rejected until its exact replacement input and full response audit pass.

The retained-left-LEG affected-demand screen reproduced successfully.
Its largest conditional individual lateral ratio is 0.58087 and washer bending
ratio 0.37028, using unchanged original nominal/partial-thread methods and new
signed forces. The ten new base_side_left bores still require affected group/
net/splitting treatment; no original twelve-bolt campaign or case pass transfer
is selected. See `current-corner-left-leg-affected-demand-screen-attempt01/`.

The rigid-normal limit screen was independently checked in exact arithmetic:
it does not resolve the existing toy stick cycle. It is not a full-frame
existence claim, a selected cycle fix or a new native queue.


### September 30: exact SPR489 replacement preflight and parent review

The original K12-rear output was checked at all seven increments: 9,044
unilateral-carrier comparisons give one strict source-coordinate exception,
SPR489 at factor 0.2. The other 9,043 comparisons pass. This diagnosis does
not accept the response or establish force equilibrium.

The corrected input attempt02 changes only model equation rows 19,433 and
19,434 and the same two emitted equation cards. All other 21,842 serialized
model equation rows remain exact. Seventeen non-equation leaf changes are
confined to declared SPR489 method metadata. Attempt01's unrelated JSON
coefficient rounding is preserved as history and is not the run input.

Parent independently checked the exact differences and actual emitted-row
owner force/first-moment transfer. AST comparison proves that the physical
response gate statements remain unchanged except the SPR489-only callback;
its geometric table law, interval bounds and action/reaction checks remain
unchanged. The scoped source scalar and token radius now use the frozen 80
physical master DOFs, matching the reviewed known-answer coupon. Parent also
replayed the complete input/method verifier: all eleven negative probes reject.
See `current-k12-rear-direct-parent-method-review-attempt01/review.json` and
`current-k12-rear-spr489-direct-response-audit-attempt02/`.

This is method/input readiness evidence. It does not produce variant frame
forces or change the two-usable-base-case count. A fresh exact-byte native
response, every-increment floor checks and independent fifty-body/global
balance audit are still required.

Parent reproduced the BG045 stiffness-sensitivity report, SHA-256
`3c114c84e9d0f2ba0292db9af97b538005bde10af99a0f5538976b7a26c1aed8`.
Its largest named Mode-IV/Ceg component ratio changes 0.22468 to 0.23137;
header seat ratios stay below 0.13 under the same conditional reference.
The existing 20 mm edge applicability questions remain explicit. These are
individual component comparisons, not complete-joint resistance acceptance.


### September 30: K12-rear response recovered; three usable cases

The one exact-byte direct-master K12-rear run terminated successfully in
53.222505 s. Its separate method audit passes all seven increments, all 9,044
unilateral-carrier checks, retained bilateral laws and generic MPC checks.
All 100 floor normal cells retain the strictly compatible 23-bearing/77-open
branch at every increment; 46 tangent channels act only at bearing cells and
154 released channels have zero action. No mask sweep, geometry, stiffness,
load, tolerance or floor-capacity assumption was changed.

The independent parent audit also passes every physical body and global
balance at all seven increments. Maximum printed component residuals are
0.000553259 N and 0.723365 Nmm within the unchanged 0.1 N/2 Nmm criteria.
The exact freeze, execution, response and audit hashes are bound in
[current K12 parent assessment](current-k12-rear-spr489-direct-native-attempt01/parent-terminal-assessment.json).
The original rejected K12 output and original method attempts remain intact.
The native slot is idle.

The [fresh corner export](current-corner-k12-rear-case-bound-export-attempt01/README.md)
retains all seven increments, 338 interfaces/232 contact rows per increment,
six new corner bolts, eight lateral planes, six ties and twelve washer seats.
It includes the complete post/spine, spine/side/inner-block, inner-block/header
path and incoming/onward transfers. Parent reproduced the exporter and
independently compared every exported owner/point/force/radius row to the
fresh response: 334 native interface rows and four independently grouped
floor vectors at each increment, 2,366 interface rows total. This is numerical
force evidence, not a complete-joint resistance pass.

The [updated six-case progress register](current-six-case-corner-response-register-attempt02/register.json)
now records three usable conditional physical responses with corner exports:
A12 rear, A1 rear and K12 rear. A12 forward, A12 left and K12 right remain
unusable; their proposed support branches have not passed strict compatibility.
The preserved attempt01 register is historical two-case evidence, not the
latest progress count. The six-case envelope, physical stiffness/engagement
bounds and complete corner resistance remain incomplete.

At full load, K12 rear gives BG001 lateral resultants 24.877/68.767 N and
post/block tie tensions 56.542/13.978 N. BG003's four lateral plane resultants
are 64.929/5.552/59.449/4.550 N, while its outer ties are 99.238/73.628 N.
BG045 lateral resultants are 74.090/15.619 N with ties 22.962/15.135 N.
Signs and physical owners are preserved in the export. The BG003 second tie
is greater than the earlier A12 value 43.508 N, so older case-specific checks
cannot simply be transferred. The affected retained left LEG bolt 2 also has
new axial tension 530.575 N versus earlier A12 529.439 N; unchanged original
resistance methods are reused only for that changed-demand screen. No blanket
revalidation of the original twelve arrangements is selected.

Current bounded follow-through: apply existing component methods to these
new corner forces; finish the explicit BG003 full-bolt statics construction
without claiming bearing/contact compatibility or an NDS capacity; diagnose
the exact A12-forward support-branch lineage without native mask iteration.
Remaining material/hardware questions include assigned block properties,
delivered shank/thread engagement and washer support/bending, alongside
splitting/net/group and lateral/axial interaction checks. Missing evidence is
not a physical failure or a fabrication release.


### September 30: bounded BG003 full-bolt statics result

The [piecewise bearing-profile packet](current-bg003-piecewise-bearing-profile-feasibility-attempt01/README.md)
now constructs all four contiguous zones per BG003 bolt: 38.1 mm spine,
two 44.45 mm middle-member halves, and 88.9 mm inner block. Opposite-flank
compressive line reactions balance the unequal, non-collinear source plane
forces while preserving the source member wrenches. The lateral diagram has
zero shear/moment at both outboard wood faces and the middle cut. The axial
tie remains through that cut; it is not a zero full internal wrench.

Parent reproduced the source-bound producer (14 increments/112 segment
states) and independently checked all profile resultants, first moments,
whole-bolt force/moment equilibrium and constructed moment maxima. The report
SHA-256 is `215bfecdd74e11688a5289c85c3179b79dbb7751c67376ff4def955f8fd6bb9e`.
At full A12 load, the two constructed peak bolt moments are 4455.172 and
2202.327 Nmm. For A1 they are 1887.848 and 1083.803 Nmm. These are values of
the explicit field, not conservative bounds on the actual bolt response.

This resolves only whether a zero-lateral-middle-cut construction is
statically possible. It does not prove opposite-flank engagement/deformation
compatibility, wood bearing/splitting, steel/thread strength, axial/lateral
interaction or an NDS/TR12 resistance. The earlier one-sided centroid argument
does not rule out this signed field, but the original warning that geometry
alone cannot justify independent single-shear capacities remains correct.
No native solve, force adoption or new geometry was needed for this result.


### September 30: K12-rear corner component and affected LEG screens

Parent reproduced `current-corner-k12-rear-component-screen-attempt01/screen.py --verify` against the fresh seven-increment K12 demand export and independent physical/export audits. The report SHA-256 is `72e0ebbccff35828c43a5bdcc55cca7cf92c0e4d5f2bedb4c8c1e4da10628db5`. BG001's largest full-load individual lateral demand is 68.77 N; its conditional Cdelta-only reference ratio is 0.1244. BG045's largest demand is 74.09 N; its conditional Ceg-only Mode-IV ratio is 0.18448 (second axis 0.03908). These are component comparisons, not complete-joint DCRs or acceptance. The six ties and twelve washer seats are retained with signs; the largest uniform modeled-annulus pressure conversion is 0.44556 MPa at BG003 side bolt 1's spine seat. Block wood grade, delivered hardware/shank/engagement, washer behavior, splitting and combined actions remain unresolved. The conditional 20 mm face-distance questions remain explicit without promoting an oblique-action comparator to an adopted pass or failure.

BG003's two outer-plane pairs have full-load magnitude ratios 11.69 and 13.07 and direction differences 41.29 and 162.97 degrees. The reused equal-action double-shear references do not establish its coupled capacity. The statically balanced piecewise-bearing construction recorded above addresses equilibrium only; it does not supply compatible bearing/contact, yield, splitting or axial-interaction resistance.

The scoped retained left LEG K12 screen is `current-corner-left-leg-k12-affected-demand-screen-attempt01/affected-demand-screen.json`, SHA-256 `f00c528f1e5dd884ce34b40cfb96f1357e6bef4a586c65b727740dc9ab6550ac`; parent reproduced its producer. Bolt 2's tie rose 1.1354 N (+0.21445%) versus A12 rear. Reused nominal partially threaded hardware calculations give conditional bolt-2 ratios 0.12027 lateral, 0.03003 steel, 0.15794 washer bearing and 0.37108 washer bending. This reuses unchanged resistance work for the exact changed demand; it does not restart qualification of the twelve original arrangements. The ten new base-side-left bores still need the affected group/net-section/splitting treatment.

Parent froze the explicitly source-derived A12-forward M4 support proposal and rechecked the unchanged pinned response input validator on the frozen model, deck and case context. It changes only the selected floor support hypothesis, retaining 37 bearing and 63 open cells. One serialized bounded run (`springa-selected-a12-forward-attempt04`) is authorized for this exact freeze, with no automatic mask iteration. New forces become usable only after every-increment source-law/floor compatibility and independent all-50-body/global equilibrium checks pass. The usable-response register remains at three cases until those gates settle the test.


### September 30: bounded A12-forward M4 test rejected

The exact frozen M4 proposal finished normally in 40.6922 seconds with zero native return code and confirmed terminal cleanup (`current-springa-selected-floor-a12-forward-attempt04`, run ID `springa-selected-a12-forward-attempt04`). Its frozen model/deck/DAT SHA-256 values are respectively `c6ff4f67459bef5217502d0f61b25e19ef2aae0c21c0f10444de0c9936795cfc`, `394653fbe1aa0d6ad5d36f66f19eabf6ddd45fef072466ec828d044aa3cf67e1`, and `2cd771182864e24d8f4ba3f71e56651a4e77e41eb450d962132b190dd70364ad`. The unchanged strict response checker rejected selected floor normal SPR1068 as not strictly positive after rounding. The parent rejection and terminal assessment preserve that result; none of the run's corner forces are adopted. This is an incompatibility of the selected conditional support branch, not evidence of physical frame failure. A bounded signed-normal diagnostic is checking recurrence against existing masks; no further native run or automatic mask iteration is queued. Usable conditional cases remain A12 rear, A1 rear and K12 rear (3/6).

Next useful corner work is a source-bound section-action reconstruction at the existing spine/block bore stations, retaining simultaneous neighboring joint/contact forces and explicit source discrete gravity. It will establish conditional N/V/M on declared cuts if opposite-side reconstruction is justified, and will stop before physical gravity-distribution, wood-strength, splitting or complete-joint claims. No changed geometry or hardware scope is authorized by this calculation.

Latest preserved six-case status is now `current-six-case-corner-response-register-attempt03/register.json`; its producer and `--verify` replay bind the M4 rejection while preserving the three usable cases and all prior register evidence. The bounded forward-test result and stop condition are described in `current-a12-forward-m4-parent-preparation-attempt01/README.md`.


The bounded M4 diagnostic found 34 strictly positive / 66 strictly separated / zero ambiguous floor cells at every printed factor, with the same sign pattern across all seven states. SPR1068 is `floor_base_floor_left_15`; the other selected-but-separated cells are `floor_base_floor_left_17` (SPR1074) and `floor_base_post_outer_left_1` (SPR1278). At full load their source scalar q intervals are respectively [-0.014633195,-0.014633185], [-0.011069735,-0.011069725] and [-0.00067066475,-0.00067066465] mm, all with zero endpoint reaction. This is not rounding ambiguity. The observed 34-cell set differs from each M1–M4 input, so no M3/M4 two-mask recurrence is established. Parent assigned preparation of one source-derived M5 input-only hypothesis using that exact stable set, with no new geometry, law, stiffness, case control or automatic follow-on run. The parent separately owns its frozen-input readiness and one bounded test; this preparation does not adopt any M4 forces.


### September 30: M5 forward hypothesis rejected; stop further mask runs

Parent independently froze and validated the source-derived 34-cell M5 proposal using the unchanged pinned input checker, then ran one serialized attempt (`springa-selected-a12-forward-attempt05`). Frozen model/deck/DAT SHA-256 values and exact execution/rejection sources are bound in `current-springa-selected-floor-a12-forward-attempt05/parent-terminal-assessment.json`. Native execution was zero-return, terminal and 43.4053 seconds. The unchanged response gate rejected inactive floor normal SPR1026 as not strictly separated with zero endpoint RF. No M5 forces are adopted, and no accepted fourth case was gained. Parent is stopping further forward mask proposals/runs; the final bounded diagnostic will name the offending cells, signed intervals and recurrence against M1–M5. No law, tolerance, source geometry or stiffness was changed, and no physical failure or global nonexistence claim is inferred.

The latest preserved status is `current-six-case-corner-response-register-attempt04/register.json`; its producer replay passes and retains three usable conditional responses and corner exports, with both fresh forward rejections and prior evidence preserved. Detailed test scope and stop condition are in `current-a12-forward-m5-parent-preparation-attempt01/README.md`. The native slot is free. Primary engineering continuation is the corner spine/block section-action reconstruction and the bounded BG003 coupled bearing/contact/resistance gap; panel qualification and unchanged original bolts are not restarted as blanket prerequisites.


### September 30: corner source-discrete section actions recovered

The completed `current-corner-conditional-section-demands-attempt01` packet supplies signed N/V/M at the four existing spine X-bore stations and two inner-block BG003 X-bore stations, including all simultaneous neighboring joint/contact forces and source discrete member loads. It covers seven increments in each of A12 rear, A1 rear and K12 rear, 42 body-state rows and 252 one-sided section results. Parent corrected the draft's source-schema reads and exact-zero assumption, kept the existing source response gates and 0.1 N / 2 Nmm physical limits, and retained whole-body residuals and point-load jumps explicitly. Both producer replay and independent native-force reconstruction pass; the independent maximum force and moment differences are zero. Source native forces, geometry, loads and laws were not changed.

Full-load section magnitudes include spine axial up to 371.47 N (A1 rear) and inner-block axial up to 141.01 N (A12 rear); complete signed shear, bending/torsion and just-below/above results are in the packet. These are source-discrete-load actions, not qualified physical self-weight distribution, bore stresses or wood resistance. Original geometry-only net areas remain context, with no capacity inferred. This fills a conditional local-action dependency without claiming splitting or BG003 continuous-bolt acceptance. The exact missing inputs remain adjusted block/member strengths, compatible bearing/contact and continuous-bolt mechanics, applicable splitting/net/group treatment, section properties/local stress transfer and delivered washer/shank/engagement information. Three load cases and physical stiffness/engagement bounds remain unresolved. No blanket original LEG/runner or panel requalification was added.


Final forward diagnostic early result: all seven M5 states classify 32 positive / 68 separated / zero ambiguous normals with one stable sign pattern. This exact pattern matches none of the M1–M5 input masks; it is the M2 31-cell input plus `floor_base_post_center_right_0`. SPR1026 is positive while assigned inactive, so strict incompatibility remains. This does not establish a recurrence or nonexistence across all support patterns. No M6 preparation/native run is queued. The usable-case count stays three. Native ledger records 53 terminal runs with the parent slot idle; source pins for the completed independent section reconstruction revalidate.


### September 30: latest bounded corner/support continuation

The independent [support/corner review](../support-corner-review-2026-09-30/README.md) was read and reproduced. The latest [coordinator checkpoint](LUNA-MAX-COORDINATOR-CURRENT-CHECKPOINT-2026-09-29.md) records the completed source-discrete section results, the adopted small BG003 compatibility diagnostic, its case-specific nominal action conversion, the BG045 conditional 5.4 mm edge deficit and proposed-move bore-web consequence, and the separately defined gravity-settle/climber-ramp task. The usable conditional case count remains three; complete-corner resistance and the six-case envelope remain incomplete. The historical blanket panel/no-demand statements near the start of this append-only file must not override the later usable exports or owner-directed corner priority. There is no further guessed-mask native retry or reviewed geometry change queued.


The bounded continuation tasks now pass parent replay: BG003 rotated vector-foundation sensitivity, BG045 conditional edge/proposal arithmetic, full gravity/climber nodal decomposition and the exact coupled contact-event fixture. See the latest coordinator checkpoint and its final source pins. These recover concrete conditional mechanics and define the remaining native readiness gap; they do not increase the usable response count beyond three or close complete-corner resistance. No native run, automatic guessed-mask retry, reviewed-axis change or blanket panel/original-bolt requalification occurred.

### September 30: clearance and corrected section results

Parent reproduced the [radial-clearance diagnostic](current-bg003-radial-clearance-diagnostic-attempt01/README.md) byte-identically. Eight bounded A12-rear BG003 bolt-1 solutions cover two hypothetical isotropic foundation stiffnesses, zero or modeled 0.575 mm radial clearance, and 16/32 meshes. Receiver/free-end/gauge closure and signed refinement pass. At 32 elements, the middle-cut bending magnitude changes from 2938.993 to 2300.459 Nmm at k=100 N/mm², and from 151.185 to 1063.546 Nmm at k=1000 N/mm². Thus clearance can increase or decrease this action; these synthetic points establish neither actual bearing stiffness nor a conservative strength bound. Physical grain-dependent bearing, shared timber/two-bolt compatibility, steel/thread/washer interaction and splitting remain open.

The [axis-2-only BG045 proposal](current-bg045-axis2-only-proposal-screen-attempt01/README.md) addresses the stated A1 loaded-edge arithmetic by moving only axis 2 inward 5.4 mm. It preserves the nearest nominal bore web of 7.453 mm, unlike the separate both-axis proposal's 2.053 mm web. This is a conditional geometry comparison using existing forces, not recalculated post-move demands or an approved axis alteration. Applicable oblique edge/profile and splitting rules, washer support/access and affected transfer remain dependencies.

The additive [net-section normal-traction packet](current-corner-net-section-normal-traction-attempt01/README.md) corrects 84 inner-block area-context rows without changing original signed actions. Independent integration recovers N/Mx/My for all 252 cuts. Its common affine strain across disconnected cross-bore ligaments is a declared proxy, not qualified local stress transfer or wood capacity. See the coordinator checkpoint for results and pins. The independently produced uppermost-block packet is available separately; its scouting ratios are not adopted failures. Usable lower-corner responses remain three of six, and complete corner acceptance remains open.

### September 30: specific native release gate and bearing demands

The [nonzero-reference release coupon](current-floor-nonzero-reference-release-native-attempt01/README.md) passed the independent parent oracle at all 12 printed increments after one exact-frozen, independently reviewed, serialized launch. It confirms immediate constraint removal, retained external loads and reaction interpretation for this two-coordinate graph. The released step has zero normal and tangent reaction throughout. Full-frame event/state selection, weighted mapping, restart behavior and gravity/rank/gauge checks remain open; the result is not a fourth frame case. The native slot is idle.

The [corner timber-contact screen](current-corner-timber-contact-pressure-screen-attempt01/README.md) supplies 588 cell demands and 147 signed pair wrenches for seven interfaces across the three accepted cases. Parent replay passes. Maximum modeled cell-average pressure is 0.513416 MPa at A1 rear header/post contact. Actual local pressure, block/member bearing resistance and complete-joint checks remain unresolved. No new geometry, panel qualification campaign, original-bolt resistance restart or corner acceptance was introduced. The coordinator checkpoint records exact source pins and minimum remaining dependencies.


### September 30: prescribed staged native mapping passed; detailing remains conditional

The [staged native coupon](current-floor-staged-reference-native-attempt01/README.md) passes all 60 increments and independent STA/DAT coverage, including both captures and open-stage zero tangent action. Both native method freezes verify against live sources; the serialized slot is idle with 54 consumed launches. This closes the prescribed small-model mapping dependency only. Actual event/state discovery, 100-cell/full-frame mapping and initial gravity/rank/gauge readiness remain open; three of six frame cases remain usable.

The [BG045 applicability packet](current-bg045-edge-applicability-attempt01/README.md) preserves the specific A1-axis-2 5.4 mm conditional edge deficit while separating unresolved oblique face selection, header mixed-grain detailing and splitting. The [BG003 necessary-bearing packet](current-bg003-bearing-necessary-bound-attempt01/README.md) gives stiffness-independent minimum required projected peaks: spine 4.8292 MPa, side 1.9855 MPa and inner block 0.4385 MPa under the sole-bore/full-engagement proxy. These are necessary lower bounds, not conservative upper demands, strength comparisons or acceptance. Complete corner resistance remains open. See the latest coordinator checkpoint for exact pins and method limits. No reviewed-axis change or blanket original-bolt/panel requalification was made.


The [six-case global floor-normal screen](current-six-case-floor-global-necessary-statics-attempt01/README.md) passes parent replay: all six load-only resultant centers fall inside the authenticated 100-point footprint, with minimum signed hull margin 343.169223 mm. This removes a necessary global vertical/overturning obstruction only; horizontal/yaw transfer and local coupled contact/history compatibility remain open. No fourth usable response or support acceptance is gained.


The [whole-corner boundary packet](current-corner-whole-assembly-transfer-attempt01/README.md) now authenticates 21 assembly states and reconstructs all 338 interfaces per state at a common datum. Internal actions cancel; 62 signed boundary ports retain simultaneous onward transfer. This supplies complete conditional boundary bookkeeping, not individual group resistance or a six-case envelope. Axial/seat three-case coverage, BG045 header-section actions and the bounded initial-rank mapping audit are the next concrete tasks, with no native solve or reviewed geometry alteration queued.


The [complete corner resistance register](current-corner-complete-resistance-register-attempt01/README.md) now names applicable existing methods, input bases and exact open failure modes across the whole BG001/BG003/BG045 path. Its source-pinned producer retains all 168 plane states and simultaneous tie/paired-plane actions; eight critical plane states are reported without combining independent maxima. This is a consolidated conditional resistance-evidence deliverable, not closure of its open rows. Compatible gravity and one previously unusable frame case remain the next response result; three of six cases are still usable.


The [BG045 header transfer-section packet](current-bg045-header-transfer-section-demands-attempt01/README.md) now supplies complete source-discrete signed header cuts and the four-action BG045 station jump. Parent replay confirms 21 native/report inventory matches and body closures, 21 cut-jump checks and 84 one-sided comparisons with zero difference. This closes the header section-action dependency; local tension-perpendicular transfer and applicable splitting resistance remain open. The complete corner resistance table is updated accordingly.


The [three-case axial-seat register](current-corner-three-case-axial-seat-register-attempt01/README.md) passes parent replay and completes 126 signed tie states and 252 physical seats. All ties are tension; maximum 119.343 N gives modeled average 0.535828 MPa on the ideal CAD annulus. Existing component references are reused, not promoted to design resistance. Hardware/thread/washer steel/seat support and applicable wood/combined-action checks remain open.


### September 30: initial-gravity mechanism dependency made concrete

The source-bound [rigid-body branch audit](current-frame-gravity-rank-readiness-attempt01/README.md) passes parent replay. At cutoff 1e-10 the all-open branch has 80 screen-null directions, far beyond six common modes; conditional floor-stick alone still leaves 65. An optimistic all-active normal envelope leaves three planar common modes, while all-active plus captured stick has none. These are cutoff-sensitive kinematic envelopes, not actual state/full stiffness evidence. The 100 fixed floor endpoint nodes are correctly traced through 300 permanent projection equations, preserving their assumed-normal ground path. Actual directional gravity-state/operator/gauge readiness remains open.

Borrowed native matrix export and a tiny SCIP indicator-state fixture are bounded to that exact missing operator/selector dependency, with no frame launch or native mask retry queued. Three of six usable cases and complete corner resistance remain unchanged. The parallel hardware/material packet is separately owned; its initial adjacent-row material misreading was corrected before adoption, and frozen DF-L No.2 stiffness/strength references remain preserved.


### September 30: borrowed coupled-state selector verified; export coupon frozen

Parent read the independent support/corner packet and replayed its diagnostics byte-identically. Its staged-reference scenario remains distinct from the rejected fixed-zero combined-load branch. No guessed-mask native retry or rejected force adoption occurred.

The [SCIP indicator selector fixture](current-coupled-indicator-selector-fixture-attempt01/README.md) passes parent replay using ephemeral PySCIPOpt 6.2.0/SCIP 10.0.2. Eight tiny source-pinned cases exhaust their binary masks: zero-force event ambiguity, supplied nonzero-reference held state, fixed-reference no-state, mirrored multiple-state, and four simultaneous two-cell stages. Each returned state satisfies coupled equilibrium and branch laws. Signed continuous unknowns have no caller-supplied finite big-M/bounds. Parent identified and the producer corrected an incomplete-enumeration oracle assertion; the forced zero-budget path now explicitly stops without a completeness claim. Terminal known-answer SHA-256 is `8b42e4282952d8174f93b5f6138de14d0c88cbb1602d3968665aba5558045e88`. References are supplied inputs; event discovery/history, current-frame operator and 100-cell scalability remain unverified.

Parent pinned-manual/archive/eight-member replay supports the built-in matrix export route. The [free C3D20 coupon](current-native-elastic-operator-export-preflight-attempt01/README.md) is frozen in `current-free-c3d20-matrix-export-native-attempt01`, SHA-256 `d463e554aaf14fbe5f1d506745a19e460987268cad1d900862e7e485caedf460`; live source verification passes. The one-run scope is 60 equations, six rigid modes, analytical shear energy and mass. Independent exact-freeze review precedes any serialized launch. No frame/gravity/contact result follows from this method coupon.

The parallel hardware/material packet is now committed on master (`cf6ebe55`, `858688a9`), and its [requirements and conditional inputs](../hardware-material-specification-2026-09-30/README.md) are available for corner arithmetic. These are profiles/scenarios, not catalog-product fit or delivered inspection. The long BG003 product profile, washer metal method and dowel-bending strength basis remain explicit dependencies. Existing geometry and the three accepted rear cases are preserved.


### September 30: built-in native matrix export observed and verified

Parent read the exact-freeze independent review, verified live inputs and launched one serialized `free-c3d20-matrix-export-attempt01` run with a 120-second limit and 2 GB cap. Pinned 2.23 exited zero in 0.2875 seconds, wrote `.sti/.mas/.dof`, and the container was confirmed terminal. The [native coupon assessment](current-free-c3d20-matrix-export-native-attempt01/README.md) verifies 60 equations, six rigid modes, no significant negative stiffness eigenvalues, normalized rigid residual 3.45e-15, analytical shear energy and mass. Parent post-run replay authenticates exact sources, all recorded outputs and the assessment. Assessment SHA-256: `fea5d33bb8874b3abfa34acfbd15ceca3d8f6dd45d346ecf638cf45ffc0b85f4`. Native slot is idle with 55 consumed launches.

This establishes a usable built-in elastic assembly/export method on the coupon, avoiding a custom C3D20 kernel. It supplies no current-frame or fourth-case acceptance. Next task unlocks constrained equation/connector/load-work mapping: one tiny GLOBAL=YES SPC/MPC/SPRING2 input proposal with analytical expanded-coordinate energy/work checks, stopping before any native/freeze/frame/controller work. Nonzero contact-event references remain separate offsets, not frequency SPC values. The borrowed selector remains the verified tiny-fixture route; actual operator, state-dependent gauge, event discovery and gravity continuation are still open.


### September 30: constrained native mapping and current physical carrier interface verified

Parent read the exact [constrained-coupon review](current-constrained-matrix-export-native-attempt01/independent-review.json), verified live freeze `221537619e0d8c3adf0ef68bd7a88231033f1df00733a81a2b2686a4d67a6c62`, and launched one serialized `constrained-matrix-export-attempt01` run. Pinned 2.23 exited zero in 0.3873 seconds and emitted all three matrix/map files. [The replayed assessment](current-constrained-matrix-export-native-attempt01/README.md) verifies exactly 58 active coordinates, all 36 rotated orthotropic plus projected-SPRING2 affine cross-energies (maximum error 1.21645e-11 N/mm), five allowed rigid modes and no significant negative stiffness mode. Assessment SHA-256 `49805f1f32857ef85ac9650e26e3ed3c1dfcadf0607fe322a3bf833932ff03b7`. The reference-offset/load-work identity remains an analytical probe, not native capture evidence. The native slot is idle with 56 consumed launches.

Parent read and replayed [the physical connector projection contract](current-frame-physical-connector-projection-contract-attempt01/README.md). It binds the exact adapter and emits 348 bilateral, 1292 unilateral and 200 separate floor-tangent rows: 1840 rows / 62607 nonzeros over 37647 physical translations. All 3876 qghost equations match; source/native row discrepancy is 1.56e-13, independent owner-point rigid-row discrepancy 3.90e-13, and dual-work discrepancy 7.11e-15 Nmm. The 100 numerical floor endpoints are preserved one-to-one, with no added anchor. Gravity remains its own authenticated nodal map. Contract SHA-256 `4ceca771e26e1f1d0bf8efca8e3d77dc6d94194553d95e1fd75652ecf2f3f2d3`.

Parent also read and replayed [all 252 conditional wood-seat comparisons](current-corner-catalog-washer-wood-compression-screen-attempt01/README.md) against the catalog minimum complete USS ring and frozen CAD annulus. Maximum transverse stress/reference ratio is 0.129640 / 0.124345; BG045 block parallel comparison is 0.060019 / 0.057567 with no adopted local parallel washer-bearing method. The current corner resistance table links these conditional results and the specified hardware profiles. This is no washer-metal, actual-support, splitting or complete-joint pass. Output SHA-256 `54b780a015fb01615361b41a4ade4cf1ced3d7f3842bc7f40963e3c1c2fca487`.

The actual pure-solid export proposal identifies no density in the static source deck; gravity is supplied explicitly. Its source-verified derived export may use a named nonphysical auxiliary positive density for stiffness-only output, with no mass-matrix gravity substitution. The rank audit replays correctly in `OPENBLAS_NUM_THREADS=1 .venv/bin/python`; an initial uv/NumPy SVD rounding mismatch was an environment difference, not changed source inputs. A bounded engine-backed free-body condensation fixture uses the already exported free cube with independent surface-traction loads and keeps body rigid equilibrium explicit; it stops before actual-frame state selection. No currently missing case or contact/splitting gate is closed by these method results.


### September 30: six-case source identity and pure-solid export readiness

Parent replayed the [six-case operator-reuse contract](current-six-case-operator-reuse-contract-attempt01/README.md). Twelve exact source equality groups match across six actual decks: physical coordinates, 1903 C3D20 elements, 50 body ownership, 218 ordered property cards and 1640 permanent connector projection rows. Each of the six physical load maps remains distinct. Contract SHA-256 `a413f858d9384cb9bf31928304626ac8ed99b61811c6e982d15089e057119e9b`. This permits reuse of a successfully exported source elastic operator and linear projections, never a force, support/contact state or case pass.

Parent also replayed the [pure-solid sparse assessment method](current-frame-pure-solid-export-assessment-method-attempt01/README.md): 13 rejection/structure fixtures and the authenticated free cube pass. The actual-frame method requires all 37647 physical labels, finite complete positive diagonals, unique triangular pairs, zero nonzero cross-body coefficients and all 300 body rigid fields. Six small rigid residuals alone do not prove full rank or positive elastic stiffness. The separate cube condensation fixture also replays with independent surface-traction oracles; all six rigid equilibrium equations per body remain explicit.

Parent froze [one unloaded pure physical-solid export](current-frame-pure-solid-matrix-export-native-attempt01/freeze.json), SHA-256 `614c9b466fd05c0b5ee6917aa26e108fd8151b36459b8b84999cd474f13d9ed3`, for one bounded independent readiness review. It preserves exact physical geometry/material cards, omits springs, MPC/SPC constraints and loads, and adds named auxiliary density solely for the frequency export companion mass, which must be discarded. Actual source gravity stays separately mapped. This is an elastic operator export, not a response solve or a fourth usable case. No guessed floor-mask retries are authorized.


### September 30: actual pure-solid frame operator exported and authenticated

The exact-reviewed [pure physical-solid export](current-frame-pure-solid-matrix-export-native-attempt01/README.md) completed once with native exit zero in 2.342314 seconds, terminal container. Parent authentication/sparse assessment passes 37647 physical labels, 2320506 unique triangular pairs, finite complete positive diagonals, exact symmetry, zero nonzero cross-body coefficients and all 300 physical rigid fields; maximum normalized rigid residual 2.6186013240290654e-13. Assessment SHA-256 `ba41b9c75815f7daf27b3517ac01afff109d5f3e3611aa985811e92c269e69ec`. The native slot is idle with 57 consumed launches.

This is actual CalculiX source stiffness, not a custom solid-element assembly, constrained tangent, gravity/support response or new corner demand. Auxiliary `.mas` remains excluded from gravity. Full elastic-subspace rank/definiteness and a reaction-free per-body inverse still need bounded checks before operator reduction; six rigid residuals alone are insufficient. The next isolated preflight uses the authenticated free-cube traction oracle and sparse borrowed linear algebra, retaining explicit body force/moment equations. The six-case identity contract can save five repeated source-operator exports; it grants no state/force/pass reuse. Exactly three rear cases remain usable. BG003 coupled clearance/material/shared receiver behavior, BG045 edge/splitting, washer steel/support and complete connection checks remain open. Reviewed 92 axes and twelve original leg/runner arrangements are unchanged.


### September 30: actual export warning reconciled to pinned parser

Parent inspected the native stdout rather than treating exit zero alone as sufficient. The constrained coupon and actual frame logs warn that explicit `GLOBAL=YES` is unrecognized. Exact pinned `frequencys.f` defaults to global true and recognizes only the `GLOBAL=NO` override; ignored explicit YES therefore leaves the global default unchanged. All three logs report global node-direction output, and the rotated and physical-map oracles remain passed. The separate [warning audit](current-frame-pure-solid-matrix-export-native-attempt01/warning-audit.json), SHA-256 `28f569bf3222ad2fe990a396c66c6990a516a0336c979f86de837063e8141b4c`, authenticates the raw logs/execution/source without editing frozen evidence. This corrects the explicit-keyword support description; future new decks should omit the redundant YES token. No rerun is required solely to remove it.


### September 30: combined source loads distinguished from gravity-only maps

Parent audited actual force sums before operator reduction and found that the physical-projection packet's `source-gravity-nodal-map.json` copies A12 `physical_body_loads`, a combined case map. Its gravity-only label/description is incorrect. The preserved file has resultant approximately (0,+300,-4424.926817) N; separated gravity is (0,0,-2200.816010) N and A12 climber is (0,+300,-2224.110808) N. This additive [six-case load audit](current-physical-load-map-audit-attempt01/README.md) authenticates actual source maps and every nodal recomposition/owner; SHA-256 `eb9d23d996f7d877edea9607e98501b080dc95e8bc888a55c0a43e01de861052`. No response/state has been calculated from the mislabeled file, and the unloaded native stiffness is unaffected.

All next gravity-settle calculations must use `current-frame-pure-solid-matrix-export-preflight-attempt01/source-load-maps.json` gravity-only fields, then add each distinct climber field during its ramp. Earlier checkpoint language describing the preserved projection-map file as gravity-only is superseded. Projection rows, distinct combined six-case load-map hashes, raw exports and geometry are unchanged.


### September 30: seven corner timber interfaces classified against proposed grain

Parent read/source-inspected/replayed the [conditional contact-grain screen](current-corner-timber-contact-grain-applicability-attempt01/README.md): all 588 existing cell states and 147 signed pair wrenches remain unchanged. Fourteen receiver/interface combinations classify as ten transverse, three parallel and one oblique (side at header/side, 40 degrees). Matching transverse cell averages compare with conditional DF-L No.2 Fc-perp625psi, dry/normal-temperature/unincised and noCb credit; CD and CF do not apply to this reference. Maximum ratio is 0.1191434164 on the header at header/post in A1rear, pressure0.5134155868MPa. Output SHA-256 `c26f8d2aff8fd13e4a9bd4c594d2897f20fc0caac2cbf400d201112ee470c0d0`. The complete corner register now links this applicability result.

This supplies conditional member-contact comparisons only; cell averages do not bound peaks, parallel/oblique local treatment remains unspecified, ripped-block material/grade is a study scenario, and actual support/fit and complete bearing remain open. No native solve, geometry change, new response or full joint acceptance occurred.


### September 30: all actual body elastic operators pass the bounded numerical gate

Parent source-inspected and replayed the sparse-border/rigid-lift known-answer fixture, including analytic traction/work, injected extra mechanism/negative direction, unbalanced point-load rejection and corrupt-factor residual rejection. Parent identified and the producer fixed the original unconditional solve PASS; KKT, gauge and multiplier gates are now explicit. These remain distinct from the unchanged final physical body/global limits.

The parent then ran [one actual 50-body audit](current-frame-body-elastic-positivity-audit-attempt01/README.md) under the shared native run lock and a single-thread 180-second /6GiB cap. All 50 exported body blocks pass rigid-lift Cholesky and condition estimation, body-loop13.255sec; minimum rcond9.93942622e-11 on main_lower_left, above declared1e-12 floor. Maximum normalized rigid residual2.215e-14. Actual assessment SHA-256 `2ad8c74b4a061ee9335c3b9f3549f325929be9148d1753f370998ec5e681c563`. Provenance verification passes. No original K, load, support, geometry or accepted response was changed. No native response or fourth usable case follows.

The immediate deliverable is engine-derived connector compliance H, rigid projection D=BR and distinct case gravity/climber load terms while retaining all300body force/moment equations. Before individually unbalanced basis columns are projected for compliance construction, a tiny independent known-answer comparison must show that their raw wrenches remain in D^T*f=W and are never silently discarded as physical loads. Current ownership: matrix_mapping_scoped_review prepares that isolated fixture; parent owns actual operator reduction/gravity/contact execution and validation; bg045_edge_applicability owns the bounded current BG045 edge/profile/splitting interpretation. corner_contact_pressures completed seven-interface grain applicability.

Parallel-owner request: the remaining86newbolt washer-seat demand/geometry coverage is unassigned here and is useful parallel work, reusing the reviewed six-corner-seat method and the three accepted all-body responses; keep the12originalLEG/FLOOR-RUNNER arrangements separate. Revision-bound stockcut/yield/BOM is also unassigned here. BG001/spine finished-section work may proceed conditionally but must preserve the known disconnected-ligament/common-affine-strain proxy boundary. None of these should duplicate the owned elastic/gravity or BG003/BG045 mechanism work or add native authority.


### September 30: actual connector reduction stopped at one numerical gate

Parent replayed the extended projected-column cube fixture using the shared sparse bordered helper; sparse H/e agree with the independent dense elastic reference, raw D^T*f=W is retained and unbalanced physical combinations reject. One source-bound [actual connector reduction](current-frame-connector-compliance-attempt01/README.md) then stopped on main_lower_left columns16:32: KKT residual7.23261944e-10 exceeds fixed1e-10. Gauge displacement3.797e-11mm and multiplier1.084e-10N separately pass their2e-10 limits; projected raw wrenches are near1e-15N. No H, force, physical response or state is accepted; all50body positivity results stand. Source snapshots/provenance of this stop verify.

Parent prepared the exact16column rejected chunk and independently compared float64/extended-precision arithmetic: same-solution residual3.00920477e-10 at extended precision, so evaluation alone still fails; difference in evaluation up to8.18436e-10. Borrowed-library standard refinement is now a bounded dependency: original K/physicalgates unchanged, fivecorrectioncap and explicitstagnation/budgetstop, tinyknownanswerfirst then this exactchunk. No fullbuild/native/contact retry is ready until that diagnostic passes. matrix_mapping_scoped_review owns the isolated refinement fixture; floor_coupon_readiness owns the100normal/200tangent sourcejoin contract for subsequent contact-state assembly, without fullstate/nativework.

Parallel-owner update supersedes the earlier optional task queue: the separate repository-review root now owns `docs/wood-joints-mvp/hypotheses/upper-block-strength-2026-10-01/` for eight upper blocks/32axes, starting outertop pair, under owner instruction. No worker in this thread owns upper resistance. Preserve its files; reuse its results later. This thread retains BG001/BG003/BG045 and elastic/gravity/contact work. No new geometry/native authority is transferred.


## September 30: owner support/corner guidance and bounded numerical follow-through

The owner-provided support/corner review README was read and its diagnostic
replayed byte-identically. Its gravity-settle/contact-event scenario remains
distinct from the rejected combined-load fixed-zero branch. No guessed masks,
rejected forces, or geometry changes were adopted. The current primary joint
is the left corner-block chain BG001 post/spine, BG003 spine/side/inner block,
and BG045 inner block/header; original leg/runner resistance remains reused.

The verified five-correction refinement wrapper cleared the exact rejected
panel chunk in one correction under unchanged gates. A separate full
connector-compliance attempt 02 completed all four panels but stopped at
kicker_left interface columns 16–31: force residual passes, but a stable
1.6435e-9 N gauge multiplier exceeds the 2e-10 N limit. No full H or physical
response is accepted. The next task is the exact original-operator multiplier
identity and rigid-mode leakage diagnostic; its stop condition is a causal
numerical disposition, with no full-H retry or gate change in that task.
See current-frame-connector-compliance-attempt02/README.md.

BG045 signed edge/end/row/splitting applicability replay passes. The A1 axis-2
20-versus-25.4 mm comparison remains a conditional 5.4 mm exception under its
minus-Y face interpretation. Header loads are mixed to grain; pair pitch is
not an NDS row check because the bolt line is not aligned with load. Three
full-load header tie resultants are retained (107.967, 139.225, 38.097 N), but
member closures are not local splitting stress or resistance. No axis move
is made. See current-bg045-edge-splitting-applicability-attempt02/README.md.

A bounded BG003 task now converts only the already computed compatible
radial-clearance scenarios to smooth-shank normal-stress references using
the simultaneous axial tie and specified Grade 5 yield. It runs no new
bearing solve and will not establish a physical demand bound or joint pass.
The parallel repository thread owns upper-block strength; this thread does
not duplicate that lane. Current usable response coverage remains 3/6.


## September 30: BG003 compatible steel screen replay and kicker causal check

Parent read and replayed the bounded BG003 steel-normal-stress screen: PASS,
output SHA 38546b1bfc72a344227285fea63ffacc8930866f4873efa7a0f31f2982d3f3eb.
The four saved A12 bolt-1 proxies give 75.370–178.131 MPa normal stress from
one simultaneous 95.96739 N tensile tie plus the paired sampled bending norm.
The maximum ratio to conditional smooth-shank Grade 5 yield is 0.280822.
Actual bearing/contact, a physical demand bound, shear/thread interaction,
splitting and full joint resistance are not established. The complete-corner
table now records this useful conditional result separately.

The exact kicker stopped iterate was replayed once under the shared ledger
lock; its history matched attempt02 exactly. The frozen operator's rigid-mode
leakage predicts its multiplier: max predicted 1.6435145875e-9 N versus actual
1.6435112275e-9 N, maximum component difference 7.7259e-15 N. This identifies
why additional refinement cannot clear the original zero-multiplier gate.
The pinned solver writer emits 14 significant digits (%20.13e), a potential
roundoff source; serialization is not yet proved to be the sole cause. The
old gate remains failed. A distinct elastic quotient/projection method needs
its known-answer and original-operator error disposition before another full
reduction. No native launch, new floor state, geometry change or accepted
frame response followed. Coverage remains three authenticated rear cases.


## September 30: source floor joins and method-oracle replay complete

Parent read and replayed the floor normal/tangent join contract and separate
current-controls two-cell reset mathematics. Both pass; all 100 normal cells
join exactly to 200 signed tangent rows and unique reference coordinates,
with zero coefficient discrepancy. Join output SHA
607ec82a8f830101a5bed07a9d1214aa85ac09179a9091472f7c951671ed8c4e.
The historical fixture's stale AGENTS pin remains explicitly failed; only
master/shared-staging controls changed, and the new mathematical replay
preserves the old result/files. Parent also replayed the pinned borrowed
SCIP/PySCIPOpt selector: PASS for its tiny known answers, including no-state,
multiple-state and zero-boundary ambiguity. No actual gravity/contact event
or frame support state is accepted by these source/method results.

Parent read and replayed the kicker equation diagnostic: PASS attribution;
the original zero-multiplier gate still FAILS. The next bounded method task
is a distinct elastic quotient known-answer preflight with explicit rigid
leakage/error reporting, before choosing any new full reduction. The task
unlocks an elastic connector operator only; it stops at method proof and
cannot adopt a floor mask, discard raw 300-coordinate body balance, relax
native physical checks, or run a native/full-frame response. The original
operator, failed attempts, criteria and reviewed geometry are preserved.


## Continuation: corner section references and quotient readiness

The preceding goal turn made progress (completed/replayed corner screens,
source floor joins and causal numerical evidence), not a blocked wait.
Parent read and replayed the new grain-aligned corner section material screen:
252 existing one-sided proxies, six case/member summaries, output SHA
 a5a27450b72ee9f4fec1ad35191c0b4552e497e60a53f4e48b493e69050b6a2c.
Spine peak raw Ft/Fc ratios are 0.107877/0.032470; inner-block peaks are
0.010454/0.004424. These are common-affine nominal section comparisons to
unadjusted conditional references, not local splitting or adjusted NDS checks.
The complete-corner register incorporates the results.

A parent read-only screen of all 50 original exported body operators found
none outside the proposed induced-infinity rigid-leakage limit of 5e-14;
maximum was 2.20820e-14 for top_outer_left_cleat. This is preliminary method
readiness only. Attempt03 integration is a draft: no inputs frozen or run.
Parent source review identified three concrete quotient-method corrections:
retain the verified bounded refinement with extended-precision audits; report
gauge-term wrench as (R.T R)lambda rather than lambda itself; and gate the
actual rigid equation closure rather than only its algebraic identity. The
Luna author is implementing these before cube/corruption fixture completion.
This is a new method with specific concerns, not a repeated cold review.
No native launch, accepted H, new case, axis change or strength pass follows.


## Continuation: all-body elastic reduction cleared

The parent-owned [attempt04](current-frame-connector-compliance-attempt04/README.md) passes all 50 bodies, separate gravity/climber columns, full-H reciprocity and positivity in 34.382 s. Provenance replay passes. The changed aggregate gate derives from the unchanged nodal residual budget through R.T, plus measured independently gated arithmetic-order error; no arbitrary absolute allowance is added. Earlier stopped records remain preserved.

This unlocks the bounded gravity-settle/climber-ramp contact-history calculation. It does not select a contact state or increase the three authenticated rear cases. Raw D/W body wrenches and all gravity sources remain explicit; physical responses still require body/global equilibrium, source laws, admissible normal/tangent states and event-captured references. No reviewed geometry, original leg/runner resistance or native execution inputs changed.


### Continuation: reduced coupled selection adapter checked

Parent prepared [reduced coupled indicator method](current-reduced-coupled-indicator-method-attempt01/README.md), borrowing pinned PySCIPOpt 6.2.0 indicators. Producer and replay pass all eight existing coupled toy oracles in compliance coordinates, including no-state/multiple-state/event-boundary/nonzero-reference outcomes, plus two signed raw D/W bilateral equilibrium oracles. This specifically validates coupling source laws to q=D*a+e-H*f and D.T*f=W; it does not solve the frame or establish a branch gauge/history.

The independent source initial-condition audit reports 100 floor normal initial spans with maximum residual 2.4158453e-13 mm. An initially bearing gravity-direction cell can capture only its zero-load tangent coordinate; no mask is chosen in advance. The frozen directional contract and existing-native response applicability replay remain pending before an actual state selection. The fixed-episode convex-QP shortcut remains separately bounded; a lowest-energy branch is not a uniqueness/history proof.


## October 1: actual gravity-direction selector stopped at its solver budget

The existing A12 native response applicability replay passes all seven increments against attempt04, with independently propagated DAT token intervals; no solver was launched by that replay. Parent read its source-bound sign mapping and reproduced the output. This clears a concrete reduction-applicability dependency without transferring physical case acceptance.

Parent then froze and ran [one a12-rear gravity-direction selector](current-a12-gravity-direction-selector-attempt01/README.md) under the shared ledger lock, single thread,6GiB/180s process cap,45s first feasibility limit. SCIP stopped at timelimit, zero feasible solutions, total46.823s. Source/output provenance passes. There is no accepted or rejected candidate force vector, no actual-branch gauge result, no uniqueness or infeasibility proof, and no fourth usable case. No guessed-mask or larger-budget retry is queued.

The exact next computational dependency is a bounded mathematical/known-answer check of the primal convex energy formulation: determine whether ordinary unilateral contact hinges can remove1192 nonfloor binary indicators while retaining100 coupled floor episodes. It must recover source equilibrium and reject extra normal-boundary reactions and ambiguous states; any future energy symmetrization must still pass original-H residuals. This is owned by corner_contact_pressures, with no actual H inversion/frame solve/native authority. The floor initial-condition contract is complete, so no missing initial-gap record is asserted.


### October 1: explicit energy approximation bounded; ordinary-contact convex algebra replayed

Parent read/replayed [primal energy condensation fixture](current-primal-energy-condensation-fixture-attempt01/README.md): three exact source classes/six prescribed branches plus the general KKT oracle pass. Crucially the no-state closed energy minimum has a0.5N extra normal-bound reaction and g_n=-0.5N at zero gap; it is rejected rather than called an admissible contact state. This supplies a checked route to remove ordinary unilateral binaries, with floor source-law/boundary checks retained.

Parent performed one [symmetric-energy factor preflight](current-frame-convex-energy-factor-preflight-attempt01/README.md) under the shared lock:1840-row Cholesky factor available in2.149s, rcond2.4413e-11, reconstruction residual3.58e-16. Raw H is unchanged. The [A12 symmetry perturbation replay](current-frame-connector-compliance-attempt04-a12-symmetry-perturbation-attempt01/README.md) is byte-identical under parent replay: max|(Hsym-H)f|7.174e-10mm across seven increments, original DAT-only compatibility and D/W gates unchanged. These are numerical/method results, not a new state or acceptance.

Parallel-owner guidance received: its next owned lane is upper-outer-load-path-2026-10-01 for the two top outer joints, frozen three-case sources, no geometry/native changes. This thread keeps primary corners, gravity and washer/fit paths. No duplicate upper study is queued. The public hardware footprint input packet is reused; washer-to-wood support remains separate from the smaller head/nut-to-washer metal footprint.

Bounded next tasks: floor_coupon_readiness prepares a tiny borrowed convex-energy SCIP adapter with only floor binaries, including source-law rejection and nonunique/boundary stops; bg045_edge_applicability checks finished-CAD wood support under the12 primary-corner outer washer seats. Neither worker runs the frame/native solver or changes geometry. Parent retains actual execution/readiness and original-H/body/source audits.


### October 1: twelve primary-corner washer support areas verified

Parent read and reproduced [finished-CAD washer wood support](current-corner-washer-wood-support-attempt01/README.md). All twelve BG001/BG003/BG045 outer seats have one source-bound trimmed support face; both catalog annulus bounds intersect fully, with zero unsupported area and modeled plane gap at most 1e-12 mm. The same 126 signed ties give 252 conditional uniform seat averages, maximum 0.558649011 MPa. This closes modeled wood support-area uncertainty, not washer metal behavior, physical contact or joint resistance. The catalog geometry remains conditional, including BG003 where no matching washer lead is recorded. No reviewed geometry or native input changed.

The owner-supplied September 30 support/corner diagnostic again reproduces byte-identically. The tiny floor-only convex SCIP adapter remains in preparation: its first known-answer solve was marked optimal but did not meet force-recovery precision. A separate prescribed-mask OSQP calculation and source-law audit are being added; no gate is widened and no frame state follows from the solver label. Rejecting one energy minimum cannot prove absence of physical states in other floor branches.


### October 1: floor-only convex adapter replay and bounded frame application

The final tiny [floor-only convex adapter](current-floor-binary-convex-energy-adapter-attempt01/README.md) passes parent replay across all 24 masks in eight source classes, plus the raw-wrench oracle and nonzero raw-H skew audit. Provisional SCIP forces are distinguished from independently polished source-valid states. The first parent replay was stale during the author's final strict-gate edit; the final stable replay passes without changing a tolerance.

Parent froze and ran [one convex A12 gravity-direction application](current-a12-gravity-direction-convex-selector-attempt01/README.md) under the existing lock and 6 GiB / 180 s caps. It uses 100 floor binaries instead of 1,292 ordinary/floor binaries, with raw-H and source-law audits retained. Construction took 1.102 s and presolve 1.15 s; the 45 s solver budget expired at one processed root node with zero feasible solutions. No candidate force vector or second branch search exists. Frozen source/output/log provenance passes. The log does not identify the root-node subroutine responsible. No new usable case, native run, geometry change, physical failure or infeasibility proof follows. Do not retry guessed masks or simply enlarge this budget.

Current corner support-area progress is usable; the floor state remains missing. A next numerical task must address a specifically identified root-relaxation or frame-scale force-refinement limitation, with known-answer checks and its own stop, rather than reopen a general solver project. BG003 physical coupled bearing and BG045 detailing/splitting remain separate primary-corner gates.


### Next bounded work after the root-node budget stop

The floor worker is diagnosing the recorded root-relaxation limitation from frozen code/logs and pinned solver documentation, with no new frame solve, factorization, altered D/W, anchors or larger budget. Its result must distinguish an identified formulation issue from a performance hypothesis; the current log alone cannot identify the expensive root subroutine.

The corner worker is preparing a known-answer anisotropic circular-clearance point-law fixture for BG003. The proposed potential minimizes anisotropic elastic energy over a circular clearance set, retaining one coupled transverse resultant. Its force oracle, isotropic/zero-gap limits, derivative/tangent and rotation tests must pass before applying it to the existing finite beam proxy. Published density-based stiffness regressions remain hypothetical inputs, not calibrated bounds. The task stops before finite joint or native execution; root owns that readiness. This addresses the specific missing combination of grain and gap, not general solver development or joint strength acceptance.


### October 1: BG003 combined grain/clearance point law replayed

Parent read and reproduced [anisotropic circular-clearance fixture](current-bg003-anisotropic-clearance-point-law-fixture-attempt01/README.md). Seven known-answer gates pass. The potential minimizes anisotropic elastic energy over a circular free-clearance set; it supplies one coupled Y/Z force with a symmetric positive tangent. A visibly mixed-force oracle, isotropic radial equivalence, zero-gap rotated-linear response, interior zero force, rotation and derivative checks pass. The recipe's quadrature weight is applied once, and root bracketing is explicitly bounded. This validates the hypothesized point law only; it does not establish a physical bearing curve or strength.

The next bounded task prepares an efficient batched finite adapter reusing the existing A12 bolt1 beam, receiver wrenches, gauges and continuation/refinement gates. Exactly eight density/mesh/gap combinations are proposed; no finite run is authorized to the worker. Root will own readiness, source freeze and serialized execution. The 350/550 kg/m³ regression inputs remain sensitivities, not calibrated bounds; axial tie, washers, splitting and the shared two-bolt timber group remain separate.


## October 1: combined BG003 grain/clearance finite proxy completed

The parent executed exactly eight frozen A12-rear bolt-1 local scenarios under
the shared lock and 180 s / 6 GiB caps; elapsed 23.58 s. No native launch,
source change, geometry change or adopted joint pass occurred.
[Parent result assessment](current-bg003-anisotropic-clearance-finite-adapter-attempt01/parent-results.md)
records signed actions, closure, independent zero-gap oracles and all four
16/32 action refinements below 0.276%. Pressure was not a declared refinement
gate: inner-block clearance pressure samples change by 3.49–4.27%, and remain
unqualified. Clearance raises sampled bearing while reducing peak bending;
its effect on middle bending depends on density. These are constitutive
hypotheses, not actual bounds. Stop the completed proxy campaign here.

Complete-corner acceptance still needs applicable bearing/group/splitting and
combined hardware checks; BG045 A1 axis 2 retains its 20 vs 25.4 mm conditional
edge exception. All three authenticated rear exports remain usable; forward,
left and right are unresolved. No original LEG/FLOOR-RUNNER resistance work
was restarted. The floor formulation diagnosis is being corrected to
distinguish energy-row null modes from full-D null modes before choosing
a next support formulation; no guessed-mask retry is authorized.


### Parent floor-diagnosis correction replay

The corrected [root-relaxation diagnosis](current-a12-root-relaxation-diagnosis-attempt01/README.md)
now passes parent read-only replay. An exact full-D null with nonzero load
work makes added raw equilibrium infeasible; a null of energy/held rows may
change released tangents and requires explicit zero released tangent forces.
Neither numerical rank evidence nor the stopped selector proves an actual
unbounded branch or identifies its solver bottleneck. An earlier parent
replay during producer editing saw a stale output mismatch; final stable
producer/output replay passes. No frame solve occurred.

The next support deliverable is preparation of one fixed-episode dual-QP
known-answer test against the full-load authenticated A12 response. Its
combined native load schedule is lambda*(gravity+climber), not the proposed
gravity-settle then climber-ramp schedule. Use exact recorded constraints,
references, source signs and released laws; no guessed gravity-start mask.
Parent owns readiness, freeze, serialized execution and final validation.
Stop on source mismatch, inaccurate solve, numerical budget or any source
compatibility/law/wrench failure. This can establish method applicability to
one known episode only, not a fourth usable case or support-history acceptance.


## October 1: fixed-episode inputs and BG045 modeled profiles

The [A12 prescribed-episode preparation](current-a12-fixed-episode-dual-qp-preparation-attempt01/README.md)
passes parent replay: 1,615 variables, 348 bilateral + 1,217 unilateral +
50 held tangent rows; 75 open normal and 150 released tangent forces stay
exactly zero. All seven native increments retain 25 strictly bearing /
75 strictly open cells. Use authenticated native forces, not the rejected
earlier screen output. The source is a conditional numerical response, not
physical branch acceptance, uniqueness or a gravity-settle episode.

The [first fixed-rho known-answer QP](current-a12-fixed-episode-dual-qp-known-answer-attempt01/assessment.json)
reached its 45 s cap at 109,470 iterations with primal residual 1.1731e-8 and
dual residual 0.0098318. It never reached solved, supplied no candidate force
file and did not proceed to physical or source-DAT comparisons. Source freeze
remained unchanged. This is a solver-budget stop, not structural infeasibility.
A separate same-budget attempt uses documented adaptive residual balancing
after all tiny source oracles pass with those exact settings; no equation,
mask, reference, tolerance or capacity is altered. Parent owns execution.

[BG045 finished-STEP station queries](current-bg045-finished-profile-edge-attempt01/README.md)
pass parent replay. All 80 queried external faces match rectangular distances;
block axis 2 minus-Y remains 20 mm at all 5 shaft-overlap stations. Conditional
25.4 mm comparison remains 5.4 mm short if that edge/provision applies. The
continuous minimum is not proved and code loaded-edge assignment/splitting
remain open. No reviewed geometry moved.

[The necessary-equilibrium augmentation fixture](current-floor-energy-equilibrium-strengthening-fixture-attempt01/README.md)
passes parent replay: 24 prescribed masks retain classification; nonempty
equilibrium oracle and zero/nonzero-work gauge toys behave as declared. Raw
equilibrium alone can balance through a nonphysical released tangent force;
the open-source law gT=0 must be imposed and independently checked. This
fixture does not prove root-bound improvement on the frame.

Parallel owner preserves published stock commits e853af55/5b10b4e0 and owns
current-finished-feature-register-2026-10-01 and current-stock-package-cost-2026-10-01.
Root has not staged, committed or edited those packets.


### A12 prescribed-episode numerical outcomes

[Adaptive residual balancing](current-a12-fixed-episode-dual-qp-known-answer-attempt02/assessment.json)
reduced the same QP from a 45 s fixed-rho stop to OSQP solved in 0.652 s / 1,250
iterations. Source freeze was unchanged. Body residuals were 5.36e-11 N and
1.18e-7 N mm; source-law error 0.001499 N and H-skew displacement 7.174e-10 mm.
Strict closed/open floor states, references and exact released forces passed.
The candidate remains rejected: minimum unilateral force −1.04588e-8 N
exceeds the declared −1e-8 N sign allowance; 69 force and 30 projected q point
comparisons exceed original DAT intervals. Native rigid-coordinate intervals
pass. No diagnostic candidate force is adopted as a joint or new frame demand.

[The saved comparison diagnosis](current-a12-fixed-episode-dual-qp-known-answer-attempt02/source-comparison-diagnosis.json)
records every failed row: 17 bilateral / 36 unilateral / 16 held-tangent force
comparisons; 4 unilateral and 26 tangent q comparisons (25 released / 1 held).
Maximum force difference 0.001081 N and q difference 1.073e-6 mm are source
reproduction failures, not structural-strength failures. Raw-H and Hsym
comparisons fail the same row counts; the cause is not established solely
by symmetrization or solver-status labels. No original interval is widened.

[A sharper absolute-only stopping criterion](current-a12-fixed-episode-dual-qp-known-answer-attempt03/preflight-stop.json)
failed the unchanged tiny preflight with maximum iterations reached. Therefore
no frame run was made in attempt03. Stop the OSQP settings campaign here.
The Luna worker's next bounded deliverable is a tiny independently checked
fixed-active-constraint linear KKT refinement, using borrowed SciPy routines
and original source sign/law/interval checks. Floor mask and episode stay
frozen; no clipped force, new support mask or unverified rank is acceptable.
Parent retains later frame readiness, freeze and serialized execution.

The active full milestone remains incomplete: only three authenticated rear
conditional exports are usable, and forward/left/right plus named corner
resistance dependencies remain open. This turn produced verified geometry,
input extraction, scalar methods and a solved-but-rejected numerical candidate;
it is progress, not a blocked-goal turn or a completion claim.


### October 1 continuation: current bounded work and geometry consequence

The original-H fixed-branch comparison is being prepared after parent replay
of its tiny general-LU method. Retain the previous force-source STOP until an
actual frozen comparison passes all original gates. No new frame force is
adopted; no native launch was made in this continuation.

Parent inspected and executed the existing source-pinned BG045 axis-2-only
proposal producer (it has no argument parser or read-only CLI). Its generated
`detail-screen.json` SHA-256 is
`c0899e9b4efdb3c1e2b44f4bd0bdde824656d4bb3d5dd8668f615eaba69e9a30`.
No producer, source geometry or reviewed axis changed. Both-face inward moves
reduce the modeled orthogonal-bore web from 7.453 to 2.053 mm; axis-2-only
preserves the governing 7.453 mm web but leaves the axis-1 conservative
component comparison unresolved. These are geometric consequences, not
splitting capacities or adopted modifications. The next proposal update
reuses this arithmetic and checks what newer finished-feature/washer evidence
can actually establish before any geometry review.

A separate tiny event-reference worker now tests gravity settling followed
by climber ramp with coupled contact states and explicit stop conditions.
It must localize contact events rather than choose favorable tangent offsets
or inherit a finite last-open-step reference without refinement evidence.
No full-frame scenario is ready solely from that assignment.


### October 1: current evidence and exact remaining work

The original opening snapshot above remains historical. Owner direction
continues Option B and prioritizes the new corner-block joints. Panel product
qualification is not a blanket prerequisite for conditional corner calculations.
The separate current panel-purchase record preserves the owner-accepted
construction scope and missing product resistance; no capacity transfers.

| Original gate | Current usable evidence | Exact remaining dependency |
| --- | --- | --- |
| Conditional support | Three authenticated rear exports; pinned original-H linear operator; small event/reset/state-classification and budget-stop fixtures pass. | Forward/left/right remain unresolved. A staged frame history needs the actual initial state and coupled event-reference selection. Original A12 operator reproduction still misses 27 force intervals; all physical and q/coordinate checks pass. |
| Panel route | Reviewed 66 screw axes, eight owner-directed moves and bounded receiver/transfer evidence retained. | Only an identified corner-transfer dependency reopens panel work; inherited catalog capacity remains absent. |
| Receiver and hardware paths | Signed complete left-corner boundary/section demands from three exports; current washer support and source-bound BG001 directional comparisons; compatible BG003 proxy and BG045 detailing proposals. | Physical BG003 bearing/clearance bounds, common two-bolt splitting/interaction, delivered shank/thread/washer compatibility and applicable BG045 edge/splitting interpretation remain open. |
| Distributed gravity/member sections | All gravity sources retained in the reduced operator and native response sources; signed sections remain available for the authenticated rear cases. | Preserve density/material hypotheses and source load decomposition; numerical response does not establish actual stock or local splitting stress. Unresolved support states block corresponding new case sections. |

The [BG003 component-reference screen](current-bg003-anisotropic-clearance-component-reference-screen-attempt01/README.md)
passes parent replay: maximum 32-division sampled pressure/Feθ ratio 0.52215
and smooth-section stress/634.318 MPa reference ratio 0.28487. These are
conditional sample/reference comparisons, not design DCRs or physical bounds.
The [BG045 proposal](current-bg045-symmetric-inward-detail-proposal-attempt01/README.md)
passes parent replay and quantifies the 2.053 mm neighboring web under symmetric
axis moves; no moved geometry or resistance is accepted.

The [saved raw-H failure diagnosis](current-a12-fixed-active-raw-H-force-failure-diagnostic-attempt01/README.md)
passes parent replay after distinguishing geometric-versus-projection
discrepancies from unisolated finite-length, printed-displacement and mapping
contributions. Emitted coefficient differences are tiny; operator construction
residuals lack a rowwise force-error bound. Candidate endpoint displacement
fields are absent. A bounded two-body recovery readiness task targets worst
row 1586; it does not queue a global rebuild, another active set or native solve.
