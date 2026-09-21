# PB-02 center: one-bolt point-model kinematic screen

Status: **model mechanism identified; no physical failure verdict, joint
rating, or drilling release.** This screen applies to the four new serial
interfaces in the [revised combined center
pose](simple-center-combined-small-tool-probe.md). It does not change the
selected candidate, the kerf-right panel outlines, or any of the 66 fixed
panel/kicker screw axes.

The [reproduction script](../../scripts/simple_center_one_bolt_kinematics.py)
uses six rigid relative degrees of freedom per interface: three translations
and three rotations. A trial bolt is represented by two lateral point
constraints at its center, with an optional no-preload axial point constraint.
Four non-collinear frictionless face samples contribute only compression-normal
constraints. The script gives every contact its normal row when finding rank;
that is the most favorable closed-contact state for this point model.

| New interface | First bolt center, mm | Face normal | One bolt, axial on/off | Illustrative second bolt, axial on |
| --- | --- | --- | ---: | ---: |
| post–corner block | (177.65, −150, 160) | X | 5 / 5 | 6 |
| corner block–header | (222.1, −130, 238.9) | Z | 5 / 5 | 6 |
| header–corner block | (15.475, −145.3, 277) | Z | 5 / 5 | 6 |
| corner block–principal | (50.95, −95, 307.5) | X | 5 / 5 | 6 |

The missing point-model degree of freedom is **relative twist about the face
normal**. A rotation of either sign about the first bolt changes neither its
point translations nor any frictionless face-normal separation. Thus the
zero-residual mechanism does not depend on the illustrative contact spans.
The two-bolt column merely places a second lateral point constraint at a
nonzero tangential offset to demonstrate that the idealized matrix *can* reach
rank six. It does **not** establish a viable second hole, edge/end distance,
wood splitting resistance, group action, tool access, assembly order, cost, or
capacity. The one-bolt result also does not evaluate the entire center frame:
other connected members may constrain some relative motions, and the four
interfaces have different actual loading.

Real through-thickness bolt–bore bearing is distributed, not a perfect point
constraint. But ideal radial bearing between a coaxial round bolt and round
bore alone supplies **no torque about their common axis** and cannot close
this particular face-normal twist. Friction, washer clamping or another
separate restraint might, but none is quantified or credited here. Merely
assuming friction from tightening an ordinary through-bolt would be an
unsupported load path. Before a one-bolt serial interface is accepted, its
actual torsional transfer and compatibility with the complete joint must be
demonstrated by an applicable model and source-backed resistance route, or
the geometry must be revised to provide a checked bolt group. All four
interfaces still need full bearing, yield, tension, washer, splitting,
contact, and same-case force/moment checks. This screen alone cannot select
hardware or justify fabrication.

Reproduce with `.venv/bin/python -m scripts.simple_center_one_bolt_kinematics`
and `.venv/bin/python -m pytest -q
tests/test_simple_center_one_bolt_kinematics.py`.
