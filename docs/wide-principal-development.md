# Wider-principal connection development

This candidate addresses the lower backing bolt's known transverse edge-distance
defect. It is not a new capacity rating or construction approval. Historical
timber and insert variants and their structural results remain unchanged.

## Inspection package

- [Interactive candidate](https://mckayreedmoore.github.io/mini-moonboard/?model=wide-principal-development)
- [Assembly STEP](../exports/wide-principal-development/wide-principal-development.step)
- [Metric/imperial parts and cuts](../exports/wide-principal-development/wide-principal-development_parts.csv)
- [Connection schedule](../exports/wide-principal-development/wide-principal-development_connections.csv)
- [Panel/insert drilling reservations](../exports/wide-principal-development/wide-principal-development_panel_drilling.csv)

There are 291 selectable entries: 103 bodies (including 56 inserts and 18 angles)
and 188 connection assemblies. Retained transport bolts remain red, panel and
bracket screws blue, inserts/angles gray. The preceding
[insert installation limits](panel-insert-development.md) still apply.

## Geometry and stock

The two central principals change from 38.1 × 139.7 mm to 88.9 × 139.7 mm
(actual 3½ × 5½ inches, nominal 4×6). Their central service gap, rear depth,
horizontal lower bearing cuts and front housings remain. The side rims, full-width
top rail, continuous lower backing, header, outer posts, legs and gussets remain.
Each adjacent midpoint rail is shortened 50.8 mm (2 inches), and its inner
connector moves with the widened principal.

Each principal is approximately 2532.626 mm long. One 3048 mm (10-foot) stock
piece also supplies two 186.9 mm vertical-grain post blocks, leaving approximately
141.574 mm for saw kerfs and end trimming. Two stock pieces supply both principals
and all four central post blocks. Saw setup must accommodate the 88.9 mm thickness;
the housed front connection still requires controlled-depth machining.

[Home Hardware lists kiln-dried #2-and-better fir/larch 4×6×10 stock](https://www.homehardware.ca/en/4-x-6-x-10-grade-2-better-kiln-dried-fir-larch/p/2828073)
with the selected actual dimensions. This Canadian listing establishes a product
format, not local availability. Confirm the supplier's grade stamp, actual section
and moisture condition before procurement. Green or oversized stock is not an
automatic substitute for this geometry and material assumption.

## Lower connection and support

The left principal spans X −127 to −38.1 mm; the right spans 0 to 88.9 mm.
Backing bolt axes move to X −82.55 and +44.45 mm. Each has 44.45 mm transverse
edge distance in its principal, exceeding the 38.1 mm screening distance for a
3/8-inch bolt at 4D. Bolt diameter, length, front recess and lower rail remain.
Clearing that geometric screen does not establish lateral capacity, splitting
resistance, net-section strength or a permissible combined loading envelope.

Two same-width post blocks beneath each principal occupy Y −175.7 to −36 mm
and −321.75 to −182.05 mm, from floor to Z 186.9 mm. They support the retained
38.1 mm header across the full principal width. A 6.35 mm gap separates the blocks.
The header bridges that gap: this is not uninterrupted direct post bearing.
Header bending, compression perpendicular to grain and the actual sloped-foot
bearing distribution remain to be checked.

There are now 18 purchased ML24Z connectors and 108 separately purchased
SDS25112 screws, an increase of two connectors and twelve screws. Each central
post receives its own header retention connector. Manufacturer nominal geometry
is reused; installation conditions and connection resistance remain unqualified.
The assembly still has 56 removable panel machine screws and 56 insert receivers.
Affected principal and front-post attachment axes move to the new centers.

## Assembly and verification boundary

Cut and label the paired post blocks from each principal's stock before assembly.
Dry-assemble the level base, then establish the principal bearing cuts and front
housings. Attach the shortened midpoint rails with the repositioned purchased
connectors. Use actual factory holes as templates; do not drill new steel holes
to make the model fit. Install the panel inserts using their separate pilot
specification, not the larger occupied-envelope holes displayed in CAD.

The new module has its own geometry, machining and connection schedule; it does
not change global settings in earlier models. Automated checks cover the intended
inventory and coordinate changes, nominal service clearance, receiver material,
post/header contact and collisions. Their results must be reported after running,
not inferred from this description. This revision has no transferred FEA result.
Leg joints, base gusset joints, panel insert qualification, floor behavior and the
lower housed connection's complete resistance remain separate validation work.

On 2026-09-08, the eight geometry and four export checks passed, alongside the
structural preparation tests. Actual stock lengths, all 108 bracket-screw receiver
intervals, reserved service space and the inherited source-hash guard are checked.
Three independent review scopes found no remaining substantial geometry/export
issues after the source guard and coverage improvements. These checks do not
close the resistance and physical-validation items above.

```bash
uv run pytest -q tests/test_wide_frame.py tests/test_wide_exports.py \
  tests/test_wide_structural.py
```
