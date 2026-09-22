# Outer/top barrel trial: exact-frame finite collision screen

This bounded check uses the kerf-right owner assembly with both center posts at
X = ±180 mm, both kicker screw backers, 66 unchanged panel/kicker screws, and
12 retained frame bolts. It checks the eight outer/top barrel trials against
the maintained T-nuts, hold-hole/50.8 mm trial projections, LEDs, wires, fixed
connections, other timber, and outer/top neighboring trial solids. The
reproducible source is the [outer/top protected probe][probe].

At the current nominal geometry, there are **no positive-volume hits above
1 mm³** against the protected T-nut/hold, electrical, panel-screw, or retained
frame-bolt solids. No outer/top trial physically intersects another outer/top
trial, and no modeled outer/top drill/access path intersects another outer/top
trial solid. The existing integrated cross-family screen also reports zero
positive-volume hits among the supplied barrel/bolt/path solids. These are
bounded negative screens, not toleranced clearances or a joint verdict.

- Outer header/post, both sides: each of two nominal bolt shafts intersects
  the same-side side rim by 52.286 mm³. Each 20 mm diameter × 40 mm bolt-access
  cylinder intersects it by 12,566.371 mm³.
- Outer base/side, both sides: each of two bolt-access cylinders intersects
  the same-side outer post by 1,568.970 mm³.
- Top outer and top center, both sides: no unrelated-timber hit above 1 mm³
  in this screen.

The header shaft/rim overlap is a modeled installed-component interference,
not merely a drill-access concern. The access-cylinder hits show that the
current assumed straight driver approach is obstructed, not that all possible
tools or assembly sequences are impossible. The previous outer-base exception
therefore remains open; its PB09-era neighbor warning cannot be dismissed from
isolated bore coverage. This check also does **not** model actual purchased
heads/washers, a socket/bit sweep, insertion order, wood removal, tolerance,
6–10 mm barrel-axis sensitivity, thread engagement, member strength, or the
changed load path. The Hillman body and mating bolt remain provisional. No
layout, drilling, fabrication, or structural release follows.

[probe]: ../../scripts/owner_barrel_outer_top_protected_probe.py
