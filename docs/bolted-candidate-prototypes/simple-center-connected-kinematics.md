# PB-02 connected center: conditional point-model kinematics

The current center loop has **no relative infinitesimal mode if every modeled
face contact is closed**. That is a conditional kinematic result, not a
complete frame proof, load path acceptance, joint rating, or drilling release.
Opening contacts can restore modes. The [script](../../scripts/simple_center_connected_kinematics.py)
reproduces the ranks below.

## Source geometry and graph

The graph now reads every bolt center from the same active
[integrated PB02 geometry](simple-center-pb02-integrated-trial.md) used by the
nominal CAD check and development viewer. The return path follows its inherited
`post_low` and `post_high` bores plus its revised `cleat_link` and `upright`
bores. Global coordinates are millimeters. Historical kinematic inputs remain
in version history; they are not silently rewritten as the active pose.

| Edge (members) | Normal | Shared-face center |
| --- | --- | --- |
| post–post block | +X | (177.65, −131.25, 166.95) |
| post block–header | +Z | (222.1, −131.25, 238.9) |
| header–principal block | +Z | (15.475, −110.35, 277) |
| principal block–right principal | +X | (50.95, −113.85, 310.5) |
| right principal–upright block | +X | (89.05, −144.9, 368.5) |
| upright block–rear block | −Y | (133.5, −175.7, 368.5) |
| rear block–post | +Y | (133.35, −175.7, 119.45) |

The bolt-axis centers are:

- post–post block: (177.65, −145, 145) and (177.65, −145, 176);
- post block–header: (208.35, −130.5, 186) and (236, −117.5, 186);
- header–principal block: (15.475, −139, 291.45);
- principal block–right principal: (34.525, −95, 312.5);
- right principal–upright block: (114.45, −144.5, 356);
- upright block–rear block: (133.5, −163.95, 370); and
- rear block–post: (140, −150.3, 110) and (140, −150.3, 190).

Each listed point is the midpoint between the active geometry's named bolt end
planes. The graph is a seven-body cycle. The old displaced center clips are not
included. Panels, screws, floor, rails, opposite-side center, and other frame
members are also outside this small graph. The return path is included as a
conditional bolted path; its face contact and load transfer have not been
verified for a signed load case.

Each timber is one rigid body with six infinitesimal degrees of freedom. At
each bolt center, the point model has two lateral constraints and, when
selected, one axial constraint. An open face contributes no rows. A closed
frictionless face contributes only four illustrative normal rows at
non-collinear points 20 mm from its bolt-group center. These rows suppress
normal separation and face rocking in a closed linearized state but offer no
face shear or frictional torque. The four points are offset 20 mm from the
actual shared-face overlap center derived from both active CAD solids. Their
spans remain rank devices, not measured bearing patches or a pressure solution.
A single axial row is an
optimistic engaged tensile/axial state; `axial off` removes all axial rows.
Actual bolt axial engagement is unilateral and may differ by bolt. Contact
must have nonnegative compression pressure and a compatible gap; the rank
calculation does not solve those complementarity or equilibrium conditions.

## Rank results

The post is fixed only as a coordinate reference. There are 36 remaining
relative degrees of freedom across six other bodies. Matrix rank uses point
velocity constraints with rotations scaled by 100 mm.

| Contact state | Axial bolt rows | Rank / 36 | Free relative modes |
| --- | --- | ---: | ---: |
| All seven faces closed | on | 36 | 0 |
| All seven faces closed | off | 36 | 0 |
| One face open, other six closed (any edge) | on | 36 | 0 |
| One face open, other six closed (any edge) | off | 35 | 1 |
| Both principal-block faces open, other five closed | on | 34 | 2 |
| Four main-path faces closed, three return-path faces open | on / off | 33 / 29 | 3 / 7 |
| All seven faces open | on / off | 27 / 17 | 9 / 19 |

With the inherited return path removed and the four main-path faces closed,
the post-anchored serial chain has **two** free relative modes. These are the
isolated face-normal twists at the two principal-side one-bolt interfaces.
The closed return loop eliminates them in this ideal point model. With the
post unfixed, the fully closed assembly has six additional rigid-body modes;
these describe arbitrary motion of the entire center, not internal freedom.
Fixing the post does **not** establish a floor anchor or a globally braced
frame. A real boundary model could add or remove effective restraints through
the rest of the frame, floor contact, and applied loads.

The rank result does not assign force or moment to any bolt. In particular,
the closed loop could need torsion or axial action at a one-bolt edge for a
given load case. Whether all assumed contacts can remain closed, which bolt
axial rows engage, actual load split, and joint/member resistance all require
a same-configuration equilibrium/contact and strength analysis. This study
does not select a second principal-side bolt or claim that one is unnecessary
for the finished frame. No strength verdict follows.

The later [signed replacement-duty fixture](simple-center-signed-duty-fixture.md)
adds a bounded equilibrium feasibility result for five authenticated historical
interface-action examples. It does not retroactively turn this rank screen into
a stiffness, pressure, strength, or complete-case solution.

Reproduce with `.venv/bin/python -m scripts.simple_center_connected_kinematics`
and `.venv/bin/python -m pytest -q
tests/test_simple_center_connected_kinematics.py`.
