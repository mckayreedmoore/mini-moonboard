# Rim-on service screen: four outer-top rim-touching stations

This is a bounded diagnostic of the current barrel-nut viewer, not a service
procedure, drilling plan, or fabrication release. The probe consumes
`scripts.export_owner_barrel_scene.build_viewer_assembly()`; it changes no
viewer shapes and cuts no wood.

## Scope and modeled sequence

Only `top_outer` and `base_outer_side`, mirrored left and right, are screened.
Each station has two bolt/barrel rows. All six panels, both side rims, all 12
original frame bolts, other frame wood, and neighboring candidate hardware
stay in place. On the active side, only the eight fixed-axis panel screws
received by that side rim may be temporarily removed. The other 58 panel
screws and all hold/T-nut, light, wire, and provisional 50.8 mm rear hold-bolt
projection envelopes remain in the protected inventory.

For each row, the probe checks the viewer's 20 mm diameter by 40 mm nominal
bolt-driver and barrel-entry cylinders, plus straight axial withdrawal
envelopes with 10 mm extra travel. The matching bolt is assumed unscrewed;
both bolts at a station are assumed out before either barrel is extracted.
For withdrawal only, the matching proposed machine or barrel bore is virtually
subtracted from the receiving timber. Other wood remains uncut in the model.

The outer-top producer supplies different orientations. `top_outer` bolts
enter horizontally from the side rim, and their barrels enter along the
inclined top-rail T direction. `base_outer_side` bolts enter upward through
the header, and their barrels enter horizontally through the side rim. The
probe derives each barrel's inward direction from the current viewer solid,
measures the access-cylinder span, and rejects a changed 40 mm path or an
entry that no longer matches the modeled bore. The derived nominal barrel
recesses are 11.049 mm and 46.449 mm, respectively.

## Current finite result

| Family | Sides | Rows | Four nominal operations per row |
| --- | --- | ---: | --- |
| `top_outer` | Left, right | 4 | No modeled blocker |
| `base_outer_side` | Left, right | 4 | No modeled blocker |

All eight rows are `CLEAR_FINITE_ONLY` for bolt-driver access, shaft
withdrawal, barrel-entry access, and body withdrawal. The finite envelopes
intersect no unrelieved wood, retained fixed protected solid, or neighboring
trial hardware above the 1 mm³ reporting threshold. This does **not** prove
that delivered hardware can be installed or removed.

## Limits and next gate

- The two producer families have shaft-only viewer stacks. Heads, washers,
  actual barrel extraction grips/slots, and delivered fastener dimensions
  are not checked by the withdrawal screen.
- A 20 mm straight cylinder does not establish a real driver, hand, rotation,
  or continuous tool sweep; tolerances and repeatable service remain open.
- Temporarily removing eight panel screws while keeping the panels in place
  does not prove that the panels are safely supported during disassembly.
- This does not prove that the side rim can be continuously withdrawn, that
  the recessed outer-header joint can be serviced with the rim installed, or
  that any complete joint or load case passes.
- Nominal bore relief is an analytical subtraction only. No physical wood is
  drilled, no bit size is released, and no structural or climbing claim follows.

Run the focused check with:

```sh
.venv/bin/pytest -q tests/test_owner_barrel_rim_outer_top_service_probe.py
```
