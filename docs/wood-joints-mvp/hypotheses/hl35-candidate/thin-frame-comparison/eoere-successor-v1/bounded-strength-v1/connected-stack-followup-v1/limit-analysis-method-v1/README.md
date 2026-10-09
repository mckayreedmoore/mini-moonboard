# Synthetic bearing and bolt-bending benchmark

This verifies a small **one-dimensional synthetic method** that limits both
bearing density and bolt bending. It addresses a method gap in the frozen
[affine bearing trial](../README.md), which equilibrates prescribed actions
without limiting the resulting bolt moment. It does not calculate any of the
eight frame joints or use a candidate force field, geometry or material value.

All 15 synthetic cases pass at three discretizations: nine published TR12
Example 3.1 input combinations and six additional coupons whose governing raw
yield modes cover Im, Is, II, IIIm, IIIs and IV. The 128-cell/member statics
loads fall below the analytical raw values by at most **0.005209%**. The
independent checker integrates all 45 recorded fields and checks every interior
moment extremum. A second run matches every output byte.
Candidate joint resistance remains **null**.

## Method and its boundary

The side and main bearing intervals are `[0, Ls]` and `[Ls + g, T]`, where
`T = Ls + g + Lm`. Each interval is split into uniform cells with independent
signed constant density `q_i`. The optimization maximizes the nonnegative
synthetic load `P`, subject to:

```text
|q_i| <= the supplied member bearing bound
integral(side q ds) = P
integral(main q ds) = -P
integral(all s q ds) = 0
M(x) = integral(0..x (x-s) q(s) ds)
|M(x)| <= the supplied constant bolt moment bound
```

The two force equations close shaft shear. The first-moment equation closes
shaft moment with zero end fixity. For a cell `[a,b]`, its contribution to
`M(x)` is `q_i * ((x-a)_+² - (x-b)_+²) / 2`. Moment is quadratic inside a
bearing cell and linear in a gap. The calculation constrains cell boundaries,
then adds constraints at any violating interior zero-shear point and resolves.
Up to six rounds were needed. Node checks alone are insufficient.

The finite cell space restricts the available bearing distributions. After
checking all exact quadratic extrema, a small uniform numerical rescaling
removes solver/cut tolerances from the recorded statics field. The minimum
scale was `0.9999999513051341`; it is a numerical correction, not a design
factor. These fields provide feasible statics loads within the documented
numerical tolerances for this idealized scalar model. No stiffness or
deformation compatibility is solved, and no physical pressure distribution
is predicted.

The existing [TR12 helper](../../../../../../../../../fea/dowel_yield.py)
supplies the six analytical **raw** yield comparisons. Published rounded
Example 3.1 references are separately checked to 0.51 lbf; the maximum
difference is 0.5 lbf. The numerical optimization is compared before any
mode-specific reduction term. Applying a single reduction term to its minimum
would not reproduce the mode-by-mode design-value procedure.

| Synthetic governing mode | Analytical raw load, lbf | 128-cell statics load, lbf |
| --- | ---: | ---: |
| Im | 12.5 | 12.499999999975 |
| Is | 12.5 | 12.499999999975 |
| II | 5.177669530 | 5.177399862 |
| IIIm | 4.274587829 | 4.274559287 |
| IIIs | 4.274587829 | 4.274559287 |
| IV | 7.759180474 | 7.759180474 |

## Verification and source basis

[Inputs](inputs.json) pin the existing helper and its published-example tests,
`uv.lock`, the preceding frozen results, Python, NumPy 2.5.2, SciPy 1.18.1,
HiGHS 1.12.0 and the installed SciPy wrapper bytes. The
[AWC TR12 source](https://awc.org/wp-content/uploads/2021/12/AWC-TR12-1510.pdf)
is the 2012 edition with 2015 copyright, Table 1-1, Part 2 and Example 3.1;
its use here is a synthetic benchmark, not adoption of a current multi-member
design method. The earlier 2026 source-access limitation remains unresolved.

The [pinned SciPy source](https://github.com/scipy/scipy/blob/v1.18.1/scipy/optimize/_linprog_highs.py)
and installed documentation establish the used dual-simplex interface, signed
bounds, status codes, tolerances and marginal conventions. The
[online API](https://docs.scipy.org/doc/scipy/reference/optimize.linprog-highs-ds.html)
identifies version 1.18.0; this version distinction is recorded in the inputs.
The benchmark explicitly selects `highs-ds` with signed bearing bounds and
requires optimum status zero. It checks primal residuals, dual signs,
stationarity and primal/dual objective agreement. The largest normalized
certificate residual is `6.67e-16`.

[The retained checker](verify.py) uses dimensional direct integration of the
recorded cells, independently of the producer's normalized matrix and prefix
recurrence. It checks the original coupon intervals and bounds, all forces,
moments and interior peaks. Its maximum member-force residual is
`9.10e-13 lbf` and end-moment residual is `3.39e-12 lbf·in`.

Signed-variable, infeasible-status and unbounded-status known answers pass.
The intentionally wrong nonnegative-only bearing control admits zero load.
Loosening the moment cap permits 2.61 times the mode-IV coupon load, confirming
that bending limits matter. Five invalid parameter controls and four
corrupted-evidence controls are rejected. Reusing an existing output directory
is rejected before writing, with issued result/detail bytes unchanged.
See the compact [result](result.json) and [verification](verification.json).

## Reproduction and retention

Run from the repository root using two new output directories. Existing
directories are deliberately refused; choose fresh names rather than clearing
old runs.

```bash
packet_dir=docs/wood-joints-mvp/hypotheses/hl35-candidate/thin-frame-comparison/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1
method_raw=fea/generated/thin-bolted-current-contact-v1/eoere-successor-v1/bounded-strength-v1/connected-stack-followup-v1/limit-analysis-method-v1
uv run python "$packet_dir/analyze.py" --out "$method_raw/reproduce-01"
uv run python "$packet_dir/analyze.py" --out "$method_raw/reproduce-02"
uv run python "$packet_dir/verify.py" --run "$method_raw/reproduce-01" --replay "$method_raw/reproduce-02" --out "$method_raw/reproduce-01/verification.json"
```

The issued run is `attempt03`; `replay` has byte-identical result/detail JSON.
The initial prototype is retained in `attempt01`. `attempt02` preserves its
inputs and source before import cleanup with successful exploratory results. Detailed
bearing fields stay in ignored output. No CAD, frame solve, geometry change,
physical work, shared staging or pruning occurred. The source, inputs, compact
results and checker remain active method evidence; all raw attempts remain
recoverable and no archive/prune operation is proposed.

Before using this method for the mixed stacks, establish the appropriate
vector bearing/bending interaction, member-wrench constraints, matched current
force fields, material and thread/moment profiles, and a justified reference
design route. Axial/washer contact, bracket bearing/heel behavior, group
action, splitting, restraint and complete joint resistance remain separate
questions. Panel/screw remedies remain paused. This benchmark supplies no
candidate strength pass or fabrication release.
