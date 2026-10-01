# K12-right floor-normal interval diagnosis, attempt 01

This packet reclassifies the exact seven printed increments from the rejected
K12-right selected-10/released-90 run. It applies the source-pinned zero-U
token wrapper (711) and stable response parser to all 100 source-bound floor
normal rows at every increment. It does not accept that run as a response:
the existing terminal assessment remains
`REJECTED_SELECTED_FLOOR_SUPPORT_BRANCH`, and the response is not suitable for
corner-force export.

All seven increments reached full load. Every state classified as 10 strictly
positive bearing intervals, 90 strictly separated intervals, and zero
unresolved intervals. The set was unchanged at all seven increments. Compared
with the rejected run's selected-10 mask, `floor_lumber_leg_left_2` and
`floor_lumber_leg_right_3` were strictly separated; `floor_base_post_center_left_2`
and `floor_base_post_center_left_3` were strictly positive. The resulting
10-cell set is recorded in `k12-right-normal-intervals.json` and in the adapter
screen. These are interval classifications of the selected-10 run only, not an
equilibrium state for the newly proposed mask.

`produce.py` pins the native inputs and outputs, exact K12-right case context
and load-register row, prior input proofs, the 711 wrapper/parser/replay
artifacts, and the immutable case-bound adapter/checker. The prior non-711
screen is only a same-case cross-check. No A1 or a12 forces, mask, or response
are reused. The interval method bounds printed DAT values and its stated
arithmetic guards; it does not bound solver residual, convergence error,
pre-format underflow, or continuum solution error.

The stable set was eligible for one input-only case-local proposal. That
proposal is prepared in
[`current-springa-case-bound-floor-input-adapter-attempt11`](../current-springa-case-bound-floor-input-adapter-attempt11/README.md).
It has not been solved or force-audited. This diagnosis establishes no floor
capacity, friction or anchorage, connector demand, joint acceptance, or
reopened LEG/RUNNER resistance. It does not imply that another case or load
will produce an admissible or unique support mask.

Run the following from the repository root to regenerate or verify the two
diagnostic outputs:

```bash
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-k12-right-normal-interval-diagnostic-attempt01/produce.py --write
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-k12-right-normal-interval-diagnostic-attempt01/produce.py --verify
```

`SHA256SUMS` pins this producer and its output files. `screen.json` is a
case-bound input-proposal screen; its rejected status and false acceptance and
force-use flags are intentional.
