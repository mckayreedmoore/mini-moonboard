# External-member balanced-force transient, attempt03 — results

## Outcome

Attempt03 is a bounded no-accepted-state-progress diagnostic. It produced no
auditable joint response and closes no mechanical criterion. The physical and
load inputs stayed frozen; the only deck change from attempt02 was the
contact-output header documented in [README.md](README.md).

The run is bound to force freeze
`1c9a612216cfcbcaf137c1e80bd9f76f395db6053d3eb149ebaa7d23a59380ed`, input
freeze `6ddd774e190a184f1918cd72ad63bfd22e4108aedb834bfe75db5614ea6e56bf`,
and readiness record SHA-256
`904997d130c835261cdf117d6ffad9c4830d94ae140459666a2c86c5d8c29e53`.
The independent input review verified all 44 frozen artifact hashes; the
terminal record reports unchanged inputs and stores the native output hashes.

The runner stopped after 1,100.94 seconds with
`no_accepted_or_monitor_progress_timeout`. Its 600-second watchdog required a
new accepted `.sta` increment or complete `PILOT_MONITOR` block to reset.
Solver iteration records continued through step 1, increment 2, attempt 1,
iteration 22 in `.cvg`; the stop does not mean the solver had no iteration
activity. The runner then stopped the named container: return code 137,
container exited, `OOMKilled=false`. There is no `pilot.rout` final response.

## Accepted state and load scale

`pilot.sta` contains one accepted state: step 1, increment 1, attempt 1,
18 iterations, at `t = 0.001 s`. The frozen load amplitude there is
`9.8506e-6` at a 1 N reference scale. The applied nodal field is below the
frozen force floor at this point: summed absolute nodal components are about
`8.77e-4 N`, and the largest nodal resultant is about `3.42e-5 N`, versus a
`0.01 N` floor. These describe the input field, not measured reactions or
internal-force balance.

The accepted-state monitor reproduces as follows:

| Measure | Observed | Frozen diagnostic stop |
| --- | ---: | ---: |
| Force-dual coordinate `q` | `2.48346e-7 mm` | `1.3 mm` |
| Maximum loaded-node displacement | `1.94976e-8 mm` | `5 mm` |
| Maximum controller rotation | `7.42084e-13 rad` | `0.05 rad` |

`pilot.dat` reports internal energy `1.020238e-12 N mm` and kinetic energy
`2.030917e-13 N mm` at that state, far below the frozen `1e-5 N mm` energy
floor. `pilot.stdout` also prints one accepted-state global energy balance:
external work `1.223180e-12 N mm`, elastic contact energy
`8.583830e-18 N mm`, total energy `1.223338e-12 N mm`, and relative residual
`0.012881%`. This native print is at the sub-floor startup state; it is not an
independently reconstructed balance and says nothing about first bearing or
post-bearing response. The run therefore does not assess the event or
kinetic-to-(strain-plus-contact)-energy gate. The first accepted state is an
underloaded startup observation, not evidence of joint response or
equilibrium.

## Last-iteration displacement output

The 147,425,303-byte `ResultsForLastIterations.frd` matches the SHA-256 in
`execution.json`. It contains 22 complete `DISP` frames, each with 120,694
node records, identified as step 1, increment 2, iterations 1–22. The file
contains displacement only: no stress, strain, velocity, acceleration,
contact force, or energy fields. Its `100CL` time labels are zero; the pinned
2.23 manual and the output known-answer coupon establish that this file holds
iteration snapshots for the final increment, so those labels are not transient
time points. See the official [CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf)
and the [known-answer output coupon](../contact-output-known-answer-attempt01/README.md).

I independently streamed those frames and reapplied the frozen monitor recipe.
Across the 22 unaccepted trial states:

- `q` stays near `5.57785e-7 mm` (displayed range `4.23e-14 mm`);
- maximum displacement over the 86 frozen loaded nodes is
  `4.06546e-8 mm` in every frame;
- the maximum over the four frozen rotation nodes ranges from
  `2.486e-12` to `5.955e-12 rad`.

These trial-state values are separate from the accepted increment-1 monitor.
They show nearly stationary monitored motion across the captured iterations;
they do not establish a converged response. The file has more node records
than the accepted `pilot.frd` physical-node set (116,162), so no global maximum
is inferred from its extra nodes. The selected monitor nodes are present.
Iteration 22 is the last fully CVG-aligned frame, not proof of the solver's
last contact evaluation.

## Contact-element topology audit

The CEL output contains 1,228,234 C3D6 elements in 41 groups. Forty of the 41
groups match `.cvg` iteration counts exactly. One step-1/increment-2/attempt-1
group, iteration 23 with 23,559 elements, has no matching `.cvg` row and no
FRD frame; its completeness is unauthenticated and it is excluded from
confirmed switching summaries.

The audit maps all parsed elements to the frozen 35 ordered contact pairs,
with zero ambiguous or unmapped records, using disjoint mesh ownership and
the contact manifest. Master/slave orientation is supported by the pinned
2.23 C3D6 known-answer coupon. That coupon directly checks one small contact
pair; the full-model mapping is coupon-mediated, not verified by inspecting
the unavailable `gencontelem_f2f.f` source.

Across 38 adjacent, CVG-aligned iteration transitions within the two
increments, cumulative face-pair signature turnover is 494,338 for bolt-seat
families and 96,928 for finite wood-to-wood interfaces; the open-bore families
remain at zero generated elements. These are generated contact-face
association diagnostics. They establish neither contact force or pressure,
physical chatter or its cause, nor convergence or capacity. The raw `.cel`,
`.cvg`, FRD and parser outputs are recorded in [`execution.json`](execution.json)
and [`ordinary-contact-iteration-audit.json`](ordinary-contact-iteration-audit.json).

## Disposition and next work

Attempt03 completes the planned output-only observation. Keep
`method_demonstrated` partial and do not start rate/timestep comparisons or
change geometry, contact, loading, constraints, or damping based on these
outputs alone. The captured files do not identify why increment 2 failed to
converge or provide the required force/moment, contact-energy, and sensitivity
evidence. Continue source-bound six-case preparation and material/hardware
work where their inputs are ready, but do not run full-frame cases until
connection behavior is defensible. `mechanical_acceptance` and
`joint_acceptance` remain false.
