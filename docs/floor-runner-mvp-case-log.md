# Floor-runner MVP fresh-case checkpoint

Selected candidate: `compact-floor-flush-development`. This is a partial,
engineer-unreviewed numerical record under the owner's conditional no-slip
floor support assumption, not a fabrication release or climber rating.

| Fresh case | Native contact | Frozen adopted checks | Bolt lateral ratio | Net member ratio | Listed ML24Z maximum | Disposition |
| --- | --- | --- | ---: | ---: | ---: | --- |
| A12 left | Converged after 14 cycles | 36/36 | 0.782215 | 0.682788 | 0.470956 | [Authenticated archive](../fea/results/floor-runner-mvp/a12-left/manifest.json) |
| A12 rear | Converged after 15 cycles | 36/36 | 0.763251 | 0.656642 | 0.516142 | [Authenticated archive](../fea/results/floor-runner-mvp/a12-rear/manifest.json) |
| A12 forward | Repeating active sets after 14, 24 and 10 cycles in three distinct searches | Not assessed; numerical acceptance false | — | — | — | Stop under FR-5 rule; no passing result |

The two accepted archives each contain a compressed native report, exact
geometry, source snapshots, manifest, first-stage checks and a separate
`flush-checks.json` with the frozen criterion inventory. The native result was
validated against hold, load direction, 250 lb load and no-slip formulation
before component assessment. Full-root bolt sensitivity is non-adopted;
partially threaded delivered bolts remain mandatory. The aggregate six-case
authority stays pending. No earlier finite-friction or spliced result was
promoted.

## Exact numerical stop

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

The final states alternate opening/closing several leg/runner face and floor
cells; their near-equal displacements do not justify averaging reactions or
declaring a pass. A targeted numerical-contact remedy must converge the same
physical case and preserve the frozen acceptance criteria before K12/A1 cases
or an aggregate can proceed. This is a solver/contact blocker, not a calculated
member or ML24Z strength failure. Do not turn the old projected-seat scalar
back into a release gate to explain this rejection.
