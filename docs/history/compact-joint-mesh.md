# Separate-body compact joint mesh

`fea.compact_joint_mesh` consumes a frozen contact-geometry package and uses
the existing pinned Docker image. It does not regenerate or modify that CAD.
Source snapshots and all 26 STEP hashes are checked before meshing. New output
directories are exclusive; failures and logs remain available.

```sh
uv run python -m fea.compact_joint_mesh --geometry fea/generated/compact-contact-smooth-v1 --output fea/generated/compact-mesh-preflight-v1 --preflight
uv run python -m fea.compact_joint_mesh --geometry fea/generated/compact-contact-smooth-v1 --output fea/generated/compact-contact-smooth-mesh-v2
uv run pytest -q tests/test_compact_joint_mesh.py
```

Each body is imported into its own Gmsh model. Only an individual integral
bolt is fragmented at the two nut-engagement planes, retaining conformal
internal connectivity. No operation merges the wood, washers, nuts or separate
bolts. The combined mesh renumbers independent bodies without coordinate-based
node merging. Curved quadratic tetrahedra preserve cylindrical surfaces.

The exact nut-engagement patch must span 87.376–95.9358 mm underhead and match
the complete cylindrical area `pi × diameter × length`. Mesh surface triangles
cannot straddle that interval. The inventory separates 25 unique planar
contact candidates, eight shaft/bore candidates and four planned nut ties;
engagement faces are excluded from shaft/bore contact candidates. No tie or
contact law is applied by the mesher.

Initial targets are 40 mm remote wood, 2 mm near cylindrical wood surfaces
and on bolt/nut hardware, and 0.9 mm on washers. They are meshing settings,
not convergence evidence. Acceptance checks include unchanged CAD volume,
integrated quadratic volume within 0.1%, centroid within 0.05 mm, positive
sampled/integration Jacobians, complete quadratic exterior-face mapping and
disjoint body ownership. The run is limited to one CPU, 4 GB and 300 seconds.

This remains an unverified hardware/contact hypothesis. Remote boundary/load
mapping, material laws, contact/friction parameters, nut-retention idealization,
mesh refinement and a complete numerical/contact audit are required before
interpreting a joint solve. No strength qualification or physical thread
resistance follows from a verified mesh.

## First smooth mesh result

The four-bolt partition preflight passed, followed by one complete bounded
smooth-geometry mesh using Gmsh 4.12.1 in the pinned image. It contains 779,675
nodes and 459,945 C3D10 elements across 26 independent bodies. Maximum relative
integrated-volume error is 0.000001536; the minimum sampled Jacobian is
0.123085 mm³. All exact engagement patches and the 25/8/4 interface inventory
passed. The output is `fea/generated/compact-contact-smooth-mesh-v1`; the
geometry package remains unchanged. The mesh is sizeable and has not undergone
a solution-cost or mesh-convergence study. No joint solve ran.

This first local run retained the three worker sources and recorded the hash
of `prescribed_tet_control.py`, but did not copy that image-selection source.
The launcher now snapshots every hashed source and verifies the copies after
execution. The first mesh remains historical evidence from the original
launcher.

The v2 command completed successfully with the corrected source snapshots.
The [v2 archive](../fea/results/compact-contact-smooth-mesh-v2.tar.gz) preserves
the mesh, manifest, launch record, log and all four launch sources. It reproduces
the original node/element counts and geometry gates: maximum relative volume
error 0.000001535314, minimum sampled Jacobian 0.123085475958 mm³ and minimum
integration Jacobian 0.123085475979 mm³. The required replay test reads the
archive without depending on ignored local output and
checks all four source hashes, the deck hash, body ownership, exterior-face
coverage, engagement intervals and the interface inventory.

The v2 meshing log reports `55 ill-shaped tets are still in the mesh` during
generation. The subsequent gates check positive sampled and integration
Jacobians and integrated geometry; they do not establish element-shape
adequacy for stress recovery or mesh convergence. The warning remains part of
the recorded evidence and must be considered before interpreting any solve.
