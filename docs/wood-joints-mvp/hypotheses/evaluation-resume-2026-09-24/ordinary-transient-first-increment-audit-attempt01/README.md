# First-increment accounting audit

The frozen pilot snapshot accounts for its completed `0.0025 s` first
increment. All 339 monitored DAT displacements were read; the 331 nodal load
vectors in the frozen deck match the serialized 1 N load pattern exactly.
The endpoint ramp amplitude is `0.001915`, and the work-conjugate displacement
`Σ f_unit · U` is `6.989744242963424e-6 mm`. Its first-increment Newmark
endpoint work, `0.5 F_end · U_end`, is `6.692680112637479e-9 N·mm`, matching
the solver log's `6.692680e-9 N·mm` within output precision.

The `23,531` DAT contact-energy rows sum to `7.466920159732914e-12 N·mm`,
matching the reported contact-element count and the solver's printed contact
energy. Printed DAT internal and kinetic energies are `3.067679e-10` and
`6.380649e-9 N·mm`; with contact energy they give `6.694883820159733e-9
N·mm` total. The DAT-rounded balance against independently calculated work is
`2.203707522254132e-12 N·mm` (`0.0329271%` of work). CCX reports
`2.203634e-12 N·mm` (`0.032926%`); the `7.35e-17 N·mm` difference follows
from the printed fields' limited precision. Nut-carrier energy is numerical
zero (`1.170119e-26 N·mm` internal, zero kinetic).

The applied nodal load pattern remains self-equilibrated to roundoff at the
current coordinates. About the actuator datum `(89.05, 42.906715329,
486.256134997) mm`, the resultant force norm is `4.46e-18 N`; the current
coordinate moment is `(5.0200e-11, -1.3905e-11, -1.6572e-11) N·mm`. Its
reference-coordinate moment is approximately zero. This is the applied
`CLOAD` wrench reconstructed from the same endpoint displacements, not a
contact-reaction or capacity result.

The work calculation is the discrete first-step Newmark endpoint quadrature:
the initial force and displacement are zero, so it reduces to
`0.5 F_end · U_end`. It is not the exact continuously integrated ramp work.
Evaluating `∫ F(t) · dU(t)` would require the displacement path within the
increment; endpoint displacement and ramp samples alone do not determine it.

The audit is limited to this completed first point, after 13 iterations. The
snapshot was captured while the native process was running; its partial later
increment is excluded. No FRD field parse was needed. The accounted point is
a very small, early transient load response under the declared stiff nut
engagement surrogate. It establishes no seated or quasistatic response,
physical nut engagement, capacity, or mechanical acceptance.

`audit.py` verifies the pinned snapshot hash
`82db7e5ccb0ad52d54a2b2c32499e6cac55b6cfb637fa2f6777a34b549f9d88f`, checks
the snapshot output hashes and verifies the read-only frozen input-deck and
actuator hashes before parsing. It reads DAT monitor, total-energy and CELS
rows, the first-increment solver log and status row, and the exact serialized
input loads. It does not invoke the native solver or read `.frd`.

Run it from the repository root with:

```sh
python3 docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-transient-first-increment-audit-attempt01/audit.py
```

The generated results are in [audit.json](audit.json).
