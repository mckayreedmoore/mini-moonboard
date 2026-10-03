# Header local transfer: signed input contract

**2026-10-02 — preparation only. Complete joint and physical release remain
HOLD.** This packet addresses remaining duty H for the six current header
connections. It preserves the original **100 mm**, strong-T, six-case
250 lb × 2 / signed 300 N scenario, reviewed geometry, hardware policy and
the full 47-criterion authority. The completed 50 mm lever sensitivity is
separate and remains frozen.

## Finite decision

The existing [header replay](header-replay.md) contains the necessary signed
actions and finished geometry. The missing result is **local transfer around
the paired through-holes under simultaneous normal force, shear and torque**,
followed by an applicable resistance check. Individual bolt references,
face/washer mean pressure, Ceg/Cg sensitivities and connected-section proxies
are completed evidence. They supply no accepted force split among disconnected
ligaments or local splitting/torque interaction.

The [producer](header-local-transfer.py) prepares that input contract from
saved JSON/CSV/NPZ records. It restores existing point actions and copies
geometry, orientation and reference evidence. It imports no mechanics helper
and performs no stress, contact, section, stiffness or frame calculation.
Parent owns method readiness and any subsequent execution. Preparation does
not establish native readiness or resistance.
The source's fixed-force seating and nonunique-pose limits remain; these
actions establish no new interface motion envelope.

## Actual duties and actions

The header grain is **global X**. Its gross section is Y = **139.7 mm**,
Z = **38.1 mm**, with length **2435.225 mm**. All six blocks have grain
**global Z**. The frozen R/T material axes retain the source transverse
orientation scenario; the geometric Y/Z section axes are not substituted
for those material axes.

| Header duty / block | Two header axes | Y pitch | Finished bore radius |
| --- | --- | ---: | ---: |
| Center post left | `center_post_header_left_1`, `_2` | 35 mm | 3.65 mm |
| Center post right | `center_post_header_right_1`, `_2` | 35 mm | 3.65 mm |
| Center principal left | `center_principal_header_left_1`, `_2` | 65 mm | 3.65 mm |
| Center principal right | `center_principal_header_right_1`, `_2` | 65 mm | 3.65 mm |
| Inner knee left | `knee_outer_left_inner_header_1`, `_2` | 93.35 mm | 3.75 mm |
| Inner knee right | `knee_outer_right_inner_header_1`, `_2` | 93.35 mm | 3.75 mm |

Axis directions, shaft centers, saved interface action points and finished bore
bindings are retained separately. A shaft center is not the force application
point. The twelve selected axes remain modeled quarter-inch bolts; no
delivered shank or new hardware capacity is established here.

Of the **72 saved bolt states**, only two lateral forces exceed 1e-7 N:

| Case / axis | Signed lateral force on block XYZ, N | Simultaneous tie, N |
| --- | --- | ---: |
| A12 left / `center_principal_header_left_2` | [+26.3921, approximately 0, approximately 0] | 18.8707 |
| K12 right / `center_principal_header_right_2` | [-29.8867, approximately 0, approximately 0] | 20.7480 |

These forces are along header grain X. The other seventy states retain their
saved small numerical forces and null first-ray diagnostics. All 36 pair
direction diagnostics remain undefined because a resultant or an individual
bolt direction is zero. The completed two-fastener Cg sensitivity supplies
no inferred equal sharing or new acceptance of the combined group.

The normal/twist actions are larger. About each saved interface datum, the
governing left-knee A12-rear wrench on the block includes
**Fz = -298.704 N, Mx = -8.434 N·m**. The right-knee K12-rear wrench includes
**Fz = -291.019 N, Mx = -8.504 N·m**. In each of these states the bolt ties
supply the entire normal force and X couple; all four face-contact forces
are zero. Their opposite header actions must be retained at the same datum.
These are group wrenches, not bending moments assigned to individual bolts.

## Finished ligaments and concurrent header loading

The saved header has 22 cylindrical finished features, including the twelve
header bolt bores and other existing openings. All those features are retained.
Six saved section planes through the paired bores have **three disconnected
Y/Z ligaments**. Their **72 case/trace rows** retain null normal and shear
references; no common strain or force allocation is supplied.

| Saved disconnected header plane | Station from header start |
| --- | ---: |
| `base_header:section:2d69ffdf7163d5db` | 133.35 mm |
| `base_header:section:f7ae23a71b2b45df` | 993.49 mm |
| `base_header:section:cbb798b352fe0eb8` | 1103.20 mm |
| `base_header:section:babb38b034c22504` | 1335.20 mm |
| `base_header:section:b2bc8028d24db3ff` | 1443.55 mm |
| `base_header:section:91b7a2e2788bd266` | 2301.875 mm |

