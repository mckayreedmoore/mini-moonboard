# Representative-joint mesh preparation

Status: third attempt passes the implemented coarse-mesh geometry checks,
2026-09-24. No native structural solve or response-convergence study has run.

The parent ran the frozen five-body STEP bundle serially in the pinned
release-v1 container, with a 40 mm global maximum, 3 mm local size at
cylindrical surfaces, a 12 mm refinement band, and high-order optimization.
The [third launch](attempt-03/launch.json) completed in 12.30 seconds.
Its 91,089 nodes and 47,469 C3D10 elements belong to five independent wood
bodies. Hardware is metadata, not a meshed or mechanically active component.

All post-optimization sampled and integration Jacobians are positive. The
minimums are 0.631599 and 0.910301 respectively; maximum relative volume
error is 0.001138%, below the implemented 0.1% threshold. The independent
[parent audit](attempt-03/parent-audit.json) parses the actual deck and checks
disjoint body ownership, ten distinct nodes per element, exact quadratic
exterior-face coverage, count and hash reconciliation, and absence of
material, contact, load, or solver cards. Thirty-one focused mesh adapter
tests pass.

The [complete compressed evidence](attempt-03/complete-mesh-evidence.tar.gz)
contains the original `mesh.json`, `mesh.inp`, and all four source snapshots.
The [contents index](attempt-03/bundle-contents.json) records their exact sizes
and SHA-256 values; the parent re-read and verified every archived member.
The report hash is `e8af81e6a92eb53b4ee72fcecc43efd9ed7ab901b3568be603509994c8b3c33c`;
the deck hash is `43f50fd605841821391f749ebddf226c639778945fef89b50ff78899c38afe56`.
The [outer manifest](attempt-03/sha256.json) also binds launch, log, tests and
the independent audit. The producer is frozen at
`915ab6d14efc6e81b4a95c4338ffb8b98cb7e4fac1478d23b592bc8bb377564b`.

Gmsh's initial distortion and ill-shaped-element warnings remain in the
[log](attempt-03/run.log). The positive checks above use the optimized mesh;
they do not erase initial warnings or establish response convergence.
Surface tags are local pointers, not physical contact identities. Semantic
mapping, active contact, material orientation, stiffness, restraints, loads,
resistance, and release remain separate unfinished work.

## Preserved failed preparation attempts

The [first attempt](attempt-01/mesh.json) ended after 3.48 seconds on the first
body. The adapter indexed flat C3D10 connectivity using
`element_index + local_index` instead of `10 × element_index + local_index`,
producing repeated node IDs. It never reached the post-optimization quality
audit and did not preserve that body's raw mesh. Its
[launch](attempt-01/attempt-01-launch.json), [log](attempt-01/attempt-01.log),
source snapshots and [manifest](attempt-01/sha256.json) preserve the failure.

The [second attempt](attempt-02/mesh.json) ended after 3.99 seconds after a
body's quality audit passed: the exterior-face coverage comparison mixed
local Gmsh element IDs with globally remapped element IDs. Its
[launch](attempt-02/attempt-02-launch.json), [log](attempt-02/attempt-02.log),
source snapshots, failed-body raw mesh and
[manifest](attempt-02/sha256.json) are preserved. The correction checks
coverage consistently in local IDs before storing remapped references.

Both failures are adapter defects, not failed timber or load criteria.
Regression coverage includes multiple elements and independent-body ID
remapping. Neither failed attempt ran a structural solve.
