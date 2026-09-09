# Revised leg joint: 100×50 mm bolt group

This is a separate development trial for **2×8 legs, +300 mm rear footprint,
100 mm along-leg × 50 mm along-rim bolt spacing and a square top 150 mm beyond
the group centre**. It does not inherit approval or joint forces from the
[compact-pattern comparison](lumber-leg-response.md).

## Native preparation and checks

The new independent C3D10 leg meshes include the additional 30 mm of top stock.
Their volumes, centroids, full floor faces and frame-interface faces are checked
against actual CAD. The remainder of the frame retains its existing node
coordinates and element connectivity. All eight leg springs move to the new
bolt points, using separate interpolation weights on the leg and rim meshes.
The eight existing gusset releases remain unchanged.

The runner reuses the compact trial's deck, solver-output audit and load
combination functions. Only geometry preparation and source identities differ.
This retains the numerical force/moment, interpolation and energy gates while
preserving the original trial's frozen sources and evidence.

The three per-axis spring assumptions remain 100, 1000 and 10000 N/mm, with
nine native basis cases and 216 linear combinations per stiffness. The frame
and legs initially retain equal E=7000 MPa and ν=0.3. Floor nodes are fixed in
XYZ; gravity/contact, orthotropic behavior, bolt holes, local bearing,
splitting and connection strength are not modeled. These assumptions are
**not physical limits, permitted anchors or construction approval**.

```sh
uv run pytest -q tests/test_spread_leg_mesh.py tests/test_spread_leg_response.py
uv run python -m fea.spread_leg_response 2x8 --extension 300 --output /tmp/spread-leg-native.tar.gz
```

Preparation tests passed before the first native solve. Native results will be
recorded after the completed archive passes independent replay and rejection
checks; preparation alone is not a result.

## Updated unanchored floor screen

The changed stock and drilling are included in new drilled-CAD mass/CG studies
for [2×6/+300 mm](../fea/results/spread-leg-floor/2x6-e300.json.gz) and
[2×8/+300 mm](../fea/results/spread-leg-floor/2x8-e300.json.gz). Each has admissible
compression-only equilibrium for all 1296 tested cases at assumed μ=0.2 and 0.4.
At μ=0.1, only 678 and 696 cases respectively are feasible. These remain rigid
equilibrium witnesses, not compliant contact predictions, measured friction,
floor-bearing checks or a stability approval.

```sh
uv run python -m fea.spread_leg_floor 2x8 --extension 300 --output /tmp/spread-floor.json.gz
uv run pytest -q tests/test_spread_leg_floor.py
```
