# Reduced static spring methods: first native result

The coordinator executed this exact frozen packet once on stock CalculiX 2.23,
after [independent input review](review.json). The serialized parent ledger
records `reduced-static-methods-attempt02` as consumed. Docker returned zero,
the native log ended with `Job finished`, and the named container was confirmed
terminal. See [execution.json](execution.json), [authorization.json](authorization.json)
and [result.json](result.json). The existing candidate geometry was not changed.

| Fixture | Maximum displacement error, mm | Maximum recovered physical force error, N |
| --- | ---: | ---: |
| Rotated directional spring | 4.286e-9 | 4.707e-6 |
| Scalar unilateral-contact active branch | 0 | 0 |
| Active radial gap with reference-load correction | 4.059e-8 | 1.350e-13 |

All three pass the frozen 2e-6 mm / 0.002 N tolerances. The actual printed
displacement rounding intervals contain zero MPC residual; the contact force
has the expected compression sign. The check uses the spring/MPC semantics
in the pinned [CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf), including
section 6.2.41 for SPRING2. The source inputs, analytical expectations and
runtime identities are retained in [freeze.json](freeze.json).

For the clearance fixture, the raw spring force includes the imposed gap
offset. Subtracting that offset is essential to recover the physical reaction.
Auxiliary local CLOAD components must not be counted as physical global loads.

This qualifies only the three tested linear active-branch methods. It does not
prove active-set convergence, frame stability, member/panel constitutive
behavior, bolt continuity, actual joint demand, fastener capacity or any MVP-E
criterion. The new reduced frame has not yet been solved. The independent
[postrun review](postrun-review.json) passed: it checked all nine output hashes,
execution bindings, analytical answers, MPC print intervals and force signs.

To replay the result assessment without another native invocation:

```sh
.venv/bin/python -m fea.wood_joint_reduced_fixture assess docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/reduced-static-methods-attempt02
```

Attempt01 was never launched and remains a superseded preparation snapshot.
Do not reuse this consumed run ID or alter its frozen native inputs.
