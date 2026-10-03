# A12 raw-H force interval diagnosis — attempt 01

This read-only packet classifies the 27 force DAT interval failures in the
parent-owned raw-H fixed-branch result. It does not change the prior assessment,
source intervals, frozen inputs, connector operators or native case. It reads
the saved response and source artifacts, computes comparisons, and parses the
emitted SPRINGA tables, endpoint MPC equations and coordinates. It performs no
factorization, state solve or native execution.

## Result

The 27 failing force rows are 18 unilateral SPRINGA rows, 8 bilateral SPRING2
rows and 1 conditional floor-tangent row. The largest absolute difference over
all 1,840 rows is at position 1464, `floor_lumber_leg_left_2`: `0.0004846632 N`
against an allowed `0.0005000001 N`, so this is not a failed row. The largest
absolute difference among the 27 failures is position 381, `contact_8_1`:
`5.15564756e-6 N` against `5.00000077e-6 N` (ratio `1.03113`). The worst
normalized failure is position 1586, the `SPR1787` outer-seat axial tie:
`9.03551894e-8 N` against `7.04444655e-10 N` (ratio `128.2644`). These are
different rows and different measures.

The native force intervals also have different precision sources. SPRINGA
centers come from endpoint internal RF projected on the emitted axis; their
failed-row radii range from `7.04416e-10 N` to `5e-6 N`. SPRING2 centers are
native scalar endpoint forces with radii from `5e-8 N` to `5e-7 N`. The floor-T
center is a recovered physical support reaction with a `5e-8 N` radius. Each
row's exact center, radius, allowed difference, ratio, family, source group,
element and owning bodies are recorded in `assessment.json`.

The emitted source deck is consistent with the reduced linear connector
inputs at the precision checked here: over the 18 failed SPRINGA rows, the
largest relative positive-branch table-slope difference is `1.4824e-14`; the
largest deck-MPC coefficient difference from the projection contract is
`4.552e-15`; the largest emitted-axis component difference is `4.920e-13`;
and the largest initial-span departure from 100 mm is `6.447e-11 mm`. The
source evaluates its nonlinear table using `dd - dd0`, with `dd` and `dd0`
the current and initial endpoint distances. The emitted initial span is the
`dd0` datum, so the recorded initial-length rounding is not a force correction.

On the already saved native final increment, the geometric table force and the
native scalar-projection diagnostic differ by as much as `0.01989 N` among
these failed SPRINGA rows. At position 1586, the native geometric table force
is `1.58279e-5 N` above the native linear projection force; the raw-H force is
`9.07344e-8 N` above that native geometric table force. This is a
geometric-versus-projection diagnostic discrepancy. The native projection
value and geometric value use different endpoint/MPC and output paths; printed
displacement rounding, mapping/projection arithmetic and finite-length response
are not separated by these values. In particular, the native source projection
at row 1586 is `9.10e-7 mm`, while its ghost and geometric elongations are about
`9.13981e-7 mm`; this does not isolate the finite-length contribution. The
saved raw-H response contains connector `q`, `f`, and rigid coordinates, but
no physical endpoint displacement vectors. Its scalar `q_raw` is insufficient
to evaluate `dd - dd0` for the raw-H state, so the native geometric result is
not applied as a correction or asserted as the cause of the interval misses.

The failed rows' owner bodies are joined to their per-body compliance audit
envelopes in `assessment.json`. Across the 24 bodies owning at least one failed
row, maximum chunk KKT relative residual is `9.2617e-11`; maximum original-K
force and moment residuals are `1.7168e-5 N` and `0.028924 N mm`. Those are
operator construction/solve accuracy diagnostics, not force-error bounds for
individual rows. Across all 50 bodies the maximum original-K force residual is
`3.9161e-5 N`. Native DAT rounding radii remain separate, and no sensitivity
bound maps the measured operator residuals to the 27 force differences. The
diagnosis therefore does not assign a cause to the remaining misses.

**Disposition:** the raw-H comparison remains stopped by 27 unchanged force
interval failures (the prior symmetric-H attempt had 25). The raw-H result
reduces the source spring-law residual, but does not pass the source force
comparison. A raw-state finite-length evaluation would first require a
candidate endpoint displacement field for the owning bodies and application
of the exact emitted MPC map. This packet does not recover that field or run a
further comparison.

## Reproduction and pins

From the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-fixed-active-raw-H-force-failure-diagnostic-attempt01/diagnose.py --verify
```

The verifier recomputes the intervals and deck/source comparisons from the
files listed in `source-pins.json`, then compares the complete result to
`assessment.json` and the hashes in `output-pin.json`. It does not change any
input packet. Current producer SHA-256 is
`1572e9725010a1a61334f7afab3c8dc65167a8542fdb944a5b6d23d33a1c3bb6`.
