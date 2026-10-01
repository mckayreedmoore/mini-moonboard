# K12-right attempt02 normal-interval diagnosis, attempt 01

This read-only packet applies the pinned 711 zero-U interval classifier to all
100 source-bound floor normals at all seven increments of the exact K12-right
attempt02 response. It binds the response, parent terminal assessment, fresh
case/load-register row, and both earlier case-local 10-cell input masks.

Every increment classified 11 normals as strictly positive, 89 as strictly
separated, and none as unresolved. The 11-cell positive set stayed unchanged
through the seven increments. The attempt02 run used the attempt11 10-cell
proposal exactly. It reproduces those ten positive cells and adds the formerly
inactive `floor_lumber_leg_right_0` (`SPR1311`). The parent 711 terminal
assessment rejects attempt02 for that same inactive normal not being strictly
separated with zero endpoint reaction; corner demands and conditional case
forces remain unusable.

The observed set is not an exact repeat of either earlier 10-cell input. It is
a strict one-cell superset of attempt11's input. Compared with attempt03's
earlier all-bearing-derived input, eight cells overlap: attempt03-only cells
are `floor_lumber_leg_left_2` and `floor_lumber_leg_right_3`; observed-only
cells are `floor_base_post_center_left_2`,
`floor_base_post_center_left_3`, and `floor_lumber_leg_right_0`. This identifies
a stable per-increment mismatch for the attempt11 run, not convergence of a
support-selection procedure, a fixed point, or a cycle. No third mask or retry
was created.

`k12-right-attempt02-normal-interval-comparison.json` contains all 700 strict
normal interval rows, per-state sets, both exact mask comparisons, source
pins, and the parent rejection/force-use boundary. The classifier checks
printed DAT intervals and its stated arithmetic guards. It does not repair the
response gates or establish a physical floor failure, floor capacity,
friction, connector demand, joint acceptance, or original LEG/RUNNER
resistance. No geometry, load, material, constitutive law, or criterion was
changed; no native run was launched by this packet.

Reproduce or verify the report from the repository root:

```bash
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-k12-right-attempt02-normal-interval-diagnostic-attempt01/produce.py --write
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-k12-right-attempt02-normal-interval-diagnostic-attempt01/produce.py --verify
```

`produce.py` verifies the pinned response and source records before classifying
the DAT; it never executes CalculiX. `SHA256SUMS` pins the producer, report,
and this README.
