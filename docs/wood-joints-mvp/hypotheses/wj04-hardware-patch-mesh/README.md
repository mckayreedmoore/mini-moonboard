# Representative physical hardware mesh

The first parent-owned mesh run completed on September 24, 2026, in 17.92
seconds. It passes the adapter's implemented mesh preparation checks for
32 independent metal bodies: eight bolts, sixteen washers, and eight hollow
nuts in the `body_to_far_wood_face` profile. The mesh contains 131,742 nodes
and 62,193 C3D10 elements. No structural response was run.

The [launch record](attempt-01/launch.json) pins the container image, source
and test hashes, runtime arguments, and unchanged before/after hashes. The
global maximum size is 4 mm, local minimum is 1.5 mm, and surface refinement
band is 3 mm. The runtime reports Gmsh 4.12.1 and NumPy 1.26.4. Nineteen
focused adapter tests and Ruff passed before execution. The independent
[deck and ownership audit](attempt-01/parent-audit.json) passes thirteen checks:
all bodies, nodes, elements, and 44,842 exterior quadratic faces reconcile,
with disjoint ownership and complete surface-node coverage. It rechecks the
reported quality summaries, but does not independently recompute Jacobians.
The minimum reported integration Jacobian is 0.123288684388 and maximum
relative volume error is 0.0065811%, below the recorded 0.1% threshold.

A separate [independent Jacobian audit](attempt-01/independent-jacobian-audit.json)
now recomputes 870,702 determinants directly from the saved node coordinates
and C3D10 connectivity using explicit quadratic shape derivatives and the
source-pinned Gmsh 4.12.1 fourteen-point integration rule. Every determinant
is positive; the minimum is 0.123288684388. Independently integrated volumes
for all 32 bodies satisfy the recorded tolerance. Six focused auditor tests
pass. Positivity at those integration points does not establish positivity
everywhere inside a curved quadratic element or response convergence.

The [compressed evidence](attempt-01/complete-mesh-evidence.tar.gz) preserves
the original `mesh.json`, `mesh.inp`, and five source snapshots. The parent
independently reread all seven archived members and verified their byte counts
and SHA-256 values against the [contents index](attempt-01/bundle-contents.json).
The [execution log](attempt-01/run.log) and frozen producer/test snapshots are
retained beside the bundle. The [outer manifest](attempt-01/sha256.json)
binds the evidence bundle, contents index, launch, log, snapshots, and audit.

The [physical hardware geometry](../wj04-mechanics-hardware/README.md)
supplies this mesh's explicit idealized profile and seating assumptions.
Legacy collision roles remain metadata. This mesh has no material,
mechanically active contacts, engagement ties, preload, restraints, loads,
or solver cards. The earlier wood mesh also still requires reconciliation
with the complete WJ24 layout. Mesh preparation does not establish delivered
hardware fit, joint stiffness, pressure, capacity, convergence, or release.
