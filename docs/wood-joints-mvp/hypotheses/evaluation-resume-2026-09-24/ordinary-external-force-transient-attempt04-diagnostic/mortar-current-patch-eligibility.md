# MORTAR eligibility of the current 35-pair patch

## Finding

The explicit MPC/SPC screen passes: no active MPC or SPC uses a current slave
contact node, including any quadratic face midside node. No constraint repair or
role reversal is indicated by the slave-edge MPC restriction. A separate
`*STATIC` deck can specify all 35 pairs as MORTAR without geometry, constraint,
or role changes, but the overlap behavior below leaves full-patch response
eligibility unresolved.

This does not authorize or validate a full-patch solve. CalculiX 2.23 MORTAR
is available only in `*STATIC`, so it cannot replace attempt04's `*DYNAMIC`
replay. The method screen's known-answer coupon remains a gate before any full
static comparison. A single-pair coupon would not validate the current patch's
shared-node behavior or result mapping. Attempt09's common-map case is an
input/control record, not a successful static response; it accepted no state
under the existing penalty formulation.

## Frozen pair and element scope

The audit used attempt04's frozen
[`contact-manifest.json`](replay-attempt01/contact-manifest.json),
[`contact-fragment.inc`](replay-attempt01/contact-fragment.inc), and
[`mesh.inp`](replay-attempt01/mesh.inp). Their SHA-256 values are respectively:

- Contact manifest: `50f7d8c9b85197f43732d49d13e75240fa6d5423673d28274e278829878a594d`.
- Contact fragment: `35a4513b7877b04b0c2be053f3084d07178a148c606780d12d54388636574b24`.
- Mesh: `117fdc67c8d3f7f7e3bf1df41d842c9d8e7fa57e1c941676bccd882878bb4803`.

The fragment declares 35 `TYPE=SURFACE TO SURFACE` pairs. Its 70 slave/master
surfaces are all `TYPE=ELEMENT`; all 22,847 referenced element faces map to
C3D10 elements in the frozen mesh. Each face is a six-node quadratic triangle:
three corner nodes and three edge midside nodes. The 35 pair categories are
3 wood interfaces, 8 shaft-to-wood bores, 8 shaft-to-washer bores, and 16
washer-seat pairs. No pair's slave and master node sets overlap each other.

I classified contact node IDs from their positions in the C3D10 element
connectivity (first four nodes are vertices; last six are edge midsides), then
intersected the explicit pair node sets with active equation, rigid-body, and
boundary records. The attempt04 and attempt09 copies of `contact-fragment.inc`,
`mesh.inp`, `nut-coupling.inp`, and `rigid-carriers.inp` are byte-identical.

## Active constraint overlaps

Attempt04's `pilot.inp` includes the frozen
[`nut-coupling.inp`](replay-attempt01/nut-coupling.inp) and
[`rigid-carriers.inp`](replay-attempt01/rigid-carriers.inp), but does not
include the external-port map. The static common-map deck in
[`attempt09`](../ordinary-port-motion-attempt09-common-map/README.md)
([`port_motion_n_plus.inp`](../ordinary-port-motion-attempt09-common-map/port_motion_n_plus.inp))
adds
[`port-motion-controls.inp`](../ordinary-port-motion-attempt09-common-map/port-motion-controls.inp)
and boundary values on its control nodes. Results below keep those two deck
contexts distinct.

| Active constraint source | Slave-node overlap | Master-node overlap |
| --- | --- | --- |
| 24 nut shaft-fit `*EQUATION` rows, all terms | None | None |
| 12 attempt09 cap-map equation dependents | None | None |
| Attempt09 cap-map equation terms | None | 36 unique master nodes; 486 terms |
| Four nut `*RIGID BODY` node sets | None | 592 nodes, only on four nut master sides |
| Attempt09 `*BOUNDARY` control nodes | None | None |

All contact slave nodes are therefore free of these explicit constraints:
0 constrained vertices and 0 constrained edge midsides. The nut equations have
24 dependent node/DOF pairs and no contact-surface node anywhere in their
equation terms. The attempt09 audit independently records that no contact
surface node is a dependent variable and that the nut dependent-DOF
intersection is false; its 486 contact-equation references are independent
terms only. The port map has 12 dependent node/DOF pairs at eight node IDs;
none is a contact node. Its 36 unique contact-node terms are all master nodes.
The 12 prescribed control nodes are `116171`–`116182`, outside both contact
roles. There is no cleat boundary condition.

The nonempty master-side equation-term intersections are:

