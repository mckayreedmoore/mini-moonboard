# Constrained native elastic export

The one serialized pinned-2.23 run exited zero in 0.3873 seconds and emitted stiffness, mass and equation-map files. Exact source/input verification and scoped independent review preceded the run; container termination was confirmed.

The stiffness has 58 independent translations, omitting exactly SPC (1,1) and MPC-dependent (9,1). All 36 compatible affine cross-energies match the independent rotated orthotropic plus projected-spring oracle: maximum discrepancy 1.21645e-11 N/mm. Five allowed rigid modes remain, with no significant negative stiffness eigenvalues. The material rotation is 37 degrees; the projected SPRING2 tangent is covered by the +25 N/mm xx cross-energy contribution.

The offset and load-work probe is algebraic, not an observation of native capture or loads: the nonzero reference remains outside the frequency tangent. The mass matrix was emitted but is not evaluated in this constrained coupon.

[Assessment](assessment.json), [replay](assess.py), [exact freeze](freeze.json), [review](independent-review.json), [execution](execution.json) and [input proposal](../current-constrained-elastic-operator-export-preflight-attempt01/README.md) preserve scope and provenance.

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-constrained-matrix-export-native-attempt01/assess.py --verify
```

This establishes a tiny SPC/MPC/spring mapping and rotated-material affine-energy method. It does not establish the actual frame operator, distorted-element behavior, gravity state, contact-event discovery, full contact history, or joint strength. Current frame acceptance remains three conditional rear cases.
