# BG045 NDS edge, end, row, and splitting applicability

**Disposition:** the source establishes conditional grain categories and several
geometric comparisons. It does not establish a Table 12.5.1C failure, a
finished-profile edge distance, an NDS row layout, or a splitting capacity.
The existing 20.0-versus-25.4 mm comparison is a valid conditional arithmetic
result for one block edge interpretation; whether that face is the required
NDS loaded edge remains unresolved. No reviewed bolt axis, geometry, freeze, or
acceptance state changes here.

## Source orientation and signed actions

The accepted A1-rear, A12-rear, and K12-rear demand reports are pinned by
SHA-256 in [`source-pins.json`](source-pins.json), alongside the complete-corner
register, header transfer-section reconstruction, three source models, their
source STEP members, and the proposed-grain maps. The three source models give
matching BG045 body geometry and proposed axes: the block grain and through-bolt
axis are both global `+Z`; header grain is global `+X`; lateral bolt actions lie
in `XY`, at 90 degrees to the bolt axis. The source grain maps explicitly say
that grain and transverse ring assignments are proposals, not observations of
the received boards.

On the block, all lateral forces are perpendicular to proposed grain, so the
perpendicular-to-grain branch of NDS-2024 Table 12.5.1C is conditionally
relevant. Because the proposed block grain and bolt axis are both `+Z`, the
orientation also matches §12.5.2.2's end-grain factor wording if the block is
confirmed as the wood main member: `Ceg = 0.67` adjusts a reference lateral
value. That factor does not change minimum dimensions, select a loaded face,
or supply a splitting check.

On the header, every full lateral action has both an `X` component parallel to
grain and a `Y` component perpendicular to grain. The per-bolt acute angles to
the proposed grain are 1.19°–74.16° across the three accepted cases. The two
20.0 mm `−Y` distances in A12-rear/K12-rear and the 26.35 mm `+Y` distance in
A1-rear are cross-grain component sensitivities, not full-vector Table 12.5.1C
checks. The header's `X` boundaries are member ends, not lateral edges; the
standard's end-distance and edge-distance rules use different directions.
The available official 2024 Chapter 12 PDF is specification text only. Its
tables give parallel- and perpendicular-to-grain branches but no oblique-grain
interpolation. The official 2018 Commentary historically says there was no
specific edge guidance for angles other than 0°/90°; that note is not asserted
to be 2024 Commentary language. No 2024 angle interpolation or component
interaction is adopted here. Likewise, no shear-area conclusion is inferred
from §12.5.1.2(b): the source lateral loads are bolt-normal lateral forces, and
the header's obliquity is relative to wood grain.

The model point-to-envelope measurements are perpendicular distances to
rectangular source-envelope faces. A ray along an oblique force is used only
to identify a candidate first face; the ray travel length is not the NDS 4D
distance. The pinned STEP BReps have modeled source-profile identity, but this
attempt does not query the local BRep face from each bolt center or establish a
finished/inspected edge, hole web, cut, or tolerance. The reported 20.0 mm is
therefore a model-envelope coordinate result, not an actual-stock observation.

## Conditional edge and spacing results

For the named `D = 6.35 mm` scenario only, `4D = 25.4 mm`, `1.5D = 9.525 mm`,
`3D = 19.05 mm`, and `5D = 31.75 mm`. NDS-2024 §12.5.1.3 makes Tables
12.5.1C/D applicable when `D ≥ 1/4 in`; the delivered bolt diameter and actual
wood bearing lengths have not been established. The model gives block-axis
length 139 mm and header wood side length 38.1 mm, so the Table C/D lesser
`l/D` geometry is conditionally 6.0.

For the block group resultant, A1-rear points toward `−Y`; the nearest bolt is
axis 2 at 20.0 mm from the source-envelope `−Y` face. If that face is the NDS
loaded edge, its conditional Table C comparison is `25.4 − 20.0 = 5.4 mm`
short, and the opposite `+Y` distance is 113.35 mm, greater than 1.5D. A
full-vector first-hit reading of A1 axis 2 gives the same candidate `−Y` face.
The standard defines a loaded edge as the edge toward which the fastener acts,
but does not prescribe a first-ray or component rule for this oblique action
into a multi-face end-grain block. Thus the arithmetic is supported, while the
required-face interpretation is conditional. It is not an adopted NDS
failure, and it does not approve the axis-2-only proposal.

For A12-rear and K12-rear, the block group resultants point toward `+X`. Their
individual source-envelope rays also first reach an `X` face, 44.45 mm away;
the 20.0 mm `+Y` values are component-only sensitivities. Requiring 4D at both
cross-grain faces is not the Table C rule, which distinguishes the loaded edge
from its opposite unloaded edge. The signed load direction reverses from
`−Y` in A1-rear to `+X` in A12-rear/K12-rear, so one fixed edge assignment
cannot be reused across those cases.

