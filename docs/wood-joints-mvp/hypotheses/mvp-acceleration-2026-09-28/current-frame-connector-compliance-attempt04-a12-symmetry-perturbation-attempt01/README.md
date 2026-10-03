# A12-rear H symmetry perturbation diagnostic

This small read-only packet applies `Hsym = (H + H.T)/2` to the same seven
source-signed A12-rear force vectors in the authenticated attempt04 replay. It
does not edit, replace, or refreeze raw `H`; it performs no native run, body
factorization, or support-state solve. Its exact sources include the previous
replay script and assessment, A12 response/DAT, and attempt04 operator packet.

`q = D*a + e - H*f` was recomputed with raw H and with the deterministic
perturbation `(Hsym-H)@f`. Both residuals are compared to the same propagated
CCX 2.23 DAT U/RF half-last-place intervals used by the raw-H replay. The H
perturbation itself is reported separately from those intervals. `D.T*f=W`
is unchanged because D, f, and W are unchanged; the prior replay's per-step
force and moment diagnostics are copied into the assessment.

| Load factor | max rowwise `abs((Hsym-H)@f)` (mm) | Raw-H max q residual (mm) | Hsym max q residual (mm) | Raw-H / DAT bound | Hsym / DAT bound |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0.100 | 7.174e-11 | 7.499e-7 | 7.499e-7 | 0.371 | 0.371 |
| 0.200 | 1.435e-10 | 6.516e-7 | 6.516e-7 | 0.320 | 0.320 |
| 0.300 | 2.152e-10 | 1.615e-6 | 1.615e-6 | 0.397 | 0.397 |
| 0.450 | 3.228e-10 | 3.433e-6 | 3.433e-6 | 0.323 | 0.323 |
| 0.675 | 4.842e-10 | 3.134e-6 | 3.134e-6 | 0.433 | 0.433 |
| 0.925 | 6.636e-10 | 3.319e-6 | 3.319e-6 | 0.416 | 0.416 |
| 1.000 | 7.174e-10 | 7.462e-6 | 7.462e-6 | 0.386 | 0.386 |

The recorded raw-H reciprocity metric is `9.383e-11`; the largest action of
symmetrization on these force vectors is `7.174e-10 mm`. All seven Hsym q
residuals remain within the original raw-H DAT-interval gate, and the prior
`D.T*f=W` checks remain unchanged. This shows numerical compatibility for
this response only. It does not accept symmetrization as the operator for an
energy method or establish method error bounds, energy convexity, another
support state, or mechanical acceptance.

Reproduce from the repository root with:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-connector-compliance-attempt04-a12-symmetry-perturbation-attempt01/quantify.py
```

Per-increment source hashes, Hsym perturbation row identities, DAT-only
interval diagnostics, and unchanged raw-H balance diagnostics are recorded in
`assessment.json`.
