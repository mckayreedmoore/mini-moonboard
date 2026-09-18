# Internal LINEAR-law arithmetic checker

`fea/mortar_linear_law.py` prepares an independent arithmetic check of the
internal variables described in [the exact 2.21 audit basis](mortar-local-audit-basis.md).
**It has not yet been applied to exported solver state and does not validate
the frame's contact solution.** It cannot accept FRD CPRESS/COPEN/CSLIP as
substitutes for the required weighted quantities.

Inputs are the pre-update weighted normal multiplier, two current and
increment-start tangent multipliers, weighted normal displacement minus gap,
two increment-relative tangent displacements, friction coefficient,
inverse regularization stiffnesses, algorithmic constants, activity and active
DOF count. Only mode-1 LINEAR normal and ordinary tangent regularization are
supported; other modes, nonfinite inputs/intermediates and an undefined slipping
direction are rejected. Excluded constraints retain `eligible=False`, even
when their arithmetic residual happens to be zero.

Outputs include signed normal/tangent residuals, weighted regularized opening,
the complementarity product, algorithmic friction bound and internal Coulomb
excess. No pass threshold is supplied. In particular, the tangent branches have
different residual definitions; do not compare them using a guessed common
dimensional tolerance or substitute unweighted physical node clearances.

The equations come from the pinned [official CalculiX 2.21 source](https://www.dhondt.de/ccx_2.21.src.tar.bz2):
`stressmortar.c`, `regularization_gn_c.f` and `regularization_gt_c.f`. The checker
recomputes arithmetic on supplied values; reconstructing those values requires
the frozen bases and coupling/state data specified in the audit basis.

```sh
uv run pytest tests/test_mortar_linear_law.py
```

The 22 synthetic checks cover compressed stick, open/inactive and excluded
states, tension and penetration mismatch, oblique slip/reversed slip,
nonzero two-component increment-start history, the source's frictionless
branch, invalid modes and arithmetic overflow. Independent review exposed an
overflow path that could falsely return zero tangent residuals, and missing
coverage of the second tangent component; both now have regression checks.

Next: connect this checker to a separately identified, read-only observer with
full-precision pre/post-state and accepted-increment provenance. Compare the
observed build with the unmodified upstream build on a small sliding coupon
before any full-frame replay. Zero residuals on these synthetic inputs are
not an observation of the actual FEA solution, joint capacity or floor behavior.
