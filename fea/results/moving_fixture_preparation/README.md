# Moving-fixture preparation evidence

This is **preparation, not a moving FEA result**. Original CAD, meshes and
solver runs are unchanged. [Comparison](comparison.json) and
[manifest](manifest.json) bind two new archives to the previously published
[`fourth-direct-quiescent.tar.gz`](../moving_hardware_control/fourth-direct-quiescent.tar.gz).

- `pose.tar.gz`: original centred context, separately translated/serialized
  washer nodes, source snapshots and geometric preflight. Exact rational
  Bernstein bounds cover entire TRI6 patches. The radial gap lower bound is
  0.0007702643 mm; the axial lower bound is approximately 0.001 mm. Retained
  CAD checks find zero overlap and 159.4669 mm² projected head bearing.
- `mass.tar.gz`: **centred**, not posed, full scalar 10×10 element blocks for
  both bodies and both integration rules, with actual context/deck, source
  snapshots and imported Gmsh version. Native body masses agree with every
  printed mass in the complete 20-state reference run: maximum relative
  errors are 3.07e−8 for the core and 5.79e−8 for the washer.

The cache records imported Gmsh version 4.12.1. The following are
**session-observed execution details, not archived or replayed runtime
provenance**: the mass calculation ran in image
`sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646`,
with no network, two CPUs, 4 GiB memory/swap ceiling, a read-only root filesystem
and 180-second inner cap. It exited 0; the named `--rm` container was confirmed
absent afterwards. No solver was launched. Raw command, exit and container
postcheck records were not retained in these archives; the publication cannot
independently prove those runtime details. A first cache generated before the
density-validator improvement remains separately preserved in local generated
evidence; the published cache comes from the corrected validator's fresh run.

Portable replay:

```sh
uv run pytest tests/test_moving_fixture_publication.py -q
```

It checks archive/member/source/input identities, recomputes posed coordinates
and full-patch mesh clearance, verifies all cached block inventories/symmetry,
compares both native masses with actual solver output, analytically rebuilds
selected native blocks, and tests rigid translation using every cached block.
It does not rerun CAD intersections, Gmsh quadrature/Jacobian checks or a solver.
Native four-point and physical Gauss8 matrices are not interchangeable merely
because their total masses agree.

Next: create a separately frozen posed preparation and integrate **its own
serialized coordinates**, run its quiet control, then investigate moving
transfer at both interfaces with independent momentum/energy checks and
refinement. Initial clearance does not establish contact enforcement, impact
behavior, timestep accuracy, joint resistance or construction safety.
