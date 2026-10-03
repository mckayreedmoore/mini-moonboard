# Current-frame pure-solid MATRIXSTORAGE export preflight — attempt01

## Result and scope

This packet produces a source-bound, input-only CalculiX deck for exporting
the unconstrained elastic operator of the current `a12-rear` physical solids.
It preserves the current geometry, C3D20 connectivity, material constants,
orientations, and section assignments while removing all nonphysical carrier
nodes, springs, MPCs, SPCs, and applied loads. The deck ends with a terminal
`*FREQUENCY,SOLVER=MATRIXSTORAGE,GLOBAL=YES` step.

The deck has not been frozen or run. No `.sti`, `.mas`, or `.dof` output is
claimed. This is one source-bound K-export proposal, not a constrained frame
operator, a contact/floor state, a gravity solution, an active-set controller,
a rank result, or joint acceptance. Parent retains freeze and execution
ownership.

The proposal is limited to candidate
`compact-floor-flush-wood-joints-development`, geometry revision
`led-clearance-2x6-runner-seated-blocks-v1`, case `a12-rear`. It makes no
geometry edit.

## Reproduce the input proposal

From the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-pure-solid-matrix-export-preflight-attempt01/prepare_export.py --verify
```

The verifier checks 161 pinned repository inputs, the read-only CalculiX 2.23
source archive and selected member hashes, all physical node and solid-element
inventories, source property-card equality, the six source load decompositions,
and byte equality of the generated files. `--write` regenerates only the deck,
the separate load-map file, and `audit.json` in this packet. Neither command
launches CalculiX. Reproduction also expects the pinned source archive at
`/tmp/ccx_2.23.src.tar.bz2`.

The existing source checks replayed for this packet are:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-gravity-settle-climber-ramp-scenario-attempt01/verify_decomposition.py --verify
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-gravity-rank-readiness-attempt01/audit.py --verify
```

The [gravity decomposition verifier](../current-gravity-settle-climber-ramp-scenario-attempt01/verify_decomposition.py)
passes all six source cases, 778 gravity entities, 50 body wrenches, and exact
nodal recomposition. The [gravity-rank audit](../current-frame-gravity-rank-readiness-attempt01/audit.py)
passes its source-only rigid-body branch screen. That audit leaves the initial
gravity gauge open; it is not evidence of an admissible gravity equilibrium.

The exact per-file source hashes are in
[`source-pins.json`](source-pins.json), and the generated checks and primary
hashes are in [`audit.json`](audit.json).

## Physical solid inventory

The adapted `a12-rear` input has 21,407 nodes, including 12,549 physical solid
nodes and 8,858 nonphysical or auxiliary nodes. The output keeps only the
12,549 unique physical nodes referenced by 1,903 C3D20 elements. All 50
physical bodies have disjoint node and element ownership; every C3D20 element
belongs to exactly one body, every physical node is used by a C3D20, and no
C3D20 connectivity node falls outside those body maps. The 68 C3D20 ELSETs and
68 corresponding solid sections are retained exactly; the four-ply panel and
kicker bodies correctly map to multiple layer ELSETs.

The node record lines are copied byte-for-byte from the pinned `a12-rear`
adapter deck. Every coordinate token matches the pinned model coordinates
using the source writer's `.14g` serialization. Connectivity records are
compared integer-for-integer against the adapter model. The audit lists each
body's node/element count and its element sets.

The deck retains all 50 source material and elastic cards, all 50 orientation
cards, and all 68 solid-section cards. After dropping the added density cards,
the emitted property cards have the same normalized ordered content and hash as
both the adapter deck and its pinned C11 property source. The unused source
materials `TIMBER` and `PANEL` remain preserved; the script does not silently
delete source property cards.

## Density is an export-only difference

The pinned source decks contain no `*DENSITY` card. To let the proposed
MATRIXSTORAGE job write its companion mass output, this derived deck adds
`*DENSITY` = `1.0e-9` tonne/mm³ to each of the 50 material definitions. This is
a **nonphysical export-only positive helper**, not a wood density and not an
adopted material property.

The exact pinned CalculiX 2.23 `e_c3d.f` and `materialdata_me.f` members support
the limited separation used here: the linear C3D20 elastic stiffness uses the
material stiffness/orientation arrays, while `rho` is used in body-force and
mass-matrix terms; density and elastic constants are read through separate
paths. The proposal has no gravity or other body-force card, rotation,
prestress, static load, SPC, MPC, or connector. Accordingly, this density does
not enter the intended unloaded elastic K assembly. The `.mas` output must be
discarded. Do not compute physical gravity as `M*g` from this auxiliary mass.

Physical gravity and climber loading remain explicit source nodal maps in
[`source-load-maps.json`](source-load-maps.json), entirely outside the operator
deck. The file preserves each of the six source-case gravity and climber maps
and verifies exact nodal recomposition against the pinned decomposition. Only
the `a12-rear` map pair has the geometry bound to this deck; the other case
maps are retained as separate source evidence and are not applied here.

## Later mapping needed to rejoin the frame

The proposed `.sti` rows must be indexed through their `.dof` node/direction
map. The input suggests 37,647 global translation coordinates (three for each
physical node), but that row count has not been observed from a full-model
export.

Before using this operator in a frame solve, derive and independently validate
the permanent displacement expansion `P` from the exact source interpolation
equations, numerical reference/ground endpoints, and boundary handling. Using
one consistent mapping, project the pure-solid operator and explicit physical
load map as `K_reduced = Pᵀ K_physical P` and `F_reduced = Pᵀ F_physical`.
Connector projection/ground coordinates must use that same expansion so
connector forces return to the physical owners rather than being mistaken for
support reactions.

The later assembled tangent also needs all 348 bilateral SPRING2 and 1,292
unilateral SPRINGA carrier laws. Their unilateral contribution depends on a
consistent state and remains outside this export. The 200 floor-stick rows
are conditional episode constraints: leave them out of this pure operator and
add or release them only through a separately validated loading/history
method. This packet does not choose a floor mask, provide event references, or
resolve the source rank audit's open-branch mechanisms.

## Remaining unknowns

- The pinned runtime profile reports `runtime_matrixstorage_feature_observed=false`. The actual 2.23 binary support remains a parent-owned check.
- Full-model input parsing and matrix export have not been observed; the actual `.sti` symmetry/storage, `.mas`, `.dof` row count/order, and memory demand are unknown.
- The source rank audit is a rigid-body mechanism screen, not a C3D20 stiffness rank or a gravity feasibility result. Initial compatible gravity, state-dependent contact tangents, and reaction-free gauge remain unresolved.
- Permanent MPC/SPC reduction, connector expansion, source load projection, unilateral state selection, conditional floor-stick history, and full-frame balance are not implemented in this packet.

The small source and manual preflight in
[`current-native-elastic-operator-export-preflight-attempt01`](../current-native-elastic-operator-export-preflight-attempt01/README.md)
supports the proposed terminal MATRIXSTORAGE route. It does not substitute for
the parent-owned freeze, actual export, or later operator-mapping checks.
