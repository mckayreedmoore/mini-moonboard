# V1 structural FEA handoff

This is the reproducible handoff for a qualified analyst. It is not an FEA
result and does not authorize construction or loading.

## Source geometry

Generate the controlled assembly before analysis:

```bash
uv run python -m mini_moonboard.export
```

Import [`mini_moonboard_v1_concept.step`](../exports/mini_moonboard_v1_concept.step)
into FreeCAD FEM (or another solver front end). CadQuery provides the named
solid geometry and STEP exchange file; FreeCAD FEM/CalculiX provides meshing,
materials, constraints, loads, and solution. Preserve the `O` datum and part
names from [`mini_moonboard_v1_assembly_layout.csv`](../exports/mini_moonboard_v1_assembly_layout.csv).

## Required model simplification

Do not mesh T-nuts, LEDs, holds, cable, screw threads, or the visual hole
details. They are not structural frame members and cause unnecessary mesh
singularities. Model instead:

- the four 18 mm main panels and two 18 mm kicker panels as orthotropic panel
  material, using received plywood data;
- laminated 36 mm rails, legs, bearing blocks, gussets, and rail-grid ties as
  orthotropic plywood members or an analyst-approved conservative equivalent;
- every through-bolt, screw group, splice, adhesive joint, and panel seam as an
  explicit connection, connector, or conservative constraint with a documented
  stiffness/strength basis;
- the two physical floor-bearing faces with a reviewer-selected friction/contact
  model. Do **not** fix the feet unless the analysis is explicitly a conservative
  bound and a separate unanchored sliding/overturning case is solved.

The Mini 2020 and Mini 2025 hold layouts use this same frame. Hold selection
does not change this FEA geometry; only the analyst's applied climbing-load
locations may be sampled at different hold locations.

## Inputs the reviewer must set

| Input | Why it cannot be guessed |
| --- | --- |
| Plywood principal-direction elastic, shear, strength, density, and moisture data | Birch plywood varies by product, orientation, thickness, and batch. |
| Lamination adhesive and joint properties | Depends on exact adhesive, spread, cure, clamp pressure, and wood surface. |
| Exact structural bolts, washers, nuts, screws, and connection behavior | Current hardware is a provisional purchase schedule, not an approved connection design. |
| User mass, applicable static/dynamic factors, and load combinations | Governs design actions and cannot be inferred safely from a render. |
| Floor friction, compliance, and load-spreading behavior | This unanchored assembly can slide, rack, or overturn. |
| Allowable stress, deflection, buckling, and connection criteria | Must come from the reviewer and applicable standard/jurisdiction. |

## Minimum load-case matrix

The reviewer should solve and document at least these cases, with gravity in
each applicable case:

1. Dead load only.
2. Worst-case normal-to-face static load at center, each exterior edge, upper
   row, lower row, and kicker/transition.
3. Worst-case board-parallel downward load at the same locations.
4. Left/right lateral-racking load at the upper board and at the leg bend.
5. Combined normal/downward and lateral load at the governing hold location.
6. Unanchored sliding, uplift, and overturning reactions at both floor feet.
7. Connection sensitivity: conservative pinned/slipping assumptions versus
   idealized fixed/joint-stiff assumptions.

Mesh-converge the governing cases and inspect panel stress away from point-load
singularities, bolt/washer bearing, screw withdrawal/shear, splice and adhesive
shear, leg buckling, floor reactions, and global displacement. A colored stress
plot by itself is not a pass criterion.

## Result and physical-test release gate

Before any physical proof test, the reviewer must issue the load magnitude,
rigging points, increments, hold time, exclusion zone, displacement limits,
inspection points, and pass/fail criteria. The first proof load must be secured
dead weight/rigging—not a climber—and only follows a reviewed calculation.
Record results in [`inspection-maintenance.md`](inspection-maintenance.md) and
link the approved analysis/report and commit in [`change-control.md`](change-control.md).
