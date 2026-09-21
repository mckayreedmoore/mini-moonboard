# PB02 conditional placement-margin revision

The [placement revision script](../../scripts/simple_center_pb02_placement_revision.py)
checks three bounded variants from committed pose `e9e4e42`. It changes only the
`post_high` bolt Z coordinate and the two vertical header-pair X/Y coordinates.
The later active revision also moves only `cleat_link` from Z370 to Z328.5.
The side-cleat solids, post/header block, other six bolt axes, and all
66 panel/kicker screw axes remain fixed.

`front_stagger` remains a viable conditional trial, but it is not the active
pose. The active `ligament_priority` variant keeps the same header-pair stagger,
95 mm block bottom, and Z145/176 post-cleat pair, but moves `post_high` alone to
Z202.0 and moves `cleat_link` to Z328.5. The post pair's crossed centerlines
are 26.0 mm apart with 18.7 mm nominal surface ligament. The side-cleat pair's
centerlines are 27.5 mm apart with 20.2 mm nominal surface ligament. One immutable
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

The selected Z202.0 active value is a separate ordinary-hardware revision. Its
upper loaded-end distance is 36.9 mm, which is 14.675 mm above 3.5D but below
the 44.45 mm 7D full-value distance. The conditional reduced end-distance
factor is `CΔ = 36.9 / 44.45 = 0.83015`. It intentionally gives up the 7D+5
project comparator, whose reserve is −12.55 mm, to achieve the 26.0 mm crossed
centerline separation without enlarging the block or requiring 10-inch bolts.
The link move retains its existing five-inch bolt and 99.7 mm wood grip. Its
51.5 mm lower grain-end distance is 2.05 mm beyond the 7D+5 project comparator.

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
| active `ligament_priority` | −12.55 mm at `post_high`; one negative row | clear |

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
