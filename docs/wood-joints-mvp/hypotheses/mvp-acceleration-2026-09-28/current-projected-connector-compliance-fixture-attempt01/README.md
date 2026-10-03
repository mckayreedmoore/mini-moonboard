# Projected connector compliance cube fixture, attempt 01

This small known-answer fixture separates elastic compliance from rigid-body
equilibrium for a free 20-node C3D20 cube. It replays the already authenticated
native cube matrix and the preceding analytic-traction fixture; it launches no
FE kernel and does not compute the current frame.

Replay from the repository root:

```sh
OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-projected-connector-compliance-fixture-attempt01/verify_compliance.py --verify
```

For sparse physical source rows `B`, a dense `Q K Q` inverse supplies the
small-cube reference only. The shared sparse bordered helper independently
constructs `H`: project each raw source column `L = B.T` into the elastic
subspace as `L_e = L - Q_r (Q_r.T L)`, then solve all columns with the
unmodified `K` in `[K R_r; R_r.T 0]`. Six already-balanced analytic traction
cases use the same sparse bordered solve to construct `e`. The fixture then
reports

```text
H = B K+ B.T       D = B R       e = B K+ F       W = R.T F
q = D a + e - H f
D.T f = W          iff          R.T (F - B.T f) = 0
```

Here `f` is force exerted by the body on its interface, so the load on the
body is `F - B.T f`. The fixture retains `D.T = R.T B.T` as the raw wrench map
for every source row. It never replaces that wrench by its elastic projection.
The projection is used only to build `H`'s elastic columns; it does not erase
the independent rigid balance equations. The only acceptable body response
has zero raw six-mode wrench after combining external and interface loads.
When balance fails, the fixture reports the wrench mismatch and computes no
physical displacement. In particular, the elastic projection is not a license
to treat an unbalanced raw load as a physical gravity response.

Rows are the three translation directions at cube nodes 1, 2, and 4. `H` is in
mm/N, `e` in mm, `D` maps translations in mm and rotations in radians to row
displacements in mm, and `W` is three forces in N followed by three moments
in N·mm. Six uniform-stress analytic face-traction cases have maximum
`|R.T F| = 1.11e-16`. All nine sparse-KKT `H` columns agree with dense `Q K Q`
to `2.49e-14 mm/N`; the two-row block differs from the saved result by
`1.51e-14 mm/N`. Sparse `e` agrees with the dense reference within
`5.67e-15 mm` and with the affine known answer within `9.46e-14 mm`. `D`
matches source rigid fields exactly; multiplying its scaled rotational columns
by 1000 recovers the unscaled-radian map exactly.

A balanced source pair verifies `q = D a + e - H f`, physical `K u = F-B.T f`,
and dual work using the shared bordered solve. A separate point-load case has
nonzero `W` and a matching interface wrench, so the combined body load is zero
and `D.T f = W`. Its standalone elastic projection matches the dense cube
reference but is explicitly marked nonphysical. The connector-only point-force
case violates the balance equation and is rejected without a displacement.

This fixture validates signs and algebra only on a small isotropic cube. It
does not establish current-frame connector compliance, load maps, contact
states, joint acceptance, construction readiness, or climbing release.
