# Updated-board FEA: shared-corner panel screws

This run evaluates the exported geometry at base commit `d2a596d`: 12 screws
per main panel and 8 per kicker panel. Subsequent working-tree changes by
another session are not covered. Official Moon documentation remains linked,
not mirrored. These are numerical screens, **not structural approval**.

## Global frame: audited load locations

The 41-part bulk frame was rerun with five equal loads near A12, C12, F12,
H12 and K12, instead of the historical top-edge loads. The load classifications
come from the [stability load-basis audit](../exports/mini_moonboard_v1_stability_screen.md).

| Load case | 60 mm mesh | 40 mm mesh |
| --- | ---: | ---: |
| 1.2 kN downward baseline | 0.364 mm | 0.368 mm |
| 2.4 kN downward sensitivity | 0.727 mm | 0.737 mm |
| Downward 1.2 kN + outward 0.3 kN sensitivity | 0.471 mm | 0.477 mm |
| Downward 1.2 kN + inward 0.3 kN sensitivity | 0.257 mm | 0.260 mm |
| 1.2 kN outward/downward normal, exploratory | 0.562 mm | 0.570 mm |
| Opposite normal, exploratory | 0.562 mm | 0.570 mm |

Values are maximum displacement **among the five loaded nodes**, not the
maximum anywhere in the frame. Meshes contain 63,021 and 123,052 nodes.
Displacements differ by approximately 1.3–1.4%; this is not a formal convergence
demonstration: the nearest load nodes move between meshes, lying approximately
3–11 mm from the exact hold targets. Summed reactions balance each applied
force within 0.1 N; this bulk check does not verify moment balance.

As in the [original bulk model](box-frame-fea.md), all timber interfaces are
perfectly bonded, every floor node is fixed in all three directions, and
holes are omitted. Material is isotropic E=7000 MPa, nu=0.3. There is no
gravity in these incremental stiffness cases. Thus **the screw reduction has
no effect on this model**. Fixed supports can resist uplift that an unanchored
board cannot; small displacement is not evidence of stability or joint safety.

## Drilled-panel screen: actual reduced screw pattern

Separate upper-left main and left kicker solids include their actual hold,
LED and screw bores and countersinks. Every modeled screw-head conical seating
surface is fixed in XYZ. The model has no backing timber, screw steel,
withdrawal springs, contact, friction or gaps. Constraints are bilateral:
they can transmit forces a real seating surface cannot. This is neither a
complete assembly model nor a guaranteed conservative bound.

Each independent case applies 1.2 kN outward, normal to the panel, distributed
over the rear T-nut flange annulus (25.4 mm outside diameter): main C10,
main C12, and kicker foothold 3. This is a local sensitivity load, not a
claim that the full global baseline acts normally through a single hold.
The imprint is meshed explicitly, with quadratic-triangle midside quadrature
and chord-area approximation, normalized to the specified resultant.

| Loaded flange | 20 mm mesh max displacement | 15 mm mesh max displacement |
| --- | ---: | ---: |
| Main C10 | 3.437 mm | 3.450 mm |
| Main C12 | 1.142 mm | 1.147 mm |
| Kicker 3 | 1.005 mm | 1.011 mm |

These are maxima over all panel nodes. Main meshes contain 160,004 and
206,352 nodes; kicker meshes contain 41,188 and 50,111. Displacement changes
are below 0.6%. This is encouraging numerical stability for this idealized
bending calculation, not convergence of the real connection behavior. The
flange patch chord area is 399.28 mm² at both levels; local circular-feature
resolution stays approximately constant while the bulk panel mesh is refined.

Peak equivalent stresses change from 80.0 to 88.2 MPa at C10, 92.3 to
91.8 MPa at C12, and 121.2 to 77.2 MPa at the kicker. **Peak stresses are
not consistently mesh-stable**, and no allowable comparison or pass/fail is
made. The exported p95 is an unweighted integration-point percentile, not a
volume-weighted material demand. Initial high-order meshing warnings were
resolved by optimization; all accepted final meshes have positive Jacobians.
A preliminary coarser kicker mesh failed and is excluded from these results.

Acceptance checks require positive element Jacobians, resolved and disjoint
screw seating patches, no load/constraint overlap, complete finite nodal
displacements and four stress integration points per C3D10 element, plus
force and moment equilibrium within 0.1 N and 1 N mm. Stress outputs are
isotropic equivalent-stress comparisons, **not plywood failure criteria**.
Sharp holes and rigid seating constraints can dominate the peak. Per-head
reaction vectors are artificial constraint reactions, not validated screw
demands; do not select screws from those numbers.

## Reproduction and evidence

Uses the existing Docker image: Gmsh 4.12.1 and CalculiX 2.21. No new host
installation or sudo is required. Implementation references:
[Gmsh](https://gmsh.info/doc/texinfo/) and [CalculiX](https://www.dhondt.de/).

```bash
uv run python -m fea.prepare_box_frame
uv run python -m fea.prepare_panels
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 \
  python3 fea/solve_box_frame.py --size 60 --audited
# Repeat bulk at --size 40.
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 \
  python3 fea/solve_panels.py --size 20
# Repeat panels at --size 15.
uv run python -m fea.record_updated_results
```

Run exports from the intended geometry revision; do not overwrite them while
solves are running. Generated STEP/INP/DAT/FRD/log files stay locally in ignored
`fea/generated/`. Small summaries and bulk DAT files are in `fea/results/`;
summaries hash the actual INP/DAT solve evidence. Large panel raw files are
not committed. The recorder reparses those raw files before publication.
The recorded Git revision identifies the export base, not proof of a clean
working tree or immutable source execution provenance.

## Decisions this analysis does not settle

- Screw withdrawal, head pull-through, edge splitting, backing contact and
  joint flexibility still need a connection model and material/fastener data.
- The earlier [primary bolt-bearing coupons](joint-bearing-fea.md) remain
  separate unit-load studies. Those joints did not change with the panel screw
  layout; rerunning them would not validate the reduced panel screws.
- Unanchored uplift/sliding, directional plywood strength, glue quality,
  buckling/racking and justified dynamic loads remain unresolved.
- No member reduction or safe-to-climb declaration follows from these solves.

The clearest next model improvement is a panel/backing connection submodel
with measured screw withdrawal and head-bearing behavior, plus orthotropic
plywood properties. C10 is the more flexible of the two sampled main-panel
locations; it is a useful first location for that refinement, not proof that
it is the worst hold on the board. These runs do not compare the previous
screw pattern, so they cannot quantify how much the screw reduction changed
stiffness. There is not yet enough evidence to prescribe additional screws,
thicker plywood or a new footprint.

## Implementation review

Independent correctness, testing and architecture reviews found no substantial
remaining issue in this bounded screening implementation; final artifact checks
also matched the tables to the recorded solves. A nonblocking future drift risk
is deferred: the seating-node selector repeats the current CAD head radius
(5 mm) and cone depth (3 mm). Update both or export shared dimensions before
changing screw geometry. Review of the implementation is not an engineering
certification of the board.
