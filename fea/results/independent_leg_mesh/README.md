# Actual drilled foot100 right-leg matched meshes

`evidence.tar.gz` preserves both verified quadratic meshes, the two half-solid
STEP exports, CAD metadata and source files, worker logs, launch snapshots and
their recorded digests. `report.json` identifies the archive digest;
`manifest.json` inventories its payload.

| Nominal mesh size | Nodes | C3D10 elements | Minimum sampled Jacobian | Runtime |
| --- | ---: | ---: | ---: | ---: |
| 40 mm | 37,389 | 22,557 | 2.641814 | 2.13 s |
| 25 mm | 64,690 | 40,172 | 2.064960 | 3.31 s |

Both plies retain the current rounded profile, four 10 mm cylindrical bores,
and complete 3670.28812456 mm² planar floor faces. They share all interface
nodes in these source meshes. A downstream independent-ply experiment must
duplicate those nodes by ownership, including floor and bore selections.

Run `uv run pytest tests/test_independent_leg_mesh.py` for portable replay:
all archived digests, ownership, shared interface, floor integration, known
CAD dimensions/volume, and full radial bore node sets reaching both ply ends.
This replay checks saved positive Jacobian and volume records; it does not
recompute Gmsh Jacobians or CAD geometry. The original worker checked both
sampled quality and integration-point Jacobians, plus integrated ply volumes.

Launch snapshots honestly preserve the code used before archive/replay code
was added. CAD source bytes were copied at publication after matching their
preparation hashes. Both workers used the recorded image ID and a 120-second
process cap. Generated originals remain in
`fea/generated/independent-leg-profile-qkvqpa4y`.

No solver, material, or capacity result is established here. Full bore
restraints and reversed distributed floor loading are ideal fixtures, not
loose bolts or unilateral floor contact. Applying the full resultant to one
ply moves its centroid 9.525 mm from symmetric sharing, changing the global
moment as well as load sharing.
