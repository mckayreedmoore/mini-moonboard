# Parent A12 fixed-active-set refinement, attempt 01

Parent read the stable [proposal](../current-a12-fixed-active-kkt-refinement-preflight-attempt01/README.md)
and its direct solve/audit code and passed the read-only input verification.
The tiny KKT known-answer and invalid/rank-stop fixtures were independently
replayed earlier. The existing 25/75 floor mask and zero held references
remain unchanged. This is a numerical check of the historical proportional
gravity-plus-climber full-load A12 episode, not staged contact selection.

The one-shot runner holds the shared mechanics lock, requires the native
ledger idle, freezes all prior source pins and new method/runner files,
and applies 180-second wall/CPU, 6-GiB memory and one-thread caps. It calls
the declared unregularized direct KKT solve once, retaining its fixed
734-row nonfloor active-bound estimate, rank and uncertainty stops and all
original physical/DAT gates. No threshold search, mask retry, force clipping,
regularization, native launch, geometry change or resistance adoption occurs.

Run once from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-fixed-active-kkt-parent-attempt01/parent_run.py
```

After execution, inspect `assessment.json`, `frozen-inputs.json` and
`output-pin.json`. The runner refuses a second launch after freezing.
Any original gate miss remains a stop even if direct KKT residuals pass.
No joint acceptance or fourth usable frame case follows from reproduction.
