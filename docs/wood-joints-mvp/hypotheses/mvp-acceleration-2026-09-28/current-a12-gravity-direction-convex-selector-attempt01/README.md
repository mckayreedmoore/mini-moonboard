# Bounded A12 gravity-direction convex selector

This parent-owned one-shot application uses the reviewed initial-condition
contract and the passing tiny floor-binary energy fixture. Its engineering
result is a candidate initial gravity direction, or an exact recorded reason
why no usable candidate was obtained. It does not authorize a native solve or
adopt a gravity-settle/climber-ramp response.

The frozen attempt04 operator retains all 50 bodies, separate gravity and
climber columns and raw body wrenches. The elastic energy uses the explicit
numerical approximation Hsym=(H+H.T)/2 and its independently checked factor.
Raw H remains the compatibility audit operator. Bilateral spring energy and
ordinary unilateral hinges are continuous; only the 100 coupled floor cells
have binaries. No contact mask, tangent reference offset, floor anchor,
finite displacement bound or physical history is chosen by energy ranking.

Execution is serialized under the existing ledger lock, with one BLAS thread,
6 GiB memory and 180 s process wall/CPU caps. The first SCIP search is limited
to 45 s. Only an audited strict candidate permits a second, 30 s search that
excludes its floor mask to check for a competing branch. Solver statistics
and logs are retained. The wrapper freezes source hashes before execution
and rejects any change during it.

SCIP forces are provisional, recovered as g=L^-T*y. Raw body force/moment,
raw-H compatibility, original spring laws, held references, released tangent
forces, strict normal signs and actual branch rank are independently checked.
Existing response gates are unchanged. A zero boundary, extra relative
mechanism, source-law rejection, competing physical mask, solver/budget stop
or source mismatch stops this attempt. Rejecting one energy minimum is not
proof that other masks lack physical states. Even infeasibility of the
symmetric approximation is not a physical failure or a proof about every
loading history.

The tiny dense primal QP polishing implementation is not applied to the frame.
If provisional forces fail any original gate, this record stops unresolved;
a separate frame-scale refinement method would need its own readiness. No
candidate result changes the three usable rear-case count, reviewed geometry,
original leg/runner resistance or fabrication status. Physical acceptance
still requires final validation and the complete loading/contact history.

The producer refuses a second invocation after inputs.json is recorded.

## Recorded result

The one-shot attempt ended at the 45 s solver limit with zero feasible
solutions, one processed root node and no candidate force output. Model
construction took 1.102 s; presolve took 1.15 s and retained 100 binary /
5,873 continuous variables, 3,732 linear constraints, one nonlinear energy
constraint and 600 indicators. The log does not resolve which root-node
subroutine consumed the remaining time. Total elapsed time was 47.092 s.
No second branch search was performed. Read-only parent provenance checks
pass for the frozen inputs, assessment and solver log. This is a runtime
stop, not a proof of no physical state; no larger-budget or guessed-mask
retry is queued.
