# A12-forward M5 floor-mask input proposal

This packet prepares exactly one input-only hypothesis from the seven printed
states of the rejected A12-forward M4 run. The unchanged strict interval
classifier found the same 34 strictly positive and 66 strictly separating
normal cells at every state, with no ambiguous intervals. The 34-cell set
differs from the M1–M4 proposed inputs. Relative to M4, it removes
`floor_base_floor_left_15`, `floor_base_floor_left_17`, and
`floor_base_post_outer_left_1`.

`prepare_m5_proposal.py` binds that set to the original A12-forward all-bearing
controls, source-load register, and case input, then calls the existing
selected-floor input adapter. Its result is in `a12-forward/`: 34 selected
normal cells, 68 selected floor tangent rows, unchanged 100 normal laws and
348 bilateral springs. The proposal is diagnostic only; rejected M4 forces
and states are not adopted.

`check_m5_input_gate.py` builds the existing case-context shape and calls the
unchanged pinned 711 `_validate_case_context` and `_validate_model` methods.
The resulting `input-gate.json` and `input-gate-source-pins.json` cover this
input gate and rehash the M5 screen’s transitive source map. This is not a
freeze or native-readiness review.

Reproduce the proposal and then its context/input gate with:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/\
current-springa-a12-forward-mask-update-proposal-attempt02/prepare_m5_proposal.py
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/\
current-springa-a12-forward-mask-update-proposal-attempt02/check_m5_input_gate.py
```

Neither command freezes or launches a native run. Any later execution requires
the parent-owned freeze, readiness review, serialized runner, and a fresh
response audit of that exact input. No response force, corner demand,
mechanical acceptance, or floor qualification follows from this proposal.
