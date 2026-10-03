# Front-face load lever: 100 to 50 mm sensitivity

**2026-10-02 — bounded analytical comparison. Complete
joint and physical release remain HOLD.** Reviewed geometry, source frame
evidence, hardware policy and the full 47-criterion authority are preserved.

## Decision and finite scope

Prepare one clearly hypothetical **50 mm front-face force lever** against
the frozen **100 mm** strong-T scenario. Preserve **250 lb × 2 =
2224.110808 N downward**, each case's signed **300 N horizontal** force,
the same hold/20 mm patch, gravity, accessory allowance and connection laws.
All six cases are included. Actual hold contact leverage is unverified;
the comparison does not adopt 50 mm or replace the original requirement.

This worker prepares reproducible load inputs and documents their arithmetic.
The main coordinator owns serialized cached-matrix preparation and the new
compatible frame response. No frame, native or CAD operation is executed
by this worker. Parent operator preparation and all twelve compatible
frame states passed their declared numerical/law gates. This worker
postprocessed the saved results.

The comparison asks whether the assumed hold leverage materially changes
panel screw and corner demands. It does not halve solved screw/bolt forces
or transfer the baseline's passes to a changed load. Signed forces and
compatible contact/clearance response remain necessary.

## Preserved force and changed couple

The [load-origin worksheet](../panel-attachment/load-realism.md) records
the original 100 mm as an illustrative hold-contact lever. It is not a
climber center-of-gravity offset or a measured dynamic bound. Shortening
it changes the force application point while preserving the full force.

Use the saved source coordinates:

```text
c = front-face patch center
p100 = saved force application point
rref = saved wrench reference point
lever100 = p100 - c                         (norm = 100 mm)
p50 = c + 0.5*lever100                     (50 mm from face)
F50 = F100                                (same signed force)
M100_at_ref = (p100-rref) cross F
M50_at_ref = (p50-rref) cross F
delta_M = (p50-p100) cross F
```

The front-face-to-reference offset remains **9.128125 mm**, half the
18.25625 mm panel thickness. Thus the reference-plane lever changes from
109.128125 to **59.128125 mm**. Halving the entire saved reference moment
would incorrectly halve that thickness offset too.

These are input-wrench arithmetic, not individual screw forces or local
bolt bending. The signed moments below use the saved reference and XYZ order:

| Case | Force XYZ, N | Original moment XYZ, N·m | 50 mm moment XYZ, N·m |
| --- | --- | --- | --- |
| A12 rear | [0, +300, -2224.111] | [-164.885, 0, 0] | [-89.339, 0, 0] |
| A12 forward | [0, -300, -2224.111] | [-206.973, 0, 0] | [-112.143, 0, 0] |
| A12 left | [-300, 0, -2224.111] | [-185.929, +21.044, +25.079] | [-100.741, +11.402, +13.588] |
| K12 right | [+300, 0, -2224.111] | [-185.929, -21.044, -25.079] | [-100.741, -11.402, -13.588] |
| K12 rear | [0, +300, -2224.111] | [-164.885, 0, 0] | [-89.339, 0, 0] |
| A1 rear | [0, +300, -2224.111] | [-164.885, 0, 0] | [-89.339, 0, 0] |

The force's outward/in-plane projections do not change. A reduction in
the local applied couple need not reduce every individual joint demand,
because contact, prying and load sharing can change.

## Reused mapping and fixed mechanical operators

The producer reuses [load_components.py](load_components.py)'s pure saved
S8 uniform-square mapping and
[traction_wrench](../../../../../fea/horizontal_panel_frame.py). Corner
weights are -1/12 and midside weights +1/3. Negative corner coefficients
are consistent quadratic nodal-load weights; they do not describe physical
tension pressure on the climbing surface. The nodal couple is distributed
on the same eight source nodes to reproduce the declared force and moment.

The current strong-T [operator packet](operators-attempt02/operator-assessment.json)
has H 1888×1888, D 1888×300, e 1888×12, W 300×12 and F 37647×12.
Its twelve columns are gravity/live pairs for the six retained cases.
Only the six live columns of **F, e and W** and associated load metadata
may change. H, D, every gravity column, B, row identities, geometry,
axes, connections, contact footprints, material binding and laws remain
unchanged.

The original nodal maps and F/e/W are first reproduced against the frozen
source. The original and target elastic load responses use only the three
loaded panel blocks of the pinned baseline K and the existing bordered
quotient gauge. No new stiffness matrix, mesh, CAD scene or native solver
is generated. In each panel's gauge:

```text
elastic_delta_F = delta_F - Q*(Q^T*delta_F)
delta_u = existing bordered quotient solve(Kpanel, R, elastic_delta_F)
e50 = e100 + B*delta_u
W50 = W100 + R^T*delta_F
F50_nodes = F100_nodes + (target_mapped_nodes - original_mapped_nodes)
```

