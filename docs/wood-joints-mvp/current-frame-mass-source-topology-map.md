# Current frame mass source and topology map

This addendum joins the parent’s read-only [current mass-centroid export](hypotheses/evaluation-resume-2026-09-24/current-mass-centroids-attempt01/mass-centroids.json)
to source geometry identities and current graph/receiver references. It gives
the next complete-frame modeler an exclusive mass inventory and conditional
integration routes. It is **not** a reduced-model mass-transfer map: no solver
nodes, elements, DOFs, carrier constraints, or connector laws are assigned.
The frozen [six-case force contract](hypotheses/evaluation-resume-2026-09-24/current-load-cases.json)
and reviewed [dead-load accounting basis](current-frame-dead-load-map.md) stay
unchanged.

## Source rows and integration routes

The generated [source-to-topology data](hypotheses/evaluation-resume-2026-09-24/current-mass-topology-map-attempt03/source-topology-map.json)
maps 778 unique inventory identities to one source mass entity each. The graph
references identify where an entity belongs in current geometry; they are not
solver attachment locations.

| Source rows | Current geometry reference | Complete-model mass route | Current integration gap |
| --- | --- | --- | --- |
| 50 structural wood/panel solids: six panels, 20 frame timbers, 24 blocks | Same-named `physical_member/<member_id>` in the 50-node current graph | For a solid model, put density on that exact meshed body. For a beam-reduced frame, distribute each member’s self-weight over its own beam elements. | No solid-mesh body or beam-element IDs are mapped. A single force at each member centroid preserves its external gravity force and first moment, but not internal self-weight bending. |
| 460 candidate hardware component rows | `candidate_installed_hardware/<axis>/<role>`; the scene and graph receiver sets agree for all 92 candidate axes, including axes with three members | Keep each component as a meshed body, use optional per-role carriers, or use a documented aggregate/condensed representation preserving source gravity force and first moments plus inertia and attachment behavior relevant to the intended analysis. | No hardware body meshes, mass DOFs, endpoint ordering, or attachment constraints are mapped. Do not apportion one role’s mass among receiver members by assumption or route it to the nearest timber. |
| 60 retained frame-bolt component rows | `retained_frame_hardware/<axis>/<role>`; 12 axes retain their source-recorded member pair | Keep each component as a meshed body, use optional per-role carriers, or use an adequately documented aggregate/condensed representation for the intended analysis. | Member-pair references do not define bolt-head/nut direction, coupling, contact, or DOFs. None is mapped. |
| 142 physical hold T-nuts | `protected_tnuts/<name>` plus a grid-label panel reference; each exported centroid is within that panel’s finished-body AABB | Keep the physical T-nut as a meshed body, use optional per-nut carriers, or include its row in an adequate aggregate/condensed representation. | Label and AABB checks establish a current panel association only. A T-nut/slot law is outside this mass inventory; add one only if the intended local interaction analysis requires it. |
| 66 panel/kicker screw mass rows | `panel_screw_axis_envelope/<axis>` plus current panel and receiver member references; eight moved axes use current locations | Current source is a 63.5 mm axial-length CAD `fixed_axes` envelope, not a detailed screw solid. Use optional per-axis carriers, a documented aggregate/condensed representation preserving intended behavior, or a detailed screw mass source. | No mass DOFs or screw-to-panel/receiver connection law are mapped. The proxy mass must not be treated as an actual detailed screw body. |

The receiver screen distinguishes the current 63.5 mm materialized CAD axis
envelope from the inventory’s historical `source_occupied_length_mm=50.8`
SPAX analysis field. Use the former for current screw centers: the builder
checks all 66 current axes at their midpoint, and for each of the eight moved
axes verifies `new_start + 31.75 mm × unchanged direction`. These are current
analysis envelopes and inventory-derived masses, not actual detailed Hillman
screw geometry, measured installed length, or engagement.

The 50 member rows have a direct body-density route only when the very same
source member is represented by a solid mesh. A beam reduction needs a
member-to-element map and distributed self-weight when member bending demand
is in scope; applying the centroid resultant as one nodal force would hide
that member’s internal gravity bending. The 520 candidate and retained
hardware rows and 142 T-nuts can use direct body-density if their component
bodies are retained in the mesh. If components are omitted, one carrier per
source role is a simple possible representation, not a requirement. A
documented aggregation or condensation may use fewer mass DOFs if it preserves
the exact inventory gravity force and first moments along with inertia and
attachment behavior needed by the intended analysis. The 66 screw proxies
have no detailed body to mesh; they can use explicit carriers, an adequate
aggregate/condensed representation, or a new source-backed detailed screw
mass model.