- `WJCP_001`: `9394`–`9395`, `10570`–`10576` (5 vertices, 4 midsides).
- `WJCP_002` and `WJCP_003`: `32554`–`32555`, `33219`–`33225`
  (5 vertices, 4 midsides in each pair).
- `WJCP_007` and `WJCP_011`: `9374`–`9375`, `9518`–`9524`
  (5 vertices, 4 midsides in each pair).
- `WJCP_015` and `WJCP_019`: `32537`–`32538`, `32705`–`32711`
  (5 vertices, 4 midsides in each pair).

The nut rigid-body intersections are also master-only:

- `WJCP_006`: 138 nodes, `71522`, `71583`–`71635`, `72187`–`72270`
  (42 vertices, 96 midsides).
- `WJCP_010`: 138 nodes, `86265`, `86326`–`86378`, `86938`–`87021`
  (42 vertices, 96 midsides).
- `WJCP_014`: 158 nodes, `100555`, `100616`–`100668`, `101228`–`101331`
  (47 vertices, 111 midsides).
- `WJCP_018`: 158 nodes, `115008`, `115069`–`115121`, `115681`–`115784`
  (47 vertices, 111 midsides).

The `WJCP` indices are the exact pair order in the linked contact fragment and
manifest. These master-side entries do not violate the documented slave-edge
rule. Preserve the existing roles; do not flip pairs to change the reported
intersections.

## Existing multi-pair coverage

Seven slave node IDs occur in both wood-interface slave sets
`WJCP_001` and `WJCP_002`: vertex nodes `7`, `12`, `122`, `123`, and midside
nodes `124`–`126`. They must remain visible as a shared edge in a future
pair-by-pair MORTAR audit; do not assume the two slave zones are disjoint.

On the master side, 5,553 node IDs occur in more than one pair: 5,386 occur in
two pairs, 160 in three, and 7 in four. Of these repeated master IDs, 1,573
are vertices and 3,980 are midsides. Their exact compact ranges are:

```text
1–6, 8–11, 17–66, 72–76, 82–121, 433–527, 569–663, 9370, 9372,
9374–9384, 9389, 9393, 9401–9407, 9416–9899, 10271–10285,
10555–10569, 10818–11801, 32536–32567, 32584–33057,
33083–33572, 34282–35636, 36088–37474
```

Across different pair records, 752 node IDs are used in both a slave and a
master set (378 vertices, 374 midsides); none is both roles in the same pair.
This shared-node coverage is not an MPC/SPC collision and does not by itself
show simultaneous contact. A full-patch decision must preserve and audit the
pair-specific coverage and output mapping instead of treating these as
independent, disjoint interfaces. The exact cross-role ID ranges are:

```text
1, 3, 8–9, 13–16, 22–26, 82–86, 132–161, 167–181, 241–255,
9370–9373, 9401–9407, 9409–9415, 57475, 57588–57614,
68823–68824, 68968–69033, 70176–70177, 70321–70386, 72630,
72743–72769, 83557–83558, 83702–83767, 84904–84905,
85049–85114, 87367, 87480–87506, 97831–97832,
97976–98041, 99193–99194, 99338–99403, 101716,
101829–101855, 112287–112288, 112432–112497,
113648–113649, 113793–113858
```

## Pinned 2.23 behavior at shared nodes

