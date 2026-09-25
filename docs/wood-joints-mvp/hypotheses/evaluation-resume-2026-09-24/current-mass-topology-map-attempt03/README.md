# Current WJ24 mass source-to-topology map, attempt 03

This read-only artifact joins the parent’s current mass-centroid export to
current geometry identities and receiver references. It maps all 778 source
mass rows one-to-one for accounting, but does not map them to FE nodes or
implement reduced-model transfer ownership. All `solver_dof_id` values are
null; no carriers or attachment constraints are built. See the canonical
[integration note](../../../current-frame-mass-source-topology-map.md).

## Mass representation choices

The 50 wood/panel/block rows can use density on the same meshed bodies. A beam
reduction needs distributed member mass/gravity over each member’s own
elements when member self-weight bending is in scope; a single member-centroid
force would preserve its external force and first moment, not its internal
gravity demand.

The 520 candidate/retained hardware roles, 142 T-nuts, and 66 screw-envelope
proxies can each be represented as separate bodies/carriers, or by a
documented aggregate/condensed mass representation. The optional JSON carrier
keys are per-source names, not an adopted node count or modeling requirement.
An aggregate/condensed alternative is valid for the intended analysis when
it accounts for every source row once and preserves exact gravity force and
first moments plus the inertia and attachment behavior relevant to that
analysis. The JSON’s 728 one-carrier-per-nonmember-source-row count is
illustrative only. No receiver distribution, connector stiffness, contact,
hold-slot law, or fastener force split is chosen here.

The current receiver screen reports 63.5 mm axial length for all 66
materialized screw-axis envelopes. The historical inventory
`source_occupied_length_mm=50.8` is a SPAX analysis field, not current CAD
axis length. The data stores these separately, checks every current screw
centroid at the axis midpoint, and checks the eight moved axes against
`new_start_global_xyz_mm + 31.75 mm × axis_global_xyz_unchanged`. These current
analysis envelopes and inventory-derived masses are not detailed purchased
screw solids or measured engagement.

The source rows total `224.420776668 kg`, center
`[-1.6445371504, 697.8575810, 1033.6090566] mm`, gravity force
`[0, 0, -2200.816009515] N`, and origin moment
`[-1535856.136568, -3619.323689, 0] N·mm`. The separate 25 kg
holds/hold-bolts/electrical allowance stays out of these 778 rows and uses the
reviewed placement scenarios in the dead-load map. The four local zero-density
nut carriers are diagnostic only; keep them massless if retained and count
the physical nut mass once in whatever future mass representation is chosen.

## Reproduction and hashes

The source-bound builder refuses changed input hashes. It performs no CAD
composition, meshing, or native solve. Use a fresh attempt path because JSON
outputs are exclusive-create:

```bash
uv run python scripts/wood_joint_current_mass_topology_map.py \
  --destination docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-mass-topology-map-attempt04/source-topology-map.json
uv run pytest -q tests/test_wood_joint_current_mass_topology_map.py
uv run ruff check scripts/wood_joint_current_mass_topology_map.py tests/test_wood_joint_current_mass_topology_map.py
uv run ruff format --check scripts/wood_joint_current_mass_topology_map.py tests/test_wood_joint_current_mass_topology_map.py
```

Four focused tests pass; Ruff and formatting checks pass. They verify unique
source rows, candidate receiver sets, T-nut label/AABB references, current and
moved screw-axis midpoints, aggregate mass/center/force/moment, optional
carrier status, and the non-inclusion of the 25 kg allowance.

| Artifact | SHA-256 |
| --- | --- |
| Parent current mass-centroid exporter | `8da82299d3b2b2b426bdace5c129a412672cacaaafba14c821fff35bcd9a2441` |
| Parent current mass-centroid JSON | `4c107b76d42d2a6f49b81c4857ba20bb236920932a7c34392c63e70d0882099a` |
| Board weight inventory | `7425c8100c9bbf0586d8e1732138eb5ec1e6147f8418b5cf3ea95dc6108e035e` |
| Current WJ24 scene | `74845b2e97165488d020d6a26202d2372f09f299cb47c9f28a3ba4642fe628bf` |
| Owner review report | `148f97623573558cd6a6c53f8a5399f2b30549d6aa1ed13c326dfe1bc3e9d695` |
| Receiver-screen attempt04 | `851495f2ccc80f286a7eae97fc54bcf602a478bb7d4e13eb28e2ae44cfb87991` |
| Complete-contact-graph attempt02 | `7806242ac48b198becf5db97b16b6a5605021b8d86b964f0f02adb6806aeec26` |
| Topology-map builder | `16645507e1910e038e83b5acc0026b9fb12940db0f194732b355b4ef76a982f9` |
| Focused tests | `6249737d78113f44bc39e1e06ebd53fa93c1d99ea171197b0f8ef4ba6576090b` |
| Generated source-to-topology JSON | `308a329a0b40db454d5b0e27c9ec2eca92d66eec96bfb222df5f7b7185bef4d4` |
