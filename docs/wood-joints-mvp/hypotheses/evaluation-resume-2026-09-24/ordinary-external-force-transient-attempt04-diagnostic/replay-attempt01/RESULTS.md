# Attempt04 output-only replay: terminal result

## Decision

The replay establishes the remaining logged mechanical convergence blocker:
contact-element-count stability. On increment 2, iterations 2–26 fail only
`contact_change_gate_clear`. Residual, displacement and viscoelastic checks
pass in all 44 completed rows. The first iteration of each increment instead
fails the separate `iit > 1` prerequisite.

This is a convergence diagnostic, not an accepted joint response. Passing
those predicates does not establish independent force/moment closure, a
physical load history, energy acceptance, or capacity. Keep the default
`delcon=0.001` and the reviewed geometry unchanged; this result alone does
not justify loosening the count criterion.

## Terminal execution

- Container: `wj-at04diag-20260927T130804Z`.
- Started: `2026-09-27T13:08:04.102020+00:00`; ended: `2026-09-27T13:25:04.998758+00:00`.
- Elapsed: 1021.04 seconds.
- Stop: `no_accepted_increment_or_monitor_progress_timeout`, after 600 seconds
  without a new accepted increment or complete monitor block.
- Docker exit: 137 following the runner's stop request; `OOMKilled=false`.
  The container is confirmed stopped. Exit 137 is not attributed to OOM.
- Accepted states: one, at `0.001 s`, increment 1 after 18 iterations.
- All 44 copied input hashes and original attempt03 input/output bindings
  match. The trace auditor verifies all nine recorded replay output hashes.
- Runtime inspection also confirmed the pinned image/binary, 2 CPUs, 12 GiB,
  disabled networking and the exact replay-directory bind mount.

The accepted `.dat` and `.sta` files are byte-identical to attempt03. Its
under-floor startup state and energy print therefore retain the limits in
[attempt03's result](../../ordinary-external-force-transient-attempt03/RESULTS.md).

## Completed trace rows

| Increment | Complete rows | First-iteration gate only | Count gate only | Passed final convergence |
| --- | ---: | ---: | ---: | ---: |
| 1 | 18 | 1 | 16 | 1 (iteration 18) |
| 2 | 26 | 1 | 25 | 0 |

The exact event audit contains 44 CVG rows, 44 convergence events, 43 contact
events and 45 CEL groups. Forty-two contact events belong to completed
later iterations; the remaining contact event and CEL group are increment-2
iteration 27, with no completed CVG/convergence row. That tail stays
unresolved. No file ends in a partial line; a newline does not make the
unfinished iteration complete.

All 44 completed CVG rows are audited without errors. The whole capture is
not complete because of the unresolved tail. All 40 CVG keys common to
attempt03 have identical tokens; the replay has four additional completed
rows (increment 2, iterations 23–26). The full key sets therefore differ,
which the audit reports separately from equality of their common rows.

The contact-energy eligibility flag depends on prior mechanical convergence;
its being false on rejected rows is not an independently evaluated energy
failure or pass. No missing tail predicate is inferred.

## Source interpretation and next decision

The [source interpretation](../contact-count-interpretation.md) identifies
what the count measures: generated face-to-face penalty springs associated
with slave-face integration points. In the pinned source, cached master-face
matches are fixed within an increment, while per-iteration signed clearance
can create or suppress generated springs. The source archive does include
`gencontelem_f2f.f`; this supersedes the earlier report that it was unavailable.

The trace cannot distinguish negligible zero-clearance classification changes
from material changes in contact state. CEL turnover and nearly stationary
monitored displacement do not supply the missing signed point clearance,
pressure or force. Preserve that limit rather than infer physical chatter.

The next work is a source-based contact-method decision, not another repeat
of this deck or an automatic instrumentation branch. Compare documented
standard formulations and their applicable convergence conditions; require
a small known-answer demonstration before any candidate method change.
A change must preserve intended unilateral contact and the free cleat, with
no added support or tuned damping hiding a mechanism. No alternative has yet
been selected or validated.

Local mathematical unit-response characterization may precede full-frame
demands under the existing criteria. Its load factor is an analytical input,
not a physical force-time history or one of the six frame cases. The prior
external-port static attempt09 remains a failed path; do not blindly repeat
it. A physical transient still requires the source-bound port histories.
The solver's implicit dynamic procedure is not a documented native dynamic
relaxation solver, and a numerical dynamic continuation cannot be called
quasi-static without equilibrium, energy, rate, timestep and branch checks.

## Records and checks

- [Execution](execution.json): SHA-256 `f26a3c3dccfacb7949d07eaf3bf31f0626eba03c41892b1faca9cb86e20e356a`.
- [Trace audit](trace-audit.json): SHA-256 `e0c80d2a60d44f93c634e87cd07d1c94ee687517427c7225135722fc36965e5c`.
- [Auditor](../audit_replay.py): SHA-256 `3d5cb8c957fe7ab10d298d3f930949cdf916c2b2f6bc1ae5d84f443bdd097af8`.
- [Launch gate](launch-gate.json) binds the passing build/coupon, binary check,
  zero-active-solver scans and frozen inputs.

The parent exercised the auditor on the fresh static coupon and confirmed
that missing contact events, inconsistent contact presence and invalid static
energy eligibility are rejected. Independent review also exercised interrupted
tails and missing interior records. Parent reran the final auditor after the
reviewer's handoff. These are bounded artifact checks; no further solver run
was launched. Mechanical and joint acceptance remain false.
