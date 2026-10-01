# Code_Aster 17.4 constraint known-answer surrogate

This small input is for a parent-controlled Code_Aster 17.4 run. The fixture
author did not launch the solver. Parent-controlled attempt01 completed with
native exit code 0; its MED output was independently postprocessed to
`nodal-history.json`. The outside checker in this directory returned PASS for
all 101 states in both runs. The parent owns the frozen input/output record at
`docs/wood-joints-mvp/hypotheses/code-aster-stock-trial-2026-09-27/constraints-attempt01/`.

The physical model is one linear TETRA4 with nodes `P1`–`P4`, unit total mass,
and a known consistent mass matrix. A separate elastic TETRA4 carrier has
`RHO=0`. A single `DIS_TR` reference node supplies translation controls and
`DRY`; 24 explicit `LIAISON_DDL` equations map both tetrahedra to the same
infinitesimal rigid translation / rotation field. The reference has zero
discrete stiffness and no assigned discrete mass. The unused `DRX` and `DRZ`
controls are fixed to avoid unrelated free DOFs.

The deck runs two independent, undamped Newmark free-response cases over
100 equal steps from 0 to 1 s. In each case the physical nodal force vector is
the exact consistent-mass product `f(t) = M a(t)` for the specified rigid
mode. The same `LIAISON_DDL`/unused-DOF conditions are included as a constant
mechanical load in both runs. The first checks uniform X translation. The second checks a small
rotation about global Y through nonzero offsets and both affected components.
The carrier receives no applied load; it follows the reference map while
adding no mass or kinetic energy.

`oracle.json` contains the geometry, mass matrix, force vectors, terminal
states, energy, tolerances, and claim limits. For Newmark average acceleration
with `alpha(t)=6e-6 t rad/s^2` and `dt=0.01 s`, the discrete endpoint angle is
`1.00005e-6 rad` (the continuous value is `1.0e-6 rad`); terminal angular
velocity is `3.0e-6 rad/s`. The analogous translation endpoint is
`1.00005e-6 m` with terminal speed `3.0e-6 m/s`. The physical tetra's expected
kinetic energy is `4.5e-12 J` in either isolated case.

## Run files and independent check

The relative-path export is `constraints.export`. It expects the input and
output names shown there in one working directory. The parent run archived
`.mess` and `.rmed`, then exported the six all-state nodal fields. The
independent standard-Python checker needs no Aster or MEDCoupling runtime:

```sh
python3 fea/code_aster_trial/constraints/check_constraints_history.py \
  docs/wood-joints-mvp/hypotheses/code-aster-stock-trial-2026-09-27/constraints-attempt01/nodal-history.json \
  --report docs/wood-joints-mvp/hypotheses/code-aster-stock-trial-2026-09-27/constraints-attempt01/constraints-check-report.json
```

It requires all 101 states for `DEPL`, `VITE`, and `ACCE` in both cases, checks
finite values, time/order alignment, every node and component against the
discrete Newmark recurrence, and computes physical-tetra `v^T M v / 2` at each
state from the consistent mass matrix. Nonzero state and energy values use the
oracle's proposed `2e-4` relative tolerance; expected zeros use `1e-12` in
their respective displacement, velocity, or acceleration units. It also verifies the
`f=M a` force vectors encoded in the oracle and reports the zero-density
carrier's zero mass-energy premise. A check PASS is evidence for this primitive
fixture only.

On parent-controlled attempt01 the checker found zero failing comparisons.
The largest nonzero state relative error was `2.46e-10` (rotation
acceleration), the largest absolute error in an expected-zero state component
was `1.11e-15`, and the largest relative physical kinetic-energy error was
`3.46e-14`. Both terminal kinetic energies were `4.5e-12 J`. These are observed
results for the pinned attempt, not general solver-error bounds.

The oracle tolerance is a proposed fixture gate, not a measured solver error
bound. If it fails, inspect the parsed constraint equations, time integration,
and output precision before changing tolerances. Do not infer performance for
the current A09 equations from this surrogate.

## Method references

These are official Code_Aster v17 manuals, matching the intended runtime line:

- [U4.44.01, `LIAISON_DDL`](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.44.01/Chargements_de_type_Dirichlet_.html#mot-cle-liaison-ddl) defines each equation as an ordered sum of coefficients times DOFs and notes that the group, DOF, and coefficient ordering matters.
- [U4.53.01, `DYNA_NON_LINE`](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.53.01/Op_randes.html#operandes-mode-stat-mass-diag) describes the consistent-mass option and the implicit Newmark route; the deck explicitly sets `MASS_DIAG='NON'` and average-acceleration parameters `BETA=0.25`, `GAMMA=0.5`.
- [U2.02.03, discrete elements](https://code-aster.org/doc/v17/manuals/man_u/u2/u2.02.03/Affectation_des_proprietes_des_discrets.html) lists the `DIS_TR` translation and rotation DOFs and its `POI1` support.
- [U4.42.01, `AFFE_CARA_ELEM` discrete characteristics](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.42.01/Mot_cle_DISCRET_DISCRET_2D.html) documents `K_TR_D_N` for a `POI1` node.
- [U4.43.01, elastic material properties](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.43.01/Caract_ristiques__lastiques_g_n_rales.html) documents `ELAS` material inputs including density.
- [U3.01.00, ASTER mesh file](https://demo-docaster.simvia-app.fr/versions/v17/manuals/man_u/u3/u3.01.00/index.html) describes the native ASCII mesh blocks used by `constraints.mail`.

## Scope boundary

This primitive check covers only linear weighted equations, their reduced
consistent-mass response under a prescribed `M a` load, a small infinitesimal
rotation, and a zero-density carrier. It does not include any A09 coefficient
rows, A09 bolt or nut mesh, contact, thread behavior, a joint load path,
strength, resistance, or candidate acceptance. An A09 one-bolt map check
remains a separate follow-up after this surrogate passes; it must use the
actual selected-axis equations and actual carrier mesh and must stay limited
to that axis and its represented rigid-motion mode.

The least expansive A09 follow-up is a separate first-axis small-angle Y
rotation trial with the actual `M00_A00` / `M03_A00` six-row map, corresponding
positive-density bolt/shaft mesh, zero-density nut carrier, and rigid-carrier
definition. Compare a direct physical-node reference with mapped runs both
with and without the carrier; apply physical-node `f=M a` loads, then compare
all-state displacement, velocity, and physical kinetic energy while checking
the carrier motion and zero inertia. The prior
[`implicit-current-map-applicability-attempt01` audit](../../../docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/implicit-current-map-applicability-attempt01/README.md)
describes the map and a CalculiX 2.23 study design. For a Code_Aster 17.4 trial,
derive the discrete mass oracle from Code_Aster's pinned element formulation
and quadrature, or an independent integral that matches it; do not reuse the
CalculiX mass/quadrature oracle without proving equivalence. This would qualify
only that actual axis and small-rotation mode, not the other three axes or a
joint response.
