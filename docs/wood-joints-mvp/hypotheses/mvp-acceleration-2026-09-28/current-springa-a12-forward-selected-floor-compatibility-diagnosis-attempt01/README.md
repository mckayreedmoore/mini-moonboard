# a12-forward selected-floor compatibility diagnosis

This is a read-only reclassification of the existing terminal `a12-forward`
31-selected/69-inactive input. It checks all 100 source floor-normal laws at
each of the seven printed load factors with the pinned `df1ed` response audit
and the exact-zero-U-token `711` audit. The producer writes projected-q and
geometric-elongation intervals plus branch classifications; it does not write
numeric spring-force or reference-RF values, export response forces, construct
an input mask, or launch a solver.

The result is deliberately rejected as a support proposal. Under `711`, the
observed diagnostic positive set is stable at 37 cells and 63 strictly
separated cells at all seven states. It matches none of the prior 31- or
35-cell masks. Three cells selected by the input are separated, including
`SPR1026` (`floor_base_floor_left_1`), while nine inactive cells are positive.
`SPR1026` is strictly separated with a zero endpoint reaction in all seven
states under both auditors; its projected-q and geometric-elongation intervals
are negative throughout. This is a real branch compatibility failure, not an
interval ambiguity or a support reversal across the printed history. The
separate `SPR1143` early-state ambiguity under `df1ed` resolves under the
exact-zero-U-token audit and does not change the `SPR1026` finding.

The exact run, screen, case-context, and audit source hashes are recorded in
[`source-pins.json`](source-pins.json). The JSON history retains all per-cell
classifications and both interval methods. The schema explicitly withholds
force adoption and corner-demand usability.

Reproduce the classification from a clean checkout with:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-a12-forward-selected-floor-compatibility-diagnosis-attempt01/produce.py
```

The producer is write-once by default. To recompute into a clean temporary
folder in this checkout without changing this packet, pass `--output-dir` to
an unused repository-local path. The script validates the pinned source and
method hashes before writing. It only parses the already-recorded DAT; it has
no native-solver invocation.
