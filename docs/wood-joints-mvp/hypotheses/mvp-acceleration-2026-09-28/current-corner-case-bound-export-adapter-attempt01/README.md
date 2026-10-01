# Case-bound corner export input boundary

This folder contains a fail-closed input boundary for one already-passed
generic case-bound SPRINGA response, plus a read-only replay of the preserved
a12-rear corner report. The current `produce.py` checks external context and
response provenance and emits no force rows or corner demands. A future
case-bound projection remains a separate step; this adapter does not perform
it.

The historical a12 response and corner report remain bound to the final
selected model `8a90452d…c1da8`, deck `e8f73768…e0aff`, DAT
`1f98a673…ffd54`, freeze `a362e551…7eb03`, and execution record
`6827b199…74f00`. `replay_legacy_a12.py` imports the exact preserved exporter
source and recomputes its report projection in memory. It writes only a small
replay summary in this new folder. The replay matches the saved report payload
after allowing one context-only difference: the current joint-check summary
file hash changed. The seven increments retain 338 interfaces, six physical
bolts, eight lateral planes, six outer-seat ties, 232 contact rows, 12 washer
seats, and 12 original LEG/RUNNER arrangements alongside the 92 candidate
axes.

The replay does not create generic case-context provenance. The historical
response has no context path, hash, or provenance fields. Its attempt02
diagnostic screen also omits the exact all-bearing controls model and deck
pins required by the generic context validator. The new CLI therefore blocks
the a12 response with no force rows. Do not synthesize context lineage or
reuse any other case's selected mask or forces. The rejected forward 35/65
response is not consumed here.

From the repository root, reproduce both recorded results with:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-case-bound-export-adapter-attempt01/replay_legacy_a12.py
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-case-bound-export-adapter-attempt01/produce.py \
  --response-audit docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-a12-rear-attempt03/response.json \
  --output docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-corner-case-bound-export-adapter-attempt01/legacy-a12-generic-boundary-block.json
```

The replay summary should report
`PASS_READ_ONLY_LEGACY_A12_PAYLOAD_REPLAY_WITH_GENERIC_CONTEXT_BLOCKED`; the
generic boundary should report `BLOCKED_CASE_BOUND_RESPONSE_INPUT`. Neither
result establishes joint resistance, complete-joint acceptance, floor
qualification, fabrication approval, or climbing release. The five remaining
cases and any future generic response projection remain outside this bounded
adapter result.
