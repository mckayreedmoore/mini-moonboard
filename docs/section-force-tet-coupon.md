# Straight C3D10 native section-force diagnostic

The corrected small benchmark supports using native `*SECTION PRINT` as a
**straight, homogeneous midmember diagnostic**, not as a frame/joint acceptance
test. It does not qualify the frame's curved quadratic elements (previously
measured maximum midside deviation 3.158 mm), material interfaces, contact,
fasteners, or allowable loads. No frame design recommendation changes here.

## Setup and measured results

A 10 × 10 × 100 mm beam, E = 7000 MPa and Poisson ratio 0, is clamped at every
Z = 0 node. Independent linear steps apply consistent quadratic triangular
end-face tractions: 120 N axial tension and a pure 1200 Nmm bending moment.
These include midside loads and the nonzero corner terms for a linear traction;
they are not point-force couples. There is no gravity, contact or nonlinear
geometry. Native opposed internal cuts at Z = 50 mm each have area 100 mm².
Structured bricks are split into six conforming tetrahedra with shared exact
edge midpoints; positive volume/Jacobian, face coverage and conformity are checked.

| Straight C3D10 mesh | Nodes | Axial Fz (N) | Bending My magnitude (Nmm) | Bending shortfall | Spurious bending Mx (Nmm) |
| --- | ---: | ---: | ---: | ---: | ---: |
| 240 elements | 525 | 119.9988 | 1199.990 | 0.000833% | 0.001107487 |
| 1920 elements | 3321 | 119.9988 | 1199.989 | 0.000917% | 0.0002812616 |

Axial error is −0.001% on both meshes. Opposed vectors reverse sign. All four
corrected endpoints pass the existing independent external force/moment balance
checks (0.001 N / 0.01 Nmm); largest component residual is approximately
1.03e−9 N and 8.44e−10 Nmm. The small My error does **not** decrease with mesh
refinement: two close results are not a general convergence proof. Native stresses
are extrapolated to nodes, averaged and integrated, so material-interface stress
jumps remain unsuitable for this interpretation. See the exact version's
[`*SECTION PRINT` manual](https://www.dhondt.de/ccx_2.21.htm.tar.bz2), node332,
and the retained [C3D8 contrast](section-force-extraction.md).

## Rejected original input and corrected contrast

The first pair is deliberately retained, not accepted. Its bending support-force
residuals were approximately 0.444075 N and 2.164900 N. This was an **input
serialization defect**, not a demonstrated solver bug or frame failure:
CalculiX 2.21 `src/cloads.f:267` reads `textpart(3)(1:20)` with format `f20.0`.
A 21-character token such as `-4.44089209850063e-16` therefore becomes
`-4.44089209850063e-1`, changing a roundoff-scale force to −0.444089 N.
The authoritative source is the [official 2.21 source archive](https://www.dhondt.de/ccx_2.21.src.tar.bz2).

The corrected pair changes force serialization only: retain `.15g` when it fits
20 characters, otherwise use `.12E`; reject nonfinite values. Before launch,
tests and the generator reread actual serialized CLOAD tokens using the solver's
20-character boundary and check nodal loads and resultant force/moment.
Existing C3D8 published decks still regenerate byte-for-byte. Historical launch
snapshots are unchanged. Original JSON status text is historical diagnostic
wording; its false bending `external_balance_pass` and unsafe input are decisive.

## Evidence and replay

The [paired report](../fea/results/section_force_tet_coupon/report.json) and
[raw archive](../fea/results/section_force_tet_coupon/evidence.tar.gz) preserve both
input decks, contexts, DAT/STA/CVG/logs and exact launch/helper sources. Hashes
bind each trial to its own sources; no assertion that historical sources equal
current source is made. The non-overwriting publisher retains original input
failures separately from the corrected contrast. CalculiX 2.21 ran in the existing
`mini-moonboard-fea:box-v1` Docker image, OMP threads 2, with a 60-second cap per
job; all four jobs completed normally.

`uv run pytest tests/test_section_force_tet_coupon.py tests/test_section_force_coupon.py`
replays saved evidence without Docker, solver, Gmsh or generated files. It checks
hashes, exact corrected deck reconstruction, original non-load geometry identity,
the rejected width violation, raw native vectors and independent external
equilibrium. This is a bounded benchmark, not a timber strength or fastener rating.