The source archive in `diagnostic-lock.json` is the same pinned 2.23 archive
used here (SHA-256
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`). In
`src/remlagrangemult.f:49–99`, the solver checks each slave node against every
other contact tie's slave and master node lists. For either overlap it sets
that slave-list occurrence to `islavact=-2` and reports that its Lagrange
multiplier is removed. `src/contactmortar.c:268–283` labels `-2` as a no-LM
node; `src/stressmortar.c:527–537` handles it through the no-LM branch. Thus,
the source deliberately handles shared slave/slave and slave/master nodes; the
overlap alone does not show an immediate unsupported-case rejection.

The seven nodes shared by `WJCP_001_S` and `WJCP_002_S` are boundary nodes on
two perpendicular slave patches. The averaged face normals at those shared
nodes are approximately `(0,-0.642788,-0.766044)` and `(-1,0,0)` (dot product
zero within the mesh-coordinate precision). The solver's overlap rule marks
both pair occurrences no-LM, so it does not retain a separate multiplier at
each of these two normals. The 752 cross-role IDs are also all boundary nodes
on their slave patch. Based on the pinned C3D10 face table in
`src/tiefaccont.f:70–75`, none of the overlap-disabled slave occurrences is a
surface-interior node. I classified a node as boundary when it lies on a
quadratic edge referenced by exactly one face in that slave patch.

| Pair(s) | No-LM occ. | Vertex / mid | Boundary / interior | Unmarked nodes* |
| --- | ---: | ---: | ---: | ---: |
| WJCP_001 | 46 | 24 / 22 | 46 / 0 | 109 |
| WJCP_002 | 46 | 24 / 22 | 46 / 0 | 105 |
| WJCP_003 | 18 | 10 / 8 | 18 / 0 | 25 |
| WJCP_004–019, each | 34 | 17 / 17 | 34 / 0 | 249–362 |
| WJCP_020–027, each | 0 | 0 / 0 | 0 / 0 | 1,616–3,829 |
| WJCP_028, 030, 032, 034, each | 28 | 14 / 14 | 28 / 0 | 59–66 |
| WJCP_029, 031, 033, 035, each | 0 | 0 / 0 | 0 / 0 | 65–67 |

Across pairs this predicts 766 no-LM slave-list occurrences: 386 vertex and
380 midside occurrences, all on the patch boundary. They represent 759 unique
node IDs: the 752 cross-role IDs plus seven shared-slave IDs; the latter count
twice because both slave-pair occurrences are disabled. The minimum raw
non-overlap slave-node count is 25 on `WJCP_003`; this is before the solver's
contact pairing and active-set decisions, not a count of retained active
multipliers.

*Unmarked nodes are slave nodes not identified by this overlap screen; the
count is before contact pairing and active-set decisions.

The 2.23 manual says not to use the same contact surface in more than one
contact definition. This fragment declares 70 distinct surface names, each
used in one pair. The manual does not say that distinct surfaces may not share
boundary node labels. It therefore does not settle whether weak contact at the
perpendicular shared edge or the cross-role boundaries is adequately
represented.

There is also a mapping limit to keep visible. `src/inimortar.c:182–199`
allocates one `islavnodeinv` entry per global node, writes master-list indices,
then writes slave-list indices. A node present in several pair lists therefore
has one last-written index, not a separate inverse index per pair. The mortar
assembly and stress routines use this map (for example,
`src/contactmortar.c:323–379` and `src/stressmortar.c:218–239, 724–730`). The
source intentionally removes multipliers at overlapping slave occurrences,
but this static read does not establish that local normals, forces, or output
fields at these shared locations are represented as intended. Treat that
model-specific behavior as unresolved pending a representative overlap/output
check; do not call the 752 cross-role nodes unsupported solely because their
labels repeat.

## Decision boundary

The explicit constraint screen supports retaining the frozen geometry, all
contact surfaces, and their current roles in a proposed static comparison.
CalculiX does not allow MORTAR and penalty contact to be mixed in one deck, so
all 35 pair types would change together. Pinned 2.23 source explicitly
suppresses multipliers at the overlap nodes, but this read-only audit cannot
confirm the resulting enforcement and output mapping at the perpendicular
shared-slave edge and cross-role boundaries. Keep the known-answer C3D10 coupon
as the next gate; a single-pair pass would not close this overlap question.
Make no full-joint launch decision from this note. No input, geometry,
constraint, pair order, or native result was changed or generated for this
audit.

References: [CalculiX 2.23 manual, Face-to-Face Mortar Contact](https://www.dhondt.de/ccx_2.23.pdf);
[official 2.23 HTML manual archive](https://www.dhondt.de/ccx_2.23.htm.tar.bz2);
[pinned source lock](diagnostic-lock.json),
[verified local source archive](build-attempt02/source.tar.bz2),
[official source archive](https://www.dhondt.de/ccx_2.23.src.tar.bz2);
[attempt04 method screen](contact-formulation-method-screen.md);
[attempt09 independent input audit][cap-map-audit].

Source-member SHA-256 values from the locked archive:

- `remlagrangemult.f`: `85376768d34d9aa2a91c96554c7a39befe476e01ceac8709d49d3de8b92308c2`.
- `inimortar.c`: `998d5f1e45715356dfcc9677527636cb3d8227e15f75c3606a110b92a29dd40f`.
- `contactmortar.c`: `67ef7ea5f3353eb1d5a009ebce289b22b0c8e0f8542c038a30392c676186f001`.
- `stressmortar.c`: `c62c65de7aba91260320a3c548ebc513a436e4243151ca0441dcc5d309dce621`.

[cap-map-audit]:
  ../ordinary-port-motion-attempt09-common-map/port-motion_n_plus-audit.json
