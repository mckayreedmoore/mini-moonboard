# Knee bridge frame response: completed conditional replay

[knee-bridge-frame.py](knee-bridge-frame.py) exposes
`run(output, operator_directory, expected_assessment_sha256)`. Import is inert;
the parent owns readiness, serialized execution, validation and publication.
The parent completed all six zero-gap and six nominal-clearance states with
fresh planning gravity. Wrapper SHA-256:
`dbdd61f1fb7fb4367174203102ce15b22a8655a0085c98d44365efc2de3b256d`.

Supply the completed gravity producer's operator child with `operators.npz`,
`B.npz`, `row-identities.json`, `model.json`, `model-inputs.json` and
`operator-assessment.json`. The parent must explicitly supply that assessment's
SHA-256; there is no default or auto-discovered digest. Its authenticated
source/output maps, operator-ready status and actual changed mass/dead factor
supply the new loads.
The gravity producer owns unchanged H/D/B/rows and fresh F/e/W under the existing
**FILLED-BORE gross-compliance MVP** assumption. The wrapper checks unchanged
B/row bytes, connections, case IDs and source live-load fields while allowing
updated case gravity bookkeeping. It authenticates the assessment's F/e/W live
fingerprints against the pinned old arrays and checks the new live columns with
the same dtype/shape/C-order hash convention. It calculates no gravity or stiffness.

The fixed integration source is `rawlocal/knee-bridge-integration/attempt02/manifest.json`,
SHA-256 `1744bb616354159c06694e99fb239251578dba3a6e860da5391dae19b5d7026c`.
Its four internal bridge bolts remain separate frozen static allocations without
global connector rows. The global inventory stays **104 bolts / 66 screws**;
the unadopted proposal census is **108 bolts / 108 nuts / 216 washers / 66 screws**.
Those allocations are referenced, not recalculated or adopted for the new response.

The output root must be a fresh immediate child of `rawlocal/knee-bridge-frame/`.
Its `.gitignore` contains `*` plus a newline and is included in the receipt.
`NUMERICAL_SEED_ONLY/frame-response.npz` is a byte-identical copy of the pinned
original `../corner-frame-attempt01/frame-response.npz`. Minimal seed metadata
retains original source paths/hashes, old mass/dead factor, response hash and case
IDs; only the new operator's actual mass/dead factor supplies compatibility with
the runner. Each `cases` entry contains its ID alone. No historical result or
pass is copied, and the numerical force guess gains no acceptance.

The pinned [existing runner](../both_corner_frame.py) writes to `response/`,
with service joints, bottom corners, all two-receiver clearances and bounded
freeplay enabled. Climber scale stays 1: **250 lb × 2 / 300 N / 100 mm**.
No stiffness, live-component, lever or other load variant is exposed. The wrapper
binds source files before/after and writes its source snapshot, call inputs and
receipt hashes for the seed and actual response/STOP artifacts. A STOP remains
unaccepted and propagates to the parent.

Completed parent command:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/bin/python -B docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/knee-bridge-frame.py --output docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-frame/attempt02 --operator-directory docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/upper-corner-screw-layout/rawlocal/knee-bridge-gravity/attempt01 --expected-assessment-sha256 ce69ba58e3c6265d31ab0dfdec1ffac4c019b93fc1106c8f9677ed9b5b2c3f95
```

For the API, the parent likewise suppresses bytecode writes and serializes the
existing analysis slot. The proposal remains unadopted. Changed-hole elastic
stiffness, local bridge compatibility, stability, hardware qualification,
complete-joint acceptance and physical release are not established by this wrapper.

## Saved result

All 59 source pins and eight receipt artifacts match. Maximum force/moment
balance errors are **8.76e-12 N / 1.53e-8 Nmm**; finite-law and circular-gap
law errors are **1.33e-6 / 6.67e-9 N**. Zero-gap states pass the conditional
coupled laws. Nominal states pass with bounded nonunique seating; their
rank/stability limitations remain, so this is not a strict stability result.
The [fresh demand export](knee-bridge-response.md) records the changed forces;
largest connector-row change is **1.418113 N**. Panel-head demand remains
**1871.246 N**, with simultaneous lateral **726.730 N**, at upper-left `edge_2`
in A12-rear. The panel reference exception remains.

| Artifact under `rawlocal/knee-bridge-frame/attempt02/` | SHA-256 |
| --- | --- |
| `response/comparison.json` | `c3a8ff024fb494032d947aedfd6f00cda8698587b8751b2cec66e4b3af243729` |
| `response/response.npz` | `62bd4116cfb577a0846f4de0d43fbeec6bb704bac7feee530ee673ded1820f90` |
| `receipt.json` | `6acb01eb1b07dc9f9175cb3a0e916fe74a9a32a7b90941cf3b18e84a24d9c599` |
| `parent-authentication.json` | `da32ea1719fcf1bd8c3cacbb57deca9841989e3d6d852c79d7e25217116e88c0` |

The initial environment stop preceded calculation: OSQP was absent. It is
preserved under `environment-stop-attempt01/`. The parent installed OSQP 1.0.4
and used Python 3.12.3 / NumPy 2.5.2 / SciPy 1.18.1 for the fresh run.
Ruff passes. No software tests, agent review, native or CAD run occurred.
