# Service-upper verification, September 30, 2026

The bounded service extraction passed its frozen source gates, unchanged
hardware/screw inventory guards and 84 force/moment balance reconstructions.
The four selected blocks retain all sixteen incident connection records and
source body loads per increment. Maximum raw residual norms are about
1.29e-5 N and 5.60e-4 N·mm, within the source 0.1 N / 2 N·mm bounds and
propagated DAT-rounding checks. Source balance results are reproduced.

The [direct native-token checker](check.py) reads the already existing
DAT RF tokens, uses the frozen scalar-carrier mappings and reconstructs
336 physical lateral vectors and 672 signed member directions. It writes
[verification.json](verification.json). Maximum vector difference is
6.31e-30 N; maximum grain-component difference is 3.55e-15 N and maximum
loaded grain-end difference is 6.75e-14 mm. This checks export bookkeeping,
not native solver behavior, bolt/contact laws or resistance.

A separate Luna agent at maximum reasoning effort independently projected
all 32 upper thread-bearing stacks, including reversed rail head order,
and verified the 24 × 127 mm / 8 × 177.8 mm counts. It found no concrete
mapping or six-mode calculation error in [partial_thread.py](partial_thread.py)
and reproduced its output. The producer also tests thread-start coordinates
one micrometre below and above each inverse quarter-bearing threshold.
The existing diameter-selector test covers exact-quarter inclusion.
That focused test also passed in this packet's final validation.

The pinned NDS-2024 bolt-axis method distinction and the arithmetic of the
declared principal/G7 interpolation were independently checked by another
Luna agent at maximum reasoning effort. It independently reproduced all
336 branch records and 84 minima. A final source audit separated the
normative 2024 chapter from the absent 2024 Commentary. The interpolation is
supported by official historical Commentary and remains unadopted; exact
2024 Commentary applicability is not claimed. The
[method note](method-correction.md) records this source boundary. Finished
geometry hashes and known-answer fixtures are checked by [end_branch.py](end_branch.py).

From the repository root, read-only byte-identical replay is:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/service-upper-frame-joint-review-2026-09-30/produce.py --verify
.venv/bin/python docs/wood-joints-mvp/hypotheses/service-upper-frame-joint-review-2026-09-30/check.py --verify
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/service-upper-frame-joint-review-2026-09-30/partial_thread.py --verify
.venv/bin/python docs/wood-joints-mvp/hypotheses/service-upper-frame-joint-review-2026-09-30/end_branch.py --verify
```

Changed frozen sources stop replay. The service wrappers verify the archived
producer/checker hashes before reuse; earlier files remain unchanged.
Ruff checks and formatting cover the four packet scripts. No native solve,
geometry alteration, adopted factor/capacity, six-case claim, inspection or
physical release follows from these checks.
