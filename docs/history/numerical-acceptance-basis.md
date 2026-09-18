# Numerical acceptance: diagnostic gates versus design evidence

Research recommendation, not a changed policy. All existing runs retain their
0.1 N force and 1 Nmm moment gates and their published outcomes. No failed run
is accepted or relabeled by this document.

## Finding

The existing absolute gates are self-selected diagnostic tolerances, not
published structural requirements. No reviewed source establishes 1 Nmm as a
universal acceptance requirement for a frame of this scale. A relative,
quantity-specific numerical error budget could be defensible for a future
study, but only if defined before its acceptance runs, supported by refinement
and benchmark evidence, and kept separate from engineering safety margins.

For arithmetic context only, 1 Nmm divided by a declared 1,000,000 Nmm moment
scale is `1e-6` (0.0001%, one part per million). A 96 Nmm residual on that same
scale is `9.6e-5` (0.0096%). These ratios neither establish an appropriate
denominator for a particular run nor make the latter acceptable. Choosing a
threshold from the observed 96 Nmm discrepancy would be result-fitting.

## What the primary documentation actually supports

| Source | Relevant guidance | Not implied |
| --- | --- | --- |
| [CalculiX 2.21 manual archive](https://www.dhondt.de/ccx_2.21.htm.tar.bz2), `doc/ccx/node242.html:382–403`, inspected locally | Default largest residual / average force criterion is 0.005; largest correction / incremental solution criterion is 0.01. Its average force is based on absolute element nodal-force components and the increment history. | Neither 0.5% of total applied load nor 0.5% of total overturning moment is the documented global-balance acceptance rule. |
| [Abaqus: solving nonlinear problems](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEANLRefMap/simaanl-c-nonlineareqns.htm) | Checks maximum force residual against a force scale and requires a small displacement correction; the latter default is 1% of the increment. | Newton convergence does not demonstrate mesh accuracy, correct contact geometry or a safe design. |
| [ANSYS CNVTOL command](https://mapdl.docs.pyansys.com/version/stable/mapdl_commands/solution/_autosummary/ansys.mapdl.core._commands.solution.nonlinear_options.NonlinearOptions.cnvtol.html) | Documents default force/moment tolerances of 0.005, with reference values, minimum references and selectable norms. Defaults can be adjusted internally. | The moment criterion is not automatically a check of summed `r cross F` about our chosen origin; solid translational DOFs do not become rotational DOFs because we postprocess their moments. |
| [Abaqus: changing convergence checks](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEANLRefMap/simaanl-c-convergencechecktype.htm) | Defaults generally need no change; alternatives require experience and testing of accuracy. | Switching to a relaxed criterion to obtain completion is not validation. |
| [Abaqus: mesh convergence](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEGSARefMap/simagsa-c-ctmmeshconverg.htm) | Compare refined meshes for the quantities of interest. Displacement can converge while stress does not; idealized sharp corners can produce nonconvergent peak stresses. Coarse models require caution about absolute magnitudes. | Equilibrium of one mesh establishes neither stress accuracy nor a mesh-independent contact response. |
| [ANSYS: contact mesh refinement](https://ansyshelp.ansys.com/public/Views/Secured/corp/v261/en/wb_sim/ds_contact_troubleshoot_mesh.html) | Resolve curvature and use adequate mesh density on both contact sides; its guidance includes several elements across a contact region. | A dense slave mesh against one deformable master brick is automatically verified, or its recommendation is a universal CalculiX element-count rule. |

ANSYS also documents a tradeoff between contact penetration and conditioning
when selecting stiffness. Contact stiffness therefore needs a separate
sensitivity assessment; merely tightening equilibrium criteria is not a
substitute. No change to our physical or contact parameters is authorized here.
[ANSYS contact settings](https://ansyshelp.ansys.com/public/Views/Secured/corp/v261/en/wb_sim/ds_contact_best_prac_solver.html)

## Four distinct questions

1. **Data and formulation integrity:** Are the actual deck, mass, supports,
   contact definitions, load nodes and output semantics correct and complete?
   Missing output, wrong restraints, double-counted reactions and unverified
   multiplier interpretations cannot be cured with a numerical tolerance.
2. **Discrete solution accuracy:** Are nonlinear force/correction and local
   contact-law residuals sufficiently small for the specified equations?
   Global force and moment sums are independent useful checks, but local
   errors can cancel globally. Conversely, frozen contact mapping may create
   a current-geometry moment discrepancy even when algebraic residuals pass.
3. **Calculation verification:** Are selected displacements, patch reactions,
   contact states and other outputs stable under mesh and increment refinement?
   Solver completion answers neither this question nor the previous one by
   itself.
4. **Physical validity and design adequacy:** Do material, joint, floor,
   friction and loading assumptions describe the actual structure? Are
   applicable safety margins and failure modes addressed? Even exact solution
   of an ideal-bonded model cannot answer this for unresolved real connections.

The separation and the future policy below are project recommendations drawn
from the cited guidance, not a vendor-prescribed acceptance standard.

## Proposed future policy, requiring separate approval

Keep current diagnostic gates as a named, immutable policy version. A future
version should report both absolute and normalized residuals, even where only
one governs. Do not silently reuse the word “pass” for a different policy.

Define scales and error budgets before the acceptance batch:

- Fix a physical reference origin `o` and characteristic length `Lref` from
  the unchanged geometry. Define `Fref` from declared applied loads and body
  weight, independent of mesh node count; do not normalize by a nearly zero
  net resultant or inflate the denominator with erroneous computed reactions.
  Record both the selected scale and its rationale. `Mref=Fref*Lref` is one
  possible declared dimensional scale, not a mandatory formula.
- Retain the actual residual vectors `RF=sum(Fexternal)` and
  `RM(o)=sum((x+u-o) cross Fexternal)` with consistently integrated body forces
  and any actual applied couples. Report, for example, infinity norms divided
  by `Fref` and `Mref`, alongside every component and per-patch values.
- Specify absolute and relative numerical budgets, potentially of the form
  `AF+rF*Fref` and `AM+rM*Mref`, but do not choose their numbers from current
  failed runs. Low-load cases need explicit handling; an absolute floor must
  not become permission for spurious support forces.
- Propagate printed-force, displacement, coordinate and integration
  uncertainty separately. If a residual estimate is `R` with a defensible
  error bound `E`, a conservative pass requires `abs(R)+E` below its budget;
  `max(0,abs(R)-E)` above the budget establishes a resolved exceedance. The
  interval crossing the budget is unresolved. Do not add measurement error
  to a physical tolerance merely to manufacture a pass.
- State the decision-relevant quantities and allowable uncertainty first.
  Their numerical error must be small enough that the engineering conclusion
  is unchanged. No fixed percentage of load guarantees this near lift-off,
  sliding, a contact-state transition, buckling or a nearly exhausted margin.

Origin dependence matters when force balance is imperfect:
`RM(o+a)=RM(o)-a cross RF`. Thus a 0.1 N force residual can change a reported
moment by as much as 100 Nmm under a 1,000 mm origin shift. This is an upper
bound, not the measured discrepancy in any run. A strict moment gate needs
joint interpretation with force balance, a fixed documented origin and
deformed load locations; it is not independently origin-invariant.

Before adopting numeric budgets, use known-answer contact benchmarks and
matched pristine/diagnostic solver comparisons. Then refine increments and
both contact-side meshes separately, holding physical assumptions fixed.
Compare the same spatial quantities rather than whichever node happens to
have the maximum on each mesh. For this project, useful quantities include
loaded-point displacement, patch force and moment resultants, support-load
distribution, active/open regions and admissible penetration/slip measures.
Track local law residuals with the formulation-specific semantics described
in [the mortar audit basis](mortar-local-audit-basis.md).

At least three levels can help reveal a trend rather than an accidental
two-mesh agreement; this is a proposed study design, not a universal rule.
Do not infer an asymptotic error estimate if contact transitions or oscillatory
results invalidate that assumption. A failed local-law check, changed contact
branch or unresolved model assumption remains visible even if the normalized
global moment is small. There is insufficient evidence now to choose a new
numerical threshold or to declare a previously rejected frame solution valid.

## Interpreting the mortar active-set override

Exact 2.21 `stressmortar.c:842–848` sets an activity flag from its local
residual checks; `:1022–1024` later clears that flag if the iteration count
exceeds `ndiverg`, with an adaptive-time-stepping comment. This is evidence
that the final flag alone is not a local-residual certificate. It is **not**,
by itself, proof that the solver is wrong or that any particular accepted
increment has excessive residuals. Test the actual accepted state and residual
history before making that claim. Diagnostic output must not alter the
numerical algorithm to force agreement with an assumed interpretation.

This document changes no code, tolerance, historical result or engineering
rating. It supports a future predeclared verification policy, not retrospective
threshold selection.
