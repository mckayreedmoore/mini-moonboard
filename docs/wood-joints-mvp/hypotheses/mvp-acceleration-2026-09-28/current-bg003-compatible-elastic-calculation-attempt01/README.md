# Exploratory BG003 elastic calculation

This packet predates receipt of the independently reviewed
[support/corner diagnostic](../../support-corner-review-2026-09-30/README.md).
Preserve its calculation as an exploratory cross-check. Use that reviewed
diagnostic as the small continuous-bolt method baseline for subsequent work;
this packet does not justify a duplicate general solver implementation.

`calculate.py` tests a continuous circular Euler beam and three independently
rigid wood receivers, with zero-gap isotropic bilateral foundations. The
three uniform line-stiffness values, 100, 1,000 and 10,000 N/mm², and steel
modulus 190,000 MPa are mathematical assumptions, not measured properties or
physical bounds. The calculation uses the three authenticated full-load rear
exports, applies each balancing receiver lateral wrench once, checks free
ends and zero gauge reactions, and refines 4/8/16 elements per receiver. It
does not represent the shared deformation of the two bolts' timber.

The local scalar field names require care when comparing signed results.
`V_on_bolt_N` records the cumulative external beam force; the reviewed
diagnostic's force on the left cut has the opposite sign. If this packet's
scalar bending quantities for global Y and Z deflections are `M_Y` and `M_Z`,
the reviewed physical left-cut couple is `(My, Mz)=(-M_Z, M_Y)`.
Magnitude agreement alone does not validate signed force conventions.

There is no physical clearance, calibrated grain-dependent law, steel yield,
washer/axial/thread interaction, splitting, group resistance or joint
acceptance in this packet. Its independently selected stiffness points are
not the reviewed diagnostic's dimensionless beta points.

Read-only replay from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python \
  docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg003-compatible-elastic-calculation-attempt01/calculate.py --verify
```
