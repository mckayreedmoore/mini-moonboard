# T09 current-frame adapter attempt01 independent review

## Assessment

The adapter is a source-identity and arithmetic boundary, not a solver launch
adapter. Its integration behavior is appropriately constrained: it joins the
pinned 50-member STEP inventory to the mass-role graph, recomputes source mass
resultants, binds six applied force/wrench inputs to explicit panel datums, and
leaves solver body, element, node, DOF, material, load, support, and contact
targets null. The frozen audit says
`source_audit_passed_readiness_blocked`; all readiness and release booleans
remain false. I found no issue that changes that boundary.

The candidate terminal manifest SHA-256 is
`20658deb3b1a701d85c1e690b39aafa16f22804dd16ab100816bdbc9d3243fc1`.
All six terminal entries match, all 11 pinned source inputs match, and all 81
paths in the frozen source-authentication map match their recorded SHA-256
values. The full records are in [verification.json](verification.json).

## Findings

**Low: blocker grouping is keyword-order sensitive.** In
[wood_joint_current_frame_adapter.py](../../../../../fea/wood_joint_current_frame_adapter.py:631),
`_blocker_category` checks for “bolt”, “hardware”, “hillman”, or “screw” before
checking “contact graph”, “mechanical”, or “duties”. As a result, the blocker
describing the geometry-only contact graph and missing connection mechanics
groups as `hardware_and_attachment_laws`; the generated category set does not
expose `connection_mechanics`. The complete source detail remains copied into
the blocker record, and this classification does not change the nine-blocker
count or any readiness gate. If downstream triage uses these categories, prefer
explicit source categories or adjust the precedence.

## Verified integration details

- The 50 STEP member IDs join exactly to the frozen bundle descriptor: 20
  timber members, six plywood panels, and 24 candidate blocks. The adapter
  binds each source ID and exact STEP path/hash/size, while all solver and
  material IDs remain null. The relevant joins are implemented in
  `validate_body_id_set` and the STEP audit path in
  [the adapter](../../../../../fea/wood_joint_current_frame_adapter.py:141).
- The 778 mass rows have 778 unique inventory names and 778 unique source
  entity IDs. Their role counts are 460 candidate hardware component rows, 142
  T-nut component rows, 66 panel-screw-axis proxy rows, 60 retained hardware
  component rows, and 50 member-solid rows. All graph member references join
  into the 50 source body IDs. These are source-map roles; they do not establish
  delivered or installed hardware.
- Independent row aggregation gives 224.420776668389 kg, center
  `[-1.6445371504155442, 697.857580973515, 1033.6090565929476]` mm, gravity
  `[0, 0, -2200.816009515055]` N, and origin moment
  `[-1535856.1365679689, -3619.3236888768397, 0]` N·mm. The separate 25 kg
  equipment allowance is explicitly excluded from the 778 rows. Recalculation
  follows [the row-level resultant checks](../../../../../fea/wood_joint_current_frame_adapter.py:239).
- All six load records bind to A12, K12, or A1 face and panel-midplane datums.
  The 100 mm outward standoff points, force components, and cross-product
  moments match the frozen source records; each load maps to its source panel
  identity and retains null solver load/target/patch-element IDs. The adapter
  checks these relationships in
  [validate_load_contract](../../../../../fea/wood_joint_current_frame_adapter.py:462).
- The nine blocker details and their source label are preserved from attempt04
  `readiness.unresolved_inputs`. `inputs_ready`, launch, model, criterion,
  acceptance, and release flags remain false. The generated audit's limits
  correctly stop short of reactions, connection demands, load sharing,
  stability, solver mapping, or structural acceptance.

## Reproduction

Run these commands from the repository root. The first reproduces the focused
suite; the second reruns the documented source audit without `--write`.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_wood_joint_current_frame_adapter.py
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B fea/wood_joint_current_frame_adapter.py --repo-root . --attempt-dir docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-adapter-attempt01
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-adapter-attempt01-independent-review-2026-09-28/verify_review.py
```

Observed test result: `7 passed`. The audit result is
`source_audit_passed_readiness_blocked`; its seven source checks pass and its
solver-mapping check is `NULL_AND_UNASSIGNED`. The reviewer helper rechecks
terminal/source hashes, recreates both generated JSON files byte-for-byte in
memory, and independently recomputes the joins, mass resultants, six load
bindings, null mappings, and readiness state. It is read-only. No Docker,
solver, CAD rebuild, mesh generation, or native execution was invoked.

This report assesses source reconciliation and its interface only. It does not
establish a current solver mesh, material model, hardware selection or fit,
mechanical attachment law, boundary-condition/contact model, response result,
or criterion acceptance.

The report packet is bound by [review-hashes.json](review-hashes.json), which
records SHA-256 and byte size for this README, the full verification record,
and the independent checker. That manifest omits its own hash.
