# Current finite-actuator work audit: first accepted point

The immutable first-knot snapshot supports one accepted work interval from the
checked input-defined driver state at time zero to `0.0005 s`. The native
process was still running when the snapshot was captured, so this is a prefix
accounting result. It does not establish a complete-joint response, time
accuracy, a seated state, capacity, or mechanical acceptance.

The audit reads the actual emitted equation
`q_proxy + Σ aᵢ Uᵢ = 0`, verifies the first dependent term is proxy node
`117162` with coefficient `+1`, and calculates `q_A = Σ(−aᵢ)Uᵢ` from all
662 serialized physical terms. Each serialized weight matches the frozen
source unit pattern within its exact decimal source-text half-quantum; the
largest error is `5e-17`. It uses the checked initial target, proxy, and
physical coordinates plus the recorded zero spring gap and zero spring
energy. It assigns no initial physical or contact energy.

At the accepted point, all 339 requested physical monitor rows and both driver
nodes' displacement and reaction rows are complete. The physical weighted
coordinate is `6.862259595705033e-8 mm`, while the proxy coordinate is
`6.862260e-8 mm`. Their `−4.04295e-15 mm` difference is inside the propagated
`1.90833e-14 mm` DAT print bound. The target displacement is `1.426740e-6 mm`;
target RF is `0.0002716235 N`. The independently calculated `200(q_T−q_P)` is
`0.00027162348 N`, with a `2e-11 N` residual inside the combined
`1.51e-10 N` displacement and reaction print bound. Proxy RF is retained only
as a diagnostic and is not used as controller force.

The accepted interval work split is:

| Signed term | N·mm |
| --- | ---: |
| Target work from target RF and target displacement | `1.93768056195e-10` |
| Actuator spring energy increase | `1.84448287218e-10` |
| Work at the proxy coordinate | `9.31975539555e-12` |
| Work at the physical emitted-MPC coordinate | `9.31975484647e-12` |
| Proxy minus physical work | `5.49080e-19` |

The discrete target-work identity residual is `1.3581e-17 N·mm`, inside the
`2.4314e-16 N·mm` propagated print bound. Every reported cumulative quantity
starts from the checked input-defined spring state. No interval is reconstructed
across a missing or rejected status row.

The continuum set reports `ELSE=1.639288e-12 N·mm` and
`ELKE=7.669528e-12 N·mm` at the accepted point. No physical-energy baseline is
assigned at time zero, so a first-interval change in `ELSE+ELKE` is unavailable.
The native global log reports zero external work; that field is not the
prescribed-target work oracle. Its internal, kinetic, contact, and global
balance fields remain separate diagnostics. The DAT CELS table has 97,275
rows, matching its CNUM count, and a raw sum of `3.7050318963e-13 N·mm`; the
sum is retained as diagnostic only and excluded from energy closure under the
current CELS source limitation. The 378 MB `.cel` and FRD files were not read.

`audit.py` operates only on an immutable snapshot directory and checks the
snapshot manifest, the frozen input artifact pins, and output hashes before
parsing. Its accepted `.sta` rows control coverage. Incomplete DAT tails and
unaccepted attempts cannot fill a missing accepted state; an accepted time
without a unique complete monitor and driver sample raises an error. The
report is in [report.json](report.json), generated from
[snapshot attempt 01](../ordinary-finite-actuator-first-knot-snapshot-attempt01/snapshot.json).

Run the focused checks and reproduce the snapshot audit from the repository
root:

```sh
.venv/bin/pytest -q tests/test_current_finite_actuator_work_audit.py
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/current-finite-actuator-work-audit-attempt01/audit.py docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-finite-actuator-first-knot-snapshot-attempt01
```
