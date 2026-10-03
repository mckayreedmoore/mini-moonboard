# A12 gravity-direction selection, attempt01

One parent-owned source-bound reduced selection under the shared native-ledger lock; no native solve. Inputs are frozen before constructing the borrowed PySCIPOpt6.2.0/SCIP10.0.2 feasibility model. It retains all 1840 q/f coordinates, all300 raw body rigid coordinates, all source bilateral/unilateral laws and all100 coupled floor cells. No contact mask, finite big-M force bounds or artificial anchors are introduced.

The reviewed source starts at u=f=q=0. Only immediately bearing directional floor cells use the initial event reference zero; all other tangent forces are zero. The source directional coefficient uses unit gravity load columns and may be scaled toward zero; native table bounds apply to physical beta*q during any future finite continuation, not this normalized coefficient.

Budgets are45s for the first feasibility selection and30s for a second floor-episode branch, with180s CPU/wall and6GiB memory caps. Earlier primitive and response replays are required and pinned. Source/output hashes and terminal status are recorded. The original .1N/2Nmm body equilibrium limits are retained. Compatibility and held-reference/released-force audits use2e-8 in their respective units. Floor sign classification uses a conservative2e-8mm directional extension threshold and1e-8N force threshold; a result inside that sign-resolution band is unresolved rather than proof of an exact mathematical zero.

If a strict candidate is found, its selected D rows determine actual branch rank. A nonzero nullity stops for identification/load-compatibility work; this attempt does not remove an arbitrary nullspace. A second candidate or numerical boundary remains unresolved. Only a proven infeasible second floor-branch search can identify a unique strict candidate, and that still does not accept finite gravity settlement or climber loading.

Do not rerun the one-shot producer. See assessment.json for the terminal result when available. Missing state evidence is not physical failure; no accepted load case count, geometry, selected candidate, bolt capacity or physical-work authority changes.

Terminal result: `BUDGET_OR_SOLVER_STOP`, SCIP `timelimit`, zero feasible solutions, elapsed46.823s. Source/output provenance verifies. No candidate force vector, branch nullspace, unique state or infeasibility proof is available. The second-branch search was not run. No automatic retry follows.
