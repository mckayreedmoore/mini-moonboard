# Matched whole-frame MORTAR increment refinement

## Predeclared experiment

Retain the original 0.25-increment experiment and compare two new runs with
initial/maximum increments 0.125 and 0.0625 in **both** nonlinear steps.
Automatic cutbacks remain enabled; the existing 200-increment ceiling stays
unchanged. Each new run has a 1,200-second solver runtime cap and two OpenMP
threads. A timeout is incomplete numerical evidence, not physical failure.

Only the two `*STATIC` increment lines change. The frozen 62,020-node,
32,511-C3D10 original untied 2×8-foot100 timber mesh, materials, gravity,
five-node 1,200 N load, contact slopes, assumed friction 0.5, and three ground
bricks remain identical. Only the twelve noncontact ground-bottom nodes are
restrained; there are no timber restraints. Exact source snapshots, deck,
context, and solver outputs are retained separately for each run. Every
consistent nodal gravity weight is checked against fresh curved-mesh
integration before launching, not merely against total mass.

Comparison quantities are all three external force and moment residual
components at accepted increments, all three bottom-support reaction
components per floor patch, each patch moment about the global origin and its
fixed undeformed bottom-node centroid, and displacement vectors of the
original five loaded nodes. Compare common accepted times; full-gravity and
full-load endpoints are compared only if available. No further increment
trials are authorized by this experiment if these runs are incomplete or
their trends are not stable.
The existing 0.1 N/component and 1 Nmm/component diagnostic gates remain
unchanged. A displacement plateau alone does not override a failed gate.

This experiment tests increment sensitivity, not mesh convergence, actual
floor compliance/friction, joint capacity, or local weak-contact admissibility.
It cannot independently select a construction design or authorize climbing.

The generic CLI permits increments from 0.005 to 1; 0.005 leaves no automatic
cutback headroom within 200 increments. This study uses only 0.125 and 0.0625.

## Terminal results

All three MORTAR schedules completed without timber restraints. The finest
run passes the unchanged **nominal global endpoint diagnostic**. This is a
numerical milestone, not a locally validated contact solution or construction
approval.

| Initial/maximum increment | Solver runtime, s | Accepted increments | Loaded moment residual X/Y/Z, Nmm | Maximum loaded-node displacement, mm |
| --- | ---: | ---: | --- | ---: |
| 0.25, preserved original | 524.121 | 8 | 204.02197 / 0.47266 / −0.00284 | 1.09490 |
| 0.125 | 784.798 | 16 | −1.509560 / 0.217568 / −0.046810 | 1.095748076 |
| 0.0625 | 1156.324 | 32 | −0.047557 / 0.011096 / 0.071317 | 1.095742862 |

The two new runs overlapped in time; runtimes are not a scaling benchmark.

Full-gravity nominal checks pass for all three. The 0.125 loaded endpoint still
fails the nominal 1 Nmm/component gate. Its conservative DAT RF/U printing-only
Mx bound is ±0.604572 Nmm, giving an interval −2.114132 to −0.904988 Nmm: the
small nominal exceedance cannot be resolved against that printing uncertainty.
This does not retroactively pass the run. Bounds exclude input/integration,
floating-point, solver and physical-model errors; they are not confidence
intervals or a replacement acceptance tolerance.

The final 0.0625 loaded force residual is
(−0.000002, 0.000036, −0.00017083) N. The last two maximum loaded-node
displacements differ by 0.000005214 mm. That stable scalar and the reduced
global imbalance support retaining this formulation/increment as the next
diagnostic baseline; neither establishes mesh-independent reactions, local
contact admissibility, or real material/joint capacity. The coarse-to-fine
moment change is not monotonic in sign; no convergence order is claimed.

For the last two full-load endpoints, the largest change in any of the five
displacement **vectors** is 0.000026383 mm. The largest patch force-component
change is 0.003210 N; the largest patch moment-component change about its fixed
bottom centroid is 1.493030 Nmm. These are observed differences, not prescribed
accuracy tolerances. The finest loaded printing-only moment intervals are
entirely inside ±1 Nmm on all axes; that statement still excludes solver/model
uncertainty.

The [raw comparison report](../fea/results/full_frame_refinement/report.json)
contains every accepted-time force/moment vector, every patch's force and
moment (global origin and fixed bottom-centroid reference), all five loaded
node displacement vectors, common accepted times, final-endpoint printing
bounds and exact archive hashes. Patch moments are floor-support resultants,
not forces in particular timber joints. The original 0.25 archive is linked,
not replaced; new archives preserve both exact launch source snapshots.

After launch, generic increment serialization was hardened to retain all
float digits; the actual 0.25/0.125/0.0625 decks are byte-identical apart from
the two predeclared increment lines. The publisher independently binds the
original archive/context/weights to its published fresh-integration witness,
then requires all refinement weights to match exactly.

Replay the archived output arithmetic and provenance without a solver:

```sh
uv run pytest tests/test_full_frame_mortar.py tests/test_full_frame_refinement.py tests/test_full_frame_mortar_publication.py
```

Next use this evidence to resolve the local MORTAR admissibility and actual
unanchored floor-response questions, while developing the joint demand/detail
envelope separately. Do not launch an indefinite sequence of finer increments
or resize timber solely to eliminate a numerical residual.
