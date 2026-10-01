# Receiver and load-path ledger — 2026-09-29

This append-only ledger binds interface identities and existing load/mass
accounting for `compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. It separates source geometry and
wrench bookkeeping from demonstrated mechanical transfer. It does not assign
capacities, infer sharing, accept demands, change geometry, or authorize a
mesh or solver run.

## Authority and frozen identity

- Governing [AGENTS.md](../../../../AGENTS.md), SHA-256
  `672203b929d51d340d39d770e71dd43b019794ea33172bc9f4f7be469fc20536`.
- Current [coordinator checkpoint](LUNA-MAX-COORDINATOR-CURRENT-CHECKPOINT-2026-09-29.md),
  SHA-256 `465895b1b4b82d56290e7d5d67e2a35f4ad9e7017a3b1cba0a49d0efb8e529d4`;
  [root continuation note](root-continuation-note-2026-09-29.md), SHA-256
  `60501849cdfb156c09e74ad6eff5cb9161180af2f0ef93fedeab5b0a312006d3`.
- Frozen [full-frame manifest](../evaluation-resume-2026-09-24/current-full-frame-input-manifest-attempt04/current-full-frame-input-manifest.json),
  SHA-256 `9e682e28c3d4c3c0594863f82c6b74d19dee2700f3856d34e1a26f69082e4f11`;
  reviewed source commit `b1e8707d5bd15208ce2dd48a65bf942e78deda62`.
- Frozen [six-case load contract](../evaluation-resume-2026-09-24/current-load-cases.json),
  SHA-256 `9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a`;
  explicit [load datums](../evaluation-resume-2026-09-24/current-load-datums.json),
  SHA-256 `c3a561b84eb56472264e92eacabae7c2e06fe33633ebba96f1de9ee974924022`.
- [Duty-path graph](../evaluation-resume-2026-09-24/current-duty-path-graph-attempt01-2026-09-28/duty-path-graph.json),
  SHA-256 `b3cf2e6b9bc6052e914bbce4ba3052dd3329075ca2043931002ce6fb7a448115`,
  classified as topology/identity only; its independent review is
  `742b47c45a21d90a159a30050f6d948a64e5af47005abede232577638a10a4db`.
- [Receiver screen](../evaluation-resume-2026-09-24/receiver-screen-attempt04.json),
  SHA-256 `851495f2ccc80f286a7eae97fc54bcf602a478bb7d4e13eb28e2ae44cfb87991`;
  [mass/topology map](../evaluation-resume-2026-09-24/current-mass-topology-map-attempt03/source-topology-map.json),
  SHA-256 `308a329a0b40db454d5b0e27c9ec2eca92d66eec96bfb222df5f7b7185bef4d4`,
  reviewed at `956a5b63047c7e49c3aedae407f008d5b0d5828aad86382ecf1d26200db196ad`.
- Current [dead-load placement scenarios](../../current-frame-dead-load-map.md),
  SHA-256 `708e2d1c02aa4746dc9d77ef6cc3da9d9dbe06bcf9343627845de63c035ad799`.
- [Candidate bolt-group inventory](bolt-groups/README.md), SHA-256
  `faa50a5f9ca08ca5c40eaff30950b4ed4a56baf5fe9415517f1be8149266b458`;
  its structured data are pinned at
  `4a8b8f78db190d2e9841e5ad266356f0f0c5a402072d371938ad0760da0accb4`.
- Source [body wrench implementation](../../../../fea/wood_joint_reduced_body_loads.py),
  SHA-256 `64b7b2ccec107a95f23d749abace7d89346d0a57191ad3746273c496c27ab1f0`;
  [c11 body wrench input](reduced-static-attempt01/body-external-wrenches.csv),
  SHA-256 `6c823add8e29fc2089bff460ce7fa59c300794511214890b638b6c1a6c77a33f`.
- [Conditional member self-weight profile](../evaluation-resume-2026-09-24/current-frame-beam-selfweight-profile-attempt01/README.md),
  SHA-256 `b0b86d8add77ad5b0906de542bbf7ce20634507ef784757d076f795ae2ed6cc0`;
  JSON SHA-256 `c3569f1c33b7b6044098c508ca6906fe325b8d430faaf1cf9110cbb9dd0f6fa3`.

## Interface disposition

“Observed” below means recorded source geometry/identity or conditional input
accounting, not inspection of built parts. “Mechanical proof” asks whether the
carrier, constitutive/contact law, stiffness, simultaneous signed interface
actions, force sharing, solver mapping, and downstream transfer are established.
For every row, those items remain **unproven** unless explicitly stated.

| Path family / interface | Observed geometry, identity, or input/wrench accounting | Mechanical carrier / law / response established? | Missing evidence and minimum next closure | Disposition |
|---|---|---|---|---|
| Six applied hold cases → panel | Frozen external patch/standoff wrenches act directly on a panel model at A12/K12/A1 datums. Cases: `a12-rear` and `k12-rear` 1,659.44 N outward; `a12-forward` 1,199.82 N; `a12-left`, `k12-right` 1,429.63 N; `a1-rear` 1,659.44 N. Global `Fz=−2224.1108 N` in each case. | No hold/T-nut-to-panel carrier is represented by this direct panel load application; no panel response. | Preserve the frozen patch, force, moment, and datum mapping; explicitly document the analytical bypass of hold fastener mechanics. A physical hold/T-nut carrier model would need geometry, engagement, stiffness, and signed actions. | **CONDITIONAL input only**; not a solved panel demand. |
| Panels / kickers → Hillman 42605 axes → receiving members | 66 screw-axis identities: 58 retained stations and 8 moved axes (four kicker-center, four lower-panel-edge); all modeled envelopes intersect raw receivers and clear finished receiver solids. Receiver screen records 22 distinct panel/receiver interfaces. | No applicable installed withdrawal law, axial stiffness, screw-group sharing, head/panel limit, active contact law, or solver mapping. The six outward resultants above are whole-panel actions, not per-screw forces. | Source-backed resistance and load-slip data for exact 42605/wood/penetration/pilot/countersink; installed engagement and head/panel limits; signed panel-to-screw group actions and downstream receiver transfer. Do not borrow SPAX values or divide equally. | **BLOCKED** for all six panel paths. |
| Center kickers → center-post/block/header chains (left and right) | Graph records identity chains: `kicker_left/right` → two moved center Hillman axes → `base_post_center_left/right` → two `center_post_*` bolts → cleat → two `center_post_header_*` bolts → `base_header`. Kicker face contacts and candidate bolt IDs are recorded. | Graph explicitly classifies each as identity chain only. No active seat/contact, edge-support share, force split, attachment stiffness, bolt action, or solver mapping. | Establish supported edge intervals/face ownership; identify operative bearing and fastener laws; recover simultaneous signed actions through posts, cleats, header, and frame. | **BLOCKED**; no center-kicker demand. |
| 24 candidate solid blocks / 92 candidate bolt axes / 48 declared bolt interfaces | Manifest binds 24 blocks and 92 axes at 22 stations; receiver screen lists 48 candidate-bolt interfaces. The candidate bolt-group inventory supplies geometric head-to-nut order proposals for 88 two-receiver axes; the independently reviewed three-member supplement supplies the remaining four axes in two stacks. Their disjoint ID sets cover all 92 candidate axes (46 geometry groups total). Graph records 460 candidate installed-hardware component roles (five modeled roles per axis); raw shaft/receiver intervals and pair identities are geometric. | Complete modeled receiver order is now available, but it does not verify delivered head-to-nut orientation or installed seating. Contact-face ownership, complete stack restraint, connector law/stiffness, group sharing, signed bolt/wood actions, and solver DOF mapping remain unestablished. 98/100 relevant member-pair geometries are finite opposed planar touch; 2 are separated; neither state proves load transfer. | Reconcile the modeled order with the intended receiver/hardware assignments by axis; establish checkable connection/contact laws and source basis; map bodies/DOFs; recover simultaneous signed bolt forces, bearing, shear, withdrawal, and group interaction with downstream equal-and-opposite closure. | **BLOCKED**; do not treat axes or former duties as capacities. |
| 12 retained starting frame-bolt arrangements | IDs: `lumber_leg_bolt_left_1/2`, `lumber_leg_bolt_right_1/2`, `rail_front_bolt_left_1/2`, `rail_front_bolt_right_1/2`, `rail_rear_bolt_left_1/2`, `rail_rear_bolt_right_1/2`. Mass map carries 60 retained frame hardware roles. | Current candidate recheck is required. Head-to-nut order, receiving stack behavior, stiffness, signed simultaneous actions, sharing, and solver map are not established. | Recheck each retained arrangement against revised adjacent members and complete stack; bind materials/geometry, connection law, signed actions, and transfer to supports. | **BLOCKED** as a frame transfer route. |
| 142 hold T-nuts → panels | Mass/topology map contains 142 physical T-nut component rows. c11 gravity bookkeeping maps their *weights* to panels while preserving force/first moment. Six external load cases bypass them and load panels directly. | No T-nut/hold mechanical attachment or load-transfer law, engagement/preload, panel bearing/pull-through response, solver mapping, or climber-load action is established. Weight attribution is not load-carrier proof. | Decide whether hold/T-nut mechanics are outside the demand scope by boundary condition, or include source-backed attachment details and solve the hold-to-panel transfer; keep gravity wrench mapping distinct. | **BLOCKED / boundary decision required**. |
| 25 kg accessory allowance → frame | Separate from the 778-row mass inventory; already-modeled T-nuts, bolt stacks, and screw-axis proxies are not double-counted. Existing dead-load scenarios sweep electrical mass from 0–25 kg, use the remainder as a hold/hold-bolt resultant at the equal-axis face centroid (plus endpoint placements), and use the volume centroid of the separate electrical CAD bodies as a location proxy. | These are explicit placement scenarios, not observed mass split/installation or actual electrical mass centroid. The physical attachment/carrier, signed transfer into panels/frame, and solver map remain unproved. | Retain an explicit split and placement envelope for conditional input; owner selects/accepts the scenario basis before freeze or supplies better measured locations/masses. Then prove the path into the frame and floor. Keep T-nut/fastener inventory separate. | **CONDITIONAL scenario inputs; path BLOCKED**. |
| Candidate block ↔ frame bearing / seats | 52 named block/frame face pairs have finite nominal intersection in receiver analysis; geometry also records 2 exterior block-to-runner seat interfaces and 2 center-post-to-header top seats. Duty graph is 2,168 identity/geometry edges, not a mechanics graph. | No verified active-bearing state, contact law, face ownership in solver, stiffness, friction basis, or bearing pressure/force sharing. Geometric touch/intersection is not proof of compression carrier; no tension transfer may be inferred. | Define the current interface inventory and unilateral bearing/contact law; establish face mapping, compatible timber properties, opening/recontact treatment, simultaneous signed normal/tangent/moment transfer and known-answer checks. | **BLOCKED** for block-to-frame transfer. |
| Frame members → runners / floor | 50 physical STEP member identities; 20 timber source bodies. Source gravity mass map contains 127.5322 kg of frame timber at conditional 600 kg/m³. New 599-bin profile closes combined gravity force (`4.67e−9 N`) and first moment (`4.60e−6 N·mm`) for accounting. | No validated global frame stiffness/connection map, member section response, runner/floor support law, floor reaction, or support force sharing. c11 is one failed `a12-rear` branch; its finite paired floor tangents are not the owner’s conditional no-slip law and its forces/reactions are not transferable. | Define and verify the conditional no-slip-while-bearing support law and references; close load path through frame/runner bearing to floor; establish support/connection stiffness and solver mapping. Resolve beam spans/releases and section-force method separately. | **BLOCKED**; no support reactions or accepted `N/V/M`. |

## Candidate bolt-axis NDS applicability exception — 2026-09-29

The verified candidate geometry inventory identifies 12 distinct axes with a
modeled axis exactly parallel to one receiver's source-proposed grain vector;
the counterpart receiver is perpendicular. Four are in `wj03_outer` (the
`knee_outer_*_inner_header_1/2` axes, parallel in the corresponding
`knee_outer_*_inner_frame_block`) and eight are in `wj05_center_x190` (the
`center_post_header_*_1/2` and `center_principal_header_*_1/2` axes, parallel
in the corresponding cleat). These are proposed model orientations, not
observed stock grain or delivered bolt orientation. The axis inventory gives
6.35 mm as modeled shaft diameter; this is not proof of delivered 1/4-inch
hardware.

The existing [conditional NDS single-bolt screen](nds-screen/README.md)
assumes a 1/4-inch full-body bolt axis perpendicular to both member grains
and explicitly excludes end-grain-axis connections. Its illustrative
individual-bolt values therefore must not be assigned to these 12 axes. The
screen records the separate NDS-2024 route for eligible main-member end-grain
lateral connections under §§12.3.3.4 and 12.5.2.2: perpendicular-grain
bearing for the main member and the `Ceg = 0.67` factor, subject to the
standard's diameter and applicability conditions. No main/side member roles,
delivered bolt properties, signed lateral actions, or group actions are
established for these candidate axes, so this route is identified but not
applied.

This exception list unlocks correct method routing for the 12 axes; it does
not supply resistance or close a demand path. Stop before assigning any
per-axis NDS value until the actual member roles/orientations and bolt
diameter are evidenced and signed actions, geometry factors, and group
interaction are available. The geometry inventory and NDS screen remain
conditional inputs only.

## Accounting that must not be mistaken for a force path

The reviewed mass/topology map contains 778 modeled source rows: 50 physical
member solids, 460 candidate hardware component roles, 60 retained frame
hardware roles, 142 T-nuts, and 66 panel-screw axis mass proxies. Its solver
DOF mapping count is zero, reduced transfer is false, and implemented
mechanical carrier count is zero. The c11 body-load routine distributes
source gravity wrenches to bodies/panels and hardware receiver point locations
with force/first-moment bookkeeping; this is load assignment, not proof that
the corresponding parts are connected or that reactions share as assigned.
The conditional beam profile advances source-based timber mass distribution
only; it does not supply support spans, exact continuous `q(s)`, section-force
recovery, or current-revision accepted member demands.

c11 remains a single `a12-rear` branch-conditional diagnostic with four active
separations carrying tension and two inactive penetrations among its
compression-only checks. No c11 bolt, bearing, panel, member, floor, or support
force is an accepted demand for this revised receiver formulation. Its run
budget is spent. The parent checkpoint defers T09; this ledger does not reopen
mesh preparation or authorize any native run.

## Integrated disposition and next evidence

**No path-complete receiver-to-floor route is currently demonstrated.**
Identity joins, axis clearance, geometric face contacts, external case
wrenches, and source gravity accounting are useful inputs, but no current
member/joint demand subset is accepted. Cross-dependencies are material:
panel screw demand depends on panel withdrawal and receiver stiffness;
receiver reactions depend on block/frame and fastener laws; member actions
depend on the same frame/floor support law and self-weight distribution; T-nut
and accessory boundaries determine which weights and applied actions enter.

The smallest next ledger-to-model closure is to resolve owner boundary inputs
(T-nut/hold inclusion and accessory contents/placement), then establish
source-backed carrier/law and solver mappings for each interface, assemble
signed simultaneous station actions with equal-and-opposite checks, and close
each receiver route through the frame to the conditional floor support. A
small known-answer test must validate each chosen law and output mapping before
any full-frame freeze. The coordinator may continue read-only evidence work;
the parent retains all freeze/readiness and mesh/solver decisions. No
capacities, shares, connection acceptance, or build release are inferred here.

## Append-only analytical boundary resolution — climber load at panel

The frozen [six-case load contract](../evaluation-resume-2026-09-24/current-load-cases.json),
SHA-256 `9c7c43c51ce635ebfeaeddabdbbe2a0ac80dfd7819ec357662dd132db648b83a`,
resolves the *analysis-scope* question in the T-nut row above: each climber
case is represented by a 20 mm square force patch on the panel at the explicit
hold-face datum, plus the equivalent moment from the specified 100 mm outward
standoff about the panel-midplane reference. The contract limits itself to
applied forces and equivalent wrenches and assumes no joint/contact law,
stiffness, resistance, sharing, or capacity. Thus the six case inputs bypass
the physical hold-to-hold-bolt/T-nut-to-panel carrier; that carrier is not a
missing model interface for this chosen equivalent-panel-load boundary.

The current reduced-case builder (`fea/wood_joint_reduced_case.py`, SHA-256
`9b442e85221c383f1ad013dd493d87c9d4a303b6e36f58b2733f5de00316e192`) further
confirms the mapping: it forms its physical body set from current members and
panels, selects the case's loaded panel, sends the single case patch through
the panel adapter, maps its nodal forces to that panel, and asserts exactly
one climbing patch record. The adapter source is
`fea/wood_joint_reduced_panels.py`, SHA-256
`50b94669a5f112a75357529af01ca56ff6acd8887f1245f4368b58e6ee4ec388`.
These source checks establish load ownership in the reduced model, not a
solved panel response or physical hold-attachment behavior.

**Engineering result unlocked.** Continue the panel/frame demand route using
the frozen panel wrenches as external actions. Do not wait for another owner
boundary choice, add the climber action again at T-nuts, or interpret the
equivalent wrench as a hold/T-nut force result. The distinct 142 T-nut weight
bookkeeping remains gravity accounting and does not restore the bypassed
climber-load transfer.

This closure does not qualify the physical hold, hold bolt, T-nut, local panel
patch, or installed assembly. It does not close panel withdrawal, screw group
sharing, receiver transfer, or the floor/member gates. If a physical
hold/T-nut capacity result is required, that is a separate scope needing the
installed hold/bolt/T-nut geometry, product and engagement properties, panel
bearing/pull-through basis, and signed actions. Stop using this boundary note
if the pinned load contract or panel patch/standoff application changes, or
if the required result changes from the equivalent panel-load case to a
physical hold-attachment check.
