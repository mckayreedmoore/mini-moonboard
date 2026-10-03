# Bottom first-order same-state component replay

The parent executed [the producer](bottom-corner-components.py) once in
`rawlocal/bottom-corner-components/attempt01/`, returning
`COMPLETE_SAME_STATE_COMPONENT_REFERENCES`: **12 block states, 24 host/interface
states and 48 bolt states**, including 24 per side. `build(output: Path)`
replays existing bottom component references on the completed
[bottom transfer](bottom-corner-transfer.md).

| Maximum conditional component index | Returned value |
| --- | ---: |
| Adjusted lateral, 45 ksi | 0.3978064027 |
| Adjusted lateral, 92 ksi | 0.2782172875 |
| Same-state 92 ksi steel reserve | 0.2804753033 |
| Finished parallel tangent path | 0.0365524248 |
| Mean supported washer-seat pressure | 0.2293396147 |
| Smooth elastic bolt stress / 92 ksi | 0.1123324054 |

Each maximum retains its own complete same-state witness in the saved result;
the maxima are not combined into one loading state. The existing model,
current geometry and simple hypotheses remain the MVP basis.

Each bolt uses its own saved simultaneous axial tie, signed host bore
resultant, beam stress, bottom receiver lengths and grain. The opposite host
bore resultant defines the cleat-directed single-shear transfer, matching the
existing first-order replay convention; the independently recovered cleat
bore resultant and its numerical discrepancy remain visible.

The replay retains the bottom packet's **4450/5600 psi** bearing basis,
45/92 ksi scenarios, original Cg/Cdelta component modifiers, signed finished
bore-tangent paths and worst combined-offset supported washer areas. It
also retains the existing 0.0318 in² axial steel reserve and washer radial
strip calculation. The saved smooth-bolt bending stress and K20 seat-pressure
samples remain separate same-state witnesses. Four original face cells per
host and the completed independent balance residuals are retained.

These are conditional component comparisons under rigid timber, concentric
washers and reference geometry. The original 100 mm frame source remains
frozen. Top geometry, indices and diameter-dependent bearing hypotheses are
not consumed. Original host-splitting demands remain historical scope; no
new whole-host cuts, group method, FEA, catalog investigation or qualification
is added. Formal, complete-joint, fabrication and physical-release flags stay
false; Ft-perpendicular and group capacity remain null.

## Frozen inputs and API

Paths below are relative to this folder unless prefixed `../` or `fea/`.

| Input or producer | SHA256 |
| --- | --- |
| `bottom-corner-components.py` | `5239f1b4897e17ade2c4c4e73b8f9a42e9433f76357fbe0f355308c84fcbd3a7` |
| `rawlocal/bottom-corner-transfer/first-order-attempt01/checks.json` | `4d255ba5ebd8f1f93fb41ef90511eb3da49906f4729f33f5f63766e0a0bd78ed` |
| `rawlocal/bottom-corner-transfer/first-order-attempt01/source-pins.json` | `5fdeb9927a759644f5c25d462b532fcd2bb9d2f389f69b462b716f33857fcb51` |
| `bolted-replay-results/bottom-attempt01/component-results.json` | `ec421ee35b9477842660faa6d2528bd957f8a06620f7d84c46d9654e40ce146a` |
| `../../hardware-material-specification-2026-09-30/material-inputs.json` | `0f33ad8fd517673a4ebbed36c4a30c1cfe07e0d8163165bdc804af91d958fc5a` |
| `../../hardware-material-specification-2026-09-30/fastener-inputs.json` | `ac8c5ca36105e3eab48f58c868794fc8a42d77cd54dfa5c76fb41f0934fd2ac2` |
| `../lateral_reference.py` | `845409d1daf0214bbd41484f0a0a58867cd266bbc7f19060d9eef9d342657e94` |
| `fea/dowel_yield.py` (repository root) | `d6c318e75c1a720d0b91f810a892e8309ef89735f66f48820ee853b753f8fe45` |
| `rawlocal/bottom-corner-components/attempt01/checks.json` | `39e698d7ffec6646e2295f5ce96be0764ea8fbe6654ed3b0e881040b410bcc95` |
| `rawlocal/bottom-corner-components/attempt01/receipt.json` | `7a241d0e035167c2d920277d9c9f33ac12a919531d2b37c74c6819a0fd58e2ff` |

The completed [result](rawlocal/bottom-corner-components/attempt01/checks.json)
and [receipt](rawlocal/bottom-corner-components/attempt01/receipt.json) bind the
unchanged producer hash above. The producer/note pair is frozen for parent
handoff; the final note hash is supplied separately to avoid a self-hash.

The producer also authenticates the completed transfer's entire 26-source
closure, including all six current finished STEP identities and unchanged
`2b05…` transfer producer. Its result stores every state, full peak witnesses
by side, source physical balances, assumptions and exact consumed hashes.

The parent output below is complete and preserved; no rerun is requested:

```sh
packet=docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 \
  .venv/bin/python "$packet/bottom-corner-components.py" \
  --output "$packet/rawlocal/bottom-corner-components/attempt01"
```

Outputs are `checks.json`, `receipt.json` and `producer.py.snapshot`, all
ignored locally. Completion means arithmetic
coverage, not acceptance of any ratio or complete joint.

The earlier implementation passed Ruff. This annotation reads the existing
parent result and hashes only; no postprocess, mechanics, CAD, tests or new
study was executed. Parent owns both producers. Only the two bottom notes
were edited in this closeout; foreign work remains preserved. Both frozen
producer/note pairs and their evidence remain active. No archiving, pruning,
staging or commit occurred; all acceptance and release flags remain false.
