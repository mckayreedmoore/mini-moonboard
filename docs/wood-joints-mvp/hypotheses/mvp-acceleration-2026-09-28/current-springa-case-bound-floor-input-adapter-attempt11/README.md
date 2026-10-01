# Case-bound floor input adapter, attempt 11

This packet contains one input-only K12-right selected-floor proposal. Its
mask comes from the strictly classified, stable 711 normal intervals of the
exact rejected selected-10 K12-right run in
[`current-springa-k12-right-normal-interval-diagnostic-attempt01`](../current-springa-k12-right-normal-interval-diagnostic-attempt01/README.md).
The immutable `current-springa-case-bound-floor-input-adapter-attempt02/prepare.py`
emitted the new case-local deck and model. The proposal selects 10 normals and
releases 90, with 20 active tangent rows. The fresh K12-right source model,
case record, load register, all-bearing controls, and diagnostic screen are
bound in `k12-right/source-pins.json` and
`k12-right/case-bound-input-context.json`.

The generic parent input audit passed source-load serialization, preserved
nodes, constraint reconstruction, and reference transfer. It confirmed 50
physical bodies, 92 candidate bolt axes, 12 retained LEG/RUNNER axes, 66
Hillman axes, and no geometry, law, load, or material change. The audit also
explicitly records `proposed_branch_accepted=false`,
`native_run_authorized=false`, and `corner_demands_usable=false`.

The proposed mask has not been frozen or solved. The original selected-10 run
remains rejected, and its normal intervals do not supply response forces for
this input. This packet creates no native response, floor qualification,
physical force adoption, mechanical acceptance, corner demands, or change to
the original twelve LEG/RUNNER resistance checks. Parent owns any later
readiness decision and serialized native run.

Reproduce the read-only parent input check from the repository root:

```bash
uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-case-bound-parent-input-audit-attempt01/check.py \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-case-bound-floor-input-adapter-attempt11/k12-right \
  --baseline docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-frame-k12-right-all-bearing-attempt01 \
  --screen docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-k12-right-normal-interval-diagnostic-attempt01/screen.json \
  --output /tmp/k12-right-attempt11-parent-input-audit.json
```

The emitted model/deck, context, source-pin manifest, adapter audit, and parent
input audit are pinned in `SHA256SUMS`. `source-pins.json` carries the exact
SHA-256 values supplied to immutable adapter02, including the register,
all-bearing controls, diagnostic screen, and fresh case model.
