# Conditional homogeneous independent-ply stiffness control

All four CalculiX 2.21 jobs passed their predeclared gates. This is a straight,
homogeneous, linear elastic mathematical control, **not a physically admissible
uncoupled assembly under arbitrary loads**: interface contact is absent, so
unequal motion can include interpenetration or separation. It provides no
plywood strength, connector, floor contact, buckling, or construction rating.

The 38.1 × 100 × 400 mm strip uses E = 7000 N/mm² and nu = 0. Composite uses
one solid; independent uses two identical 19.05 mm solids, separately meshed
with disjoint node IDs even where coordinates coincide. No tie, equation,
contact, rigid plate, or inter-ply coupling is present. Each ply's z = 0 face
is independently fixed in all translations. The loaded z = 400 end carries
consistent quadratic-triangle axial tractions with zero net force and a
1000 N mm total moment; in-plane and out-of-plane bending run separately.
Symmetric sharing applies 500 N mm per ply; inner-only applies 1000/0 N mm.
Inner denotes negative X. The two identical straight plies and fixtures are
mirror equivalent, so an outer-only rerun adds no independent information.

The exact nu = 0 pure-bending field satisfies the clamp: for bending coordinate
q measured from each centroid, u_q = -k z²/2 and u_z = k q z, with k = M/(EI).
The reported comparison point is each ply's end-section centroid, identified
explicitly by node ID in each context. Quadratic C3D10 elements reproduce this
polynomial field. Two structured meshes use 2 and 4 subdivisions per transverse
direction and 10 and 20 along the length, per solid. Refinement is a control
consistency check, not evidence of convergence for a drilled bent member.

| Independent/composite ratio | In-plane | Out-of-plane |
| --- | ---: | ---: |
| Symmetric, each ply tip displacement | 1 | 4 |
| Symmetric, total half-work energy | 1 | 4 |
| Inner-only, loaded ply tip displacement | 2 | 8 |
| Inner-only, total half-work energy | 2 | 8 |

Both meshes give these displacement ratios to the printed output precision.
Energy ratios agree within 1.1e-7 relative. Energy is **one-half external nodal
load work**, equal to strain energy for this linear, zero prescribed
displacement model; it is not an independent native element energy integral.
The maximum recorded relative mesh change is below 9.8e-8.

Frozen gates in the launch source and manifest are 0.1% for analytic tip
displacement, half-work energy, expected ratios, and mesh change; 0.001 N and
0.01 N mm per-ply equilibrium residual; 1e-10 mm for unloaded and fixed
displacements; 1e-10 N mm unloaded energy; and 1e-8 absolute serialized load
resultants. The audit also requires finite complete nodal outputs at every
expected step and verifies each ply's serialized loads and reactions.

`evidence.tar.gz` retains exact launch sources, decks, contexts, manifest,
and raw solver files, with SHA-256 digests. Original run directory:
`fea/generated/independent-ply-control-khbiuou_`. Docker image
`mini-moonboard-fea:box-v1` ID:
`sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646`.
Each solver process had a 60-second limit and OMP_NUM_THREADS=2.

Before the solver launch, all four parameterized implementation checks passed.
The added portable evidence test regenerates every deck byte-for-byte, checks
archived hashes, re-audits raw DAT results, and reproduces the comparisons:

```sh
uv run pytest -q tests/test_independent_ply_control.py
```

Rerun the experiment with the documented Docker image using
`python3 -m fea.independent_ply_control` from `/work`; set CONTROL_IMAGE_ID to
the actual inspected image digest so the new manifest records provenance.
