# Timber-base structural diagnostics

Physical geometry: `timber-base-development`, commit `3e36eda`. This is not the
solver/preparation revision: the accepted midpoint representation is included
with this report and bound by its recorded source hashes. **Not construction or
climbing approval. These are moment and optimistic bulk-stiffness diagnostics,
not a complete joint/contact FEA or a climber weight rating.**

## Scope and retained details

The current drilled CAD supplies the mass and floor-contact geometry for the
separate moment screen. Included mass is 176.360 kg using assumed wood density
600 kg/m³ and steel density 7850 kg/m³. Fasteners, holds, LEDs and glue are
omitted. Delivered materials have not been weighed or mechanically qualified.

The stiffness model retains the new service pockets, principal housings and
plywood gussets. It omits face and fastener bores, steel angles and fasteners.
Timber is isotropic at E=7000 MPa and Poisson ratio 0.3; touching interfaces
and separate leg plies are ideally bonded. Floor nodes are fixed in XYZ.
There is no gravity, contact separation, frictional sliding, connection slip,
bolt/screw compliance, material failure or buckling model.

Five corrected row-12 locations share the applied force equally. Reported
displacement is the maximum at those loaded nodes, not a whole-model maximum
or the response to a single hold. This deliberately optimistic calculation
cannot qualify the actual gussets, connections or local hole stresses.

## Moment screen

All 96 selected cases meet the project's illustrative 1.5 edge-moment target:

| Assumed climber | Minimum edge-moment factor |
| --- | ---: |
| 150 lb | 1.884 |
| 200 lb | 1.822 |
| 250 lb | 1.764 |
| 300 lb | 1.710 |

Cases include 1×/2× body weight, 0/300 N horizontal force over all azimuths,
0/50/100 mm standoff and 80%/100% included mass at fixed center of gravity.
These factors do not establish sliding resistance, dynamic behavior, safe
climber weight, floor capacity or stability under every possible load.

## Accepted stiffness diagnostics

| Check | 60 mm mesh | 40 mm mesh |
| --- | ---: | ---: |
| Nodes | 74,453 | 146,734 |
| Loaded-node maximum, 1.2 kN downward | 1.0324 mm | 1.0377 mm |
| Loaded-node maximum, 2.4 kN downward | 2.0648 mm | 2.0755 mm |
| Loaded-node maximum, 1.2 kN downward + 0.3 kN outward | 1.3289 mm | 1.3327 mm |

Both runs pass the independent solver checks described below. The 2.4 kN
displacement changes by about 0.52% between these meshes. This is sensitivity
evidence, not general convergence: mapped load nodes change and local stress
behavior is not qualified. The 2.4 kN case is approximately 540 lbf applied to
the modeled five-point distribution, not an approved climber weight.

## Meshing diagnosis

The original 60 and 40 mm attempts both stopped before solving: Gmsh reported
overlapping boundary facets at surfaces 623 and 587. Those surfaces have the
same bounds and area at the touching midpoint-rail interface. Generic duplicate
cleanup, Boolean union and a small Boolean tolerance did not resolve the mesh.

For the **already ideal-bonded** stiffness model only, each midpoint-rail pair
is now constructed as one rectangular section with the same service pockets.
The physical CAD, part count, joints and cut schedule remain two separate rails.
The preparation rejects a material-volume difference above 0.01 mm³ per pair;
regression checks compare the actual geometry in both directions. This numerical
representation does not establish that the real rails act as one glued member.

The solver retains independent positive-Jacobian, straight quadratic midside,
volume, connected-mesh, target/support and reaction-equilibrium checks. Gmsh
shape-quality warnings are not a local stress-convergence qualification even
when the positive-volume tests pass.

## Reproduction and evidence

Accepted result metadata and compressed input/output archives are under
[`fea/results/timber-base`](../fea/results/timber-base/). Source hashes bind the
geometry, load positions, preparation, solver and archived outputs. The tests
recompute published reactions/displacements and independently check current
mass/contact geometry. Historical failed attempts remain in the local ignored
`fea/generated/timber-base-fragmented-attempts/` directory.

To reproduce, use a separate clean working copy of the commit containing this
accepted report and updated preparation, and verify its recorded source hashes.
Checking out physical-geometry commit `3e36eda` alone restores the failed
midpoint representation, not the accepted analysis preparation.
The preparation deliberately refuses an existing generated directory or
`fea/results/timber-base/stability.json`; preserve the checked-in evidence and
run in a scratch copy with those output paths absent. Use the documented
`mini-moonboard-fea:box-v1` Docker image, then:

```bash
uv run python -m fea.timber_structural prepare
# Inside the FEA container, with the repository mounted at /work:
python3 -m fea.timber_structural solve --size 60
python3 -m fea.timber_structural solve --size 40
```

Publish the two resulting JSON paths with
`uv run python -m fea.publish_timber_structural RESULT60.json RESULT40.json`.
Publishing also refuses to overwrite accepted archives.

## What remains

Real connection qualification remains the controlling next step: gusset
net-section/bearing/splitting, bolt-group force distribution, loaded edge
distances, panel attachment and manufacturer connector load directions.
In particular, the recessed backing bolts have only 2D principal side-edge
distance; this calculation cannot authorize cross-grain racking resistance.
Do not substitute a small bulk displacement for those missing checks.
