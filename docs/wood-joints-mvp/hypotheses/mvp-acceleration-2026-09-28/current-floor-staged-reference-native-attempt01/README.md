# Native staged-reference coupon

The scheduled ten-step CalculiX 2.23 coupon passed its independent parent
oracle at all **60 accepted increments**. STA and DAT output coverage agrees:
six increments in each of ten stages, with all seven nodes represented.

The run settles the synthetic open state, captures t=-2 mm at first bearing,
unloads and releases that reference, changes both load components while
open, then captures t=-1 mm at re-engagement. Constant reference amplitudes,
load replacement/interpolation, persistent equations and OP=NEW release all
match the prescribed history. Open stages have zero generalized tangent
force. The final re-engaged state is t=-1 mm, q=0.5 mm, N=1 N, T=-0.5 N.

Native output confirms Newton iterations with geometric effects off. Maximum
displacement discrepancy is 3.34e-7 mm, reaction discrepancy 1.81e-16 N,
and generalized equilibrium residual 7.00e-7 N. Normal-law and ground-spring
checks pass at every printed increment.

Parent consumed one exact-frozen, independently reviewed, serialized launch
with a 120-second bound. It returned zero in 0.53625 seconds with confirmed
container cleanup. No automatic retry was made.

- [Exact freeze](freeze.json), SHA-256
  `02c0ea77685cc8ae40483c931096d2518bf3635929556c8c318745f08bf16c44`.
- [Independent readiness review](independent-review.json).
- [Execution](execution.json).
- [Every-increment assessment](parent-staged-assessment.json), SHA-256
  `5d8aafe1097850057e0f18ede01fa8a61f2ace52dc73c3a9743c5a785ea6e783`.
- [STA/DAT coverage](increment-coverage.json).
- Native DAT SHA-256
  `b6d77329091d3302450a768bda39864b048fcc0cb0f4ef0ab516098206b8ec0e`.

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-staged-floor-native-mapping-preflight-attempt01/parent_staged_check.py docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-floor-staged-reference-native-attempt01
```

The exact checker and known answers are also retained under frozen `sources/`.
This is a small prescribed-history method test. Event coordinates and active
sets are supplied by the rational oracle, not discovered by the native deck.
It does not validate an event-search algorithm, restart continuation,
full-frame weighted mappings, a 100-cell coupled state selector, initial
gravity equilibrium, or a zero-reaction frame gauge/rank check. Those remain
specific readiness dependencies for the actual gravity-settle/climber-ramp
scenario. Three authenticated frame cases remain usable; this coupon adds
no fourth frame case or joint/strength acceptance.
