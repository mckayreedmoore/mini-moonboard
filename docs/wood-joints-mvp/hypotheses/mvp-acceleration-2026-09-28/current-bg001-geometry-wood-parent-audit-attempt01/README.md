# Independent BG001 reference audit

`check.py` independently checks the pinned signed a12-rear actions, selected
loaded ends, arithmetic of the recorded angle-interpolation method, minimum
group geometry factor and scaling of the individual lateral references. The
two resulting conditional comparisons are 0.60184 and 0.69728. It does not
establish a mixed-direction group-action factor or adjusted resistance.

The same audit checks the Appendix E parallel-component arithmetic. The
519.4605 N parallel group component gives unadjusted row-reference comparisons
of 0.17301 for the spine and 0.21626 for the post. Two shear lines with the
triangular stress distribution described in E.3.3 give `n Fv t s_critical`;
there is no extra factor of two. The candidate spine net-area reference uses
575 psi and 5036.82 mm². These component comparisons do not resolve the
oppositely directed cross-grain actions, splitting or complete joint behavior.

The unsupported Chapter 5 glulam `Cvr` factor is excluded from this solid-sawn
scenario. Applicable Chapter 4 material/service adjustments remain unresolved.
The audited geometry and material inputs remain conditional; this audit does
not inspect parts or reopen unchanged original LEG/FLOOR-RUNNER resistance.

Reproduce from the repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg001-geometry-wood-parent-audit-attempt01/check.py
```

`audit.json` records the exact two input-screen hashes and the claim limits.
