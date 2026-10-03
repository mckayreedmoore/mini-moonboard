# Elastic quotient method preflight, attempt 01

This isolated fixture checks the proposed elastic quotient on the authenticated
free C3D20 cube. It solves with the original, unmodified bordered matrix
`[K R; R.T 0]`; refinement reuses that same factor for at most five
corrections. The quotient screen accepts a balanced basis RHS when the
projected elastic force and gauge residuals pass, while preserving `lambda`,
the original `K u - p` residual, and its six raw body-wrench components.

The implementation is in [quotient_method.py](quotient_method.py), and the
replayable known-answer check is [verify_quotient.py](verify_quotient.py).
Run it with `.venv/bin/python verify_quotient.py`; use
`.venv/bin/python verify_quotient.py --verify` to compare with
[assessment.json](assessment.json).

The fixed screens are: induced-infinity `||K R|| / (||K|| ||R||) <= 5e-14`,
KKT and projected elastic force residuals each at most `1e-10` relative to
`max(1 N, ||p||∞)`, `||R.T u||∞ <= 2e-10 mm`, and the actual rigid identity
`R.T K u + R.T R lambda - R.T p` within `1e-10 N` absolute plus `1e-10`
relative to its term scale. Products and residuals are evaluated in extended
precision; the existing factor remains double precision. The `5e-14` rigid
leakage threshold is a numerical screen, not a certified bound on assembly
error. The pinned `%20.13e` stiffness writer and its coefficient-token
round-trip are recorded, but finite-element assembly roundoff remains
unbounded.

The six-face constant-traction test compares the quotient solve to an
independent 54-coordinate elastic solve and affine displacement/energy
answers. A deterministic rigid-elastic coupling perturbation leaves the
projected elastic operator, displacement, and energy unchanged. Corrupted
elastic/gauge states fail their strict gates, and an unbalanced point load is
rejected before the factor is called. The saved `kicker_left` chunk is only an
audit of its existing iterate: it passes these quotient numerical screens,
while its previous zero-lambda gate still reports `FAIL`. That diagnostic is
not a new factorization or accepted connector response.

For parent integration, call `solve_quotient_chunk(factor, system, K, R, p,
operator_report=...)` once per balanced projected RHS chunk. The operator
report may be reused for later chunks of the same authenticated body matrix.
The global caller must retain all 300 raw rigid equilibrium coordinates and
enforce `D.T @ f = W`; projecting connector basis columns does not equilibrate
raw gravity or point loads. Existing native force/moment gates of `0.1 N` and
`2 N mm` are unchanged and were not evaluated here.

This preflight computes no current-frame `H`, full-frame state, or native run.
It does not establish mechanical acceptance, fabrication readiness, or a
climbing release. Parent review is required before any attempt03 computation.
