# Integrated barrel frame: local joint kinematic screen

22 September 2026; [reproducible source](../../scripts/owner_barrel_integrated_kinematics.py).
This screen reads the **maintained 46-pair, 24-duty integrated barrel assembly**
and its current trial-cut face points. It changes no frame geometry. It gives
conditional ranks for each timber pair and for the connected framing timbers.
It is **not** a signed-case solve, load path acceptance, joint rating, or
drilling release.

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

## Connected framing sensitivity

The source-built graph contains **20 framing timbers in one component**, joined
by 46 barrel bolts and the 12 retained frame bolts. Its six plywood panels
are excluded from this framing-only rank; **no structural panel-screw or floor
support credit** is taken. The closed-face state adds 132 trial barrel-face
points and 72 retained-bolt face points. The two right rim/leg retained points
use the [corrected kerf-right shared face](../../scripts/owner_barrel_retained_interfaces.py)
at X = 1216.025 mm, rather than the inherited official-width X = 1219.200 mm.
Fixing the base header removes six coordinate-gauge motions; it is **not** a
physical anchor. The remaining relative rigid-body model has 114 degrees of
freedom.

| Idealized state | Matrix rank / 114 | Free relative modes |
| --- | ---: | ---: |
| All 58 bolts carry axial and lateral point constraints; all faces open | **112** | 2 |
| All 58 bolts full; all 204 face cells closed | **114** | 0 |
| Barrel axial constraints omitted; retained bolts full; all faces closed | **114** | 0 |
| Both single-bolt center faces open; all other barrel and retained faces closed; all bolts full | **114** | 0 |

This says the present 20-timber *ideal point graph* has no disconnected frame
member. It also has two relative infinitesimal modes when every wood face is
open, even if all 58 bolts are optimistically engaged in three directions.
The rest of the connected frame can kinematically remove the isolated center
twist when **other** faces are assumed closed. That is an inference about
constraint rank, not proof that signed loads keep those faces compressed or
that their wood, bolts and barrels can carry the required reaction. Likewise,
the lateral-only/closed-face full rank does **not** establish that barrel axial
engagement is unnecessary. The retained-face points are inherited
uncut-face quadrature, not a checked pressure field at every cut runner/leg
interface. No signed loading, unilateral pressure, joint slip, member
deformation or floor stability is solved here.

The current [face inventory](owner-barrel-native-connector-inventory.md)
contains 46 bolt crossings and 132 contact cells; all 24 faces preserve exact
local cut-cell areas and first moments. The owner-approved N = 42 mm left center-rail first rows
clear the two previously modeled bore/service crossings; delivered bolt
threads, barrel properties, pockets, tolerances,
and rim-first service remain unqualified. No axial barrel or lateral wood
resistance is assigned by this rank calculation.

The next mechanics decision is to show, for each of the six signed cases,
which contacts can actually remain closed and how the **connected** frame,
retained bolts, backing, panels and floor react. An optimistic all-closed
local rank cannot substitute for that equilibrium/contact calculation. This
screen does not approve drilling the revised left rows or adding a new bolt;
both require separate physical design decisions. All release flags remain false.
