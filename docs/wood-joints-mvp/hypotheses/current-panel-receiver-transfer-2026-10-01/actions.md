# Current panel screw actions and receiver-transfer diagnostics

`actions.py` joins the current 66 Hillman 42605 panel/kicker axes to saved
per-connection response actions for three frozen cases and seven increments
per case. `build_report(root=ROOT, inventory_report=None)` returns `(report,
pins)`. With the source inventory supplied, the report contains 1,386 same-state
screw records and 4,158 signed scalar records: two bilateral `SPRING2` local
components at DOFs 2 and 3, plus one tension-only `SPRINGA` withdrawal
component. It retains source row IDs, laws, source stiffness values, signed
forces, RF radii, and model/response application points. Lateral rows list the
panel first; withdrawal rows list the receiver first. The output retains this
source endpoint ordering and applies each role’s endpoint sign separately.

The lateral pair is reconstructed through its recorded force basis and checked
against the saved endpoint vector. Withdrawal remains one tension-only source
scalar projected along the saved normal. Its parametric law and stiffness are
source-model values, not Hillman properties. The source scenario continues to
state `hillman_physical_stiffness_bounds_established: false` and
`hillman_ratio_status: non-qualifying diagnostic only`; its ratio is not a
Hillman property. Geometry application points remain separate from the current
inventory origins. The report records their signed axial offsets and refuses
transverse disagreements.

## Transfer refusal and separate physical-body projection

The recursive reduced-free-DOF mapping is retained as a diagnostic and remains
`REFUSED` when it does not reproduce a same-state source endpoint force or
point moment under the unchanged comparison checks in `nodal_transfer.py`
(1e-7 N and 1e-5 Nmm). Across the frozen rows, it records 42 force refusals and
77 point-moment refusals. The force refusals occur in `a1-rear`; moment
refusals occur 14 times in `a12-rear`, 49 times in `a1-rear`, and 14 times in
`k12-rear`. They are confined to the left/right center-1 and rim-1 kicker screw
members. The report preserves each signed difference at the response point and
body datum, RF radii, endpoint and node coordinates, scalar DOF entries,
recursive terminal weights, fixed/unowned terminal IDs, and equations on
physical-owned pivots that the recursive path traverses. It does not reinterpret
these differences as added couples or relax the helper checks.

For example, the `a1-rear` left center-1 lateral SPRING2 receiver mapping starts
at SPR1570 receiver DOF `(17733, 3)` and recursively reaches nonphysical fixed
keys `(18781, 1)` and `(18783, 1)` with weights 1.327194 and -0.442398. Its
withdrawal SPR1571 projection reaches `(18780, 1)` and `(18782, 1)` with the
same weights. These keys have no physical-body owner. The report keeps their
contribution separate; it does not label them floor reactions, add them to a
physical-body resultant, or claim a physical support channel. The largest
reported recursive point-moment discrepancy is 2,346.935 Nmm for the full
`a1-rear` left center-1 lateral action.

The code also reports a distinct **physical-body endpoint projection**. This
mapping stops at the first DOF whose node is in the receiver’s
`physical_body_nodes` inventory, before recursively eliminating a physical
pivot into later nonphysical or fixed keys. It retains the projected physical
node actions and compares their force/moment wrenches with the response point
actions. The independent source-only replay across 5,544 endpoint records
found no force or point-moment mismatches under the same helper comparisons.
That result is labeled diagnostic-only. It does not promote the refused
recursive reduced-free-DOF mapping, establish a support reaction, qualify a
receiver, or claim load-path acceptance. The bottom/finished-host point-action
screen uses physical point actions and does not rely on `MPCExpansion`.

The same report retains modeled panel/contact receiver actions by body and the
same-state receiver screw wrenches with lateral and withdrawal kept separate.
Its parent all-body/global audits remain bound to their exact response and
model bytes. The saved audit still covers 50 physical bodies with its original
0.1 N / 2 Nmm gates, rounding radii, interval flags, and numerical-ground
exclusion. This code preserves those audit records; it does not replay them
under a new balance limit.

## Inputs, pins, and limits

The source join checks the upper-joint manifest and geometry inventory, the
three case model/response pairs, the same-state response gates, all 66 axis and
member identities, source SPRING2/SPRINGA component identities, and the pinned
parent all-body audit for each case. For every case, it also checks the current
bytes of the attempt04 input manifest, receiver screen, and contact graph
against that model's `source_geometry_hashes`; changing one of these shared
inventory inputs while retaining the same revision and axis IDs refuses the
join. `pins["sources"]` contains repository-relative paths, byte sizes, and
SHA-256 values for the action/helper sources, case inputs, audits, and all
three checked reports; when called by `produce.py`, inventory pins are merged
with conflicts refused. Missing ignored evidence or any byte/identity change
refuses the source join.

Tests are source-only. The known-answer MPC fixture places a receiver-owned
physical pivot under a separate nonphysical fixed equation with a nonzero
moment arm; it checks the physical-body projection, the separately reported
fixed-key contribution, and force/moment-radius propagation. It does not
reinterpret that key as a support reaction. The tests need no local CAD files
or solver. A synthetic shared-source test mutates the receiver-screen bytes
while keeping the inventory revision and all 66 axis IDs unchanged, and checks
that each case pin rejects it. Rebuilding the full report requires the pinned,
ignored case and inventory evidence.

The upstream files were left unchanged. Their exact-byte verification
continues to cover 42 states and 672 block transfers, with no affected top
cleat paths:

```bash
uv run --no-sync python docs/wood-joints-mvp/hypotheses/upper-outer-load-path-2026-10-01/actions.py --verify
uv run --no-sync python docs/wood-joints-mvp/hypotheses/upper-outer-load-path-2026-10-01/nodal_transfer.py --verify
```

Focused checks for this action packet are:

```bash
uv run --frozen pytest -q docs/wood-joints-mvp/hypotheses/current-panel-receiver-transfer-2026-10-01/test_actions.py
uv run --frozen ruff check docs/wood-joints-mvp/hypotheses/current-panel-receiver-transfer-2026-10-01/actions.py docs/wood-joints-mvp/hypotheses/current-panel-receiver-transfer-2026-10-01/test_actions.py
```

No native solve, model change, geometry regeneration, Hillman law or capacity
qualification, common-strain calculation, three-dimensional section split,
joint acceptance, fabrication release, or climbing release is performed.
