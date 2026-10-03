# Free-body condensation preflight, attempt 01

This packet supplies a reusable per-body rigid-lift positivity audit and a
sparse bordered free-body solve, checked against the authenticated free C3D20
cube. It does not assemble or solve the 50-body frame. The parent may use
`condensation.py` after independently authenticating the current-frame export.

Replay the fixture from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-free-body-condensation-preflight-attempt01/verify_preflight.py --verify
```

## Method

For each body, `rigid_basis(labels, node_xyz, rotation_scale_mm=1000)` uses the
arithmetic mean of unique source mesh-node coordinates as the datum. Its three
translation columns are dimensionless; rotation columns are
`cross(axis, x-center) / 1000 mm`. Generalized coordinates are three
translations in mm and three `1000 mm * radians` rotations, so all six entries
have units mm. `R.T @ load` is in N; multiply the last three entries by 1000 mm
to report the physical moment in N·mm.

The free-body equations preserve all six rigid balances. With `f` defined as
the force exerted by the body on its interface, its physical load is
`g = F - B.T f`, and the exact balance requirement is
`R.T @ (F - B.T f) = 0`. The row displacement is

```text
q = B R a + B K+ (F - B.T f)
```

where `K+` acts only on the elastic subspace. The implementation never forms
that inverse for the frame. It audits and factors the original body stiffness
with these operations:

1. Check symmetry, six rigid fields, and their normalized `K R` residual.
2. Form `Khat = K + gamma Q Q.T` for one body, where `Q` is an orthonormal
   basis of the six rigid fields and `gamma = ||K||_infinity` in N/mm.
3. Require dense Cholesky success and a LAPACK `pocon` reciprocal 1-norm
   condition estimate at least `1e-12`. A failed Cholesky is rejected. A
   lower estimate is `UNRESOLVED_NEAR_SINGULAR`, not an asserted physical
   failure. The lift is only a numerical audit; it is discarded, and physical
   equations use unmodified `K`.
4. Factor the sparse bordered system `[K R; R.T 0]` with SciPy SuperLU.
   Loads are checked for the full six-component wrench before solving. The
   force-equilibrium residual is checked in N relative to applied force; the
   displacement gauge `R.T u` is checked separately in mm; the gauge
   multiplier is checked separately in N. A nontrivial multiplier is never
   interpreted as a support reaction.

The cube fixture passes the rigid-lift audit at reciprocal condition estimate
`1.368e-3`. A deliberately added elastic zero mode gives
`UNRESOLVED_NEAR_SINGULAR` at `1.24e-17`, while a negative elastic direction
fails Cholesky. A corrupt-factor fixture verifies that a failed bordered
residual cannot return a pass.

The sparse bordered solve is checked with six independently integrated
uniform-stress tractions on the cube faces. Quadratic-face shape integrals are
`-1/12` for each corner and `+1/3` for each edge midpoint. These loads are
analytic continuum tractions, never `K*u`. The six responses match centered
affine fields modulo rigid motion; maximum relative displacement error is
`1.98e-13`, and maximum cross-work error is `5.0e-14 N·mm`. A two-row balanced
source-force pair verifies the condensation equation and dual work. An
unbalanced `+1 N` point load reports `[1,0,0 N; 0,-0.5,+0.5 N·mm]` and is
rejected without returning displacement.

## Scope and scaling

The parent-owned pure-solid export contains 37,647 physical coordinates in 50
uncoupled bodies. The source map gives a largest body of 6,567 DOFs; one dense
lift is 345,003,912 bytes (329.0 MiB). The summed leading Cholesky work over
50 sequential body audits is approximately 339 billion floating-point
operations. This is a size estimate, not an observed runtime. Sparse border
fill, solve time, and peak library workspace are unknown. The helper processes
one body at a time and does not retain dense body blocks or inverses.

The frame export passed its sparse structure and 300 rigid-field screen, but
that does not prove full elastic rank or positive stiffness. The parent audit
must stop on the first failed or unresolved body. The `1e-12` rcond floor is a
conservative numerical stop threshold; a real thin-panel mode near it remains
unresolved and requires review. Even a pass does not validate source material
properties or joint behavior.

No gravity load map was read or used here. The projection contract's file
named `source-gravity-nodal-map.json` was subsequently found to contain
combined gravity and climber load. Any later gravity stage must use the
separately decomposed `gravity_nodal_map` and `climber_nodal_map` in
[`current-frame-pure-solid-matrix-export-preflight-attempt01/source-load-maps.json`](../current-frame-pure-solid-matrix-export-preflight-attempt01/source-load-maps.json)
and preserve the parent recomposition audit.

This result establishes only a small-cube condensation method fixture and a
source-based per-body size estimate. It does not compute a current-frame
operator inverse, connector compliance, gravity/contact state, physical frame
response, joint acceptance, construction readiness, or climbing release.
