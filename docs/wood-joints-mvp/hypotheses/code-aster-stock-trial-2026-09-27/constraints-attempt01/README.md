# Code_Aster 17.4 constraint known-answer surrogate

This small input is for the parent-controlled Code_Aster 17.4 run. It has not
been run by the fixture author. The parent must freeze the executable/image
digest, documentation revision, and copied input hashes with the run record.

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

## Run files

The relative-path export is `constraints.export`. It expects the input and
output names shown there in one working directory. Run it with the pinned
17.4.0 runtime and archive `.mess` plus `.rmed`; inspect all 101 time states,
especially the terminal `DEPL`, `VITE`, and `ACCE` fields at the eight solid
nodes and the reference. Recompute kinetic energy from the physical tetra
velocity field and the listed mass matrix. Confirm the carrier state follows
the same mapped rigid field and contributes zero kinetic energy.

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
