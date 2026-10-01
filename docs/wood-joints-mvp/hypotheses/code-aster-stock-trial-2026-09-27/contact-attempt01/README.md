# Code_Aster stock contact coupon

This is a small input/output method fixture for the pinned Code_Aster 17.4
trial. It contains two 10 mm by 10 mm plane-strain elastic blocks with
duplicate nodes at their initially touching interface. The right block is
driven through opening, closure, compression, unloading, and reopening. The
single straight interface uses stock `DEFI_CONTACT(FORMULATION='CONTINUE',
FROTTEMENT='SANS')`; no custom contact code or constitutive extension is used.

The 2-D model represents unit depth. All `DY` degrees of freedom are held at
zero to produce uniform uniaxial plane-strain response. With `E=1000 MPa`,
`nu=0.25`, `L1=L2=10 mm`, width `10 mm`, and depth `1 mm`, the axial plane-strain
modulus is

`C11 = E(1-nu)/((1+nu)(1-2nu)) = 1200 MPa`.

Thus the series stiffness is `k = C11*A/(L1+L2) = 600 N/mm`. For imposed
right-end displacement `u`, the expected contact resultant magnitude is
`k*max(-u, 0)`. The expected slave gap is `max(u, 0)` while separated and zero
while touching/compressed. At exact zero displacement both are zero. Expected
loads at the archived compression points are 60 N at -0.10 mm, 120 N at
-0.20 mm, 240 N at -0.40 mm, and then 180/120/60 N on unloading.

`contact_trial.comm` prints `CONT_NOEU` data for both slave nodes and
`FORC_NODA` for both prescribed right-end nodes to separate semicolon-delimited
tables. Run `check_contact_trial.py` against those two files after the parent
has run the frozen input. The oracle groups rows by time, sums `RNX` on the
slave and `DX` on the right end, checks those independent resultants against
the analytic series force, and checks gap/force state against the imposed
history. It accepts a small absolute force/gap tolerance because the
continuous contact formulation uses a numerical enforcement method.

## Version-specific method basis

- [Code_Aster v17 `DEFI_CONTACT` syntax](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.44.11/Syntaxe.html)
  documents `FORMULATION='CONTINUE'`, `FROTTEMENT='SANS'`, and the
  `GROUP_MA_MAIT` / `GROUP_MA_ESCL` zone specification used here.
- [Code_Aster v17 `DEFI_CONTACT` principles](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.44.11/Principes.html)
  documents automatic `CONT_NOEU` output, slave-node `JEU` and `RNX`, and says
  contact-force components in this field are nodal forces: only their
  resultant has physical interpretation; they are not contact pressures.
- [Code_Aster v17 `STAT_NON_LINE` load syntax](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.51.03/Chargements.html)
  documents multiplying an imposed-displacement load with `FONC_MULT`.
- [Code_Aster v17 `POST_RELEVE_T` syntax](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.81.21/Syntaxe_g_n_rale.html)
  documents `CONT_NOEU`, `FORC_NODA`, `TOUT_ORDRE`, and grouped nodal
  extraction. [Code_Aster v17 `IMPR_TABLE` syntax](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.91.03/Syntaxe.html)
  documents the delimited table output used for the independent checker.

The contact documentation recommends linear surface elements in the
continuous formulation where curved quadratic surfaces can create local gap
inconsistencies. This coupon uses straight `SEG2` surfaces deliberately; it
does not test the curved C3D10 contact features in the A09 model. It also does
not test shared-edge surface topology, 3-D face pairing, friction, large
sliding, wood orthotropy, joint load sharing, or any candidate strength or
acceptance criterion. A successful run only establishes the tested stock
method path for this elementary plane-strain case.

## Files and execution

- `contact_coupon.mail`: two block elements, oriented contact segments, and
  groups.
- `contact_trial.comm`: 17.4 command file.
- `contact_trial.export`: relative-file export definition for `run_aster`.
- `check_contact_trial.py`: independent analytic/resultant oracle.

No native solve has been run from this directory. The parent owns freezing and
serialized execution under the pinned image.
