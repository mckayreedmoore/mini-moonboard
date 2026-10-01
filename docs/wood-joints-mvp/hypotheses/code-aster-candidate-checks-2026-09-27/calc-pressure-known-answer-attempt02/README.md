# `CALC_PRESSION` plane-interface known-answer

This fixture adds Code_Aster's documented `CALC_PRESSION` post-processing to
the existing two-block plane-strain contact coupon. It explicitly requests
`SIEF_NOEU` first so the frozen rerun distinguishes stress-field generation
from the macro's later result attachment; the pinned v17.4.0 macro also
requests that field automatically when absent. It tests the pressure
output on a straight 2-D interface only. A pass establishes this output path
for the tested coupon; it does not establish pressure accuracy on the curved
3-D quadratic faces in the wood-joint model.

The mechanical model and prescribed 14-state displacement history match
`fea/code_aster_trial/contact/contact_trial.comm`: two 10 mm by 10 mm elastic
blocks, `E=1000 MPa`, `nu=0.25`, plane strain, frictionless contact, and 1 mm
unit depth. The plane-strain modulus is `C11=1200 MPa`; two 10 mm lengths in
series therefore give `k=600 N/mm`. For compression `u<0`, expected pressure
is uniform `P=-k|u|/(10 mm × 1 mm)`, with zero shear `CISA`. The frozen
compression states have expected pressures -6, -12, -24, -18, -12, and -6
MPa. Integrating the mean of the two nodal pressures over the 10 mm interface
and 1 mm depth must recover 60, 120, 240, 180, 120, and 60 N.

`CALC_PRESSION` reports the Cauchy-stress projection `n·σ·n`; the macro does
not provide a separate active-contact mask. In the open states, the imposed
positive displacement stretches the right block, so the slave face has
expected tensile normal stress `C11*u/10 mm` (6, 18, 24, and 12 MPa at the
positive displacement values). Those are not contact tractions, and are not
integrated as contact force. The pressure integral is compared with the
analytic contact resultant only in compression. This distinction is part of
the oracle, rather than treating every value in `PRES_NOEU` as a nonnegative
contact-only pressure.

The limits were fixed before execution: maximum nodal normal-stress error
`1e-6 MPa`, maximum absolute `CISA` `1e-6 MPa`, compressed-state
pressure-resultant error `0.01 N`, and numerical-field parity with the
archived mechanical contact attempt03 of `1e-10` in each reported common
field. The unchanged contact and
right-end reaction tables are compared with that independently frozen run to
ensure the added output command did not alter the response. Run
`../contact/check_contact_trial.py` as well as
`check_contact_pressure.py` after the parent freezes and serially executes the
prepared inputs.

Code_Aster v17's [pressure/contact output methodology](https://code-aster.org/doc/v17/manuals/man_u/u2/u2.04.04/M_thodologies.html)
recommends `CALC_PRESSION` when contact pressure from stress is preferable to
directly post-processing `LAGS_C`. The official [v17 syntax](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.81.43/Syntaxe.html)
allows extraction by result order and surface group. This fixture uses
`GEOMETRIE='INITIALE'` because the contact plane is vertical and held fixed in
the displacement direction. The method documentation specifically cautions
that curved-contact pressure may oscillate and may benefit from this
stress-based extraction; that is a reason to test the actual curved faces
separately, not evidence that the present 2-D result transfers to them.

Files:

- `pressure_coupon.mail`: the two plane-strain blocks and oriented contact
  segments.
- `contact_pressure.comm` and `contact_pressure.export`: the unchanged
  mechanical history plus pressure-field extraction.
- `check_contact_pressure.py`: analytic pressure/resultant and output-parity
  checker.
- `check_contact_trial.py`: existing independent gap and force oracle.

The parent controls frozen inputs and serialized solver execution. Solver
completion alone is not method or joint acceptance.
