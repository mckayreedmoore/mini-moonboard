# Zero-Hillman-withdrawal frame scenario

**Outcome: all six cases stop; no accepted no-withdrawal response exists.**
The missing upper-panel normal load path is confirmed by necessary statics,
rather than inferred from a solver timeout. Mechanical acceptance, engineering
MVP completion and physical release remain false. The reviewed geometry is
unchanged.

## Numerical result and decisive check

The corrected producer selects the exact source role
`non_qualifying_parametric_screw_withdrawal`: 66 rows, indices 1470–1535.
Their stiffness and force are constrained to exactly zero. The unchanged
`simple_frame.py` helper supplies the original floor lumping and case solver.
The first six-case calculation returned
`QP run time limit reached; no accepted response` for every case, using the
unchanged 10-second OSQP branch limit. Its 60.238-second result is retained
under `prior_numerical_attempt` in
[no-withdrawal-frame-results.json](no-withdrawal-frame-results.json).

One representative A12-rear necessary-condition calculation then used
SciPy 1.15.3 `linprog(method='highs')` on `D.T @ f = W`, omitting all removed
forces, retaining unilateral nonnegative bounds and **all** floor tangents.
Elastic spring laws and bearing-set restrictions were omitted. This gives
statics more freedom than the frame scenario. HiGHS returned status **2**:
“The problem is infeasible.” Its reported model status is 8, after 157
iterations, with 1,498 force variables and 300 body equilibrium equalities.
Primal and dual feasibility tolerances were 1e-9; one thread was requested.
SciPy reported that the `threads` option was forwarded to HiGHS verbatim.
No second six-case QP run was attempted.

## Missing restraint and original removed-row demands

Both `main_upper_left` and `main_upper_right` require restraint against
outward motion along the source normal
`n = (0, 0.766044443119, -0.642787609687)`.
This normal has a downward component, so even the distributed dead load
has a positive outward projection. The removed upper-panel rows are
1512–1523 on the left and 1524–1535 on the right: twelve screw axes each.

In the source convention `D.T @ f = W`, each removed withdrawal row has
normal coefficient +1; the retained face-compression rows have coefficient
−1. Physical spring forces on the panel have the opposite sign: withdrawal
pulls inward, while face contact pushes outward. Each upper panel has 96
normal contact rows. Retained lateral rows lie in the panel plane; their
largest normal coefficients are only 9.27e-17 left and 1.17e-16 right.
Positive unilateral normal coefficients are likewise at coordinate roundoff
(at most 1.62e-16). These directional zeros are screened at 1e-10.
Consequently, retained rows cannot supply a positive normal component of
`D.T @ f`, while all six required components below are positive.

The withdrawal sums below are reconstructed from the original, pinned
`simple-frame-response.npz`; they are parametric demands, not Hillman
capacities or accepted product behavior.

| Case | Final status | Required normal component, left/right (N) | Original withdrawal normal sum, left/right (N) |
| --- | --- | ---: | ---: |
| a12-rear | STOP | 1775.663 / 115.835 | 2957.453 / 262.780 |
| a12-forward | STOP | 1316.036 / 115.835 | 2479.060 / 260.411 |
| a12-left | STOP | 1545.850 / 115.835 | 2725.403 / 277.195 |
| k12-right | STOP | 116.219 / 1545.465 | 304.085 / 2276.276 |
| k12-rear | STOP | 116.219 / 1775.279 | 291.801 / 2560.329 |
| a1-rear | STOP | 116.219 / 115.835 | 247.272 / 225.698 |

All final case statuses are `STOP_PANEL_NORMAL_EQUILIBRIUM_SCREEN`.
For example, original A12-rear left-panel normal balance is
`2957.453 − 1181.790 = 1775.663 N`; the contact term is negative in the
source convention. Setting withdrawal to zero cannot satisfy that balance
with compression-only contacts. The largest original individual removed
upper-panel screw force is 1922.134 N, on the left in A12-rear. The same
sign conflict applies to both upper panels in every case; the HiGHS check
was performed for A12-rear only. This establishes a sufficient cause for
all six failures, without claiming to exhaust other bodies or failure modes.

## Response, checks and corner comparison

- **Accepted response count: 0/6.** Biggest no-withdrawal translation is
  unavailable; no finite displacement or numerical equilibrium pass is claimed.
- **Actual solved axial forces: unavailable.** All 66 withdrawal forces were
  constrained to zero; no accepted force vector exists in which to measure
  those zeros. [no-withdrawal-frame-response.npz](no-withdrawal-frame-response.npz)
  is an intentionally empty, 22-byte NPZ archive, with no case arrays.
- Necessary panel normal equilibrium fails. Spring-law residuals, held-floor
  motion and complete body force/moment residuals cannot be assessed on an
  accepted no-withdrawal state. The original helper gates remain 0.1 N force
  and spring law, 2 N·mm moment, 1e-5 mm held-floor motion and 10 mm source
  unilateral motion; none were loosened.
- **Top outer corner demand change: unavailable.** There is no equilibrated
  no-withdrawal state to compare with the original corner forces. Parent joint
  calculations must use the original source cases and keep their parametric
  withdrawal assumption explicit. The original largest body translation was
  4.523589 mm in K12-right; it is not a no-withdrawal result.

The real unresolved requirement is a supported panel normal load path or
applicable evidence for the actual screw withdrawal connection. A corner
calculation alone cannot close this panel requirement. This scenario adds
no restraint, changes no geometry and establishes no joint or MVP acceptance.

## Reproduction and provenance

The read-only included-usage check reported 10% used and ordinary usage
allowed. Execution used the existing shared file lock and required an idle
analysis ledger. Heavy work is complete and the lock is released.

```sh
export PYTHONDONTWRITEBYTECODE=1
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 /usr/bin/timeout --signal=KILL 180s \
  uv run --offline --no-project --python 3.12 \
  --with numpy==2.2.6 --with scipy==1.15.3 --with osqp==1.0.4 \
  python docs/wood-joints-mvp/hypotheses/mvp-resume-2026-10-01/simple_frame_no_withdrawal.py
```

The current producer performs the representative statics discriminator and
six panel normal screens; the earlier six QP timeouts remain in the JSON.
Exact source, original-response, helper, producer and output hashes are
recorded there. All three frozen operator/identity/assessment pins and the
original simple-frame helper, results and response were unchanged before
and after calculation. The helper SHA-256 remains
`3d8c14cccf9306766a4993bad9ea39501bbc9c812af9e79b393875d5d3c09d34`.
The original response SHA-256 remains
`7ca2131e9f636437c00cf15c69be79bcd93ee33b1cd069af7550f35a42d25996`.

Only the four assigned files were written. Scoped Ruff check and format
checks passed. No software tests, native solves, additional agents, staging,
commits, branches or pushes were performed. These four files remain the
active evidence for this bounded scenario; no raw-run archival or deletion
is needed.
