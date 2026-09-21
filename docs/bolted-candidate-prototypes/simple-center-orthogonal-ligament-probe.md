# PB02 orthogonal bore ligament lead

This is a bounded nominal CAD follow-up to the
[current placement inventory](simple-center-current-placement-table.md), using
its ten-bore tolerance pose and `shorter_8in_trial` post/header block. The
[probe](../../scripts/simple_center_orthogonal_ligament_probe.py) changes only
`post_cleat_2` from Z=180 to **176 mm** and `cleat_link` from Z=370 to
**390 mm**. Each bore keeps its axis direction, diameter and full grip length.
All wood shapes, both inner kicker supports, the three other post/header
bores, the remaining inherited bores, and all 66 panel/kicker screw axes
retain their source geometry. This is an adjustment lead, not a selected pose.

| Pair in shared member | Current centerline gap / nominal wood | Trial gap / nominal wood |
| --- | ---: | ---: |
| `post_high` / `post_cleat_2`, shifted post | 10 / 2.7 mm | 14 / 6.7 mm |
| `upright` / `cleat_link`, upright side cleat | 10 / 2.7 mm | 30 / 22.7 mm |

Wood here is the shortest surface gap between nominal Ø7.3 mm cylindrical
holes: centerline gap minus 7.3 mm. It is a local geometric ligament, not a
stress capacity or a measured as-drilled minimum. The trial retains ten
fully received bores, full bearing at its four moved exposed washer faces,
and no positive-volume bore/bore, bore/unintended-wood, bore/fixed-screw,
or moved outward-hardware/wood-or-screw hit. The fixed screw inventory is
48 panel plus 18 kicker axes. The support result follows from unchanged wood
and screw shapes in the maintained pose; the new probe does not requalify
that support mechanically. The moved post pair has 31 mm pitch, leaving
only **0.6 mm** over the *conditional* 4D=25.4 mm plus one 5 mm project
allowance. The raised link has 70 mm to the top grain end of its two cleats.

There is a tight source-bound limit on this particular post fix. Holding
the 95 mm block bottom, the Z=190 `post_high` axis, and the two post/block
bolts as a Z pair, a conditional 7D=44.45 mm bottom end marker plus 5 mm
requires the lower bolt at Z≥144.45. A conditional 4D=25.4 mm pair pitch
plus 5 mm then requires the upper at Z≥174.85. Thus this downward-shift
family can increase the `post_high` centerline gap to at most **15.15 mm**,
or **7.85 mm** nominal surface ligament. The Z=176 trial stays within that
arithmetic limit. This is a limit for that fixed block and those chosen
markers, not a global impossibility proof for every center design.

Let each hole center stray toward the other by at most *e* mm and each hole
diameter exceed 7.3 mm by at most *δ* mm. A conservative local bound is
`ligament ≥ nominal ligament − 2e − δ`. For the trial's post pair this is
`6.7 − 2e − δ` mm; for the upright/link pair it is
`22.7 − 2e − δ` mm. For illustration only, `e=2.5, δ=0` leaves lower
bounds of 1.7 and 17.7 mm. The project 5 mm placement allowance has not
been established as an actual drilling tolerance, and its comparator
arithmetic must not be substituted for measured hole position or diameter.

The [current inventory](simple-center-current-placement-table.md) still
reports conditional deficits at the inherited `post_high` top grain end
(−0.55 mm), the `upright` front edge (−14.3 mm), and the vertical
header-bolt pair (−2.9 mm); moving these two axes does not resolve them.
Orthogonal neighbor rules, load directions, split paths, net wood section,
bolt bearing and group action, actual wood properties, moisture, hole
quality, washer seating, insertion/tool access, and stress interaction need
their own evaluation. No NDS pass, strength rating, fabrication or drilling
release is claimed. No half-lap or custom steel is introduced.

Run `.venv/bin/python -m scripts.simple_center_orthogonal_ligament_probe`
and `.venv/bin/python -m pytest -q
tests/test_simple_center_orthogonal_ligament_probe.py`.
