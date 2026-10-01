# A12-forward attempt03 floor-pattern diagnosis

This source-bound report classifies all 100 floor-normal SPRINGA carriers in
the already completed `springa-selected-a12-forward-attempt03` run at all
seven printed load factors. It uses the pinned exact-zero-U 711-token strict
normal audit. The parent terminal assessment remains
`REJECTED_PROPOSED_SELECTED_BEARING_SUPPORT_BRANCH`, with selected SPR1050
not strictly positive after rounding.

The strict classifier finds 37 positive, 63 separated, and no ambiguous
normals at every printed state. The 37-cell positive pattern is identical at
all seven states. It does not exactly recur to any compared same-case input:
the attempt01 35-cell mask overlaps by 35, the attempt02 31-cell mask by 29,
and the attempt03 37-cell mask by 34. SPR1050 is selected in attempt03 and
strictly separated at every printed state.

The pattern is stationary along this run's printed load ramp. That result does
not test convergence of a support-mask update algorithm or demonstrate an
iteration cycle: attempt03 used one fixed 37-cell input and no mask updates.
The three prior comparisons read frozen model masks only; no earlier response
forces are used. The report contains displacement classification intervals
and withholds spring-force and reference-reaction values. It creates no new
input, retry, freeze, or solver run, and it makes no support or mechanical
acceptance claim.

`diagnosis.json` contains all per-cell classifications and mask comparisons.
`source-pins.json` binds the report to attempt03, the three same-case input
masks, the selected-floor method, current A12-forward case context, and the
frozen source inventory. All 150 attempt03 freeze source pins were rehashed.

Recompute into this packet only before its first report is written, or into an
unused repository-local directory with `--output-dir`:

```bash
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt02/produce.py
```
