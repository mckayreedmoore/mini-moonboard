# Free C3D20 native elastic matrix export

The parent-owned serialized native run passed the exact-freeze review and the analytical export oracle. Pinned CalculiX 2.23 emitted stiffness, mass and equation-map files and exited zero in 0.2875 seconds; container cleanup was confirmed.

The exported operator has 60 equations and six rigid modes, with no negative stiffness eigenvalues below the declared tolerance. Maximum normalized rigid-mode residual is 3.45e-15. Observed shear energy is 2.000000000000205e-5 Nmm versus 2e-5; unit translation mass is 1.000000000000008 versus 1.

[Assessment](assessment.json), [replay](assess.py), [exact freeze](freeze.json), [review](independent-review.json) and [execution](execution.json) preserve distinct provenance and mechanical-result roles. Replay from repository root:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-free-c3d20-matrix-export-native-attempt01/assess.py --verify
```

This verifies the built-in export route on one free isotropic unit cube. It does not verify rotated wood, constrained equation mapping, actual frame geometry/rank, gravity mapping, normal/tangent state selection, captured reference history or joint strength. Current frame acceptance remains three conditional rear cases. A constrained mapping proposal is the next bounded dependency; no frame run is ready.
