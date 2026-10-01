# Code_Aster 17.4 TETRA10 mass reference and probe

This directory contains an independent implementation of the Code_Aster v17
TETRA10 interpolation and the pinned-runtime `FPG15` integration rule, plus a tiny
curved one-element deck for the pinned 17.4 runtime. It does not run a solver.
The parent agent owns the native run and its frozen comparison gate.

## Source basis and local node map

The source for the Code_Aster reference tetrahedron, the quadratic shape
functions, and the integration-point schemes is the official v17 manual
[R3.01.01, Volumetric elements](https://code-aster.org/doc/v17/manuals/man_r/r3/r3.01.01/Les__l_ments_volumiques.html),
TETRA10 reference-element and quadrature tables. Its local nodes are four
corners followed by edge nodes 12, 23, 31, 14, 24, 34. This is the same
edge-node sequence used by Abaqus C3D10: the official [Abaqus continuum
theory interpolation](https://docs.software.vt.edu/abaqusv2025/English/SIMACAETHERefMap/simathe-c-tritetwedge.htm)
assigns the quadratic tetrahedron's nodes 5 through 10 to shape products
`4*lambda1*lambda2`, `4*lambda2*lambda3`, `4*lambda1*lambda3`,
`4*lambda1*lambda4`, `4*lambda2*lambda4`, and `4*lambda3*lambda4`,
respectively. This agrees term-by-term with the Aster table. The basis used by
the implementation is

```text
lambda1 = y                 lambda4 = x
lambda2 = z                 lambda3 = 1 - x - y - z
N1 = lambda1*(2*lambda1-1)  N5 = 4*lambda1*lambda2  (edge 1-2)
N2 = lambda2*(2*lambda2-1)  N6 = 4*lambda2*lambda3  (edge 2-3)
N3 = lambda3*(2*lambda3-1)  N7 = 4*lambda3*lambda1  (edge 3-1)
N4 = lambda4*(2*lambda4-1)  N8 = 4*lambda1*lambda4  (edge 1-4)
                              N9 = 4*lambda2*lambda4  (edge 2-4)
                             N10 = 4*lambda3*lambda4  (edge 3-4)
```

The coordinate file and module follow that order. This confirms an identity
local-node map for C3D10 input meshes: no midside-node permutation should be
applied when the source mesh uses the conventional Abaqus numbering.

The same official reference lists FPG15 as a 15-point degree-five tetrahedron
scheme. Its weights in this implementation sum to the reference volume
`1/6`. The native comparison below confirms that the pinned Code_Aster 17.4
ordinary 3D `CALC_MATR_ELEM(OPTION='MASS_MECA')` operator selects the FPG15
matrix for this curved TETRA10 fixture. The official Abaqus interpolation
reference also identifies 15 integration points for the quadratic
tetrahedron's consistent mass; this is independent corroboration, not the
source for Code_Aster's selection. Do not use the FPG4 discriminator as an
attribution to Code_Aster.

## Why the curved map matters

The element map is quadratic. The module evaluates the full isoparametric
Jacobian determinant at every quadrature point, rather than replacing the
curved element with a vertex-only tetrahedron or a linearized volume. `FPG15`
is degree-five exact. For a curved TETRA10 the determinant may be cubic and
`N_i*N_j*det(J)` may reach degree seven, so the FPG15 discrete matrix is not
assumed to equal the exact physical integral in general. The separate
Duffy-transformed Gauss-Legendre order-8 matrix evaluates that physical
integral exactly in exact arithmetic: under the Duffy map the per-coordinate
polynomial degrees are at most 9, 8, and 7, within the 8-point rule's
degree-15 exactness. The generated JSON also compares orders 6 and 8 as an
independent roundoff/convergence check.

## Probe and independent result

The fixture uses a 100 mm reference tetrahedron with three displaced midside
nodes (3.5, -2.0, and 1.5 mm in Z), steel density `7.85e-9 tonne/mm^3`, and
the local ordering above. It compares the complete 30x30 translational matrix
from the ordinary `MASS_MECA` option with the independent FPG15 reference.
The Aster command writes the full matrix, DOF-to-node/component mapping, and
input coordinates as JSON on unit 80. A parent-owned checker should reindex
using that explicit map before comparison. The parent froze its entrywise
comparison bounds in
[`mass-probe-readiness.json`](../../../docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/mass-probe-readiness.json)
before the native run.

On pinned image `simvia/code_aster@sha256:d8d19ea91989eac0d38195bc5795c54c69f530f7196f53d67697ffa57c9106d5`,
the parent-controlled attempt01 returned zero and the independent parent audit
checked all 900 entries. Maximum absolute entry error was `1.21973e-19`
tonne; normalized maximum error was `1.25499e-15` against the frozen `1e-10`
relative plus `1e-15` tonne absolute bound. Normalized symmetry error was zero.
The measured FPG4/FPG15 Frobenius separation was `0.221536`. The audit and
runtime record are archived in
[`mass-probe-attempt01`](../../../docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/mass-probe-attempt01/parent-audit.json).

The standalone curved reference demonstrates that a degree-2 FPG4 matrix
differs from FPG15 by 22.15% in relative Frobenius norm even though the total
mass happens to agree to roundoff for this specific fixture. A rigid-motion
or total-mass check alone could therefore miss the wrong element matrix.
The sampled FPG15 Jacobian determinants range from 893109.5881 to
988729.8335 mm^3 and are positive; this is a quadrature-point diagnostic, not
a proof of positive Jacobian everywhere. This probe moves three midside nodes
only in Z while its X and Y maps remain affine, making this fixture's
determinant linear and its mass integrand degree five. Therefore its order-8
Duffy physical-integral matrix agrees with FPG15 to a relative Frobenius
difference of about `1.38e-15`. That fixture-specific equality does not remove
the need to distinguish solver quadrature from the exact physical integral
for generally curved TETRA10 elements.

Regenerate the JSON reference with:

```sh
.venv/bin/python fea/code_aster_trial/mass_reference/build_reference.py
```

Artifacts:

- `aster_tetra10_mass.py`: independent FPG15, FPG4 discriminator, and
  high-order curved-map mass/inertia integrals.
- `curved-tetra10-mass-reference.json`: frozen geometry, mass matrices,
  inertia matrices, and quadrature-separation/convergence values.
- `tetra10_curved_mass.comm`, `.export`, and `.mass.mail`: small native probe
  input for the parent-controlled pinned 17.4 run.

This fixture validates neither the actual A09 bolt/nut mesh nor its constraint
map. Its mass and inertia are only a known-answer method check before using the
same reference on that actual mesh.
