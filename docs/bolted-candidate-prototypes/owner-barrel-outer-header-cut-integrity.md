# Recessed outer-header nominal cut-solid integrity

The [detached screen](../../scripts/owner_barrel_outer_header_cut_integrity.py) uses
`export_owner_barrel_scene.build_viewer_assembly()` without changing the viewer.
It subtracts only four provisional counterbores and their machine bores from
`base_header`. For each outer post, it subtracts only that side's two barrel
cross-bores and machine bores. A path is clipped to its intended host before
the Boolean cut; no side rim, panel, other post, or other wood is cut.

| Current kerf-right viewer member | Uncut mm³ | Cut mm³ | Cut solids |
| --- | ---: | ---: | ---: |
| Base header | 12,961,655.528 | 12,942,617.585 | 1, valid |
| Left outer post | 1,271,561.973 | 1,259,826.352 | 1, valid |
| Right outer post | 1,271,561.973 | 1,259,826.328 | 1, valid |

The header's smallest modeled radial side-edge stock is 6.35 mm beside a
counterbore; its modeled floor below each 6.651 mm recess is 31.449 mm.
Each post's smallest modeled radial side-edge stock is 15.3 mm beside a
machine bore. Each cross-bore has 64.996 mm to the post top in the current
model. These are axis-aligned geometric residuals, not NDS edge/end-distance
acceptance or net-section capacities. Boolean subtraction differs from an
independent removed-solid calculation by less than 0.1 mm³ because of CAD
precision; the output reports both cut and removed volumes.

For the removed material, the nearest finite fixed panel-screw envelope is
44.912 mm from the header cut and 2.706 mm from each post cut. The nearest
retained frame-bolt envelope is 136.035 mm from the header cut and 42.135 mm
from each post cut. No fixed panel-screw or frame-bolt envelope intersects
the modeled removed material above the 1 mm³ reporting threshold. The
2.706 mm nominal post/screw gap and 6.35 mm header side residual are both
decision-relevant **REVISE** findings, not clearance approval. Delivered parts,
hole placement, and tolerances could consume those margins. The fixed
66 panel/kicker screw axes and 12 frame-bolt axes are checked unchanged.

This Boolean exercise does not establish wood strength, splitting resistance,
fastener ratings, thread engagement, tool access, repeated removal, other
protected-solid clearance, or the full joint load path. A single connected
solid can still be structurally inadequate. All source release flags remain
false. The screen explicitly reports **REVISE / no clearance approval**, and
this document is not a cutting or drilling instruction.

Focused validation: `pytest -q tests/test_owner_barrel_outer_header_cut_integrity.py`.
