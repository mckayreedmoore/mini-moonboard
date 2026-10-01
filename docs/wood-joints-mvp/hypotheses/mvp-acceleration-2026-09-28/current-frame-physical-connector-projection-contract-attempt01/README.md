# Current-frame physical connector projection contract, attempt 01

This packet expands the pinned `a12-rear` connector laws onto the 12,549
physical solid nodes, so their sparse rows can be paired with a future physical
stiffness operator without carrying interpolation ghosts or numerical spring
grounds as structural coordinates. It is an input-only mapping result. It
does not assemble stiffness, run a solver, choose a unilateral active set, or
accept a joint or frame.

The producer binds the exact A12 adapter model and the source floor constraint
audit used by the current rigid-body rank audit. All rank-audit input hashes
are carried forward in `source-pins.json`; the producer hash is included too.
The floor audit and adapter share the same embedded C11 input-model hash. The
contract retains the source gravity nodal map in its own file, separate from
all connector and floor rows.

The physical coordinate index is
`3 * physical_node_index + (global_dof - 1)`, with node tags sorted ascending
and global translational DOFs 1, 2, 3. `physical-index-map.json` provides the
node tag, body owner and coordinate for each node index. Every emitted row is
a sparse list of `{coordinate_index, coefficient}` terms against that map.
No physical node is fixed by the adapter. The producer excludes exactly the
200 conditional floor-stick pivot equations before recursively expanding the
permanent MPCs and substituting SPC-fixed numerical coordinates with zero.
Each of the remaining connector rows closes only on unique physical
translation coordinates.

The output contains 348 bilateral SPRING2 rows with their positive stiffness
and energy-gradient sign, 1,292 source-matched unilateral SPRINGA rows with
their piecewise law and source physical-action sign, and 200 separate
conditional floor-tangent constraint rows. The floor rows come from the
original 200-by-800 source matrix over unique physical masters; their 200
conditional physical pivots remain coordinates in those rows. No stiffness
is assigned to these exact constraint rows. Their arbitrary row orientation
is recorded as a per-row sign in the rigid-owner comparison.

All 3,876 serialized SPRINGA qghost equations were found unchanged in the
permanent MPC set. The source projection extension and the native SPRINGA
geometric-axis projection agree to a maximum absolute coefficient residual
of `1.56e-13`. The row directions projected onto the source owner-point rigid
coordinates agree within `3.90e-13` for the 1,640 connector rows; the floor
constraint rows agree with the owner-point tangent displacement rows, up to
their recorded arbitrary sign, within `1.82e-13`. These rigid comparisons use
the rank audit's arithmetic-mean body datum and `1000 mm * radians` rotational
coordinates. They are kinematic checks, not a rigid-body stiffness
approximation.

For every row, a deterministic trial vector checks `q=B*u` and the dual-work
identity `f*(B*v) = v dot (B^T*f)`; the restoring sign is recorded separately
as `-B^T*f`. Across all 1,840 rows, the maximum absolute work residual is
`7.11e-15 N mm`. The 100 floor-normal SPRINGA rows still map one-to-one to the
100 fixed nonphysical floor endpoints through their source projections.
Those endpoints remain numerical ground projections only; this packet adds
no physical anchor. The other SPRINGA ground endpoints are likewise retained
as SPC grounding metadata, with ground reactions outside the physical row
vector.

Reproduce and compare all four generated payloads from the repository root:

```sh
uv run --no-sync python3 \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-physical-connector-projection-contract-attempt01/produce.py \
  --verify
```

`--write` regenerates only this attempt directory's projection contract,
physical index map, source gravity map and source pin record. The sparse rows
unlock a source-bound row interface for a later physical-matrix rejoin. They
do not establish material stiffness assembly, nonlinear/contact equilibrium,
ground reaction recovery, floor bearing, local splitting resistance or
candidate acceptance.