The largest saved absolute torque among these disconnected-section rows is
**12.768 N·m**, A1 rear, left-knee plane at 133.35 mm, after trace. Its
simultaneous centroid vector is:

```text
[N, VY, VZ, T, MY, MZ]
[-3.319134 N, +151.378204 N, -155.117256 N,
 -12768.261359 N mm, +8240.562206 N mm, -12998.207201 N mm]
```

The existing connection-zone Y diagnostic reaches **159.964 N**, K12 rear
at the center-post-right paired-bore plane. This is a scoped section/zone
action, not the net Y force of the header bolts or a transverse-tension
stress. It is not the maximum over every header section. Preserve the saved
section vector and its simultaneous moments.

The existing whole-header torque witness is **29.333 N·m**, A1 rear at
22.225 mm, outside the twelve header bolt center planes. Its simultaneous
Z shear is **1048.584 N**. Other header supports, panel/kicker connections,
contact patches and body loads contribute to the header actions. A local
bolt-pair wrench alone cannot reproduce this loading.

## Prepared model contract

The output contains the following source-bound data. It is an input inventory
for a subsequent method, not an executable mechanical model.

| Data | Required retention |
| --- | --- |
| Seven timber bodies | Header plus the six blocks, exact finished STEP bindings, surface features, bore/passage intervals, profile planes and frozen L/R/T axes. |
| Twelve header axes | Exact current connection records, receiver identities, shaft direction/center and matched finished bore geometry. |
| Seventy-two axis states | Original lateral vectors, separate signed ties, raw row identities and completed references. |
| Thirty-six header interfaces | Original ten block-side point actions, the ten corresponding saved header-side actions, full signed role wrenches and their common datum. |
| Six whole-header action sets | All 394 source actions per case, including concurrent connections, contacts and discrete body loads. |
| Contact evidence | Saved cell areas/normal/point and globally indexed source patches, with exact patch boundaries and member ownership. |
| Completed sections | Byte copy of the 1260-row header CSV and source metadata for all 105 matching planes; disconnected/null fields remain unchanged. |
| Raw rows and laws | Current ownership, directions, force conventions and laws for referenced action/state rows. No law is retuned. |

For a future transfer method, apply each action once. Use the role and
interface resultants to audit the point loads. Retain free couples and
source positions, including the separate normal ties; the saved lateral
vectors alone do not describe the full interface.

Those points are the source spring/action representation. For example, a
center-post tie uses the shared analytical point at Z = 277 mm on both bodies.
It is not a measured bearing-face location. A future traction mapping must
locate the supported physical seats/patches and preserve the full wrench.
Cell areas, points and whole-patch boundaries do not establish a unique local
pressure field; that spreading assumption must be declared by the method.

Wrenches use XYZ order and `[Fx,Fy,Fz,Mx,My,Mz]`, in N and N·mm. At another
datum B, transform the wrench reported at A with:

```text
F_at_B = F_at_A
M_at_B = M_at_A + (A-B) cross F_at_A
```

The source field `pair/lateral_wrench_about_body_datum` uses the supplied
interface-pair datum despite its name. Its datum must remain explicit.
Original whole-body balances and interface reciprocity are preserved evidence.

If a subsequent method crops the header, it must declare both boundary
section wrenches, their half-body sign conventions and every intersected
contact footprint. Existing boundary cuts are point-action equilibrium;
they establish no integrated local traction. The full-header inventory
avoids silently omitting those contributions without requiring a new
whole-frame solve.

## Resistance basis and method limits

