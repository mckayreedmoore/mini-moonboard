# Current full-frame adapter audit — attempt01

This append-only attempt binds the current full-frame source manifest at
attempt04 to its preserved attempt03 baseline, the exact 50-member STEP export,
the attempt03 source mass-topology map and centroid export, and the frozen six
current load cases with their explicit global datums. The adapter checks source
hashes, exact body/member/mass-role identity joins, mass and gravity
resultants, topology references, and each applied wrench against its datum.

This is a distinct integration boundary from the existing source-manifest
producer and mass-topology map. Those artifacts publish source inventories and
their geometry/topology references. This adapter consumes their frozen outputs
and checks whether the identities and analytical inputs can be carried into a
future solver adapter without inventing solver assignments. It emits explicit
identity-only mass assignment slots; mass values and graph references stay in
the pinned topology map. It also emits null solver body, element, node, DOF,
material, load, support, and contact targets. It does not rebuild CAD, generate
a mesh or mechanics model, select properties or hardware, infer reactions or
connection forces, or qualify any criterion.

Attempt04 still reports `inputs_ready=false`. The six panel layups and
model-specific material properties remain unset; current solver body, element,
node and DOF assignments do not exist; hardware and attachment laws are
unresolved; mass rows have no solver transfer; there is no full-frame support
or contact model; and the six cases contain applied wrenches only. All
readiness, criterion, and release flags in the generated adapter audit remain
false. A passing source audit means only that the frozen source identities and
listed arithmetic reconcile.

## Reproduction

From the repository root, run the focused tests and then write the deterministic
offline audit:

```sh
UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q tests/test_wood_joint_current_frame_adapter.py
UV_CACHE_DIR=/tmp/uv-cache uv run python fea/wood_joint_current_frame_adapter.py --repo-root . --attempt-dir docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-frame-adapter-attempt01
```

The adapter verifies nested source hashes in the pinned mass and load
contracts, as well as all 50 STEP file hashes and byte sizes. The generated
`terminal-hashes.json` records the code, focused tests, source pins, README, and
generated audit/contract bytes; it omits its own hash by definition. No native
solver, CAD rebuild, mesh generation, or container command is involved.
The initial output write used `--write`; it creates the three generated files
exclusively and refuses to replace an existing attempt artifact. The command
above reruns the audit without changing those recorded bytes.

## Current handoff boundary

This attempt is an offline identity and arithmetic audit, not a launch packet.
The next executable T09 work item is a separate source-only mesh identity
packet: freeze the actual current solver mesh export and join its body IDs,
element IDs, and node populations back to these 50 STEP member IDs. That input
does not exist yet, so no solver identity can be mapped. Then bind source-backed
material assignments, component identities, mechanical connection laws, and
support/load targets as separate audited inputs before considering any native
case. All solver mappings remain null and current-frame cases remain blocked
until those inputs exist and are reviewed.
