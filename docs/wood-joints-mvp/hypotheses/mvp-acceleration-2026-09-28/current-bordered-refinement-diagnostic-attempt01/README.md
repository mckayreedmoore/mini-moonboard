# Bounded bordered-solve refinement diagnostic

This isolated diagnostic tests a bounded way to improve the existing sparse
free-body KKT solve after a strict residual gate fails. It leaves the
factorization and original stiffness matrix unchanged. It does not calculate a
physical response for the parent frame case and does not establish mechanical
acceptance.

The reusable implementation is `bounded_refinement.py`. For each right-hand
side block it evaluates `r = b - A x` in `numpy.longdouble`, then asks the same
existing float64 SuperLU factor to solve for the correction `delta`; it updates
`x += delta` and checks the original force, gauge, and multiplier gates again.
It stops after at most five corrections, on non-finite values, or when the
componentwise backward error improves by less than 0.1% in a step. The strict
gates remain `1e-10` for relative KKT force residual and `1e-10` absolute plus
`1e-10` relative for gauge displacement and gauge multiplier. A failed or
stagnated check returns an unresolved status; neither the gauge multiplier nor
any rigid wrench is treated as physical support or discarded.

SciPy's [`splu` documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.linalg.splu.html)
documents an `IterRefine` option for the SuperLU factorization options, and the
[SuperLU guide](https://portal.nersc.gov/project/sparse/superlu/ug.pdf)
describes its expert-driver refinement modes. For the pinned local SciPy
1.18.1, however, the [`SuperLU.solve` implementation](https://raw.githubusercontent.com/scipy/scipy/v1.18.1/scipy/sparse/linalg/_dsolve/_superluobject.c)
calls `gstrs` directly. A small runtime probe with and without
`options={"IterRefine": "EXTRA"}` returned bitwise-identical `.solve` results.
Thus this diagnostic performs and checks its own correction steps instead of
assuming the option causes refinement on `.solve` calls.

`verify_diagnostic.py` exercises the same projected bordered-solve path on the
authenticated small cube. The nine-column compliance result agrees with the
saved dense `QKQ` reference within `2.49e-14 mm/N`, with zero correction steps;
the relative force residual is `2.49e-15`, the gauge residual is `1.69e-15 mm`,
and the maximum gauge multiplier is `9.26e-13 N`. Separate fixtures confirm
that a deliberately corrupted initial result corrects in one step, non-finite
values reject, stagnation returns unresolved, and a slowly improving factor
stops at exactly five corrections.

The exact parent failure packet is checked read-only: `main_lower_left`, 6,567
DOFs, 920,143 stiffness nonzeros, and the 16 interface columns at source row
positions 268–275 and 568–575. The saved raw rigid wrenches and the projected
right-hand sides replay from the pinned basis. This script does not factor or
solve that body packet. The parent reported its double residual as
`7.23261944e-10`; evaluating that same solution in extended precision gives
`3.00920477e-10`, still above the unchanged `1e-10` gate. Those observations
motivate the correction diagnostic, but do not mean the corrected parent
columns pass; only the parent-owned replay can determine that.

Replay the fixture and read-only packet checks from the repository root with:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bordered-refinement-diagnostic-attempt01/verify_diagnostic.py --verify
```

`assessment.json` records the fixture outputs, code hashes, exact input packet
hashes, source row identities, and the explicit `physical_response_computed:
false` and `mechanical_acceptance: false` limits.
