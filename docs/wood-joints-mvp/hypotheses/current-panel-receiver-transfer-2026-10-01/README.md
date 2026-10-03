# Current panel receiver transfer

This packet joins all 66 purchased Hillman 42605 panel/kicker axes in
`compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`, to the current finished receivers
and the three frozen A12-rear, A1-rear and K12-rear diagnostic responses.
It preserves the reviewed geometry and purchased screw policy. It does not
establish screw resistance, a complete receiver joint, or a fabrication or
climbing release.

The [inventory](inventory.md) distinguishes the 58 retained stations and
eight previously directed moves, current receiver identity, nominal overlap,
finished bore patches, panel/receiver contact and timber-neighbor graph
associations. The four center-kicker axes now enter the two center posts;
the old inner backer names remain provenance. Nominal geometric overlap is
not installed thread engagement, and contact geometry is not continuous
edge-support evidence.

The [action method](actions.md) retains two signed bilateral SPRING2 lateral
scalars and one tension-only SPRINGA withdrawal scalar per screw, at each of
seven saved increments in each case. The join contains 1,386 screw records
and 4,158 scalar records. It reconstructs native physical endpoint vectors
and same-state force/moment resultants, projects connector loads through the
recorded attachment equations onto their first physical-body nodes, and preserves the
original pinned body/global audit gates and rounding radii. It does not
combine peaks from different screws or states.

The original extension of the upper-block helper continued through physical
support pivots into reduced free DOFs. That mapping is retained as a refused
diagnostic: across 5,544 endpoints it produced 77 moment discrepancies and
42 force discrepancies, on seven role/receiver memberships of four kicker
screws. It describes support elimination rather than the applied load on a
physical receiver body. The distinct physical-body endpoint projection stops
at the first owned physical DOF and keeps support reactions separate. An
independent recursive reconstruction of all 5,544 endpoints then matches
the saved point forces and moments under the original comparison bounds.
Neither mapping adds a physical couple or changes a source response.

The existing upper point-action and native-transfer exact-byte verifications
still pass for 42 top-cleat states and 672 connection transfers. Those checks
cover their stated top-cleat paths. The primary's bottom/finished-host packet
reads saved physical point actions directly and does not use this recursive
MPC mapping.

The [Hillman applicability note](hillman-applicability.md) records the product
source check and limits. The source models explicitly label their Hillman
axial/lateral ratio of 1.0 as a non-qualifying diagnostic assumption and leave
physical stiffness bounds unestablished. Numerical actions under that law
do not qualify actual Hillman stiffness, load sharing or resistance. SPAX and
SDS properties do not transfer to these screws.

## Reproduction

With the frozen local source closure available:

```bash
uv run python docs/wood-joints-mvp/hypotheses/current-panel-receiver-transfer-2026-10-01/produce.py --write
uv run python docs/wood-joints-mvp/hypotheses/current-panel-receiver-transfer-2026-10-01/produce.py --verify
```

`receiver-transfer.json` and `source-pins.json` are local ignored artifacts.
The producer checks exact source-byte bindings and writes deterministic JSON;
`--verify` requires exact saved bytes. This operation reads saved JSON and
hashes its STEP source closure without importing CAD or running a solver.
A public checkout without that closure cannot reproduce the full report.

The synthetic checks run without the frozen JSON or STEP files:

```bash
uv run pytest docs/wood-joints-mvp/hypotheses/current-panel-receiver-transfer-2026-10-01
uv run ruff check docs/wood-joints-mvp/hypotheses/current-panel-receiver-transfer-2026-10-01
```

Validation results and the final output hashes are recorded in
[review.md](review.md). The selected baseline and historical passes remain
separate authority; this packet adopts no new criterion pass.
