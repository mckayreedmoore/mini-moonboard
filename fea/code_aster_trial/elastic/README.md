# Code_Aster 17.4 elastic method fixtures

These two small decks are method checks for the pinned stock Code_Aster 17.4
runtime. They are intentionally separate, linear known-answer problems. They
do not model or qualify a wood joint.

## Run

From the repository root, use the serialized freezer/runner with a new attempt
directory each time:

```sh
python fea/code_aster_trial/run_frozen.py \
  fea/code_aster_trial/elastic orthotropic.export \
  docs/wood-joints-mvp/hypotheses/code-aster-stock-trial-2026-09-27/orthotropic-attempt02 \
  --image simvia/code_aster@sha256:d8d19ea91989eac0d38195bc5795c54c69f530f7196f53d67697ffa57c9106d5

python fea/code_aster_trial/run_frozen.py \
  fea/code_aster_trial/elastic liaison.export \
  docs/wood-joints-mvp/hypotheses/code-aster-stock-trial-2026-09-27/liaison-attempt02 \
  --image simvia/code_aster@sha256:d8d19ea91989eac0d38195bc5795c54c69f530f7196f53d67697ffa57c9106d5
```

The parent-owned runner requires a fresh destination and records the copied
input hashes, command, image digest, process status, and stdout. Use a distinct
attempt name if one already exists.

## Orthotropic unit-cube oracle

`orthotropic.mail` is one unit HEXA8 cube in metres. Its `ELAS_ORTH` properties
are `E_L=1000 Pa`, `E_T=500 Pa`, `E_N=250 Pa`, three distinct shear moduli, and
zero Poisson ratios. The deck uses `AFFE_CARA_ELEM/MASSIF` with
`ANGL_REP=(90,0,0)` and displaces the top face by `0.001 m` in global Y. The
intended uniform state is `u_y=0.001 y`, `SIYY=E_L*0.001=1 Pa`, and total
axial resultant `1 N`. Each corner on a loaded or supported face carries
`0.25 N`; the checked top and bottom nodal reactions therefore have opposite
signs.

All four `TEST_RESU` analytical checks use `CRITERE='ABSOLU'` and
`PRECISION=1e-9`: top-node `DY=0.001 m`, top-node `SIGM_NOEU.SIYY=1 Pa`,
top-node `REAC_NODA.DY=+0.25 N`, and bottom-node `REAC_NODA.DY=-0.25 N`.

The v17 `AFFE_CARA_ELEM/MASSIF` page is internally inconsistent about the
zero-angle local-axis order: §13.3 says `(x,y,z)` corresponds to `(N,L,T)`,
while §13.7 describes the default as `(X,Y,Z)=(L,T,N)`. This fixture avoids
relying on that default. In the parent-run attempt, the explicit angle and
independent stress/reaction oracle produced `DY=0.0010000000000000002 m`,
`SIYY=1.0000000000000013 Pa`, `+0.2500000000000001 N`, and
`-0.25000000000000006 N`; all four analytical checks passed at `1e-9` absolute
tolerance. This validates this specific angle/material/input combination in
the recorded 17.4 image. See the [frozen attempt record](../../../docs/wood-joints-mvp/hypotheses/code-aster-stock-trial-2026-09-27/orthotropic-attempt01/input-freeze.json),
[check audit](../../../docs/wood-joints-mvp/hypotheses/code-aster-stock-trial-2026-09-27/orthotropic-attempt01/embedded-check-audit.json),
and [native stdout](../../../docs/wood-joints-mvp/hypotheses/code-aster-stock-trial-2026-09-27/orthotropic-attempt01/native.stdout).

## Linear constraint and work oracle

`liaison.mail` has two independent unit-length `BARRE` elements, each with
`E=1 Pa` and area `1 m²`, so both axial stiffnesses are `k=EA/L=1 N/m`.
Only one scalar equation links the single end node of each bar:

```text
u_S - 2 u_R = 0
```

The command lists `GROUP_NO=('S','R')`, `DDL=('DX','DX')`,
`COEF_MULT=(1,-2)`, and `COEF_IMPO=0`; each group has exactly one node.
The deck applies `1 N` in X at S, fixes each opposite bar end, and sets Y and
Z motion to zero at S and R. It does not tie a face or make either bar end
rigid. The exact equilibrium follows from
`Pi = 0.5*u_S^2 + 0.5*u_R^2 - u_S`, with `u_S=2*u_R`: `u_R=0.4 m` and
`u_S=0.8 m`. The corresponding bar forces are `0.4 N` and `0.8 N`.

The constraint multiplier is `0.2 N`, so its nodal actions, in the residual
sign convention reported by `REAC_NODA`, are `-0.2 N` at S and `+0.4 N` at R.
Their virtual work vanishes for every compatible variation:
`(-0.2)*delta(u_S) + 0.4*delta(u_R) = 0` when
`delta(u_S)=2*delta(u_R)`. The force ramp's external work is
`0.5*1*0.8=0.4 J`; the two bars' strain energy is
`0.5*(0.8^2+0.4^2)=0.4 J`.

The six analytical checks use `CRITERE='ABSOLU'` and `PRECISION=1e-9`:
`DEPL.DX` at S (`0.8 m`) and R (`0.4 m`); `REAC_NODA.DX` at S (`-0.2 N`)
and R (`+0.4 N`); and the two support reactions (`-0.8 N` and `-0.4 N`).
In the parent-run pinned-image attempt, the solver returned respectively
`0.8`, `0.39999999999999997`, `-0.19999999999999996`, `0.4`, `-0.8`, and
`-0.4`; all six checks passed at `1e-9` absolute tolerance. See the
[frozen attempt record](../../../docs/wood-joints-mvp/hypotheses/code-aster-stock-trial-2026-09-27/liaison-attempt01/input-freeze.json),
[check audit](../../../docs/wood-joints-mvp/hypotheses/code-aster-stock-trial-2026-09-27/liaison-attempt01/embedded-check-audit.json),
and [native stdout](../../../docs/wood-joints-mvp/hypotheses/code-aster-stock-trial-2026-09-27/liaison-attempt01/native.stdout).

## Limits and documentation

The cube checks one uniform axis-aligned uniaxial state with zero Poisson
coupling. It does not validate off-axis stiffness, nonzero Poisson coupling,
shear response, arbitrary material-frame rotations, or wood properties. The
bar test checks one two-node scalar constraint and its dual force/work map. It
does not validate distributed face mappings, multi-node constraints, rigid
carriers, rotations, or the full timber/bolt/contact load path. Passing these
fixtures is not joint acceptance.

The syntax and method choices are tied to the official v17 manuals:

- [`DEFI_MATERIAU / ELAS_ORTH`](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.43.01/Caract_ristiques__lastiques_g_n_rales.html) defines the orthotropic elastic constants and points to material-axis assignment.
- [`AFFE_CARA_ELEM / MASSIF`](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.42.01/Mot_cle_MASSIF.html) defines `ANGL_REP` and local axes; see the axis-order caveat above.
- [`AFFE_CHAR_MECA / LIAISON_DDL`](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.44.01/Chargements_de_type_Dirichlet_.html) defines the scalar linear displacement equation and coefficient ordering.
- [`AFFE_CARA_ELEM / BARRE`](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.42.01/Mot_cle_BARRE.html) documents bar-section properties and syntax.
- [`TEST_RESU`](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.92.01/Op_randes.html) documents analytical result checks and tolerances.
- [ASTER mesh format](https://code-aster.org/doc/v17/manuals/man_u/u3/u3.01.00/index.html) documents hand-authored mesh files and groups.
