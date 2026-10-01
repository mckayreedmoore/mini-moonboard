# K12-rear SPR489 direct-master response method preflight, attempt02

This input-only packet validates the SPR489 direct-master method candidate
against the unchanged K12-rear selected-floor baseline. It does not freeze
inputs, launch a solver, recover variant forces, or accept the frame. Attempt02
supersedes attempt01's incomplete serialized-model diff claim; attempt01 is
preserved unchanged.

The validator first invokes the pinned 711 `_validate_model` on the original
baseline model, deck, and case context. It then constructs the only permitted
variant record from that baseline: equation records 19,433 and 19,434 are
replaced by the audited SPR489 Qy/Qz direct-master rows; all other 21,842
serialized equation records must compare exactly to the original JSON. Outside
the equations, only `/input_method_variant` and declared method/qghost metadata
under the two mirrored SPR489 binding records are allowed to differ. The
emitted deck has the same two equation-row changes and no other card changes.
The exact recursive model difference is recorded in `input-contract-check.json`.

The force-recovery fork obtains SPR489's scalar coordinate from the pinned 80
physical master DOFs as `q = -sum(c_i U_i)` and propagates output-token radius
as `sum(abs(c_i) U_radius_i)`. It uses that value only for SPR489; the other
1,291 nonlinear carriers, 348 retained bilateral springs, floor reaction
recovery, physical-owner mapping, and body/global balance checks remain in the
pinned 711 response core. The unchanged baseline has 50 physical bodies and a
23-bearing/77-inactive floor branch.

The read-only replay ends
`PASS_INPUT_CONTRACT_AND_READ_ONLY_METHOD_DIAGNOSTICS_ONLY`. It includes the
known-answer scalar-map algebra fixture, byte-identical input-copy validation,
and 11 rejected negative probes, including changes to an untouched
high-precision equation row and to one of the two allowed target rows. The
replayed old baseline DAT still has its previously recorded 9,044-check
SPR489 qghost/projection interval exception at time 0.2. A direct-master
coordinate comparison of those old U tokens is diagnostic only: it contains
no direct-variant endpoint forces, equilibrium, or response acceptance.

Reproduce the contract and read-only method checks from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-spr489-direct-response-audit-attempt02/verify_method_and_diagnostic.py
```

The future postprocessor command requires a parent-created post-freeze context
and a native result from the exact frozen input copy. Neither exists in this
packet:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-k12-rear-spr489-direct-response-audit-attempt02/response_core.py \
  <parent-created-variant-context.json> <frozen-run-packet/model.json> \
  <frozen-run-packet/model.dat> <frozen-run-packet/model.inp> \
  <frozen-run-packet/execution.json> \
  --output <frozen-run-packet/response-audit.json>
```

Pinned attempt02 input hashes are model `8f1d9bce9b62b18b3694f81816ef5c4c7cbe5e94b4c459a640fce7a98db68dbd`, deck `6c6f8dc02616d3b92dda2f15db1a196e47935233e47eee0afaa56fda694fd3aa`, and input audit `c593c94d206c6798b190d3b42b4956aaa898a503dfe11a1303b20a126266d8cf`. The verifier and input validator bind those exact files plus the original baseline, 711 methods, and reviewed direct-scalar coupon sources; `source-pins.json` records the complete digest set.
