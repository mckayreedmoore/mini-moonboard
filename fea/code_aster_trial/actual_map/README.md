# Code_Aster 17.4 actual A09 first-map inertia fixture

This fixture prepares one bounded method check for the actual first A00 bolt/nut
weighted map. It compares a free physical-body response with the same body under
the exact first six source map equations, then repeats the mapped response with
the zero-density A00 nut carrier. It does not model contact, preload, threads,
wood, joint capacity, or a complete joint.

The source geometry and weighted coefficients are read from the pinned
`ordinary-port-motion-attempt09-common-map` files and are not edited. The
generator writes three independent Code_Aster `.mail` / `.comm` / `.export`
sets in `input/`, plus `oracle.json` and `input-manifest.json`. `GROUP_NO`
singleton groups preserve the source node/DOF term order for the 754-term rows;
source coefficients are emitted with their original numeric text. Numeric
source IDs receive `N` and `M` prefixes in the ASTER mesh so Code_Aster reads
them as names.

The input body contains 5,490 C3D10/TETRA10 elements and 11,348 positive-density
physical nodes. The optional M03 A00 nut carrier adds 519 TETRA10 elements and
1,107 nodes with `RHO=0`. The physical force vector is the same in all three
cases and is assembled as `f=M a` from the consistent scalar mass matrices.
The mode is infinitesimal rotation about global Y through the source pivot
`(134.5, 1.178456090256, 410.856889078727) mm`; there are 10 Newmark increments,
`dt=1e-5 s`, ending at `1e-4 s`. The acceleration ramp is
`alpha_y(t)=1.2e6 t rad/s^2`, giving the discrete endpoint rotation
`2.01e-7 rad`. The short time scale was selected to keep elastic and rigid-body
inertia scales numerically well separated without changing geometry, material,
or target angle.

The pinned Code_Aster 17.4 ordinary 3D `MECA_TETRA10` mass rule is FPG15, with
pointwise curved Jacobians; this oracle does not reuse the CalculiX four-point
rule. An isolated native mass probe matched every entry of a curved TETRA10
consistent mass matrix against FPG15 to normalized maximum error `1.25e-15`.
The independent aggregate mass review gives physical mass
`4.208482861852778e-05 tonne` and pivot `Iyy=0.1538313026661648 tonne mm^2`.
The checker rebuilds the element matrices, verifies the nodal `M a` vector and
computes `v^T M v / 2` from every measured physical-node velocity state.
The energy values are in `tonne mm^2/s^2`, equivalently `N mm`, not joules.

The carrier equations express a linear PETIT rigid field about the pivot using
the reference-node translations and rotation-node translations. The two
control nodes intentionally remain separate, coincident source nodes. The MED
extractor therefore must use node groups to identify them; matching by
coordinate alone is ambiguous. The checker uses singleton source-name groups
to map every node identity, then reports the small MED coordinate
serialization error separately. This checks one small-motion mode and makes
no finite-rotation claim for the carrier.

## Frozen acceptance checks

The checker reads the parent-frozen
[`actual-map-readiness.json`](../../../docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/actual-map-readiness.json)
and fails if it is not marked frozen. It does not modify or infer tolerances.
For each field and state, every physical component must satisfy
`|actual - expected| <= absolute_floor + 1e-5 * physical_mode_peak`, where the
peak is the maximum absolute analytical physical-body component at that state.
The same bound is applied to each pair of physical cases. The frozen floors are
`1e-12 mm` for displacement, `1e-10 mm/s` for velocity, and `1e-7 mm/s^2` for
acceleration. The time tolerance is `1e-12 s`; energy uses relative `1e-5` and
the initial zero-energy floor `1e-22 tonne mm^2/s^2`. Source coordinates and
ordered equation coefficients in the input decks must match exactly. MED
coordinates are matched through source-ID singleton groups because Code_Aster
round-trips some literals through its mesh representation. The output
serialization error is reported separately and bounded at `1e-10 mm`; it does
not alter mechanical field or energy tolerances.

For mapped controls, `NREF` translations are compared with zero and `NROT`
translations are interpreted as angle, angular rate, and angular acceleration
because that is how the source map encodes rotation controls. Those `NROT`
comparisons use their own expected angular-component peak and the same
numerical floor in the encoded units. Carrier nodes are checked both against
the analytical mode and against the measured `NREF + theta × r` field at every
state, using the frozen physical-body mode-peak bound.

