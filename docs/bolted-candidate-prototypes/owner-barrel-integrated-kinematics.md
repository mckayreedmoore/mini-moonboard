# Integrated barrel frame: local joint kinematic screen

22 September 2026; [reproducible source](../../scripts/owner_barrel_integrated_kinematics.py).
This screen reads the **maintained 46-pair, 24-duty integrated barrel assembly**
and its current trial-cut face points. It changes no frame geometry. It is a
conditional six-degree-of-freedom check of each timber pair in isolation,
**not** a signed-case solve, load path acceptance, joint rating, or drilling
release.

Each joint treats its first timber as a coordinate reference. A modeled bolt
contributes two ideal lateral point constraints; the optimistic engaged case
adds one axial point constraint. A fully closed, frictionless face contributes
one normal constraint at each of its source-built contact cells. An open face
contributes none. The cells' areas are **not** force capacities or additional
constraints. The model uses `q = [translation, 100 mm × rotation]` and
`J(d,p) = [d, (p − origin) × d / 100 mm]`. Matrix rank comes from singular
values above `1e-8`; all 24 ranks are unchanged at `1e-9` and `1e-7`.
[NumPy's rank documentation](https://numpy.org/doc/stable/reference/generated/numpy.linalg.matrix_rank.html)
explains why an explicit singular-value threshold matters. Synthetic one/two
bolt tests also check the Jacobian against a small rigid motion and verify
rank invariance under changed origin and rotation scale.

| Current station group | Duties | Bolts per duty | Engaged bolts, face open | Engaged bolts, all face cells closed | Lateral-only bolts, all face cells closed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Center principal/header | 2 | 1 | 3/6 | **5/6** | 5/6 |
| All other current families, including both outer header/posts | 22 | 2 | **5/6** | **6/6** | 6/6 |

The two single-bolt principal/header joints retain a local **rotation about
the face normal** even when all their frictionless compression points are
optimistically closed and the bolt resists axial plus lateral motion. A
connected frame path might restrain that motion, but this isolated result
does not prove one. At every two-bolt duty, opening the face leaves an ideal
rotation about the bolt-pair line; adding all face points removes that local
mode only in the closed-face linearization. A rank of six says merely that
the specified ideal point constraints remove infinitesimal rigid motion.
It says nothing about whether a real barrel engages, a face stays compressed,
the cut wood survives, or the joint is stiff enough.

The current [face inventory](owner-barrel-native-connector-inventory.md)
contains 46 bolt crossings and 120 contact cells; only two faces have exact
local cut-cell areas. The other 22 distribute their measured total cut-face
area proportionally. The viewer still has two left center-rail bore/service
crossings, and delivered bolt threads, barrel properties, pockets, tolerances,
and rim-first service remain unqualified. No axial barrel or lateral wood
resistance is assigned by this rank calculation.

The next mechanics decision is to show, for each of the six signed cases,
which contacts can actually remain closed and how the **connected** frame,
retained bolts, backing, panels and floor react. An optimistic all-closed
local rank cannot substitute for that equilibrium/contact calculation. This
screen neither requests a new bolt nor approves the proposed left bore move;
both would be physical design decisions. All release flags remain false.
