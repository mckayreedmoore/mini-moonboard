# Independent WJ24 mesh Jacobian audit

The independent Gauss5 Jacobian and volume audit passed on the saved WJ24
baseline mesh. [Attempt 01](attempt-01/README.md) preserves the report, command,
frozen auditor/test sources and readback checks. The input deck and report are
archived with the [WJ24 baseline mesh](../wj24-baseline-patch-mesh/attempt-01/README.md).

The result covers 89,743 nodes, 46,629 C3D10 elements and 652,806 Gauss5
determinants across five bodies. All determinants are positive. The maximum
volume error against `WJ24_finished_geometry.volume_mm3` is 1.1373814184922892e-05.

The earlier [attempt 00 schema rejection](attempt-00-rejected-hardware-contract.md)
remains preserved; it created no audit output. This audit establishes neither
contact nor material response, strength, or release.
