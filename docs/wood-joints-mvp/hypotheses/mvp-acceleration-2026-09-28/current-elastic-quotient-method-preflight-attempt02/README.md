# Coordinatewise rigid-wrench residual propagation

This parent-owned method retains original K, bordered factors, raw residuals and the existing nodal force, projected force, gauge, operator-leakage and bounded-refinement gates. It changes the aggregate rigid-identity gate to the norm propagation of the unchanged nodal force budget through the recorded rigid basis R.

For r = K u + R lambda - p, coordinate j obeys abs((R.T r)_j) <= sum_i abs(R_ij) max_i abs(r_i). The separately evaluated identity differs from R.T r only by the measured contraction-order difference. The new gate adds that measured difference coordinatewise; the difference remains independently gated by the old absolute/relative arithmetic criterion. No arbitrary absolute margin is added to the propagated budget. Rotational coordinates use the recorded 1000 mm scale.

The previous absolute aggregate gate and zero-multiplier gate remain reported diagnostics. Previous stopped attempts are preserved. This is an elastic quotient method, not a physical body response: raw body wrench equilibrium must be recovered before physical forces can be accepted.

Known-answer replay: `OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-elastic-quotient-method-preflight-attempt02/verify_quotient.py --verify`.

Independent scaling and corruption fixture: [scaling fixture](../current-rigid-wrench-residual-scaling-fixture-attempt01/). No geometry, source stiffness, contact mask, physical equilibrium tolerance or native input was changed here.