The header `Y` face sensitivities are 26.35/119.70 mm in A1-rear,
113.35/20.00 mm in A12-rear, and 113.35/20.00 mm in K12-rear (axis 1/2).
Because each full force is mixed to the header grain, none of these values
alone determines a required 4D loaded edge. The 20.0 mm header comparisons are
not a basis for moving a reviewed axis.

The full-factor-one force and source-envelope comparison for each bolt axis is:

| Case / axis | Force on block `Fx,Fy` (N) | Block first envelope face / normal distance | Force on header `Fx,Fy` (N) | Header angle to `+X` grain | Header cross-grain Y face / distance |
|---|---:|---|---:|---:|---|
| A1 / 1 | `−17.472, −61.591` | `−Y / 113.35 mm` | `17.472, 61.591` | 74.163° | `+Y / 26.35 mm` |
| A1 / 2 | `50.096, −71.224` | `−Y / 20.00 mm` | `−50.096, 71.224` | 54.879° | `+Y / 119.70 mm` |
| A12 / 1 | `89.016, 14.035` | `+X / 44.45 mm` | `−89.016, −14.035` | 8.960° | `−Y / 113.35 mm` |
| A12 / 2 | `24.272, 5.761` | `+X / 44.45 mm` | `−24.272, −5.761` | 13.353° | `−Y / 20.00 mm` |
| K12 / 1 | `74.074, 1.540` | `+X / 44.45 mm` | `−74.074, −1.540` | 1.191° | `−Y / 113.35 mm` |
| K12 / 2 | `−14.930, 4.590` | `−X / 44.45 mm` | `14.930, −4.590` | 17.089° | `−Y / 20.00 mm` |

For the header, `−X/+X` first-ray boundaries are member ends, so those ray
results are not Table 12.5.1C edge measurements. The Y values are perpendicular
to grain face projections; they remain component sensitivities for these
mixed forces.

Other named table screens are strictly geometric:

| Provision | Source geometry and conditional comparator | Applicability result |
|---|---|---|
| Table 12.5.1A end distance | Block lateral load is perpendicular to proposed grain: 2D minimum / 4D at `CΔ = 1`, or 12.7 / 25.4 mm. The modeled bolt-axis span is `z=238.9…416.0 mm`; its midpoint is `z=327.45 mm`, giving 50.45/88.55 mm to block envelope cut ends `z=277/416 mm`. Header `X` end projection is at least 133.35 mm versus 7D softwood-tension (44.45 mm) and 4D compression (25.4 mm). | Block values assume the modeled axis-span midpoint is the physical bolt center; header's full action is mixed, so its `X` component alone is not an end-distance check. Actual bolt center, loaded-end class, product, and finished profile remain unverified. |
| Table 12.5.1B spacing in a row | Axis pitch is 93.35 mm, above the 3D minimum (19.05 mm) and 4D parallel comparator (25.4 mm). | §12.1.2.4 defines a row as two or more fasteners aligned with load. The bolt line is `Y`; resultant directions differ from that line by 13.80° (A1), 80.09° (A12), and 84.08° (K12). The pitch alone is not an applicable row check. For `CΔ = 1` perpendicular loading, the table refers to spacing required for attached members; no oblique-load resolution is claimed. |
| Table 12.5.1D spacing between rows | At `l/D = 6`, the named comparators are 5D = 31.75 mm perpendicular to grain and 1.5D = 9.525 mm parallel to grain. The 93.35 mm pair pitch exceeds both numbers. | The accepted layout/actions do not establish two fastener rows under the NDS row definition. The pair pitch is not a Table D compliance check. |
| §12.5.1.3 outermost-fastener distance | The BG045 pair alone is 93.35 mm across `Y`, 33.65 mm below the 127 mm sawn-member 5 in limit. | This is not the whole-member outermost-fastener check. Other header fasteners and the actual sawn-lumber versus glulam product category are not settled. |

The source profile model records a 0.9980 header and 0.9878 block
actual-to-envelope volume ratio, with cylindrical faces in each STEP solid.
Those summary ratios do not bound the local edge distance at a specific bolt;
the needed profile measurement is a finished-profile query tied to the bolt
center and actual hole/cut geometry.

## Splitting and member-level actions

