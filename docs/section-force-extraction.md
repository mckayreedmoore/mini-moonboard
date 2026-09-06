# Native section-resultant check

CalculiX has a native `*SECTION PRINT` facility; no custom stress integrator is
needed to request section forces, moments and areas. It is **not yet qualified
for extracting this frame's member or joint demands**. The small experiment below
finds substantial mesh-dependent bending error even in a homogeneous member.

The [exact CalculiX 2.21 manual](https://www.dhondt.de/ccx_2.21.htm.tar.bz2),
node332, states that `SOF`, `SOM` and `SOAREA` each request all three outputs.
Vectors use global coordinates, and selecting the opposite side of an internal
face reverses their signs. The method extrapolates stresses from volume
integration points, averages at shared nodes, then interpolates and integrates
over faces. The manual specifically warns about stress jumps at material
interfaces. A native section resultant is therefore not an exact nodal cut-force
balance and is not automatically an accurate fastener or bond demand.

## Bounded analytic coupon

The [report and raw evidence](../fea/results/section_force_coupon/report.json)
retain two small CalculiX 2.21 runs:

- Homogeneous 10 × 10 × 100 mm C3D8 beam; E=7,000 MPa and Poisson ratio zero.
- Fully clamped Z=0 face; no gravity, contact, glue, bolt or material interface.
- Independent 120 N axial and 1,200 Nmm pure-bending end-traction cases.
- Analytically integrated consistent nodal end loads; no computed-stress
  integration outside CalculiX.
- Opposing internal face selections at Z=50 mm; `SOF` on one and `SOM` on the
  other. Both return all native section quantities.
- Linear small-displacement analysis, with reference-coordinate external
  force/moment balance. This is not the nonlinear floor-contact audit.

| Mesh | Elements | Native axial force, N | Native bending magnitude, Nmm | Bending shortfall |
| --- | ---: | ---: | ---: | ---: |
| 2 × 2 × 10 C3D8 | 40 | 119.9952 | 799.9815 | 33.335% |
| 4 × 4 × 20 C3D8 | 320 | 119.9952 | 1,066.6300 | 11.114% |

Exact targets are 120 N and 1,200 Nmm. The axial shortfall is 0.004% in both
meshes. External equilibrium passes the coupon's 0.001 N force and 0.01 Nmm
moment limits. Both native face selections report 100 mm² and opposite vector
signs. Nevertheless, the extracted bending moment remains substantially below
the exact external free-body value. Refinement improves that discrepancy; it
does **not** establish convergence or prove its precise numerical cause.

This is useful retained sensitivity evidence, not a reason to silently accept
native member forces. In particular, the frame uses quadratic C3D10 elements:
these C3D8 results neither validate nor condemn that formulation's section
output. The Poisson-zero homogeneous coupon is also not a plywood material model.

The separate [straight-C3D10 follow-up](section-force-tet-coupon.md) now matches
the known bending moment within 0.001% on both tested meshes. Its initial
load-serialization failure and corrected runs are preserved separately.
That narrower success does not change the C3D8 results or qualify curved frame
elements and joint-interface demands.

## Application boundary and next step

Use native section output as a diagnostic candidate at an interior section of a
continuous homogeneous member. Before using it for frame decisions, demonstrate
matching external free-body resultants and mesh sensitivity on representative
curved C3D10 geometry, then on selected frame sections. Avoid treating averaged stresses
across different materials, joints or fastener-contact regions as connection
forces. Neither the current test nor the API itself supplies a bolt rating.

Exact launch source, helper hashes, decks and raw results are archived. Recheck
without CalculiX, Gmsh, generated directories or CAD libraries:

```sh
uv run pytest -q tests/test_section_force_coupon.py
```

No new frame mesh, load rating, geometry change or construction approval follows
from this experiment.