The saved originals are retained as the base of each delta update, avoiding
a change in their prior rounding residuals. Reproduction tolerances retain
the source method's limits: original nodal/F error below 1e-5 N, e below
1e-8 mm and scaled W below 1e-7 N. New local/global wrench checks and
unchanged-array/file receipts are saved; a preparation stop remains a
numerical stop, not a mechanical failure.

## Readiness and result receipts

The frozen producer passed parent execution with status
`PASS_UPDATED_ELASTIC_FRAME_OPERATORS`. Static method inspection is
complete and Ruff passes. No software tests, operator preparation or
frame run were executed by this worker. After parent preparation, this
worker independently authenticated all **110 source pins and 10 output
pins** by reading saved files; the mechanical calculation was not rerun.

| Original-response reproduction | Returned error | Retained strict limit |
| --- | ---: | ---: |
| Saved original nodal map | 0 N | 1e-5 N |
| Original live F columns | 1.819e-12 N | 1e-5 N |
| Original elastic e columns | 2.403e-9 mm | 1e-8 mm |
| Original scaled W columns | 0 N | 1e-7 N |

All three loaded panel quotient calculations passed their unchanged
gates after one bounded correction each. Maximum relative projected
elastic-force residual was 7.10e-12; maximum gauge residual was
9.24e-14 mm. H/D, gravity columns, B/row identities, geometry and
connections retain their source fingerprints. These checks establish
load preparation and reuse, not joint resistance.

Producer SHA256: `b9aa2d327f88e51dcd5990811153fa7ba51f84f8485f507e01062fa2ad00830f`.
The main coordinator ran, from the repository root:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/load-lever.py \
  --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/load-lever/operators-attempt01
