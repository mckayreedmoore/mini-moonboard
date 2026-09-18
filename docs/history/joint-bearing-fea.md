# Bolted-joint timber bearing FEA

This is a local **bearing-traction stress screen**, not a complete assembled
joint contact model or a strength approval. It supplements the perfectly
bonded bulk FEA, which cannot resolve connection stresses.

## Geometry and boundaries

Four timber submodels come from the current CadQuery frame:

| Submodel | CAD member | Included region | Bolt group |
| --- | --- | --- | --- |
| leg_wall | box_side_right | S=1480–1880 mm | S=1540,1620,1740,1820 mm |
| leg_member | leg_right | S=1480–1880 mm | same four bolts |
| seat_wall | box_side_right | S=245–555 mm | S=376,424 mm |
| seat_member | cross_seat_right_1 | complete seat, S=345–455 mm | same two bolts |

S runs uphill along the board; N is perpendicular toward its support side.
Each timber member is 38.1 mm thick. The real 10 mm bolt bores are retained;
secondary screw holes are omitted to isolate primary bolt bearing. Thus the
local net-section effects of nearby screws are not represented. All nodes
at each crop's lowest S plane are fixed in XYZ. These artificial cut-plane
constraints represent separate coupons, not the complete assembled joint.

Each coupon is solved independently: there are no steel bolt solids, mating
wood contact, pretension, clearance take-up, or friction between members.
The two timber responses must not be added and called measured joint slip.

## Loads and material

Three reference cases act at the bolt group: 1000 N along S, 1000 N along N,
and a 100 N·m in-plane group moment. These are **unit-response cases**, not
forces extracted from the bulk FEA and not a claimed dynamic design envelope.

An equal-stiffness bolt-group calculation distributes shear equally and
moment in proportion to each bolt's distance from the group centroid. With
100 N·m, the four-bolt group's largest force is about 302 N; the two-bolt
seat group carries about 2083 N per bolt. This explains why a short bolt
spacing can produce larger bearing demand for the same imposed moment;
it does not establish the actual moment in either connection.

Compressive-only radial tractions are prescribed on the loaded half of each
bore. A discrete cosine-pressure distribution is normalized to the specified
resultant. Surface loads use three-point midside quadrature on quadratic
triangles (area/3 at each midside, zero corner weight for constant traction),
with chord-triangle areas and pressure sampled at the quadrature nodes.
Applied group force and moment are checked before solving; summed
support reactions and their moments are checked after solving. This is not
a solution of contact pressure between deformable wood and a deformable bolt.

Material is provisional isotropic E=7000 MPa, nu=0.3, using the existing Docker
Gmsh/CalculiX installation. Quadratic C3D10 elements are used, with high-order
mesh optimization and a positive minimum-Jacobian check. Two mesh sizes are
compared. Equivalent (von Mises) stress is only a convenient scalar comparison;
**it is not a plywood failure criterion**. Component stress extrema are also
retained. The 95th percentile is over integration points, not volume weighted.

## Completed results

All 24 linear solves completed (four crops × three cases × two meshes).
Every volume mesh passed the positive-Jacobian check. Each DAT was reparsed
against its actual INP: force residual is within 0.1 N, global moment residual
within 1 N·mm, and all nodal displacements and all four integration-point
stress records per C3D10 element are present and finite.

| Timber crop | Reference case | Max displacement, 8 mm mesh | Peak equivalent stress, 12 → 8 mm mesh |
| --- | --- | ---: | ---: |
| leg_wall | shear_s | 0.00664 mm | 0.95 → 0.96 MPa |
| leg_wall | shear_n | 0.01831 mm | 1.02 → 0.99 MPa |
| leg_wall | moment | 0.01241 mm | 1.23 → 1.16 MPa |
| leg_member | shear_s | 0.00559 mm | 0.94 → 1.00 MPa |
| leg_member | shear_n | 0.06693 mm | 1.58 → 1.77 MPa |
| leg_member | moment | 0.04925 mm | 1.21 → 1.22 MPa |
| seat_wall | shear_s | 0.00541 mm | 1.93 → 1.90 MPa |
| seat_wall | shear_n | 0.00990 mm | 1.96 → 1.96 MPa |
| seat_wall | moment | 0.01447 mm | 8.32 → 7.92 MPa |
| seat_member | shear_s | 0.00515 mm | 1.86 → 1.93 MPa |
| seat_member | shear_n | 0.02215 mm | 2.59 → 2.47 MPa |
| seat_member | moment | 0.05842 mm | 8.35 → 8.50 MPa |

Displacement changes are below 0.9% across these mesh levels. Peak equivalent
stress changes reach about 12.2% (leg member, N shear); these stress peaks
are **not established as mesh-converged**. Integration-point percentiles
change with the nonuniform sampling distribution and are not convergence
criteria. The results compare individual coupons, not overall board motion.

The two-bolt seat group is more moment-sensitive under the same imposed
100 N·m reference moment. Establish its actual service moment and load path
before deciding whether to widen bolt spacing, enlarge the seat or change
the connection. No actual joint has been assigned a strength pass/fail here.

Compact [12 mm](../fea/results/joint_bearing_12_7000.json) and
[8 mm](../fea/results/joint_bearing_8_7000.json) results include input/output
hashes. Raw solver files stay local in `fea/generated/` to avoid committing
hundreds of megabytes. `evidence_sha256` identifies the actual INP/DAT pairs;
`audit_context_sha256` identifies source/STEP files at re-audit time, **not
immutable solve-time provenance**. The old equal-node-load trial results are
not used; both published mesh runs use the corrected midside quadrature.

## Interpretation and remaining joints

Do not compare these stresses with a generic birch strength to claim a factor
of safety. Directional plywood properties, actual bolt loads, load reversals,
wood crushing/splitting, bolt bending, washer embedment and glue durability
remain unresolved. Clamp-edge and bore-edge peaks can be mesh sensitive.

Panel-to-batten screws, plywood-edge screws, kicker splices and adhesive
interfaces are **not yet covered by joint FEA**. Screw withdrawal and head
pull-through require product/material data and a different local model.
Reducing main-panel screws to four per edge is a geometric design change,
not a validated fastening schedule. This work does not approve that spacing.

The next useful evidence is the actual force/moment demand at each joint from
a justified whole-frame load model, then connection compliance/contact and
directional material data. No footprint or member reduction follows solely
from these unit-response experiments.

## Reproduce

```bash
docker build -t mini-moonboard-fea:box-v1 -f fea/Dockerfile .
uv run python -m fea.prepare_joints
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 \
  python3 fea/solve_joints.py --size 12
```

Repeat with `--size 8`. STEP, INP, DAT, FRD, logs and result JSON are retained
in ignored `fea/generated/`. The FRD files include displacement and stress
fields for inspection with a compatible results viewer.

After both runs, `uv run python -m fea.record_joint_results` independently
reconstructs input forces/moments, checks complete DAT output, and refreshes
the compact committed summaries. Re-run the solves after geometry changes;
recording alone does not refresh an old analysis.
