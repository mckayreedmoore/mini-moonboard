# PB02 conditional placement-margin revision

The [placement revision script](../../scripts/simple_center_pb02_placement_revision.py)
checks three bounded variants from committed pose `e9e4e42`. It changes only the
`post_high` bolt Z coordinate and the two vertical header-pair X/Y coordinates.
The integrated side-cleat pose, post/header block, other seven bolt axes, and all
66 panel/kicker screw axes remain fixed.

`front_stagger` remains a viable conditional trial, but it is not the active
pose. The active `ligament_priority` variant keeps the same header-pair stagger
and uses the 0.1-mm drawing coordinate Z189.4 for `post_high`. This clears the
7D plus 5 mm project comparator by 0.05 mm while retaining 6.1 mm nominal
orthogonal-bore surface ligament. One immutable
candidate-local trial specification and one geometry builder feed the integrated
CAD check, placement table, stack screen, connected kinematics, and V4 viewer.
`working_reference`, `front_stagger`, and rejected `rear_stagger` remain named
alternatives.

## Viable conditional co-design

The `front_stagger` trial uses these bolt-axis coordinates in millimeters:

| Axis | Integrated pose | Revised pose |
| --- | ---: | ---: |
| `post_high` Z | 190.0 | 189.0 |
| `cleat_header_1` X/Y | 208.35 / −130.0 | 208.35 / −130.5 |
| `cleat_header_2` X/Y | 235.85 / −130.0 | 236.0 / −117.5 |

The diagonal header-pair spacing is 30.5536 mm. Against the conditional 4D plus
5 mm comparator of 30.4 mm, both the header and cleat rows have **+0.1536 mm**
reserve. Lowering `post_high` by 1 mm changes its upper grain-end distance to
49.9 mm and its conditional 7D plus 5 mm reserve to **+0.45 mm**. The placement
table has no negative conditional rows. Its overall minimum is 0 mm because the
unchanged upright remains exactly at one side-cleat edge comparator.

The selected 189.4 mm active value sits between those bounded alternatives. Its
upper grain-end distance is 49.5 mm, its 7D plus 5 mm reserve is +0.05 mm, and
its nominal crossed-bore surface ligament is 6.1 mm.

The revised pose retains nominal CAD fit:

- all ten Ø7.3 mm modeled bores are fully received by their intended wood;
- all 20 modeled washer seats have full bearing;
- every bolt has at least one clear modeled straight insertion end;
- all reported wood, bore, hardware, washer, socket, and fixed-screw collision
  categories are empty;
- the revised side cleat has no other-wood or fixed-screw overlap; and
- all 66 panel/kicker screw solids match the fixed source by name, bounds, and
  modeled volume.

## Bounded controls

| Trial | Target conditional result | Nominal CAD result |
| --- | --- | --- |
| `working_reference` | −2.9 mm minimum; three negative rows | clear |
| `rear_stagger` | 0 mm minimum; no negative rows | rejected |
| `front_stagger` | 0 mm minimum; no negative rows | clear |

The rearward stagger demonstrates that placement arithmetic alone is
insufficient. Its second vertical bore intersects both horizontal post-cleat
bores by 238.42571 mm³. The front stagger avoids those intersections while
retaining the full nominal fit checks.

This is a reproducible conditional geometry comparison only. The project
comparators remain conditional, whole-center placement classification remains
incomplete, and this work provides no strength, drilling, fabrication, or
installation release.

Run:

```text
.venv/bin/python -m scripts.simple_center_pb02_placement_revision
.venv/bin/python -m pytest -q tests/test_simple_center_pb02_placement_revision.py
```