The check requires all 11 states and all expected MED nodes, finite `DEPL`,
`VITE`, and `ACCE` values, one-to-one source-name-to-MED-index mapping,
coordinate serialization, physical/carrier group agreement, and distinct
one-node `NREF` and `NROT` groups at the same source pivot. It checks the
carrier translations against the linear small-motion field and confirms that
its zero-density mass contributes no kinetic
energy. Any failure is reported against the frozen bounds; the checker must
not relax a tolerance after seeing native output.

## Extraction and checking

The parent serializes the native runs and exports the MED histories. Extract
each case with the repository's pinned MEDCoupling environment. Keep the two
coincident controls distinguishable by requesting their node groups:

```sh
.venv/bin/python fea/code_aster_trial/extract_candidate_med.py direct.rmed \
  --all-singleton-groups --node-group PHYS_NODES > direct-history.json
.venv/bin/python fea/code_aster_trial/extract_candidate_med.py mapped_no_carrier.rmed \
  --all-singleton-groups --node-group PHYS_NODES \
  --node-group NREF --node-group NROT > mapped-history.json
.venv/bin/python fea/code_aster_trial/extract_candidate_med.py mapped_carrier.rmed \
  --all-singleton-groups --node-group PHYS_NODES --node-group CARRIER_NODES \
  --node-group NREF --node-group NROT > mapped-carrier-history.json

.venv/bin/python fea/code_aster_trial/actual_map/check_actual_map_history.py \
  --direct direct-history.json \
  --mapped-no-carrier mapped-history.json \
  --mapped-carrier mapped-carrier-history.json \
  --input-root fea/code_aster_trial/actual_map/runtime_input \
  --report actual-map-check-report.json
```

The offline checker verifies source-file pins, the ordered six-row equation
digest, the exact node/DOF/coefficient tokens in both mapped `.comm` files,
the generated-input hashes, identical physical nodal forces in all cases, and
the independently rebuilt FPG15 mass/load oracle before it inspects histories.
If the parent raises a native `.export` time limit, the checker accepts only
that single `P time_limit` change and records it; all `.comm` and `.mail` files
must still match the manifest. It never launches Code_Aster or requires
MEDCoupling. Its Python environment needs NumPy for the TETRA10 integration.

The parent-controlled native run and this checker passed all three cases. All
11 states were present for each case. The largest analytical physical-field
error divided by its frozen bound was `4.97e-8`; the largest pairwise physical
case difference divided by its bound was `4.82e-8`. The carrier's measured
control-to-node consistency error was at most `7.88e-10` of the frozen bound
over its 1,107 nodes and all 11 states. The largest control-history normalized
error was `2.27e-7` of the bound.

At the endpoint, the FPG15 expected physical kinetic energy is
`2.7689634479909567e-6 N mm`. The measured values were `2.7689634479911706e-6`
for direct, `2.7689634479914675e-6` for mapped without the carrier, and
`2.7689634479918935e-6 N mm` with the carrier. Across all states, the largest
per-case relative energy error was `3.39e-13`, and the largest pairwise
relative difference was `2.61e-13`. The maximum MED coordinate serialization
error was `1.14e-13 mm`; generated input coordinate tokens and all source
TETRA10 connectivity/order were checked exactly. Full metrics and audits are
in the parent evidence
[`actual-map-audit.json`](../../../docs/wood-joints-mvp/hypotheses/code-aster-candidate-checks-2026-09-27/actual-map-audit.json).

The intended syntax follows the v17 manuals: [`LIAISON_DDL` equations and
ordered lists](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.44.01/Chargements_de_type_Dirichlet_.html#mot-cle-liaison-ddl),
[`DYNA_NON_LINE` with consistent mass and Newmark](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.53.01/Op_randes.html#operandes-mode-stat-mass-diag),
[`DIS_TR` control nodes](https://code-aster.org/doc/v17/manuals/man_u/u2/u2.02.03/Affectation_des_proprietes_des_discrets.html),
[`K_TR_D_N` discrete stiffness](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.42.01/Mot_cle_DISCRET_DISCRET_2D.html),
and the [volumetric-element FPG15 rule and TETRA10 node order](https://code-aster.org/doc/v17/manuals/man_r/r3/r3.01.01/Les__l_ments_volumiques.html).

The native cases were parent-controlled; the checker itself does not execute
Code_Aster. A checker pass supports only the observed first-axis small-motion
inertia/mapping method check; it is not a joint acceptance, strength result,
finite-rotation validation, or construction release.
