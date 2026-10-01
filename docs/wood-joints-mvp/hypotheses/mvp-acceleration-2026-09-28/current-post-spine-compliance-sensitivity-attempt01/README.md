# BG001 existing-compliance scenario sensitivity

This parent-scoped calculation applies the existing property producer's 24
paired outer-seat scenarios to the refined local post/spine experiment. It
holds geometry, zero gap/preload, rigid members, 256² pressure quadrature and
normal penalty 100 N/mm³ fixed. No native/frame run, geometry change or
original leg/runner resistance requalification occurs. Rebuilding the property
input inventory is not a resistance check or recovery of C11 forces.

The producer verifies the maintained property-builder hash and the previously
frozen input/geometry hashes. It reuses the stored scenario definitions:
independent two-seat ring choices, wood-column depths 0.5/1/2 times equivalent
washer diameter, and steel modulus 190,000/210,000 MPa. These yield 24 paired
scenarios and 96 imposed unit-moment calculations. No new property range is
invented or treated as a measured/statistical bound. Source pins and complete
per-scenario two-bolt actions are in [sensitivity.json](sensitivity.json).

| Prescribed joint moment on spine | Conditional total tie action range (N per N·m) |
| --- | ---: |
| My positive | 16.608–16.785 |
| My negative | 18.058–18.107 |
| Mz positive | 10.800–11.155 |
| Mz negative | 27.429–28.781 |

Effective tie stiffness ranges from 1,780.926 to 8,869.699 N/mm. Within these
declared scenarios, the refined moment-sharing result varies far less than
the prior coarse-centroid result (207.169 N for negative Mz). This supports
the sampling diagnosis within the conditional local model. It does not
establish real stock stiffness, calibrated seat compliance, actual pressure,
washer bending, preload, complete corner force sharing or a design envelope.

The exact baseline second-seat modulus is 750.149593 MPa rather than the
rounded 750.176 MPa shown in the earlier reuse table; its pinned directional
projection accounts for the small difference. The existing property producer
reproduces baseline tie stiffness 4,670.054188 N/mm. Material constants and
actual directional effective seat moduli must remain distinct.

All 96 probes satisfy physical force/moment residual checks; maximum residual
is 3.02e-12 N or N·mm. A second starting point agrees on local displacement
and individual tie forces for every probe. Reproduction checks source hashes,
scenario identities and per-tie actions. These are conditional arithmetic
checks using the previously documented pressure solver, not acceptance.

**Engineering result:** the selected existing compliance scenarios do not
reproduce the large coarse-sampling tie increase for these four imposed
moments. The remaining demand dependency is the simultaneous complete-corner
action set and its member/contact compatibility, not another repeat of this
local stiffness sweep. Keep all seven internal bearing pairs and outward
member carriers. The 256² fixed-grid result has the small numerical
resolution differences recorded in the earlier refinement packet; it is not
an exact continuum solution or physical upper bound.

Reproduce from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-post-spine-compliance-sensitivity-attempt01/produce.py
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-post-spine-compliance-sensitivity-attempt01/produce.py --verify
```

No criterion, candidate selection, physical-work permission or native budget
changes. This packet must not supply substitute six-case frame demands.
