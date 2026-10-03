# Validation record

The producer joins all twelve current retained arrangements for all 21 frozen
states. The focused tests cover signed off-axis wrench/radius known
answers, physical nodal loads and complete boundary coverage, and rejection of
missing/duplicate axes or receivers, missing projection rows, wrong owners,
false source-law gates, wrong elements, duplicate scalar components and changed
source bytes. A fresh-process hash-seed regression also checks byte-identical
replay after sorting the pinned floor adapter's unordered tangent-port records.
All eight tests pass. The final added endpoint-census assertions also pass a
focused rerun, and Ruff passes for all three Python files.

The complete eight-body reconstructions match the original all-body residuals
and component rounding radii at the exact source reporting references. The
largest absolute residual among these 168 body states is
0.0008138950434499748 N and 0.47536919938170286 Nmm. Source checks retain
0.1 N and 2 Nmm. Origin moments have no substituted physical gate.

The report has 143 authenticated input files, 252 bolt states, 504 combined
receiver wrenches and 756 retained scalar-channel states. Each case preserves
568 physical boundary interfaces / 720 scalar channels. All source input files
remain untouched; all acceptance/release flags stay false.

Reproduce from the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/retained-frame-bolt-current-load-path-2026-10-01/produce.py --check > /tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01.json
.venv/bin/python -m unittest discover -s docs/wood-joints-mvp/hypotheses/retained-frame-bolt-current-load-path-2026-10-01 -p 'test_*.py' -v
.venv/bin/python docs/wood-joints-mvp/hypotheses/retained-frame-bolt-current-load-path-2026-10-01/raw_oracle.py --report /tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01.json > /tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01-raw-oracle.json
.venv/bin/ruff check docs/wood-joints-mvp/hypotheses/retained-frame-bolt-current-load-path-2026-10-01
```

The independent raw-token oracle passes 21 states, 756 raw channels
(504 bilateral SPRING2 and 252 tension-only SPRINGA), 504 combined endpoint
wrenches and 168 authenticated receiver datums. It reads strict native RF
tokens with its own parser, checks both endpoint signs and rounding radii,
reconstructs complete retained vectors, and verifies reference/origin moments
and their radii. It does not import the producer or response parser. The
reviewed freeze and projection have independent fixed byte pins; the report's
matching input-pin entries are also required. Numerical grounds remain outside
physical actions. This proves the stated token-to-report reconciliation only.

Two findings were corrected during independent review: unstable floor-port
iteration order in the reused adapter, and a missing independent hard freeze
pin in the new oracle. The scoped review receipts are
[correctness-review.md](correctness-review.md),
[testing-review.md](testing-review.md) and
[architecture-review.md](architecture-review.md). Final review disposition is
recorded in those receipts.

All three independent Luna/max reviews pass for these frozen inputs. The
correctness reviewer additionally checked all 36 case-specific retained
SPRINGA projection node/ground/owner bindings and all 252 qghost force-vector
alignment states. The largest off-axis component residual is 1.54e-12 N, inside
the propagated raw-token intervals. The oracle does not itself add an
off-axis-zero refusal or a direct SPRINGA projection-node comparison; the
producer checks the node map, and these additional current-data checks are
recorded in the correctness receipt. These are explicit future-source
coverage limits, with no current result discrepancy.

The testing reviewer independently matched every body's pre-elimination
physical-load force and moment and its propagated origin radius. Four isolated
force-sign, receiver-owner, missing-channel and origin-moment mutations refuse,
as does a forged freeze-pin report. Optional additional regression cases in
the testing receipt do not change the verified current result.

| Final artifact | SHA-256 |
| --- | --- |
| `produce.py` | `af0a9569da228a8858f23107c16c7c8b3d9e0dbb50769733b5a399743eea6e24` |
| `test_load_path.py` | `0a806d6bba1b28b53b587791b53c36e05fe6a56fa1bcff163519eae02d2c3d6d` |
| `raw_oracle.py` | `9d04a698227d42207533e23b33afa08b7031518d8c80499251cdf4d4e791e758` |
| Full report, `/tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01.json` | `f068cd5afc93c2b7027624b1fbec94ccb419f664833d920d2959f79bed661cc1` |
| Raw oracle receipt, `/tmp/mini-moonboard-retained-frame-bolt-current-load-path-2026-10-01-raw-oracle.json` | `c6d43017d67f864dfc25e6a77832a542a97257a1da23f4ca3a12e82d6a829ea9` |

The full report is a 32.3 MB local replay artifact; it is not copied into source
control. Fresh producer replays across distinct process hash seeds are
byte-identical to the canonical report. No native solve, CAD execution,
shared-file update, staging, commit or push is performed by this task. All work
uses included usage; credits and paid fallback remain prohibited.
