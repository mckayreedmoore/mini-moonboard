# Post-mechanical acceptance gates

This supplement separates the Newton mechanical test from the full
increment-acceptance path for the frozen implicit face-to-face contact case.
It describes pinned upstream CalculiX 2.21 source behavior; it does not prove
that a packaged solver binary has identical behavior, authenticate the
reported progress values, or identify the cause of any observed convergence
or cutback.

## Source behavior after the mechanical test

`checkconvergence.c` first computes `iconvergence` from the mechanical
residual, active-contact stability, and correction tests described in the
README. Before treating that result as final, it applies two relevant
post-mechanical paths:

1. If the mechanical test passed while `kscale > 1`, source resets `kscale`
   to `1` and clears `iconvergence`. The increment must then be resolved with
   the original contact stiffness; the earlier scaled-stiffness pass is not
   acceptance. On face-to-face cutback paths, `checkconvergence.c` and
   `checkdivergence.c` can set `kscale` to `kscalemax` for a reattempt. The
   default `ctrl[55]` value is `100.5`, assigned to integer `kscalemax`.
   The current value of `kscale` therefore needs to be observed at the
   mechanical test and through any reattempt.
2. For implicit dynamics with mechanical-only thermal mode, coupled solving,
   a mechanically converged iterate, and current or initial contact spring
   elements (`ne != ne0 || neini != ne0`), source calls `checkimpacts.f`.
   For face-to-face contact (`mortar == 1`), its energy-history tests can set
   `idivergence=1` and request a reduced increment after an impact or rebound;
   the final acceptance branch requires both `iconvergence == 1` and
   `idivergence == 0`. If it does not flag divergence, it can still change
   `sizemaxinc` and `istab`, affecting the next increment. This is a contact
   impact/time-step strategy, not a proof of energy balance or a physical
   contact cause.

The relevant branches are conditional. `checkimpacts` is reached only after
the Newton test still has `iconvergence == 1` after the `kscale` reset and
only when its contact-presence condition is satisfied. These source paths
show what must be observed; they do not show that either path triggered in
the progress report.

## Minimal future diagnostic contract

To explain an actual accepted or retried increment without changing solver
decisions, retain the existing mechanical-test fields and add a separate
post-test record keyed by `istep`, `iinc`, `icutb`, `iit`, `time`, and current
`dt`:

- At the Newton decision: raw `ram[0]` immediately before the `1e-6` clamp,
  the post-clamp value passed to the test, `qa[0]`, `qam[0]`, `cam[0]`,
  `uam[0]`, selected `c1[0]`/`c2[0]`, `ntg`, `iflagact`, current and prior
  contact-spring counts, and `iconvergence` before special handling.
- Across stiffness restoration and retries: `kscale` before and after the
  mechanical decision, whether it was reset, and its value used for the
  current assembly. Preserve the cutback/attempt identity so a reset and
  reattempt cannot be mistaken for one accepted solve.
- If the `checkimpacts` condition is true: record `mortar`, `ne`, `ne0`,
  `neini`, `uncoupled`, `ithermal`, and `nmethod`; energy arrays
  `energy[0:4]` and `energyini[0:4]`; `energyref`, `allwk`/`allwkini`,
  `dampwk`/`dampwkini`, `emax`, `enetoll`, `r_abs`, `theta`, `dtheta`,
  `tmin`, `tmax`, `tper`, `temax`, `sizemaxinc`, and `istab` at entry; plus
  `idivergence`, `iforceincsize`, `r_abs`, `enetoll`, `sizemaxinc`, and
  `istab` at return. Record `iconvergence` after this path and the final
  accepted / reattempt decision.

The residual and contact counts should be the values actually consumed by
the decision code, not stdout reconstructions. If fields are not emitted by
the packaged binary, conclusions should remain limited to source semantics
and whichever outputs are independently pinned. No new inference should be
made from rounded `average force`, `largest residual force`, or unaligned
progress estimates.

## Source pins

All source files below are from the upstream CCX 2.21 archive pinned in the
README. The `checkconvergence.c` and `nonlingeo.c` hashes also appear there.

| Source | SHA-256 |
| --- | --- |
| `checkconvergence.c` | `a9f417fe198b0bc227a28f1f4775382d2bba22a7e436d60ba6d523ab91713e50` |
| `checkimpacts.f` | `704c9f3a730ab78425825f6b5f445a7c8fcf79b1ac14559df4b51f3b553e1500` |
| `checkdivergence.c` | `f8646660df1ac6772d16a2452feec6711f690df24bd6df8c486fdadb18f0748b` |
| `nonlingeo.c` | `0be7d7d6037868c364a621e12a3802a703f189b09ba200de95cf2e9d1b211f1b` |
| `ini_cal.c` | `1d195e679e6692d03da0b3bd48e7ea52f733c96328bedfef3f5f7da6f3dd0d1f` |
| `springforc_f2f.f` | `b06588c45d1b00522cea8f66e08fe20f76f9edb537500d8d8a269074ae3da3a6` |
| Frozen `pilot.inp` | `1763d0ad15c2d53d86bdcf25ea136f3a3d267739b682d0dcd5d3cb2167387485` |
| Solver image named by input freeze | `sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0` |

The image digest identifies the configured container image only. It does not
show that its packaged CalculiX executable is built from the separately
hashed source archive.
