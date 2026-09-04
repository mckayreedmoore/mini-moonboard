# V1 structural FEA handoff

This is the reproducible handoff for a qualified analyst. It is not an FEA
result and does not authorize construction or loading.

## Installed analysis tools and solver smoke test

This workspace can use the Windows-side **FreeCAD 0.21.2** and **Gmsh 4.11.0**
installation from WSL. CalculiX is also available without sudo as the pinned
Docker image `calculix/ccx@sha256:b18b56fec00ad965d85e091454f26195d62115ee9a05feb4c130fa15406b6f7a`
(the fetched image reports CalculiX 2.16). Verify the solver, independently of
the board, with:

```bash
docker run --rm -v "$PWD/fea:/input:ro" calculix/ccx@sha256:b18b56fec00ad965d85e091454f26195d62115ee9a05feb4c130fa15406b6f7a \
  bash -lc 'cp /input/calculix-smoke.inp /tmp/smoke.inp && cd /tmp && ccx -i smoke'
```

[`calculix-smoke.inp`](../fea/calculix-smoke.inp) is a one-element cantilever
whose only purpose is proving that the solver runs. It is not a structural
model, a material model, or a result for this board. Solver outputs remain in
the container and are intentionally not versioned.

## Architecture decision (minimal analysis pipeline)

The analysis architecture is deliberately a short file pipeline:

```text
CadQuery source -> committed STEP -> FreeCAD/Gmsh mesh -> pinned CalculiX container -> analyst report
```

The interactive viewer is the connection-layout review view: it adds selectable
cyan, simplified representations for every primary bolt and rail-to-panel screw
from the generated connection schedule. They show the assumed axes, nominal
shanks, heads, washers, and nuts before FEA. The STEP frame remains thread-free;
the analyst must convert each reviewed connection to an appropriate connector,
constraint, or contact model rather than meshing those cosmetic solids.

| Decision | Keep / skip | Reason |
| --- | --- | --- |
| CadQuery as the geometry source of truth | Keep | It already generates the named assembly, exports, and geometry checks. A second parametric model would drift. |
| STEP as the FEA boundary | Keep | It is the existing neutral exchange artifact; no custom importer or mesh format is needed. |
| Existing Windows FreeCAD + Gmsh | Keep | They provide the interactive meshing/inspection workbench already installed on this machine. |
| Pinned CalculiX Docker image | Keep | It runs without sudo, is reproducible, and avoids a host solver install. |
| Python FEA API, custom solver wrapper, database, or web service | Skip | No recurring automated analysis exists yet; these would only hide analyst choices about wood, joints, floor contact, and load combinations. |
| FEA in GitHub Actions | Skip | CI should verify geometry and exports. It cannot establish the missing material/joint/floor inputs or turn a solver run into engineering approval. |
| Committed result meshes/plots | Skip | They are generated analysis artifacts and meaningful only with their reviewed input deck and report. Commit the approved report/review record later. |

This is a deliberate `ponytail` decision: add a scripted board-analysis deck
only after the reviewer supplies the physical material, connection, floor, and
acceptance inputs. Until then, the checked-in smoke deck proves the smallest
useful operational fact—the solver actually runs.

## Source-backed preliminary design actions

Use these as initial analyst inputs, not as a declaration of standard
compliance. The CWA document expressly says it does not specifically apply to
portable climbing structures, which is material because V1 is unanchored.

| Check | Initial action | Source and use |
| --- | --- | --- |
| One unroped climber | 1.2 kN / 270 lbf | CWA Table 1 value. Apply at all governing hold locations and directions; V1's provisional capacity is one climber only. |
| Unanchored stability | 1.2 kN times capacity at the most destabilizing point; separately 718 N/m² / 15 psf uniform load | CWA's no-protection-anchor stability procedure. Include actual dead load, floor contact/friction, sliding, uplift, and overturning. Do not credit a second climber as ballast. |
| Overturning | Factor of safety no less than 1.5 | CWA floor requirement; an analyst must select the governing local design method and factor combination. |
| Surface panel | 0.8 kN point load and maximum deflection `l/100` between fixations | EN 12572-2:2017 preview. Treat as a panel check in addition to, not instead of, global 1.2 kN and stability cases. |
| Insert/offcut | Five representative panel/insert samples; after the standard's stated test step, deformation no more than 0.5 mm at 1.2 kN and no pull-out after its procedure | EN 12572-2:2017 preview. This is a physical test requirement to be specified and supervised; do not improvise it with a climber. |

Sources: [CWA Design & Engineering Specification (2022), Table 1 and §§4.5–4.7](https://www.cwapro.org/file/secure/cwadesignpecfinal2022.pdf) and [EN 12572-2:2017 preview, §§4.5–4.7](https://preview.sist.si/sist-preview/39968/eb82f102549541eba9b79bad025432c2/SIST-EN-12572-2-2017.pdf).

## Current unanchored-screen result

[`mini_moonboard_v1_stability_screen.md`](../exports/mini_moonboard_v1_stability_screen.md)
uses the actual current CAD volume/centroid, a declared 600 kg/m³ density
screen, and the 1.2 kN top-row force. It finds a negative floor reaction in
both opposite normal directions. Therefore the current footprint is **not** a
candidate for fixed-foot FEA or construction. Revise the base/ballast strategy
and kicker-to-main load path first; then evaluate floor contact, friction,
sliding, and overturning.

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
| Final load vectors, dynamic factors, and load combinations | The source-backed screening actions above are a starting point; a qualified reviewer must set the final combinations. |
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