Reuse the primary NDS constraints already recorded in
[block-group-resistance.md](block-group-resistance.md). NDS §11.1.2 requires
member checks and local multiple-fastener stresses to follow engineering
mechanics; §11.1.3 requires an appropriate procedure where an eccentric
connection induces transverse tension. These requirements do not supply a
numerical sawn-lumber tensile-perpendicular allowable. See the pinned
[AWC NDS 2024 Chapter 11](https://awc.org/wp-content/uploads/2026/09/AWC_NDS2024_withCommentary_20260911_Website_Chapter-11-Mechanical-Connections.pdf),
pp.70–71. The cached primary PDF/extract is preserved in the existing group
packet; this preparation introduces no alternative resistance standard.

The source F90 values remain **characteristic diagnostics**, with design
resistance unestablished. Their small ratio cannot qualify normal-force,
hole-ligament or torque transfer. The preserved parallel-grain lateral
component references also do not cover the normal Z actions and moments.
An external couple alone establishes no actual tensile-perpendicular
stress; the transfer method must establish the stress/load-path mechanism
before a resistance comparison is selected.

The decisive missing facts are therefore a justified **load-spreading and
ligament-sharing procedure for this finished section**, and its applicable
**combined local shear/normal/splitting resistance basis**. No source force
resultant, bore location or grain direction is missing. This packet assigns
no Ft-perpendicular or converted F90 design value. It adds no physical test,
external sign-off, geometry change or stiffness sweep as a prerequisite.

## Readiness, reproduction and next step

The producer is frozen at SHA256
`4118f6462a66386f4a8986edca6a2d8a00a8518b9eb33601d3d2236c6ad579a3`.
Static source inspection and targeted Ruff are complete. No producer execution,
software tests or mechanics were performed by this worker. Parent preparation
completed with exit 0 and status
`PREPARED_HEADER_INPUT_CONTRACT_FOR_METHOD_SELECTION`. From the repository root,
parent ran:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/header-local-transfer.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/header-local-transfer/attempt01
```

The producer requires a fresh child of the owned raw folder. It authenticates
direct consumed artifacts and seven finished STEP bindings before and after
the join, saves an immutable snapshot and receipt, and retains inherited
mutable producer hashes as provenance. A preparation stop establishes no
mechanical failure. Successful extraction still leaves native readiness,
mechanical execution and new resistance flags false.

| Frozen direct input | SHA256 |
| --- | --- |
| Original `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| Original `frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| Header replay `joint-actions.json` | `2a37efc475fce1e6eb65b23a8e7fd7b0e8bbdd3be3af9f3f41df0620a262452f` |
| Header replay `joint-states.json` | `be78ec533e93963ab900103d107e391b57a1d52125025e47eb06a37f16ef6232` |
| Header replay `header-sections.csv` | `f32ab4731eb4cb12fbdc400f81a0fb9ba8d8065eabbccc378483ecd0b36e5953` |
| Member `geometry.json` | `c61139087fac34e8094f2336f15dd6de5c0112d26d37b9535526f47332f453af` |
| Member `action-section-arrays.npz` | `ddfa310266661ea5ba6e188d2bf473121d99158d50921c84760744519e2a7caf` |
| Finished-feature `surfaces.json` | `33fff67eee4bc4e96ccef5703f6eebd0d4e004541c6114a4b1da4a5332b2f6eb` |

After parent execution, this worker independently authenticated all **26
direct source pins and six output pins**, without rerunning the producer.
The prepared packet contains seven bodies, six cases, twelve axes, 72 axis
states, 36 interfaces with ten actions on each receiver, 394 whole-header
actions per case, 105 section planes, 1260 section states, six disconnected
planes, 242 referenced raw rows and 140 contact cells. The section CSV is
byte-identical to the completed source.

All five boundary flags remain false: native readiness, mechanics executed,
new resistance established, complete joint acceptance and physical release.
Source/output pins are in the immutable
[receipt](rawlocal/header-local-transfer/attempt01/receipt.json) and
[source register](rawlocal/header-local-transfer/attempt01/source-pins.json).

| Prepared artifact | SHA256 |
| --- | --- |
| `model.json` | `eae4fc005cdd079f90f527be611e45a137aa275b129e16eebf964c422d69ae52` |
| `inputs.json` | `cccd8969132c30e996fe5d3509069dbe851720786cec92a46a064cc0f7c0758b` |
| `header-sections.csv` | `f32ab4731eb4cb12fbdc400f81a0fb9ba8d8065eabbccc378483ecd0b36e5953` |
| `receipt.json` | `3b3afc6924dee426c4f0073077e119d906efddcb5ed03a683ec4a3f16fc189a8` |
| `source-pins.json` | `db488dbda8fdb7dcb82dcc42de015f584bd61a961b160107b5bb515d5c92f139` |

Only `header-local-transfer.py`, this note and ignored
`rawlocal/header-local-transfer/` belong to this task. Parent owns shared
consumers, execution, integration and publication. All earlier evidence,
completed component/reference checks and release flags remain preserved.

The next bounded local study should use **A1 rear / left-knee paired-bore
plane, 133.35 mm, after trace**, as the existing largest disconnected-section
torque witness. Keep its simultaneous six signed section actions and all
concurrent header loads. Establish force transfer among its three ligaments
before selecting an interaction or splitting resistance. The other saved
six-case inputs remain available without another frame run. This is a method
proposal; no local mechanics run is authorized by this preparation.
