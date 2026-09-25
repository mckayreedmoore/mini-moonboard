# Native mechanics adapter readiness

Status: implementation plan, 2026-09-24. The owner has authorized native
mechanics execution for this wood-joint lane. No further execution permission
is needed within that scope. Model and method readiness remain unfinished;
no fresh wood-candidate case has run. See the
[authorization record](../history/decision-log.md#wood-joint-native-mechanics-authorization-september-24-2026).

The WJ12, WJ16 and WJ18 compositions remain partial historical development
layouts. The [WJ24 composition](hypotheses/wj24-integrated-static/README.md) now
contains all duties and passes its implemented static/source checks. Hold, tool
and G7 LED-extraction findings still prevent a final layout freeze. A response
from an earlier partial layout cannot close the complete-candidate six-case gate.

The [full-stock ordinary-joint input report](hypotheses/wj16-full-stock-mechanics-inputs/README.md)
now binds eight actual WJ16 bolts and four interfaces to their source axes,
ordered receivers, explicit grain directions, and contact-plane datums.
It distinguishes wood seats, under-head positions, and provisional hardware
bounds. This closes that bounded input extraction task; pressure, overlap,
stiffness, resistance, and complete-frame input coverage remain unfinished.
The [conditional response method](ordinary-joint-response-method.md) now
specifies a five-body local patch, independent timber meshes, finite
compression-only contacts, and numerical and material sensitivities. It is
a preparation path, not an implemented or solved model. Read the six-inch
bolt bounds with the [source-attribution correction](bolt-dimension-source-correction.md).

The [full-stock thread-bearing screen](hypotheses/wj04-full-stock-thread-screen/README.md)
now covers all eight bolts at 128 independent washer/layer corners. All 256
member fractions beyond the recorded minimum smooth-body boundary are below
one quarter; the maximum is 7.8549%. This is a conditional dimensional screen,
not a delivered-hardware observation, adopted diameter decision, or resistance.

The [five-body STEP export](hypotheses/wj04-patch-geometry/README.md) now
preserves the representative joint's finished solids with zero measured
round-trip symmetric difference, explicit grain, eight bolt identities and
four interface bindings. A bounded parent probe also finds finite nominal
common faces at all four interfaces, with pair distances no greater than
2.306e-7 mm. This closes geometry export and that overlap investigation;
solver surface ownership, active contact, mesh verification, materials, and
response remain separate work.
The [third mesh preparation attempt](hypotheses/wj04-patch-mesh/README.md)
passes the implemented coarse-mesh checks: five independent bodies, 91,089
nodes, 47,469 quadratic tetrahedra, positive post-optimization sampled and
integration Jacobians, and maximum relative volume error 0.001138%.
An independent parent deck audit reconciles node and element ownership and
every exterior quadratic face. Two earlier adapter failures, their sources,
and Gmsh's initial quality warnings are preserved. This establishes one mesh
preparation result; response convergence, materials, restraints, and the
structural solve remain unfinished.
The [surface classification and independent normal audit](hypotheses/wj04-patch-surfaces/README.md)
now bind all four wood interfaces and sixteen candidate bore/member pairs
to that mesh. Outward planar normals agree with the signed CAD datums.
Larger host faces remain distinct from finite paired footprints; hardware
contact, zero-preload seating, material orientations and response remain open.
Existing CAD heads and nuts are collision cylinders, including a solid nut
envelope that overlaps the shaft; they are not physical steel solids. The
[separate hardware export](hypotheses/wj04-mechanics-hardware/README.md) now
provides two response-only profiles, each containing eight continuous bolts,
sixteen annular washers and eight hollow nuts. All 64 STEP solids reproduce
their source geometry with zero measured symmetric difference. The profiles
retain explicit thread-transition and idealized engagement assumptions.
The [parent seat and envelope audit](hypotheses/wj04-mechanics-hardware/seat-and-envelope-audit/README.md)
confirms containment in the complete WJ24 nominal collision envelopes and
finite opposed common faces at all 64 named seat pairs. The [first physical hardware mesh](hypotheses/wj04-hardware-patch-mesh/README.md)
now passes its implemented preparation checks for 32 independent steel bodies,
131,742 nodes and 62,193 quadratic tetrahedra in one profile. An independent
deck audit reconciles disjoint ownership and all 44,842 exterior quadratic
faces. A separate independent audit then recomputed 870,702 integration-point
Jacobians from saved coordinates/connectivity, all positive, and reconciled
the integrated body volumes. These are mesh checks, not response convergence.
Contact implementation, free-mode treatment, delivered geometry, pressure,
resistance and stability remain unfinished. That historical five-wood mesh
predates WJ24. The [WJ24 reconciliation and new export](hypotheses/wj24-patch-reconciliation/README.md)
now prove four representative bodies unchanged and identify the principal's
new and removed holes. The separate current WJ24 baseline mesh completed in
13.8156 seconds with five bodies, 89,743 nodes and 46,629 quadratic tetrahedra.
Its preparation checks pass; independent ownership and Jacobian audits are
pending. It includes no G7 relief variant. The independent Jacobian tool's
first invocation rejected this new wood schema because its original contract
accepts only physical hardware meshes; extend that contract explicitly before
auditing the new mesh. Neither old metal containment nor unchanged bore shapes
alone establishes complete current wood/metal/contact identity.

The contact adapter now has a historical WJ16 preparation fragment; its
radial-only nut/root contact cannot transfer axial thread force. A conventional
unadjusted surface tie across the modeled radial gap also fails exact rigid
rotation invariance. An objective, explicitly idealized engagement constraint
is being developed with coverage and rigid-motion checks. Finite common
loading patches and active-set free-mode treatment remain open. No native
response has run.
The [elastic material scenario](orthotropic-material-scenario.md) supplies
an explicit reciprocal nine-constant proposal and a positive-compliance
check; it is not measured stock data or an adopted resistance law.

## Available execution environment

A read-only container probe on 2026-09-24 confirmed the existing
`mini-moonboard-fea:release-v1` image
(`sha256:083de8eefd4d9d9029d28ac1fdbb933a3b1e024225d8048165d6ef580d1b8f59`).
It provides Gmsh 4.12.1, NumPy 1.26.4 and CalculiX package 2.21-1.
The `/usr/bin/ccx` executable SHA-256 is
`6adaabf5bf0382fc2bfd692b984320ed375dba777f7dc8297562f818043faa1b`.
The probe imported libraries and read package/binary metadata only; it did
not mesh or solve a model. Pin the actual image and executable in subsequent
run evidence. An available executable does not close model readiness.

## Reusable boundary

Use one adapter over a frozen composed layout, an explicit mechanics contract,
and a case definition. It should return the structure and metadata expected
by [`current_response_run.run`](../../fea/current_response_run.py). The runner
provides CalculiX execution, active-set iteration, signed connector forces,
equilibrium checks, and source authentication. Its normal preparer and the
[floor-flush preparer](../../fea/floor_flush_mesh.py) contain selected-frame
geometry assumptions; calling them with a new candidate name is insufficient.

The [PB03 mechanics adapter](../../scripts/simple_pb03_native_mechanics.py)
shows inventory validation, finite contact cells, and activation of existing
bolt springs without duplication. Its geometry, stiffness values, contact
rows, and results do not transfer to wood joints.

| Input or output | Required candidate-specific work |
|---|---|
| Bodies | Bind every source and connector body, finished cuts, actual local frame, and declared grain. Do not infer grain from the longest bounding-box dimension. |
| Bolts | Supply one structured axis and receiving-member record per physical bolt, with grip, interfaces, and hardware assumptions. Five CAD component roles are not five fasteners. Preserve and recheck the twelve starting frame bolts. |
| Panel screws | Preserve the 66 fixed Hillman axes and exact receiver mapping. Keep their mechanics distinct from structural bolts and from SPAX properties. |
| Contacts | Supply named physical face pairs, normals, finite areas, opening behavior, and contact ownership. Zero nominal gap does not establish a bonded interface. |
| Stiffness | Define supported axial/lateral/slip/rotation assumptions and bounded sensitivities. Existing spring or four-cell examples do not provide physical stiffness by themselves. |
| Actions | Aggregate signed connector/contact point forces and their `r × F` moments about each declared interface datum. Preserve simultaneous six-component actions and equal/opposite member ownership. |
| Evidence | Bind geometry, family producers, case inputs, mechanics contract, loaded modules, convergence, equilibrium, and every applicable criterion output to the same candidate. |

`physical_forces()` in the runner supplies signed point forces, not a complete
bolt-bending or interface-wrench result. The accounting helpers in
[`bolted_joint_mechanics.py`](../../mini_moonboard/bolted_joint_mechanics.py)
can shift and transform wrenches; they do not establish contact distribution,
joint resistance, or stiffness. The
[criteria method map](criteria-method-map.md) retains all 36 migrated questions
and eleven candidate obligations until supported dispositions exist.

## Mesh and local-check boundary

The recorded criteria do not impose meshing every bolt hole as a blanket
prerequisite. They do require the actual taper/mesh identity checks and the
finished geometry for contact, fit, and net-section checks, including all
bores and cuts and the applicable simultaneous section actions. A documented
global idealization is an option only with a bounded and validated stiffness
and load-path model. Separate net-section checks alone do not validate that
idealization. Neither such an equivalent model nor an arbitrary finished-solid
mesh adapter is accepted for this candidate yet.

Finish the full layout and representative joint methods, bind the mechanics
manifest, validate preparation and numerical behavior, then run the six cases
from [`clear_space_batch.CASES`](../../scripts/clear_space_batch.py) serially on
the frozen complete configuration. Preserve failed attempts. Numerical
convergence is separate from resistance and the final MVP disposition.

Bounded local mesh and unit-response diagnostics may precede the complete
layout once their own inputs and methods are ready. Label their exact bodies,
restraints, loads, and limitations. They can test the adapter and representative
joint behavior, but cannot count as a complete-candidate load case.
