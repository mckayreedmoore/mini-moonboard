# Unguided full-frame contact comparison

Neither run supplies an accepted loaded frame result. MORTAR completed the
solver schedule but failed the unchanged independent moment limit; penalty
reached its bounded runtime before completing gravity. These are diagnostic
results, not evidence of physical safety or instability.

## Matched basis

The frozen original untied `2x8-foot100` timber mesh has 62,020 nodes and
32,511 C3D10 elements. Both formulations use the same geometry, E = 7,000 MPa,
Poisson ratio 0.3, density 600 kg/m³, gravity, and subsequent 1,200 N load
distributed across the original five load nodes. No timber node is restrained.

Each of three floor patches has a separate C3D8 ground brick, 100 mm deep,
extending 100 mm beyond that patch's bounding box on each lateral side.
Only the four bottom nodes of each brick are fixed; its master top nodes
remain free. Ground E = 7,000 MPa and Poisson ratio 0.3 are a controlled
numerical compliance, not measured flooring properties. Contact uses assumed
friction μ = 0.5, normal penalty 10,000 N/mm³ and tangential penalty 100 N/mm³.
Both nonlinear steps use common initial/maximum increments of 0.25, with
automatic cutback permitted. There is no guided seating step or hidden timber
restraint. The only formulation change is penalty versus MORTAR.

## Terminal evidence

| Formulation | Runtime | Terminal solver state | Independent result |
| --- | ---: | --- | --- |
| Penalty | 600.172 s | Bounded timeout; gravity accepted through 50% | Full gravity/load endpoints unavailable |
| MORTAR | 524.121 s | Exit 0; gravity and 1,200 N completed | Gravity passes; loaded moment fails |

The limits remain 0.1 N per force component and 1 Nmm per moment component,
with moments about the original global origin using **deformed coordinates**.
Only noncontact bottom-support reactions are external reactions. Gravity uses
consistent integrated C3D10 nodal volume weights; five applied forces use the
displaced load-node coordinates. Free contact-node RF is not counted again.

| MORTAR endpoint | Maximum absolute force residual | Moment residual (X, Y, Z), Nmm | Maximum timber displacement |
| --- | ---: | --- | ---: |
| Full gravity | 0.00007083 N | (−0.07754, −0.20448, 0.00985) | 0.34218 mm |
| Gravity + 1,200 N | 0.00007083 N | (204.02197, 0.47266, −0.00284) | 1.23018 mm |

Maximum displacement among the five loaded nodes at the rejected final
endpoint is 1.09490 mm. These displacements describe a rejected numerical
solution and must not be used as design deflection predictions. The 300, 600,
and 900 N intermediate load outputs also exceed the moment gate. Raw arithmetic
for every accepted increment, including the partial penalty run, is in
[`report.json`](../fea/results/full_frame_mortar/report.json).

There is no completed matched penalty endpoint for ranking formulations.
The earlier approximately 96 Nmm residual used different ground constraints,
guided preload/release and 0.1 increments; comparing it directly to 204 Nmm
would confound those changes. Coupon-level success has not established
whole-frame loaded equilibrium. Local MORTAR gap/traction/complementarity and
friction-law acceptance remain unvalidated. A horizontal resultant friction
ratio is only approximate when deformable ground tilts or warps.

## Reproducibility and provenance

Separate [penalty](../fea/results/full_frame_mortar/penalty.tar.gz) and
[MORTAR](../fea/results/full_frame_mortar/mortar.tar.gz) archives preserve exact
terminal decks, contexts, DAT/FRD/log/STA/CVG files, launch Python snapshots,
and auxiliary solver outputs. Auxiliary files are retained without claiming
they contain enough state to audit the local weak contact law. Archive and
individual file hashes are recorded in the report.

After launch, the auditor gained an independent mesh-weight reintegration
guard; neither deck nor solver output changed. The separate
[`weight_validation.json`](../fea/results/full_frame_mortar/weight_validation.json)
and `postrun_audit_sources/` identify that updated auditor. A fresh Gmsh 4.12.1
check reproduced all 62,020 weights exactly (maximum difference zero), including
10,140 valid negative weights from the curved quadratic mesh. This check did
not accept the failed loaded moment balance.

Portable archive/hash/global-arithmetic replay (does not repeat integration):

```sh
uv run pytest tests/test_full_frame_mortar_publication.py
```

Fresh independent integration and production rejection replay, from the repo
root with the documented FEA image already built:

```sh
docker run --rm --user 1000:1000 -v "$PWD:/work" mini-moonboard-fea:box-v1 python3 -m fea.results.full_frame_mortar.replay_weight_validation
```

The replay script checks current auditor hashes against the recorded snapshot;
future auditor changes require explicitly restoring or running those snapshots
in an isolated checkout. It does not overwrite results or launch a solver.
The original diagnostic commands were `python3 -m fea.full_frame_mortar
--formulation penalty --max-seconds 600` and the same command with `mortar`.

Next work should qualify the local MORTAR output and use a matched refinement
experiment before any full-frame design inference. No finer-increment trial or
physical design change is included in this milestone.
