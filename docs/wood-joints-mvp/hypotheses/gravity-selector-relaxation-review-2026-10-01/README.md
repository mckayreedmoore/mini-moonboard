# Read-only review of the stopped gravity selector

**Checked:** 2026-10-01. **Disposition:** two valid, redundant inequalities
are identified for the mechanics owner's formulation review. No selector,
native solve, optimization fixture or model change was run by this packet.
There is no demonstrated speedup, new equilibrium state or case acceptance.

## Actual stop and inspected formulation

Parent authenticated all thirteen recorded source hashes, the selector input
record and its output pin. The frozen A12 gravity-direction attempt returned
`BUDGET_OR_SOLVER_STOP`, SCIP `timelimit`, zero feasible solutions and
46.823214661 seconds elapsed. This is neither an infeasibility proof nor an
accepted or rejected physical force vector. The second-branch search was not
run. The owner retains readiness, future execution and response validation.

The existing construction method uses PySCIPOpt 6.2.0 / SCIP 10.0.2. The
authenticated projection has 348 bilateral rows, 1,292 unilateral rows and
200 conditional floor-tangent rows. There are 1,840 force/extension pairs and
300 raw rigid-body coordinates. Every unilateral row introduces a binary
variable, including the hundred floor-normal rows. Floor tangents use those
same floor-normal binaries; they are not additional independently selected
masks. All force variables are initially declared without finite bounds.

For each unilateral row with positive stiffness `k`, the method encodes:

| Binary branch | Row requirements | Implication |
| --- | --- | --- |
| Bearing | `q >= 0`, `f = k*q`, `f >= 0` | `f >= 0` and `f >= k*q` |
| Open | `q <= 0`, `f = 0` | `f >= 0` and `f >= k*q` |

Both **`f >= 0`** and **`f >= k*q`** therefore hold for every feasible
integral branch. They can be added as unconditional linear inequalities
without excluding a state admitted by these source laws. They impose no
finite upper force bound, guessed contact mask, stiffness, anchor or gauge.
They must apply only to these positive-stiffness unilateral rows: bilateral
and floor-tangent forces may have either sign.

## Why they may help, and what is unproved

The two inequalities describe the epigraph of `max(0, k*q)`. They are
necessary for the source row but do not enforce equality, select a bearing
state or implement floor history. The indicators and all floor coupling,
compatibility, raw body balance and validation checks must remain.

The upstream [SCIP 10.0.2 indicator implementation and documentation](https://raw.githubusercontent.com/scipopt/scip/v10.0.2/src/scip/cons_indicator.c)
describes a linear inequality with a nonnegative slack and an SOS1 condition
linking that slack to its binary. Ignoring the SOS1/integrality enforcement
allows positive slack to relax the indicated inequality. Thus an
unconditional inequality need not be represented by the initial slack-based
linear relaxation merely because the integral disjunction implies it.
SCIP also performs propagation, preprocessing and separation; the inspected
construction alone does **not** show whether it already derives an equivalent
bound or cut on this particular frame.

Two algebraic relaxation witnesses illustrate the distinction, rather than
an observed SCIP run. With `k = 1`, set the branch binary to `0.5` and relax
its SOS1 enforcement. At `(q,f)=(0,-1)`, all indicated linear inequalities can
be satisfied using nonnegative slacks, but `f >= 0` is false. At `(q,f)=(1,0)`,
the same is possible but `f >= k*q` is false. They are not physical states
and might be removed by actual solver processing. They only establish that
the explicit inequalities can strengthen the elementary relaxation before
such processing.

Accordingly, weak relaxation is a **possible contributor** to the recorded
time limit, not an established cause. No timing, node, presolve-bound or cut
comparison was measured here. Increasing the budget without diagnosis is
not a result of this review. Removing valid source laws or treating an
epigraph point as a physical response is not proposed.

## Bounded handoff to the mechanics owner

If the owner selects this formulation change, use the existing frozen method
fixtures and signed raw-body response adapter to check unchanged admissible
results. Inspect the transformed formulation to determine whether the bounds
are already implied there. Any newly frozen actual-frame comparison must
retain the same source inputs, physical gates and recorded execution budget,
and report construction/presolve/solve time separately, available solutions,
and terminal status. This is a recommendation, not execution authorization or
a queued retry. It does not replace gravity settling, branch-nullspace
identification, capture/release events or six-case validation.

## Inspected record hashes

The following paths are local mechanics-owned packets under
`hypotheses/mvp-acceleration-2026-09-28/`; their publication remains with that
owner. They are recorded as text rather than links to unpublished files.

| Record | SHA-256 |
| --- | --- |
| `current-reduced-coupled-indicator-method-attempt01/method.py` | `953659834d56c1f1614cdc6359afff4e7eb7ca5df70f32e2ed8b1c03050de04c` |
| `current-a12-gravity-direction-selector-attempt01/select_direction.py` | `5ad1e656a10871a53c713702082b0e19d028aff05483cbd1b1e1e86f2471b821` |
| Selector assessment | `fec6e3b0d498439f858bd6c555202c25e4e96eff90d902e95e3fd68e571f4b34` |
| Physical connector projection JSON | `4ceca771e26e1f1d0bf8efca8e3d77dc6d94194553d95e1fd75652ecf2f3f2d3` |

See the [independent review](independent-review.md). This packet changes no
reviewed geometry, historical evidence, physical-work authority or applicable
criterion disposition.
