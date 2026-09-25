# WJ24 independent C3D10 Jacobian audit, attempt 01

Status: independent Gauss5 Jacobian and volume audit passed on 2026-09-24. The audit consumed the saved WJ24 five-body deck and report; it imported no CAD or Gmsh, generated no mesh and ran no solver.

[The exact audit report](independent-jacobian-audit.json) and its [execution command record](execution.json) are preserved with the frozen auditor and test snapshots. The result covers 89,743 nodes, 46,629 C3D10 elements and 652,806 Gauss5 determinants across the five WJ24 bodies. Every determinant is positive; the minimum is 1.5292878761987154 mm³. Maximum volume error against `WJ24_finished_geometry.volume_mm3` is 1.1373814184922892×10⁻⁵.

The audited inputs are part of the [WJ24 baseline mesh archive](../../wj24-baseline-patch-mesh/attempt-01/README.md). The saved WJ24 `mesh.json` and `mesh.inp` hashes recorded by the independent report match the archived input members. [readback-verification.json](readback-verification.json) records the archive/source/report hash checks.

This verifies positive Jacobians at the pinned 14 Gauss5 points and volume consistency at the reported tolerance. It does not prove positivity at every point within each quadratic element, nor establish contact, material behavior, stiffness, strength, response or release. The earlier [attempt 00 schema rejection](../attempt-00-rejected-hardware-contract.md) remains preserved as history.
