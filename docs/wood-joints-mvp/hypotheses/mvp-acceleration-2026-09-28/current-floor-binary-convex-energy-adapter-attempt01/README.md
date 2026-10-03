# Tiny floor-binary convex-energy adapter — attempt 01

This packet tests a small borrowed-solver formulation for selecting a floor
episode mask. It is limited to the eight pinned analytical selector cases and
the two-carrier raw-wrench KKT oracle. It does not load the current frame
operator, factor, geometry or loads, and it does not solve a frame state.

## Method

For a symmetric positive-definite fixture operator, the producer verifies
`H_sym = L L.T`, sets `y = L.T g`, and expresses compatibility as
`q = D a + e - L y`. The SCIP model has signed, unbounded `a`, `y`, and `q`
coordinates. Every ordinary unilateral spring uses the convex hinge
`s >= sqrt(k)*q`, `s >= 0`; there are no ordinary-spring binaries. Bilateral
energy is normalized with `z_i = sqrt(k_i)*q_i`, so each spring contributes
`.5*z_i^2` instead of placing `k_i` in the quadratic epigraph. Only floor
cells have binaries: closed means `q_n >= 0` and each supplied `q_t` equals its
episode reference; open means `q_n <= 0` and leaves `q_t` unconstrained. The
recovered open tangent effort must be zero.

SCIP minimizes a linear objective with a convex quadratic energy epigraph. Its
output is a provisional optimizer candidate for one mask. Each returned mask
is then independently polished by a fixed-mask convex QP in OSQP. The QP is
not a second mask selector. A polished state is accepted only if it satisfies
raw equilibrium, the raw-operator compatibility audit, each original spring
force law, all floor sign/reference conditions, and zero floor-normal
bound-reaction error. Thus a constrained energy minimum with a spurious
normal-bound reaction is recorded as rejected even when it is the best energy
candidate for that mask.

For the raw-operator audit, the QP coordinate map independently forms
`q_sym = D*a + e - H_sym*g`; the verifier separately forms
`q_raw = D*a + e - H_raw*g`. Their maximum difference is checked, and the
original force laws are evaluated using `q_raw`. A deliberately injected
`2e-11` skew probe produces a recorded nonzero `2e-11 mm` compatibility
residual, demonstrating that the check is not an identity. The probe remains
inside this tiny fixture's `2e-7 mm` acceptance tolerance.

## Known-answer result

The stored [assessment.json](assessment.json) is produced from the two pinned
fixture packets listed in its `source_sha256` map and their upstream source
pins. Replay enumerates all 24 masks across the eight cases. It recovers the
expected classifications: one zero-force boundary ambiguity, one held
reference state, one no-state result after rejecting both bound-contaminated
minimizers, one pair of distinct admissible states, and four two-cell
one-mask results. Accepted polished states have zero reported source-law and
floor-normal bound-reaction error at the recorded precision. The independent
generalized-force oracle checks `D.T*g = W` with one bilateral and one
unilateral spring; its fixed-mask OSQP polish returns the known
`a=0.3`, `g=(0.5, 1.0)`, and `q=(0.5, 0.5)`.

The stored source and producer hashes bind the exact fixture inputs and this
producer. The stored assessment contains numerical results, solver/runtime
versions and checks, but no nondeterministic wall-clock duration.

## Reproduction

From the repository root, run with the recorded package versions and one BLAS
thread:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-project \
  --with pyscipopt==6.2.0 --with numpy==2.5.2 \
  --with osqp==1.0.4 --with scipy==1.18.1 \
  python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-floor-binary-convex-energy-adapter-attempt01/verify_adapter.py --verify
```

Use `--write` instead of `--verify` only when intentionally regenerating the
assessment after review. The implementation follows the pinned PySCIPOpt
documentation that SCIP takes a linear objective and supports an equivalent
epigraph-variable formulation for a nonlinear objective: [PySCIPOpt 6.2.0
FAQ](https://pyscipopt.readthedocs.io/en/v6.2.0/faq.html) and [nonlinear
expressions tutorial](https://pyscipopt.readthedocs.io/en/v6.2.0/tutorials/expressions.html).

## Limits

This result demonstrates a tiny formulation and a fixed-mask polishing check;
it does not establish frame-scale conditioning, runtime, or solver success.
The toy no-state classification is valid because every mask in that toy is
enumerated. Rejecting one constrained-energy minimum on a larger problem does
not prove the physical problem has no state in another untested mask. Energy
ranking does not select physical history, resolve a zero-force event, prove
floor episode uniqueness, or establish any gravity-settling or climber-ramp
state. A frame application needs its own bounded search and must stop on
budget, unresolved multiplicity, event ambiguity, or a failed raw/source-law
check. No native run, geometry edit, physical acceptance, or frame state is
included here.
