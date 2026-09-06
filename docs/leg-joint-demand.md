# Retained baseline aggregate leg-joint demand

`fea/leg_joint_demand.py` recovers the total force and moment transferred by
each original bonded leg to its rim. It reads the exact archived 0.0625
increment run, authenticates its deck and outputs, and runs no new FEA solve.
This is an aggregate demand bridge for subsequent connection experiments,
not a bolt force, ply sharing, candidate result or resistance check.

Whole C3D10 elements outside the rim's X boundary identify each leg. Every one
of their ten nodes must remain within that leg's thickness and actual undrilled
CAD profile. Shared nodes must lie on the rim interface; the selected leg must
own its complete floor patch and contain none of the climber load nodes.
The CAD sources recorded by the original archive must match. Current geometry
dependencies are additionally snapshotted; the historical source manifest is
not represented as a complete historical dependency closure.

The existing Gmsh volume integrator reintegrates each selected element set.
It retains signed quadratic consistent nodal weights and checks total volume
within 0.1% and centre of volume within 1 mm of CAD. It never partitions the
full frame's nodal weights by node coordinates. These geometric diagnostics
do not bound physical or numerical model uncertainty.

The massless static ground brick transmits its noncontact bottom support
resultant to the leg. Adding the leg's gravity gives **leg-on-rim** force and
moment; the opposite sign is rim-on-leg. Gravity moments use accepted deformed
timber positions. The fixed reference is the mean four upper bolt Y/Z location
on the undeformed rim/leg interface. Components are also resolved into global
X, uphill S and board-normal N, a right-handed orthonormal basis.

All accepted increments are reported with their existing global diagnostic
status. This is equilibrium recovery, not an independent check of interface
traction. Local contact acceptance remains separate. Printed DAT precision,
generic material assumptions, bonded interfaces and baseline load history
remain limitations. Do not scale these nonlinear results to another climber
weight or distribute them equally among four bolts or two plies.

Run focused checks, then the extraction from the repository root:

```sh
uv run pytest -q tests/test_leg_joint_demand.py
uv run python -m fea.leg_joint_demand
```

The extraction uses the existing immutable `box-v1` Docker image by digest
only for Gmsh integration, with no network and a read-only container root.
Each run creates a unique `fea/generated/leg-joint-demand-*` directory with
source snapshots, authenticated input/element ownership, integrated weights,
execution log and a report. Existing results are never overwritten.

## First retained-output extraction

The completed local extraction is
`fea/generated/leg-joint-demand-iwk1l84z`, using Gmsh 4.12.1 in image
`sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646`.
Both legs contain 968 C3D10 elements, 2147 nodes and 179 shared rim-interface
nodes. Their integrated volume differs from CAD by 0.0000644%; their centre
differs by 0.000408 mm. Each leg retains 394 negative consistent nodal weights.

At the gravity-plus-1200-N endpoint, forces and moments **exerted by the leg
on the rim** are:

| Side | FX, N | FS, N | FN, N | MX, N·m | MS, N·m | MN, N·m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Left | 5.244 | 775.788 | 850.979 | 137.861 | 10.921 | -11.864 |
| Right | -4.469 | 735.946 | 819.167 | 120.323 | -10.868 | 11.400 |

These moments use fixed world references
`(-1257.3, 991.349642, 1571.139334)` and
`(1257.3, 991.349642, 1571.139334)` mm. The local X/S/N basis is identical
on both sides; X points globally right and is not mirrored outwards.
The opposite signs give the load applied by the rim to the leg subassembly.
The result supplies an aggregate conditional target, not an equal four-bolt
distribution or the candidate's actual load allocation.

The report retains all 32 accepted increments. The original global diagnostic
passes at time 1 and 2, but fails at seven intermediate accepted times:
1.0625, 1.125, 1.1875, 1.25, 1.3125, 1.75 and 1.8125. Those rows remain
explicitly flagged and must not be presented as qualified demand cases.
Even the passing endpoints remain conditional on the original contact model;
this extraction does not settle its local contact audit.

SHA-256 identities:

| Artifact | SHA-256 |
| --- | --- |
| Original `0.0625.tar.gz` | `b7191366c224835aa6f790996671cc491ad3ae878cb9b797698a04d45e0b373b` |
| Extraction `input.json` | `9213c757c25fa44a724d94d555c66e6ab2bcdf8880a09a59679fd525622277a1` |
| Extraction `integration.json` | `98d072fdc9637c58294a48bda6e6a2b62ac52ff059e8ca18d3293c076f5c7c64` |
| Extraction `report.json` | `6c09595cccfb5f58e44a3f20035fd60c41f82d6a0a702b85f4ac83a4b8c06c49` |

The first attempt, `fea/generated/leg-joint-demand-oqh1pq63`, is retained
as a failed container-launch record: it invoked unavailable `python` and
never integrated or solved. The successful run uses `python3`. Four focused
tests and Ruff checks passed before the successful extraction.

The [portable evidence publication](../fea/results/leg_joint_demand/README.md)
now preserves both directories as separate archives. The additional offline
regression authenticates the successful archive, original frame archive, all
retained source snapshots, input, integrated weights, log and report. It then
uses the production `assemble_endpoints()` helper to reproduce every value
in all 32 rows, including both legs' five six-component force/moment vectors
and all seven failed diagnostic flags. Deleting a node from the first accepted
timber displacement block must fail the production coverage check.

This later refactor and test do not replace the original launch-source
snapshot or imply another integration. The test reads archives through the
standard library and requires neither Docker, Gmsh nor CAD construction.
