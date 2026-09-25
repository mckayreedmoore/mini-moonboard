# Checkpoint diagnostic outcome

The parent launcher stopped this run at its 600-second bound, with 605.691
seconds elapsed including the stop grace. Return code 137 follows the parent
stop; it is not evidence of an out-of-memory failure. The terminal record is
[`execution.json`](execution.json), SHA256
`2e40136b0110b031193039b15eaa2ba6ef779de76df4eb9347b7a7e59ef2326f`.
All frozen input hashes and terminal output hashes were independently checked
after the launcher exited.

The convergence file records 34 trial iterations of the first increment. No
complete monitor sample or converged increment was produced, and `pilot.rout`
is absent. This attempt supplies no checkpoint to reuse and does not reproduce
pilot03's accepted first point. It leaves the longer pilot and joint response
unresolved.

The run did preserve `ResultsForLastIterations.frd` (223,870,747 bytes) and
`pilot.cel` (195,027,021 bytes). Separate audits must distinguish complete
diagnostic fields from any interrupted final record, map contacts to their
frozen owners, and compare trial motions without calling them converged.
The final recorded contact count is 40,510; counts alone do not establish
which interfaces switched or why. No geometry, restraint, contact tolerance,
or material was changed to obtain this record.

The restart source review also identifies a separate limitation: velocity is
serialized, but acceleration is not explicitly serialized and a new nonlinear
dynamic step allocates a fresh acceleration array. Even a future successful
checkpoint requires a continuation-equivalence check before substituting for
an uninterrupted trajectory. No continuation is prepared from this attempt.
