# Box-frame global stiffness screen

Four actual CalculiX solves were completed for the 41-part box-frame geometry
introduced in commit `7d070e1`. This is a **bulk, perfectly bonded, fixed-floor
stiffness screen**, not a model of the screwed joints or unanchored use.

## Model and tools

- CadQuery exports the same frame parts with `frame_parts(drilled=False)`.
  Hold, LED, relief and fastener bores are omitted. Their local effects and
  actual joint flexibility are therefore not represented.
- Gmsh 4.12.1 fragments the touching solids into conforming interfaces and
  generates quadratic tetrahedra. Its Abaqus exporter supplies C3D10 node
  ordering directly to CalculiX 2.21. Solid elements were used so the current
  part geometry can be meshed directly without inventing shell offset ties.
- All contacts between timber parts are perfectly bonded. No slip, gaps,
  bolt bearing, screw withdrawal, glue failure or lamination failure exists
  in this idealization. In particular, entire touching panel edges are tied.
- **Every node at Z=0 is fixed in X/Y/Z**, including the kicker base and
  cheeks as well as both feet. Real unanchored supports cannot supply the
  tensile reactions that these constraints permit.
- Material is isotropic E=7000 MPa, nu=0.3, with E=3500 MPa as a sensitivity
  run. Neither is a verified property of the purchased plywood. Orthotropic
  material and joint properties remain necessary for design evaluation.
- Each base case distributes 1200 N equally over five nodes along the top
  panel edge, including its corner interfaces. These are **not hold datums**.
  The combined case adds 480 N lateral to 1200 N face-normal load. These
  cases assess global top-edge response, not local panel bending at a hold.
- No gravity or dynamic amplification is included in these incremental
  stiffness solves. Current self-weight is used separately in the rigid-body
  stability screen. Output here is displacement and summed reactions, not
  stresses, joint forces or utilization ratios.

Implementation references: [Gmsh manual](https://gmsh.info/doc/texinfo/) and
[CalculiX documentation](https://www.dhondt.de/).

## Results: maximum displacement among the five top load nodes

| Load case | 100 mm mesh, E7000 | 60 mm mesh, E7000 | 40 mm mesh, E7000 | 60 mm mesh, E3500 |
| --- | ---: | ---: | ---: | ---: |
| Normal toward support | 0.5791 mm | 0.5834 mm | 0.5869 mm | 1.1667 mm |
| Normal toward climbing side | 0.5791 mm | 0.5834 mm | 0.5869 mm | 1.1667 mm |
| Down the board | 0.0310 mm | 0.0330 mm | 0.0364 mm | 0.0660 mm |
| Lateral | 0.0721 mm | 0.0743 mm | 0.0769 mm | 0.1487 mm |
| Combined | 0.5796 mm | 0.5839 mm | 0.5875 mm | 1.1679 mm |
| Mesh nodes | 27,584 | 63,021 | 123,052 | 63,021 |

The dominant normal/combined response changes about 0.6% from the 60 mm
to 40 mm mesh. The smaller down-board response changes about 10.4%, so
**not all cases are mesh-converged**. Halving E doubles the displacement
at the same mesh, as expected for the stated linear model.

Raw [DAT output and JSON summaries](../fea/results/) are committed. All four
DAT files were independently reparsed: all five cases have finite top-node
vectors and summed floor reactions balance the applied forces within 0.1 N.
The earlier three JSONs retain the original run schema; the DAT files are
the reaction evidence. The current runner validates equilibrium automatically.

## What this changes—and what remains

The deep frame has a stiff global load path **when every contact is bonded
and the full base is fixed**. This is useful evidence for the concept, but
it cannot establish the stiffness of the proposed screw/bolt connections.
The former beam model used a different idealization and boundary layout;
do not quote the numerical difference as a measured improvement factor.

The current CAD-derived unanchored screen still predicts negative floor
reaction in both normal-load directions. At 600 kg/m3 assumed density the
timber weighs about 188.6 kg; the two test cases have negative reactions
of approximately -464 N and -907 N. Geometry clearance and this bonded
FEA do not resolve that overturning issue.

The next engineering changes should address the base/support footprint and
the real wall/leg and plywood-edge screw joints. Then use contact/friction,
connection compliance, directional plywood properties, actual hold-load
locations, local stress checks and buckling/racking cases. The present
results do not justify reducing member sections or approving climbing.

## Reproduce in Docker

```bash
docker build -t mini-moonboard-fea:box-v1 -f fea/Dockerfile .
uv run python -m fea.prepare_box_frame
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 \
  python3 fea/solve_box_frame.py --size 100
```

Repeat with `--size 60`, `--size 40`, and `--size 60 --modulus 3500`.
Generated STEP, INP, DAT, FRD, logs and JSON stay in ignored `fea/generated/`.
The Dockerfile pins its Ubuntu base digest; apt package revisions can change
on rebuild. The runs above used CalculiX 2.21 and Gmsh 4.12.1. No host sudo
installation is needed. The checked-in results are historical evidence of
this geometry, not automatically refreshed results for later designs.

## Implementation review

Three independent review passes covered CAD correctness, tests and export/
analysis architecture. Confirmed issues were fixed: neighboring washer
overlaps, crossing screws, missing inter-fastener checks, incomplete raster
visibility, triangulation-dependent dimensions, asymmetric collision status,
decimal solver filenames and material-assumption metadata. Final reviewers
reported no remaining implementation blockers within this screening scope.
