# Actual 50-body elastic positivity audit

The parent evaluated all 50 isolated timber operators from the authenticated CalculiX export. Every body passes the known-answer-verified rigid-lift Cholesky and reciprocal-condition check. Runtime for the sequential body loop was 13.255 seconds under a 180-second CPU/wall and 6 GiB address-space cap, single BLAS thread. Largest blocks have 6,567 physical DOFs. The shared native run lock was held throughout; no native run occurred.

Minimum estimated reciprocal one-norm condition was `9.939426220484847e-11`, on `main_lower_left`, above the declared `1e-12` numerical floor. Maximum normalized six-mode rigid residual in this audit is `2.2150368034685093e-14`. Original physical K is unmodified. The lift adds `gamma*Q*Q.T` only for the numerical definiteness audit, with Q spanning the source-coordinate six rigid modes. It supplies no floor support or physical reaction.

This is numerical evidence that the isolated elastic operators can proceed to reaction-free reduction under the recorded tolerances. It is not an exact symbolic rank proof, an assembled frame tangent, a support/contact state, a load response or structural acceptance. The next reduction must retain `R.T*(F-B.T*f)=0` explicitly for every body; an intermediate projected elastic RHS cannot replace those physical balances.

[inputs.json](inputs.json) pins the native outputs, source model, helper, fixture result and assessment code; Python sources are snapshotted. [assessment.json](assessment.json) records all 50 results and condition estimates. Assessment SHA-256: `2ad8c74b4a061ee9335c3b9f3549f325929be9148d1753f370998ec5e681c563`. The one-shot producer refuses an automatic rerun. To authenticate recorded provenance without repeating the heavy numerical check:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-body-elastic-positivity-audit-attempt01/assess_bodies.py --verify-record
```
