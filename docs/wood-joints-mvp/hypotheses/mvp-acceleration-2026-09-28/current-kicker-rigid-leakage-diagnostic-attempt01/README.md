# Kicker rigid-leakage equation diagnostic

This packet explains the `kicker_left`, interface columns 16–31 stop in
connector-compliance attempt02. It reconstructs the exact source-bound chunk,
then checks the parent-saved last improving iterate against the frozen body
operator. It does not refactor that body, recompute compliance, launch a native
solve, or accept a frame response.

For the saved iterate, the bordered equations use
`K u + R lambda - p = r` and `R.T u = 0`. Premultiplying the first equation by
`R.T` gives `R.T K u + (R.T R) lambda - R.T p = R.T r`. On this chunk, the
maximum `R.T K u` and `(R.T R) lambda` terms are both about `2.94e-7 N` with
opposite signs. The projected-load wrench is only `2.36e-16 N`; the rigid
equation closes to `4.04e-13 N`, matching `R.T r` to `2.12e-18 N`. Solving this
small six-coordinate identity predicts the saved maximum multiplier within
`7.73e-15 N`. The saved iterate has a maximum upper-force residual of
`1.84e-11 N` and gauge residual `2.18e-17 mm`.

That identifies the multiplier as a consequence of the exported operator's
small but nonzero rigid coupling `K R`, rather than evidence of an inaccurate
KKT factor solve. The original zero-multiplier gate still fails:
`lambda_max = 1.64e-9 N` exceeds its recorded `2.0e-10 N` tolerance. The saved
array is correction 3, the last improving iterate; correction 4 is the
rejected stagnating candidate listed at the end of the history.

The pinned CalculiX 2.23 source archive is
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`;
`matrixstorage.c` SHA-256 is
`2b2a502637761a7663e50e43a7f5afe9322c6c775aa6c44fd7b433976bbe59c4`. Its
two symmetric-matrix writer statements use `%20.13e`, or 14 significant
decimal digits. The computed per-entry serialization bound is enough to cover
the observed `K R` scale, and the authenticated one-element cube has similar
rigid leakage (`3.51e-15` in the common infinity-norm metric) while its
independent constant-stress traction, displacement, and energy checks pass.
This makes text rounding a plausible contributor; the unrounded assembled
matrix is unavailable, so the source does not prove that serialization alone
caused the leakage.

The original attempt therefore remains stopped under its declared gate. A
separate elastic-quotient method may be reviewed: solve on the rigid
orthogonal complement, retain and report the multiplier and unprojected
`K u - p` residual, and enforce projected force and gauge checks. Its
per-body rigid-leakage screen must be explicit. That method must keep the raw
connector wrench map `D`, load wrench map `W`, and global balance `D.T f = W`;
the multiplier is never support. This diagnostic itself does not run that
method on the frame or produce an accepted compliance matrix.

Reproduce the equation and cube checks with:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-kicker-rigid-leakage-diagnostic-attempt01/equation_diagnostic.py --verify
```

`packet.json`, `parent-result.json`, and `parent-iterate.npz` retain separate
input, solver-result, and saved-iterate pins. `equation-assessment.json`
records the rigid identity, writer pin and rounding bound, known-cube replay,
and the explicit no-compliance/no-acceptance limits.