```

After successful preparation, parent launched the existing `conic_frame.py`
entry point with `--operators` selecting that packet and `--output` selecting
`rawlocal/load-lever/frame-attempt01`. The new assessment declares the
honest `declared_front_face_force_lever/v1` schema and records the original
schema as provenance. Parent owns any targeted schema support in later
joint postprocessors; this packet does not masquerade as the original
layout producer.

The original 100 mm operator/response packets remain preserved. Outputs
belong only under ignored `rawlocal/load-lever/`; no new input replaces
the selected authority or the original force source.

| Frozen source | SHA256 |
| --- | --- |
| `load_components.py` | `3e7152b5e035e702178a08327df94353e5d77066fba623de71ac9bc05acfd3b8` |
| `operators-attempt02/operators.npz` | `c9483639c69c0696b29f3fd69522e6c9a8e673aa7ce82277788103b14c955ba3` |
| `operators-attempt02/operator-assessment.json` | `1a82cd2adbfece3942bf8c90f593f1e21a150adb65db625135aadd258fd5024a` |
| `operators-attempt02/model-inputs.json` | `e2109cabed9fcbc0a14346ef63b707abb1aed358ebf5fa126b2cba216aa771cc` |
| `frame-250-attempt02/comparison.json` | `bea6cbc330af3cdb20499d774a8f6bb24481d687c3150adb01ede18e4c1d50ca` |
| `frame-250-attempt02/response.npz` | `0625196497b0dbc7b297724d7b9947f7c7c61bb282cd4d9681705629302c76c7` |
| `rawlocal/load-lever/operators-attempt01/receipt.json` | `d98e5a037fd796f20a5a475519e367d55e35f795a3a4dcfaef36d604a70ee2e5` |
| `rawlocal/load-lever/operators-attempt01/operator-assessment.json` | `f1a30a6af71ba82b394462b70288c1cdc5112ae79e684d91897eadd09c43d85c` |
| `rawlocal/load-lever/operators-attempt01/operators.npz` | `0dfc77e66e4fb42db9eff380e41ecefd843a440d6e50d9a7f6b5446bf9eabe7c` |
| `rawlocal/load-lever/frame-attempt01/comparison.json` | `bcadee52af205a364d2a39a03fc9013fbff350ae73b8d68765ea80e20ead419c` |
| `rawlocal/load-lever/frame-attempt01/response.npz` | `17ef2c6c9d2e2fffa5c00a19c976b92e25e0a52d9c2a770b2f927804a2882604` |
| `rawlocal/load-lever/worksheet.py` | `0b67f0c068cf245ca76e749c68e69011bce42476e59532fa0932a36b383b1737` |
| `rawlocal/load-lever/worksheet.json` | `4d566e9ae5b4d6bc1585a39301df5085311ae2b18f8b46f2f8d037069d4eb1b4` |

## Returned comparison

All six zero-clearance cases returned
`PASS_CONDITIONAL_COUPLED_FRAME_LAWS`; all six nominal-clearance cases
returned `PASS_CONDITIONAL_LAWS_WITH_BOUNDED_SEATING`. No states are
missing. Maximum returned force balance residual is 1.05e-11 N,
moment residual 5.52e-9 N·mm, finite-law error 2.81e-7 N and circular-gap
law error 4.56e-9 N. These are declared model-law results, not product
qualification or whole-joint acceptance.

The ignored worksheet authenticates both comparisons and their bound
responses, prepared artifacts and producer hash. It checks unchanged mass,
load factors, panel screw laws, clearance planes and floor footprints.
The six saved clearance-joint identities, bolt axes, receiver identities
and common block datums are retained. It reads summaries only and performs
no mechanics solve. Reproduce it with:

```bash
python3 docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/load-lever/worksheet.py
```

The script requires a fresh `worksheet.json` destination. Preserve the
existing receipt before a deliberate postprocessing rerun.

### Same-case nominal-clearance demands

Each cell gives **100 mm → 50 mm**, in N. Bolt columns cover the six saved
clearance joints. Individual column peaks need not occur on the same bolt.

| Case | Hillman lateral | Hillman withdrawal/head demand | Bolt lateral | Bolt tension |
| --- | ---: | ---: | ---: | ---: |
| A12 rear | 1244.3 → 1126.5 | 1871.3 → 1707.6 | 961.5 → 906.8 | 642.8 → 604.8 |
| A12 forward | 1051.7 → 907.0 | 1513.8 → 1307.3 | 804.7 → 733.3 | 541.0 → 489.5 |
| A12 left | 1105.2 → 979.0 | 1810.4 → 1570.5 | 975.1 → 876.8 | 660.7 → 590.0 |
| K12 right | 1046.6 → 947.0 | 1530.1 → 1337.3 | 1097.6 → 989.5 | 757.3 → 679.2 |
| K12 rear | 1214.7 → 1115.2 | 1603.4 → 1462.5 | 1098.8 → 1033.5 | 744.1 → 699.4 |
| A1 rear | 487.5 → 403.2 | 987.4 → 768.7 | 243.4 → 172.6 | 176.6 → 126.6 |

Nominal peak Hillman withdrawal/head demand remains at
`round_panel_upper_left_edge_2`, A12 rear: **1871.251 → 1707.613 N**,
an **8.745% reduction**. Peak lateral remains at
`round_panel_upper_left_rim_4`, A12 rear: **1244.301 → 1126.477 N**,
a **9.469% reduction**. These are axial/lateral demands, not assigned
Hillman resistances.

Among the six clearance joints, peak nominal bolt lateral changes
**1098.757 → 1033.543 N** (-5.935%), both K12 rear/right `side_2`.
Peak tension changes **757.336 N**, K12 right/right `rail_1`, to
**699.356 N**, K12 rear/right `rail_1` (-7.656%); the governing case moves.
Peak receiver force magnitude changes **1100.310 → 1034.750 N** (-5.958%).
Peak common-block-datum receiver moment magnitude changes
**39.074 → 35.566 N·m** (-8.977%), moving from K12 right to K12 rear.
Both receiver witnesses are the right cleat/`base_side_right` interface.
These moments are receiver wrenches, not local bolt bending.

Every reported same-case peak decreases, but individual forces can grow.
For example, K12 rear/bottom-right `side_1` tension rises
**5.361 → 7.561 N**. A1 rear's peak Hillman lateral witness also moves
from the lower-panel rim to `round_kicker_left_rim_1`. The worksheet retains
these identities and all saved per-axis/wrench demands.

The six zero-clearance cases are retained separately in the worksheet.
Their global Hillman lateral peak changes **1086.577 → 982.256 N**
(-9.601%; governing case moves from A12 rear to K12 rear), and axial peak
changes **1923.816 → 1760.281 N** (-8.501%; A12 rear). Their maximum saved
bolt lateral/tension changes **1500.285 → 1425.071 N** and
**353.486 → 333.736 N**. These reference cases are not substituted for
nominal-clearance results.

## Interpretation and next decision

**Robust within this frozen comparison:** shortening the lever lowers
the returned peak demands, but the approximately 46% local applied-couple
reduction produces only approximately **5–10% reductions in governing
nominal screw/bolt/receiver peaks**. The unchanged force, frame geometry
and compatible sharing still drive substantial demand. This sensitivity
does not provide a large margin by itself.

**Assumption-dependent:** the quantitative values depend on the hypothetical
50 mm lever, preserved panel elastic properties, explicitly unqualified
Hillman stiffness, clearance/contact laws and no-slip floor assumption.
The 1707.613 N nominal screw axial demand establishes no actual Hillman
head pull-through or withdrawal resistance. Saved local washer results
retain their original forces; this frame comparison does not update
washer stress or establish that a washer deficiency is resolved.

**Next useful check:** finish the existing combined block/bolt/timber
resistance screen against the preserved 100 mm scenario. Retain this
50 mm packet as sensitivity evidence. The actual intended hold-contact
lever determines whether its reduced demands can support a later adopted
load envelope; parent is already obtaining that information. No further
lever sweep is needed for this finite decision. All joint and release
HOLD boundaries remain unchanged.
