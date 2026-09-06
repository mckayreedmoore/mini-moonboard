# Dynamic momentum operators: qualification pending

`fea/dynamic_momentum.py` contains two separate C3D10 reference-volume
operators. `consistent_mass` uses Gmsh Gauss8 to integrate physical mass and
quadratic interpolation products. `calculix_221_mass` reconstructs the
untransformed CalculiX 2.21 implicit mass matrix using the four quadrature
points and weights specified in its source. Both return element blocks for
`momentum`, which computes mass, linear momentum, angular momentum about the
origin using current position `X+u`, and kinetic energy. Units follow the
provided coordinates, density and time.

Neither operator has been qualified against actual native dynamic solver
output. The four-point reconstruction excludes mortar basis transformations,
explicit lumping, and mass scaling. Passing its numerical tests does not
authorize a candidate fourteen-body solve or establish dynamic contact balance.

## Source evidence

The inspected files are under
`/tmp/contact-source-2.21/CalculiX/ccx_2.21/src/` and match their members in the
official [CalculiX 2.21 source archive](https://www.dhondt.de/ccx_2.21.src.tar.bz2).
The local archive `/tmp/contact-source-2.21.tar.bz2` was hashed and verified as
`52a20ef7216c6e2de75eae460539915640e3140ec4a2f631a9301e01eda605ad`.

| Source file | SHA256 | Relevant evidence |
| --- | --- | --- |
| `e_c3d.f` | `74652da7eb31a1df3c8b0c65c9304819d24f52cafd088288e9865e83dc584d61` | Lines 308–310 choose four C3D10 points regardless of `intscheme`; 335 loads reference coordinates; 576–580 select `gauss3d5`; 863 includes `detJ` in `shpj`; 984–987 accumulate `rho*N_i*N_j*detJ*weight`; 1913 limits lumping to explicit dynamics. |
| `gauss.f` | `aed2d48b6a63e30894e747a531f6edc32e3cd921338e370902dfb62d8e304df2` | Lines 142–147 specify the four tetrahedron points; 339–341 specify weights approximately `1/24`. |
| `resultsmech.f` | `7aadd7376c5d6176dcfe61b9fa8b0d472e7cc3ca6627bd9a617f571f2461080c` | Lines 1095–1107 interpolate nodal velocity and compute `rho*|v|^2/2` at the integration points. |
| `printoutelem.f` | `d0a8d83575eb6525c8f20063fa38adbc8d6cb5a3d3210ac5fd67da91b9bbc056` | Lines 256, 288–289, 363–366 and 430 integrate native ELKE over reference geometry using the four-point rule. |

Mortar transforms the interpolation basis when enabled (`e_c3d.f:677–702`
and `:981–983`). Such a path requires additional verification of the state
and mass transformations before this untransformed reconstruction can be
used for a discrete balance.

The native four-point tetrahedron rule is degree two. A straight C3D10 mass
entry contains a degree-four product of shape functions; curved quadratic
geometry adds a determinant of degree up to three. The native quadrature is
therefore not generally exact even on straight elements. Gauss8 has sufficient
polynomial degree for the physical reference operator. Jacobian positivity
is checked at the selected quadrature points, not certified everywhere in
the element.

## Checks completed

Host tests verify translation, off-origin rotation, current-position angular
momentum, shared-node assembly and invalid inputs. A source-rule regression
uses a unit straight tetrahedron at density 1, with velocity `(1,0,0)` only
at corner 1. Its four-point kinetic energy is `1/1200`; exact integration
gives `1/840`. Native quadrature is 30% lower than exact; exact is about
42.857% higher than native. Straight-element translation and rigid rotation
alone would not expose this discrepancy because their velocity-squared
fields have degree at most two.

A bounded, network-disabled Gmsh test in immutable image
`sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646`
checks both straight-element matrices against independent barycentric
calculations, checks CalculiX/Gmsh midside ordering, and compares physical
Gauss8 with Gauss10 on curved geometry. This container runs Python/Gmsh,
not CalculiX. Gauss8/Gauss10 entries differ by about `4e-12` in that fixture;
the comparison tolerance is `1e-10` for tabulated-rule precision.

Run these checks with:

```sh
.venv/bin/python -m pytest -q tests/test_dynamic_momentum.py
.venv/bin/ruff check fea/dynamic_momentum.py tests/test_dynamic_momentum.py
```

## Required before a dynamic momentum audit

1. Verify the installed solver's velocity-output request (`V` on `*NODE PRINT`), actual
   output labels, time association, and complete nodal displacement/velocity
   coverage using a bounded native control. Do not infer a velocity field
   from displacement output or compare different output times.
2. Obtain actual native ELKE for a straight tetrahedron control containing
   a quadratic velocity field, including the corner-only fixture above.
   Reconstruct KE from the emitted velocities at the same time and compare
   four-point and physical integrals separately. Record output precision
   and tolerances; analytical source reconstruction alone is insufficient.
3. Repeat the ELKE comparison on curved C3D10 geometry and any applicable
   transformed-contact path, preserving the exact solver, deck and output
   identities. Confirm that constraints, density and mass options match the
   reconstruction's assumptions.
4. Use the qualified solver operator for discrete momentum/impulse balance.
   Report the physical Gauss8 result separately and assess its discrepancy
   with refinement. Do not interpret quadrature disagreement as missing
   external impulse or silently relax a balance tolerance to absorb it.

These native controls and the candidate fourteen-body solve remain unlaunched.
