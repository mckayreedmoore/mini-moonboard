# A12 selector root-stop diagnosis, attempt 01

This read-only audit identifies a plausible formulation risk behind the
recorded A12 gravity-direction selector stop. It does not identify the solver
subroutine that consumed the time, prove that the model is unbounded, or
establish a physical state. The frozen run reached one node in 45 seconds with
no incumbent and no finite dual bound. Its log contains presolve and overall
status only; it has no root-separation or subroutine timing breakdown.

The pinned selector uses

```text
q = D*a + e - L*y,       g = L^-T*y
minimize eta - W_g^T*a,  eta >= convex spring-energy expression
```

The 300 `a`, 1,840 `y`, 1,840 `q`, and scalar `eta` variables have no finite
bounds (`lb=None`, `ub=None`). The selector encodes 100 conditional floor
normal states and 600 indicator constraints; an all-open floor state leaves
the 200 floor tangent coordinates without held-reference equations. The
reported presolved model had 5,973 variables, 4,333 constraints and one
nonlinear energy epigraph constraint.

The recession test is row-subset-specific. Let `D_energy` contain connector
rows carrying spring energy on a declared branch. A candidate direction `v`
must satisfy `D_energy*v = 0`, keep any held floor-tangent rows unchanged, and
keep all unilateral hinge active-side/sign and floor-normal inequalities
feasible along the chosen ray. Released floor-tangent rows are omitted from
`D_energy`; their `q` may change freely without energy or floor-admissibility
cost. Along such a feasible ray, `a -> a + t*v` with `y` fixed leaves the
energy unchanged and changes the objective by `-t*(W_g^T*v)`. If raw gravity
work has the objective-decreasing sign, the branch objective is unbounded
along that ray; zero work leaves a flat coordinate. Near-null directions can
instead yield weak curvature and extreme displacement scales.

This is distinct from an exact null of the full projected `D`. If `D*v = 0`
exactly, then adding `D.T*g = W_g` makes any branch with `W_g^T*v != 0`
infeasible, because multiplication by `v` gives `0 = W_g^T*v`. With zero
work, the full-D gauge remains compatible and flat. A no-floor-tangent
`D_energy` null can have nonzero entries in released tangent rows, so it need
not be a full-D null. Raw equilibrium can then be balanced by nonzero
released-row `g_T`; that violates the physical release law `g_T = 0`. The
equilibrium equality alone is insufficient unless released-row laws are also
imposed and audited.

The stored evidence is numerical, not an exact null certificate. The
all-normal/no-floor-tangent 1,640-row screen reports rank 297 and nullity 3 at
relative cutoffs `1e-10` and `1e-12`, then rank 300 at `1e-14`. The full
1,840-row all-bearing envelope reports rank 300 at its recorded cutoffs. The
all-open bilateral-only screen has 80 numerical modes at `1e-10` (six common
plus 74 relative), but gravity work on those 74 was not evaluated. None of
these screens identifies the actual gravity-start contact branch or proves
an exact recession direction of the stored matrices.

The three common planar modes in the optimistic all-normal/no-floor-tangent
row screen have normalized row residuals about `2.5–2.9e-14`. The A12-rear
gravity virtual work is about `4.2e-16 N mm` in `Tx`, `-2.8e-13 N mm` in
`Ty`, and `2.8623e-10 N mm` in `Rz`; the maximum absolute work over the six
recorded gravity maps and these modes is `4.0899e-10 N mm`. These values are
below the source review's `1e-8 N mm` screen but are not bitwise zero. The
all-open bilateral-only kinematic screen has 80 numerical null directions at
cutoff `1e-10` (six common modes and 74 additional relative mechanisms); rank
changes at tighter cutoffs. That screen did not calculate gravity work on the
74 additional modes. Neither screen identifies the actual gravity-start
contact branch.

The log's SCIP sentinels (`Primal Bound +1e20 (0 solutions)`, `Dual Bound
-1e20`, infinite gap) document that no finite incumbent or dual bound was
reported. They do not mean SCIP proved unboundedness. The run could have
stopped while working on a weak or difficult root relaxation. The current
evidence cannot distinguish that performance hypothesis from other causes.

An explicit raw equilibrium equality `D.T*g = W_g`, with `y = L.T*g`, is a
valid candidate strengthening. In the original fixed-floor-mask convex
energy formulation, stationarity with respect to free `a` gives exactly this
force balance; floor state constraints act on `q` and add no `a` term. Thus
every exact physical branch optimum already satisfies the equality. Adding it
can cut non-equilibrated relaxed points, but its effect on SCIP's root bound
is untested. For an exact full-D null with nonzero work it makes the branch
infeasible; for a D_energy-null direction changing released tangents it may
not suffice unless `g_T = 0` is enforced. In an augmented optimization its
multiplier enters `g`-stationarity, so an early-stop feasible point still
needs independent raw compatibility and source spring/tangent-law checks.
The equality alone is not a physical-state certificate.

The bounded next check is to add this equality only to the existing small
bilateral, unilateral, boundary, no-state and multiple-state fixtures. Verify
that the exact admissible states and classifications remain unchanged, and
add exact-zero-work and deliberately perturbed-work gauge toys. Do not project
raw `D` or `W`, add an arbitrary anchor, or retry the frame with a larger
budget. If those toys pass, the parent can separately decide whether a
revised root formulation merits review. A frame use would first require a
raw-operator gauge/load compatibility certificate with declared units and
tolerances; a cutoff-sensitive SVD is not an exact null proof.

PySCIPOpt 6.2.0 documents `lb=None` and `ub=None` as unbounded variable
sides. Its pinned FAQ/tutorial describe the linear-objective epigraph pattern
used here. That validates the modeling pattern, not its root-bound quality or
performance for this model:

- [PySCIPOpt 6.2.0 model API](https://pyscipopt.readthedocs.io/en/v6.2.0/api/model.html)
- [PySCIPOpt 6.2.0 FAQ](https://pyscipopt.readthedocs.io/en/v6.2.0/faq.html)
- [PySCIPOpt 6.2.0 expressions tutorial](https://pyscipopt.readthedocs.io/en/v6.2.0/tutorials/expressions.html)

Reproduce the hash/algebra-record replay from the repository root:

```bash
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-root-relaxation-diagnosis-attempt01/diagnose.py \
  --verify
```

The replay hashes the frozen selector inputs, source copies, solver log,
assessment, source-only rank/operator reports and this packet's producer. It
does not load operator matrices, run a solver, rebuild `H`, or change geometry.
The machine-readable findings and exact source pins are in
[`diagnosis.json`](diagnosis.json).
