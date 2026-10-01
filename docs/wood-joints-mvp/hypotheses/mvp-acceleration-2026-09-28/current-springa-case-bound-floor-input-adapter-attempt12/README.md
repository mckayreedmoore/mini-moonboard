# Case-bound floor input adapter, attempt 12

This packet contains one input-only K12-right proposal with 11 selected floor
normal cells and 89 released cells. The mask is derived only from the pinned
K12-right attempt02 711 normal-interval diagnosis in
[`current-springa-k12-right-attempt02-normal-interval-diagnostic-attempt01`](../current-springa-k12-right-attempt02-normal-interval-diagnostic-attempt01/README.md).
It adds `floor_lumber_leg_right_0` to attempt11's 10 cells because that
previously inactive normal is strictly positive in all seven attempt02
increments. Attempt02 itself remains rejected at that normal; its response
forces are not used for this input.

The immutable attempt02 adapter used the original case's all-bearing controls
and the fresh K12-right load-register row as physical/load authority. It
emitted `k12-right/model.json` and `model.inp`; the parent input audit
independently passed the source-load, node, constraint, and reference-transfer
checks. The prepared input retains 50 physical bodies, 92 candidate bolt axes,
12 LEG/RUNNER axes, and 66 Hillman axes, with 22 active tangent rows. It
records no geometry, law, load, or material changes.

This is a reviewable input proposal only. The adapter and independent parent
audit both leave `proposed_branch_accepted`, `native_run_authorized`, and
`corner_demands_usable` false. There is no freeze, native response, force
promotion, corner demand, floor qualification, or joint acceptance in this
packet. Parent owns any readiness decision and any later serialized run; this
proposal does not authorize mask iteration.

`screen.json` is regenerated from the pinned attempt02 report with:

```bash
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-case-bound-floor-input-adapter-attempt12/prepare_screen.py --verify
```

Re-run the independent input audit from the repository root:

```bash
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-case-bound-parent-input-audit-attempt01/check.py \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-case-bound-floor-input-adapter-attempt12/k12-right \
  --baseline docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-frame-k12-right-all-bearing-attempt01 \
  --screen docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-case-bound-floor-input-adapter-attempt12/screen.json \
  --output /tmp/k12-right-attempt12-parent-input-audit.json
```

`k12-right/source-pins.json` records the immutable adapter's complete input
pin ledger and emitted model/deck hashes. `SHA256SUMS` pins the screen
producer, screen, case packet, and independent audit.
