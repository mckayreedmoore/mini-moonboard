# Top-joint end-distance revision

This separate `top-joint-development` candidate preserves the published
`selected-hardware-development` model and its evidence. It is a nominal geometry
revision, not structural qualification or a construction drawing.

## Change

Move the two top-rim bolts on each side 47 mm downhill, from board stations
2375/2415 mm to 2328/2368 mm. Keep their normal coordinate at 63 mm, their
selected products and grip lengths unchanged. Extend only the rim-facing leaf
of each custom 6 mm steel angle downhill to station 2313 mm. The rail-facing
leaf still starts at 2359.5 mm; its screws do not move.

Four receivers are rebuilt from undrilled geometry and all incident bores are
recut. Old bolt holes are absent in this new-manufacture candidate; this is not
an instruction to fill or relocate holes in an already-built frame. The other
83 bodies and 274 connections remain unchanged. Total inventory stays at
87 bodies and 278 connections.

| Nominal wooden-rim quantity | Metric | Imperial |
| --- | ---: | ---: |
| Uphill end distances | 110.4 / 70.4 mm | 4.346 / 2.772 in |
| Bolt spacing | 40 mm | 1.575 in |
| Side edge distances | 81 / 103.15 mm | 3.189 / 4.061 in |
| Chosen 7D end-distance screen, D = 9.525 mm | 66.675 mm | 2.625 in |
| Chosen 4D spacing screen | 38.1 mm | 1.500 in |

These are conservative layout screens retained from the
[connection audit](product-connection-audit.md), not proof of resistance under
the unresolved mixed load directions, material properties or fabrication
tolerances. They are not steel-edge requirements.

## Remaining steel question

The lower bolt is 31.5 mm (1.240 in) downhill of the rail-facing leaf. Its load
must pass through the extended steel leaf. Bending, prying, bend/weld transition,
fabrication and installation remain unqualified. The custom connector remains
unselected. A 140 × 38.1 × 115.4 mm bounding blank does not describe its stepped
profile; generated solid geometry governs that profile.

If this extension cannot qualify, review a combined top-cap/top-rail connector.
Simply moving a second bolt rearward at the same station would conflict with
the existing top-cap angle and bolt layout. No capacity or new FEA result is
claimed here.

## Verification scope

`tests/test_top_joint_frame.py` checks the exact changed inventory, preserved
rail-facing leaf, replaced bores and every connection's open core and receiver
material, nominal timber distances, minimum washer
bearing annuli, and the existing reserved LED/routing envelopes.
`tests/test_top_joint_screen.py` checks the full nominal body/hardware collision
screen and requires exactly the 24 previously documented installation-order
tool obstructions, with no solver errors or extra collisions. Those tool
obstructions still require ribs before skins and edge screws before legs;
the screen does not approve an erection procedure or actual socket engagement.

Local verification: `uv run pytest tests/test_top_joint_frame.py
tests/test_top_joint_screen.py -q` passed all nine cases. Repository Ruff and
diff whitespace checks passed. Two independent three-scope review passes
(correctness, testing, architecture) found one missing incident-bore regression
check; it was added and the final pass had no substantial findings. These are
software/geometry review results, not professional structural review.

## Viewer and matching exports

- [Interactive revised top-joint model](https://mckayreedmoore.github.io/mini-moonboard/?model=top-joint-development)
- [STEP assembly](../exports/top-joint-development/top-joint-development.step)
- [Metric/imperial parts schedule](../exports/top-joint-development/top-joint-development_parts.csv)
- [Connection positions and hardware schedule](../exports/top-joint-development/top-joint-development_connections.csv)
- [Source and artifact hashes](../exports/top-joint-development/manifest.json)

![Revised top-joint candidate, generated perspective](../exports/top-joint-development/top-joint-development_front.png)

The selectable `selected-hardware-development` variant remains the predecessor
with shorter top-bolt end distances. Do not treat the two as identical. All
[predecessor assembly-access and service reservations](product-frame-integration.md)
remain applicable, except the explicitly relocated top bolts and extended leaves.

Adding the exporter branch updates only the shared exporter-source hash in the
six predecessor manifests. Their CAD, images, schedules and viewer artifact
bytes are unchanged. The export regression checks the old and new variants
against their respective geometry and source closures.

Publication checks: all eight cases in `tests/test_joint_exports.py` passed,
covering all seven development variants and the bore-probe control case.
The local browser loaded 365 entries, selected 16 parts/connections through
actual pointer events (including the extended leaf and moved bolt), retained
the plywood default and reloaded this variant through the selector without
page/request errors. Desktop and 390 × 844 narrow-screen captures were inspected.
The narrow-screen check verifies horizontal fit only; the scrollable status
header still overlays the upper scene. This is not a mobile usability sign-off.
