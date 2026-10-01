# BG001 pressure-resolution sensitivity

This parent-scoped calculation addresses the specific coarse-contact concern
from the prior post/spine prescribed-action experiment. It holds rigid-member
geometry, zero preload/gaps, the two existing 4,670.054 N/mm ties and numerical
normal penalty 100 N/mm³ fixed. Only pressure quadrature changes. It is not
a native run, a six-case frame response or a complete corner qualification.
No reviewed geometry or execution budget changes.

The contact geometry and C11 **input** hashes are verified in the producer.
The source rectangle is sampled with midpoint grids, excluding the two modeled
radius-3.75 mm bores. Full sound-contact area is 13,139.962707 mm². The 512²
grid represents it with area error +0.048730 mm²; bore boundaries are still
approximated, not integrated exactly. No rejected C11 force/active state is read.

| Prescribed interface action on spine | Previous four-cell total tie N | 512²-grid total tie N | Relative change, 256² → 512² |
| --- | ---: | ---: | ---: |
| My +1 N·m | 22.622 | 16.715 | 0.00253% |
| My −1 N·m | 23.489 | 18.103 | 0.00290% |
| Mz +1 N·m | 16.152 | 10.980 | 0.00229% |
| Mz −1 N·m | 207.169 | 28.119 | 0.00886% |

The reverse-Mz tension is about 86.4% lower than the four-cell result and
approaches the earlier 26.247 N unrestricted-pressure lower bound. A finite
pressure/stiffness scenario need not attain that bound. This demonstrates
coarse-centroid bias in this imposed-action, rigid local mechanism. It is
not a physical failure finding or an adopted demand. The reported last-grid
changes are observations, not rigorous error bounds or a new acceptance
threshold. Results do not establish a calibrated timber compliance law.

The pressure rule is `p=100 max(-g,0)` with `g=a+b*dz+c*dy`; ties engage only
at positive opening. Force/moment balance is solved in three scaled opening
coordinates using SciPy's documented nonlinear least-squares routine with
an analytic Jacobian. [SciPy method documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.least_squares.html)
describes local cost minimization; optimizer success alone is not acceptance.
The producer instead requires physical action residual below 1e-6 N / N·mm,
checks a separate starting point, and reproduces an independent diagonal
spring known answer. Runtime SciPy 1.18.1 and NumPy versions are recorded;
the referenced manual is the SciPy 1.18 reference, not native-solver guidance.

All 24 resolution/moment probes close, with maximum residual 1.60e-12 in
the stated physical components. Independent initial guesses match the local
states/tie forces. Source-pinned reproduction passes. These are arithmetic
and sensitivity checks of this fixed law, not proof of complete mechanics.

**Result unlocked:** the prior 207 N per N·m action must not be treated as
a resolution-independent local bolt demand. Resolving pressure within the
same geometry removes most of that sampling effect. Remaining applicability
inputs are timber/member compliance, actual seat/contact conditions and
simultaneous loads through all seven corner bearing pairs and bolt groups.
Pressure resolution remains necessary for other interfaces and load states;
this one local experiment does not validate them. Global floor support and
receiver sharing still prevent accepted six-case corner demands.

Reproduce from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-post-spine-pressure-resolution-attempt01/produce.py
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-post-spine-pressure-resolution-attempt01/produce.py --verify
```

[resolution.json](resolution.json) records all grids, actions, two tie forces,
sample peak pressures, area errors, residuals, versions and source hashes.
The pressure peaks are outputs of the hypothetical law, not actual stresses.
