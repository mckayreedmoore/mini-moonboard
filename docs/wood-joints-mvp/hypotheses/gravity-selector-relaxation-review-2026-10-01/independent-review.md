# Independent review: redundant unilateral-law inequalities

**Reviewed:** 2026-10-01. **Finding:** the two proposed global inequalities are
valid for every exact unilateral source-law state. They are redundant for the
integer model, and could strengthen a relaxation. The frozen records do not
show whether SCIP already derives equivalent bounds or whether adding the
rows would improve runtime.

I independently checked the frozen method and selector inputs. All thirteen
paths in the selector's `inputs.json` match their recorded SHA-256 values; the
assessment also matches its output pin. The method hash is
`953659834d56c1f1614cdc6359afff4e7eb7ca5df70f32e2ed8b1c03050de04c`, the
selector hash is `5ad1e656a10871a53c713702082b0e19d028aff05483cbd1b1e1e86f2471b821`,
and its assessment hash is
`fec6e3b0d498439f858bd6c555202c25e4e96eff90d902e95e3fd68e571f4b34`.

The pinned projection contains 1,292 `unilateral_springa` rows, 348 bilateral
rows and 200 floor-tangent rows (projection hash
`4ceca771e26e1f1d0bf8efca8e3d77dc6d94194553d95e1fd75652ecf2f3f2d3`). The
unilateral source stiffnesses are positive; their minimum is
436.78276397458944 N/mm. In the method, each such row uses one binary `z` and
the two exact branches:

| Branch | Constraints | Consequence |
| --- | --- | --- |
| `z = 1` | `q >= 0`, `f = k*q` | `f >= 0`, `f >= k*q` |
| `z = 0` | `q <= 0`, `f = 0` | `f >= 0`, `f >= k*q` because `k > 0` |

Thus unconditional `f >= 0` and `f - k*q >= 0` rows for those unilateral
indices preserve every exact branch state, including `q=f=0`. They do not
apply to the bilateral or tangent rows, whose force signs are not restricted
by these unilateral branches. The method already places the sign and spring
equalities inside indicators; it does not currently add `f >= k*q` globally.

This logical proof establishes validity for the integer disjunction, not a
solver speedup. The stopped A12 assessment reports `BUDGET_OR_SOLVER_STOP`,
SCIP `timelimit`, zero solutions and 46.823 seconds elapsed; no presolve
statistics or transformed-model bounds are recorded. The selector script
hides solver output. Its result neither demonstrates that presolve misses the
inequalities nor that the 45-second stop was caused by their absence. The
small pinned known-answer fixture is not evidence about presolve or runtime
for the 1,292-row frame model. Whether SCIP 10.0.2 derives either inequality
on this model remains unanswered by the inspected record.

I agree with the parent README's recommendation to treat the rows only as an
optional formulation strengthening for the mechanics owner to assess. Any
authorized comparison should keep the source indicators and physical gates,
check the same admissible states, inspect presolve/transformed bounds, and
report construction, presolve and solve outcomes separately. No solver,
native run or fixture replay was performed for this review.

The parent README inspected here has SHA-256
`031600277b90e56ae2808f9dd93703d8558c2dbd96ea2378d731443d0b85d9ee`.
Other inspected source hashes: reduced-method assessment
`509509a6da7c34d129e93baffa5eb99d69d7df11b75747a1ca3fccbc4037a7af`,
projection join contract
`607ec82a8f830101a5bed07a9d1214aa85ac09179a9091472f7c951671ed8c4e`,
and selector input record
`54fd5bb8b0c310f4a8dcf1b125d99bcc0ef03fef13fb28e7aebcfc0a5c46a4bc`.
