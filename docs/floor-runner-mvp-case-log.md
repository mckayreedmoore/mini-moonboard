# Floor-runner MVP six-case record

Selected candidate: `compact-floor-flush-development`. All six current,
engineer-unreviewed cases use the owner's conditional no-slip floor support
assumption. This is not a fabrication release or climber rating.

| Fresh case | Native contact | Frozen adopted checks | Bolt lateral ratio | Net member ratio | Listed ML24Z maximum | Disposition |
| --- | --- | --- | ---: | ---: | ---: | --- |
| A12 left | Converged after 14 cycles | 36/36 | 0.782215 | 0.682788 | 0.470956 | [Authenticated archive](../fea/results/floor-runner-mvp/a12-left/manifest.json) |
| A12 rear | Converged after 15 cycles | 36/36 | 0.763251 | 0.656642 | 0.516142 | [Authenticated archive](../fea/results/floor-runner-mvp/a12-rear/manifest.json) |
| A12 forward | Converged after 69 cycles | 36/36 | 0.754919 | 0.537592 | 0.413041 | [Authenticated archive](../fea/results/floor-runner-mvp/a12-forward/manifest.json) |
| K12 right | Converged after 13 cycles | 36/36 | 0.768869 | 0.677095 | 0.516174 | [Authenticated archive](../fea/results/floor-runner-mvp/k12-right/manifest.json) |
| K12 rear | Converged after 10 cycles | 36/36 | 0.754388 | 0.648895 | 0.569078 | [Authenticated archive](../fea/results/floor-runner-mvp/k12-rear/manifest.json) |
| A1 rear | Converged after 12 cycles | 36/36 | 0.128982 | 0.211091 | 0.286071 | [Authenticated archive](../fea/results/floor-runner-mvp/a1-rear/manifest.json) |

All six archives contain a compressed native report, exact
geometry, source snapshots, manifest, first-stage checks and a separate
`flush-checks.json` with the frozen criterion inventory. The native result was
validated against hold, load direction, 250 lb load and no-slip formulation
before component assessment. Full-root bolt sensitivity is non-adopted;
partially threaded delivered bolts remain mandatory. The [authenticated
aggregate](floor-runner-mvp-evidence.json) governs the selected case set; the
[24-angle demand ledger](floor-runner-mvp-angle-demands.json) records the
catalog-unlisted actions without assigning them a capacity. No earlier
finite-friction or spliced result was promoted.

## Numerical-search history

All three A12-forward searches used the same selected geometry and physical
no-slip law. Native global equilibrium, member equilibrium and MPC checks were
true on the final reported iteration, but the compression-only contact active
set did not converge. The rejected reports remain in local ignored native
directories for numerical diagnosis:

| Search | Local native directory | Search variation | Cycles | Final report SHA-256 |
| --- | --- | --- | ---: | --- |
| 01 | `fea/generated/floor-runner-mvp-a12-forward-01/` | Full active-set updates from closed initial contacts | 14 | `003652fbeeaf5f3db782b7fc88f01da1e13c2d0944f430441e1b1d58cbe19d7e` |
| 02 | `fea/generated/floor-runner-mvp-a12-forward-02/` | One floor-cell change per body per update | 24 | `eccbb359379f0859b723a5232c1f47e13671bb0ada19f3fb3ab8d7c5056ca8c9` |
| 03 | `fea/generated/floor-runner-mvp-a12-forward-03/` | Accepted A12-left contact set used only as an initialization seed | 10 | `4bdd1b30fbdba5cce77b029f180df15aac18faa13fef6904e29c469fff9ccc3c` |

Those rejected states alternated opening/closing leg/runner face and floor
cells, with violations much larger than printed-coordinate tolerance. A fourth
search used one normal-contact pivot per iteration while retaining the same
geometry, loads, no-slip contact law and final compression-only acceptance
gate. It converged in 69 native cycles and passed all 36 frozen checks.
The three rejected responses remain diagnostic only; the accepted fourth
response alone supplies A12-forward force evidence. Do not turn the old
projected-seat scalar back into a release gate.
