# K12-rear attempt03 SPR489 qghost diagnosis

This packet diagnoses the one strict response-audit exception in the terminal
K12-rear 23-bearing proposal. It replays the pinned response audit against the
unchanged attempt03 model, deck, DAT, and case context, then reconstructs the
SPR489 source coordinate and qghost coordinate from the printed U tokens and
the *EQUATION coefficients actually emitted in the deck.

The strict gate fails at load factor **0.2**. SPR489 is
`contact_70_0`, connecting `base_rail_service_lower_right` to
`wj04_lower_full_stock_cleat`; source q is `u(15671,1)-u(15670,1)` and the
qghost nodes are 19800/19801. At that state, qghost projects to
`1.6491829449091622e-6 mm` and source q is `1.6492999999999911e-6 mm`.
Their `-1.1705509082897213e-10 mm` gap exceeds the combined token radius plus
the pinned arithmetic guard by `1.6343569375211753e-11 mm`.

The emitted qghost y equation (zero-based equation row 19433) has residual
`-9.260465640168983e-11 mm` and rounding radius `6.477876096868e-11 mm` at
0.2; after its arithmetic guard, its own interval is missed by
`2.781879000565223e-11 mm`. The qghost z equation passes, as do both
source-projection equations (rows 9360 and 9363). The same qghost y equation
misses its local interval at 0.45 by `1.973983237138955e-13 mm` after the
guard, but the aggregate qghost/source interval check passes there. At the
other five recorded states, both checks pass. All emitted MPC rows remain
within the response method's general `1e-5 mm` residual criterion. The qghost
axis coefficients differ from the source axis by at most `1.11e-15`,
consistent with deck decimal formatting.

This is a small native-output qghost MPC residual outside a rounding-only token
interval, not evidence of a source-projection mapping or geometry mismatch.
The pinned method's separate general MPC criterion is `1e-5 mm`, much wider
than this residual; the response files do not expose a solver-internal MPC
residual that would let us separate finite solver residual from the rounding-
only gate. The token parser and emitted coefficient mapping are consistent.
Do not label this a token-decoding bug or physical failure. No tolerance is
relaxed here.

The same pinned normal-law method classifies all 100 floor normals at every
recorded increment: 23 strictly positive and 77 strictly separated, with zero
ambiguous rows. The positive set is stable and matches this proposal's mask.
This classification does not bypass the independent SPR489 gate. The packet
does not export response forces, adopt corner demands, qualify floor support,
or claim joint acceptance.

Run the read-only reconstruction from the repository root with:

```bash
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-k12-rear-qghost-diagnosis-attempt01/produce.py
```

The producer refuses to overwrite `diagnosis.json` and `source-pins.json`.
The attempt03 source hashes, method hashes, detailed per-state equations and
100-cell classifications are recorded in those files.