The optional carrier keys in the JSON are stable names for one possible later
integration route; they are not created nodes. A count of 728 applies only if
the modeler chooses one non-member carrier for each of 662 hardware/T-nut
rows and 66 screw-proxy rows. It is illustrative, not adopted or required.
All 778 `solver_dof_id` values are null, the implemented carrier count is
zero, and no current graph edge supplies a constraint or joint law. The
outstanding model choices are:

- the 520 candidate/retained hardware roles need a body, carrier, or aggregate
  representation suited to the intended analysis; candidate receiver sets
  can contain two or three members, but the source does not order bolt roles or
  specify a reduced coupling;
- the 142 T-nuts have label-based panel references, not a defined local
  hold-to-panel connection. A T-nut/slot law is needed only if local
  interaction behavior is in scope;
- the 66 screw-axis proxies need a mass representation suited to the intended
  analysis, or detailed screw mass geometry if that level is in scope;
- the 50 structural members need either exact solid-mesh body IDs or a
  member-to-beam-element map with mass distributed over each member; and
- any chosen carrier needs actual solver DOFs and a declared attachment path;
  a chosen aggregate/condensed load needs a declared mapping to model DOFs or
  elements and evidence that it preserves the behavior in scope.

Do not use nearest-timber routing, a uniform frame split, the former angle
stiffness/capacity, or an invented bolt-force split to fill these gaps. The
source graph associations preserve identities and receiver sets without
choosing those mechanics.

## Gravity checks and scope

The 778 modeled inventory rows total `224.420776668 kg`, with global center
`[-1.6445371504, 697.8575810, 1033.6090566] mm`, gravity
`[0, 0, -2200.816009515] N`, and moment about the global origin
`[-1535856.136568, -3619.323689, 0] N·mm`. The generator recomputes the
row-level vertical force and moment and checks the aggregate mass, center,
force, and first moment against the parent export. Per-row source centers must
be retained; the family totals are not a replacement for per-body gravity.

The separate 25 kg holds/hold-bolts/electrical allowance contributes
`245.16625 N` at `9.80665 m/s²`. It is not included in these 778 rows and has no
measured or source-bound aggregate center in the weight inventory. Keep its
reviewed explicit placement parameters and endpoint sensitivity scenarios in
[the dead-load map](current-frame-dead-load-map.md); do not add the 142 modeled
T-nuts or inventoried frame, block, and panel fasteners to that allowance
again. The local engagement diagnostic’s four zero-density nut carriers are
not physical inventory: leave them massless if retained and represent the
physical nut mass once through its actual component or explicit carrier.

Static mass-center loads preserve each row’s gravity force and first moment.
They do not create a solved support reaction, member demand, stiffness,
capacity, fatigue result, or acceptance. Gravity for the current native
N–mm–tonne–second convention is `g = [0, 0, -9806.65] mm/s²`; pair it with
`6.0e-10 tonne/mm³` for the 600 kg/m³ wood rows and
`7.85e-9 tonne/mm³` for 7,850 kg/m³ metal rows. In SI, use
`g = [0, 0, -9.80665] m/s²` with kg/m³ densities.

## Reproduction

The source-bound builder reads pinned JSON artifacts and refuses any changed
input hash. It performs no CAD composition, meshing, or native solve. From the
repository root, generate a fresh artifact with:

```bash
uv run python scripts/wood_joint_current_mass_topology_map.py \
  --destination docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-mass-topology-map-attempt04/source-topology-map.json
uv run pytest -q tests/test_wood_joint_current_mass_topology_map.py
uv run ruff check scripts/wood_joint_current_mass_topology_map.py tests/test_wood_joint_current_mass_topology_map.py
uv run ruff format --check scripts/wood_joint_current_mass_topology_map.py tests/test_wood_joint_current_mass_topology_map.py
```

The focused tests check the 778-row identity mapping, current receiver-set
consistency, moved-axis count, T-nut label/AABB references, and independently
reconstructed gravity resultants. Passing them validates the pre-solve mass
inventory only; it does not validate the model’s attachment or mechanical
response.
