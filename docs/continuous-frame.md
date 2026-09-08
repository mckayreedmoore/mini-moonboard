# Continuous top and bottom rails

This revision corrects the split crossmembers in the lean frame. It is an
inspection design, **not a structural approval**.

The [structural evaluation](continuous-frame-evaluation.md) identifies a lower
ledge fastener edge-distance failure against the retrieved product basis and
unqualified joints. Both attempted FEA meshes failed quality checks; no new
FEA displacement or strength result is accepted.

- One unspliced top rail and one unspliced lower deep rail each span the full
  2438.4 mm / 96 in between the perimeter rims.
- Each is nominal 2×6 stock: 38.1 × 139.7 mm / 1½ × 5½ in.
- Central uprights end beneath the top rail; their new cut length is
  2260.6 mm / 89 in. There are no overlapping solids at that intersection.
- Existing clips connect each full-width rail to both perimeter sides and
  the central uprights. The separate mid-level rails and localized lower
  flat ledge/kicker transition remain unchanged.

The new members provide continuous wood across the former central break;
the plywood is no longer the only continuous element there. This does not
establish the resistance of the clip joints, panel screws, racking system,
legs or kicker splice. Earlier FEA and stability results are not approval for
this changed assembly.

Geometry checks retain official face holes and rear hardware reservations,
check body/fastener collisions and actual receiver paths, and explicitly test
full-width single-piece stock and material spanning the former center gap.
Native STEP/STL and metric/imperial schedules are checked against the CAD.
All 12 focused CAD/export tests pass. Browser checks load all 265 selectable
meshes, exercise front/rear views and verify selection with updated dual-unit
upright dimensions. The rendered views were visually inspected.

[Inspect the revised backing](https://mckayreedmoore.github.io/mini-moonboard/?model=continuous-lean-frame&view=rear).
[STEP](../exports/continuous-lean-frame/continuous-lean-frame.step) ·
[Parts](../exports/continuous-lean-frame/continuous-lean-frame_parts.csv) ·
[Connections](../exports/continuous-lean-frame/continuous-lean-frame_connections.csv) ·
[Grouped blanks](../exports/continuous-lean-frame/continuous-lean-frame_blank_groups.csv) ·
[Hole entries](../exports/continuous-lean-frame/continuous-lean-frame_hole_entries.csv).

The [split-beam predecessor](lean-frame.md) remains frozen for comparison, not
the current recommended topology. Its old top-rail and upright cut lengths
must not be used for this revision.