The accepted demand rows also include simultaneous bolt-axis outer-seat ties.
The full-factor-one tie resultants on the header are `+Z` 107.967338 N
(A1-rear), 139.224710 N (A12-rear), and 38.096890 N (K12-rear), with equal
and opposite forces on the block. In the source header section, the geometric
section center is `z=257.95 mm` and the tie seat is at `z=238.9 mm`, 19.05 mm
below that center. The source signed action is relevant to the possible
perpendicular-to-grain tension mechanism and is retained in the transfer
section actions. The section center is a geometric reference only, not a
verified neutral axis for the finished perforated member.

NDS-2024 Table 12.5.1C footnote 2 addresses heavy/medium concentrated loads
suspended below the neutral axis of a single sawn-lumber or glulam beam and
requires mechanical or equivalent reinforcement for perpendicular-to-grain
tension. The source geometry supplies a below-center tie location and signed
force, but not the NDS heavy/medium load classification, confirmed beam/product
status, local transfer field, or reinforcement detail. NDS §§3.8.2 and 11.1.3
require avoiding or appropriately engineering perpendicular-to-grain tension
and eccentric-connection effects; they do not give a general splitting
resistance equation for this BG045 topology.

The accepted header section resultants close the member-scale equilibrium with
all source-discrete loads and neighboring transfers. They do not produce local
tension-perpendicular stress/strain around the fastener/washer, identify an
admissible split plane, or provide a resistance. NDS Appendix E addresses
closely spaced fastener groups loaded parallel to grain; its net-section and
row tear-out terms use adjusted parallel-to-grain `Ft`/`Fv` and defined net or
critical areas. The block actions are perpendicular to grain and the header
actions are mixed. The record cannot be converted to an Appendix E capacity by
checking `Fx` alone, and no NDS splitting/net-section/shear-out/group DCR is
computed from these forces.

The reusable section reconstruction reports 21 closure checks, 84 segment
wrench comparisons with maximum force and moment differences of zero, and no
splitting demand or resistance. Its three full-factor-one left-segment
resultants immediately after the BG045 transfer are:

| Case | Force `Fx,Fy,Fz` (N) | Bending `My,Mz` (N·mm) | Torsion `Mx` (N·mm) |
|---|---:|---:|---:|
| A1-rear | `−15.141, −91.760, −61.789` | `−4943.877, 1146.033` | `−4354.451` |
| A12-rear | `113.288, 19.796, −135.022` | `2489.099, −2662.251` | `−4592.303` |
| K12-rear | `59.145, 6.130, −26.024` | `−2127.421, −3966.466` | `−1694.568` |

The remaining blockers for a numeric splitting or group check are the actual
bolt diameter/length/center and wood bearing lengths; confirmed main/side
member roles and row layout; finished hole, edge, end, and cut profiles with
tolerances; received product/species/grade/moisture and actual grain; adjusted
design properties and applicable load combination; the NDS heavy/medium load
classification and any reinforcement; and a topology-compatible local
perpendicular-tension/splitting method or supporting test evidence.

## Source basis and reproduction

The official source pins, edition, URLs, digests, and scope notes are in
[`source-pins.json`](source-pins.json). The standard text was taken from the
official [AWC NDS-2024 Chapter 12 PDF](https://awc.org/wp-content/uploads/2026/08/AWC_NDS2024_withCommentary_20250328_WebsiteChapter-12-%E2%80%93-Dowel-type-fasteners.pdf),
[Chapter 3](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240718_AWCWebsite_Chapter-3-Design-Provisions-and-Equations.pdf),
[Chapter 11](https://web-media.awc.org/wp-content/uploads/2021/12/17205958/AWC_NDS2024_20250124_AWCWebsite_Chapter11.pdf),
and [Appendix](https://web-media.awc.org/wp-content/uploads/2021/12/17210019/AWC_NDS2024_withCommentary_20240719_AWCWebsite_Appendix.pdf).
The [current AWC errata](https://awc.org/wp-content/uploads/2026/03/2024-NDS-Errata-and-Addenda-03.23.26.pdf)
was checked for changes to the cited connection requirements. The AWC
[2024 NDS resource page](https://awc.org/resources/2024-nds/) identifies the
edition as the current standard package. The [2018 Commentary](https://awc.org/wp-content/uploads/2021/10/AWC_NDS2018-withCommentary_20200827_AWCWebsite_Commentary.pdf)
is cited only as historical context for the oblique-grain gap.

Reproduce the source hash and numerical checks from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg045-edge-splitting-applicability-attempt02/produce.py
```

The producer is read-only unless invoked with `--write`. It verifies all local
source pins, checks the six full-factor-one signed BG045 action pairs against
the accepted register, checks force balance and geometry identity, and reads
the already independently verified header section resultants. It performs no
CAD query, native run, axis change, or capacity calculation.
