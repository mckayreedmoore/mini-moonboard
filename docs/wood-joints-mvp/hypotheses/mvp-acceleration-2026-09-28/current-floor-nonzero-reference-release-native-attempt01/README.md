# Native nonzero-reference release coupon

The pinned CalculiX 2.23 coupon passed its independent parent check at all
12 printed increments across two static steps. Holding the scalar reference
at t=-2 mm with ramped external loads reaches q=0, N=0 and generalized
tangent reaction T=+1 N. Releasing that reference at unchanged external load
reaches t=-4/3 mm, q=-1/3 mm and N=T=0 from the first printed released
increment onward. No residual restraint force was observed.

The constant reference amplitude, persistent equations, reissued permanent
SPCs, retained concentrated loads and candidate reaction mapping
`T=Ft-RF(T_REFERENCE,1)` all match the coupon oracle. The normal reaction is
`RF(NORMAL_GROUND,2)`. Native output confirms Newton iterations with geometric
effects off. Maximum displacement and force discrepancies are 3.34e-7 mm and
3.34e-7 N; the maximum generalized equilibrium residual is 7.00e-7 N.

The parent froze the exact inputs, obtained the scoped independent review,
and launched one serialized process with a 120-second limit. It returned zero
in 0.43745 seconds; container cleanup is confirmed. The ledger records the
consumed terminal run `floor-nonzero-reference-release-attempt01` and is idle.

- [Exact freeze](freeze.json), SHA-256
  `632885e5e3ac8c47e286f48250d4ed04c087ed39dafe1348af4011515444b73b`.
- [Independent readiness review](independent-review.json).
- [Execution record](execution.json).
- [Every-increment parent assessment](parent-release-assessment.json), SHA-256
  `40132a2667702b86de2a97082e024362b5f91ca330085028f11476de24495862`.
- Native DAT SHA-256
  `20c5395b0d256b7090126adc8b7b8bf2a97ee0f13b1f920ce6470cdf68977487`.

Replay the assessment without a native rerun:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-staged-floor-native-mapping-preflight-attempt01/parent_release_check.py docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-floor-nonzero-reference-release-native-attempt01
```

The exact checker is also retained under `sources/` in this freeze. The
[method proposal](../current-staged-floor-native-mapping-preflight-attempt01/README.md)
records the pinned manual/source basis and known-answer preparation.

This establishes native constraint-release behavior only for the coupon's
equation graph and load path. It does not validate weighted frame mappings,
100-cell coupled state selection, event capture/refinement, restart
continuation, gravity-settle existence or a reaction-free frame gauge/rank
check. Those remain prerequisites for the proposed staged frame scenario.
No fourth frame response, corner resistance, physical floor qualification or
construction acceptance follows from this result.
