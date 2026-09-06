# Actual stitch geometry and mesh evidence

This archive preserves the actual drilled right-leg geometry from the screw-spacing development candidate: two separate 19.05 mm plywood plies and three nominal stitch assemblies. Each assembly has a fused shaft/head, two separate annular washers, and an annular nut. The 9.525 mm shanks have 0.2375 mm radial clearance in the 10 mm plywood bores. Smooth nut bores do not establish threaded axial retention.

The prepared mesh contains 14 disjoint bodies, 145,787 nodes, 70,148 C3D10 tetrahedra, and 83 complete CAD surface groups. Coincident coordinates are not shared nodes. Body-wise integrated volume error is at most 0.000174895%, below the predeclared 0.1% gate. The minimum recorded sampled quadratic Jacobian is 0.1706681578; all recorded integration Jacobians are positive.

The immutable Docker image completed mesh preparation in 7.40 seconds with exit code zero, under a 120-second process timeout, a 6 GiB memory limit, two CPUs, and no network. The included post-hoc inspection records that the named container was absent. GNU time measured the Docker client; its RSS is not container peak memory.

`evidence.tar.gz` contains all 14 STEP files, geometry metadata and frozen geometry sources, the actual INP mesh and metadata, worker source snapshots written before Gmsh initialization, the worker log, runtime record, post-hoc inspection, publisher source, and a SHA-256 inventory. The companion manifest is identical to the archived manifest; the report binds the archive and publisher hashes.

Run portable replay checks from the repository root:

```sh
.venv/bin/python -m pytest tests/test_stitch_joint_mesh_publication.py -q
```

Replay independently parses the actual INP, verifies disjoint body ownership and complete quadratic exterior surface coverage, and checks geometry/STEP/source provenance, runtime evidence, and recorded volume/quality gates. It does not execute archived source, import CAD/Gmsh, recalculate CAD geometry or Jacobians, or run a solver.

This is geometry and mesh preparation only. No materials, contact laws, interface ties, fixtures, preload, friction, bolt engagement, load sharing, structural response, strength, or capacity have been verified. Actual-leg contact response remains future work.
