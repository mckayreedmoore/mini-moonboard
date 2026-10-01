# Consistent solid self-weight method check

One pinned stock CalculiX 2.23 run completed with exit zero. Five C3D20 elements
represent a 100 × 50 × 1,000 mm bar with E = 7,000 MPa, zero Poisson ratio,
2.5 kg uniform mass and its bottom face fixed. The exact axial displacement is
`uz(z) = -q*z*(L-z/2)/(E*A)`, with `q = mg/L`. The predicted tip displacement
is -0.0003502375 mm and total upward support reaction is 24.516625 N.

The maximum displacement error over all 68 nodes is 2.50e-11 mm. Correctly
recovered total reaction differs by 3.83e-6 N. Both pass the original frozen
tolerances. See [result.json](result.json), [execution.json](execution.json)
and the independent input [review](review.json).

The first assessor incorrectly treated the printed fixed-node RF sum as pure
reaction, producing an apparent 0.817217 N imbalance. That failed assessment
is preserved in [initial-assessment.json](initial-assessment.json). The
[pinned manual](https://www.dhondt.de/ccx_2.23.pdf), PDF pages 398 and 568,
explains that RF also includes loads applied at those nodes. Subtracting the
fixed-node CLOAD sum of -0.817220833 N recovers the support reaction. This
fixture has no DLOAD or MPC contribution. The local manual's pinned SHA-256,
page references and corrected postprocessor hash are recorded in the result.

No deck, native output, expected answer or tolerance was changed, and no
second native invocation was needed. The freeze retains the original source
snapshot; the live postprocessor has the documented output-reading correction.
Use `verify(..., check_live=False)` to verify this historical frozen packet.
The independent [postrun review](postrun-review.json) passed. It checked the
original output hashes, execution/authorization/ledger bindings, pinned manual
and corrected reaction/displacement recovery without rerunning the solver.

This verifies the consistent nodal gravity method on a prismatic isotropic
bar. It does not qualify current timber properties, panel layups, omitted-hole
mass details, hardware condensation, frame equilibrium or any physical joint.
The whole-frame audit recovers physical floor/interface forces independently
of fixed-node RF and excludes auxiliary local gap-reference loads.
