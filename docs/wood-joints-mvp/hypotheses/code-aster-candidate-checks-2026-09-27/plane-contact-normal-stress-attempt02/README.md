# Plane-contact normal-stress known-answer

This fixture checks whether the pinned Code_Aster result contains the
analytically expected normal stress on a straight plane-strain contact face.
It uses the tensor component directly; it does not call `CALC_PRESSION`.
That distinction matters because the separate frozen attempts
[`calc-pressure-known-answer-attempt01`](../../../docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/calc-pressure-known-answer-attempt01/),
[`attempt02`](../../../docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/calc-pressure-known-answer-attempt02/),
and
[`attempt03`](../../../docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/calc-pressure-known-answer-attempt03/)
all completed the nonlinear coupon states and explicit `SIEF_NOEU`
calculation, then aborted in `CALC_PRESSION` with a Fortran `CRTYPE`
"Bad value during integer read". This occurred both with all instants and
with one instant; input files remained unchanged. The v17.4 source places the
macro's final `CREA_RESU` append after stress extraction and pressure-field
construction, making result attachment the leading failure location. The
exact malformed internal name/value is not available in the job log.

For a vertical face with normal parallel to global X, the official
[Code_Aster v17 contact methodology](https://code-aster.org/doc/v17/manuals/man_u/u2/u2.04.04/M_thodologies.html)
defines contact pressure as `nᵀ σ n`, which reduces here to `SIXX`; the
tangential traction reduces to `SIXY`. The test therefore extracts nodal
`SIEF_NOEU` stress components from the same two-block frictionless contact
coupon and checks them against a closed-form plane-strain solution. It
demonstrates the stress-based force resultant on this aligned plane only. It
does not establish that the `CALC_PRESSION` macro runs in this case or that
the result transfers to curved 3-D contact faces.

The two 10 × 10 mm blocks use `E=1000 MPa`, `nu=0.25`, and 1 mm unit depth.
Their plane-strain modulus is `C11=1200 MPa`; the two 10 mm lengths in series
give `k=600 N/mm`. For opening (`u>0`), the contact face is free and the
right block translates rigidly, so its normal stress is zero. At zero
displacement, stress is also zero. For compression (`u<0`), the two blocks
share the imposed closure equally and the interface stress is `C11*u/20 mm`.
For compressed states only, the mean nodal `SIXX` times the 10 mm face length
and 1 mm depth must recover the known contact resultant.

Before this fixture's run, the acceptance limits were fixed at `1e-6 MPa`
for each nodal stress component, `0.01 N` for the compressed-state stress
integral, and `1e-10` for each common field in the existing contact and
right-end reaction tables. The latter parity check confirms that adding
stress extraction did not change the mechanical response. The six frozen
compression forces are 60, 120, 240, 180, 120, and 60 N.

Files:

- `pressure_coupon.mail`: the two plane-strain blocks and oriented contact
  segments.
- `contact_pressure.comm`: the original contact history with `FORC_NODA`
  and `SIEF_NOEU` fields and a nodal stress table.
- `check_contact_stress.py`: analytic stress/resultant oracle and output
  parity checker.
- `../contact/check_contact_trial.py`: existing independent contact-gap and
  force check.

The parent controls frozen inputs and serialized native execution. A pass
validates this plane-stress extraction only, not curved-face pressure, joint
resistance, candidate acceptance, or release.
