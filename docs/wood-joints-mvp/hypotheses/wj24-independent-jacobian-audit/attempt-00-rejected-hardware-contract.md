# WJ24 independent Jacobian audit: rejected hardware-only input

Status: rejected at report-contract validation; no independent audit output
was created.

The first CLI attempt targeted the WJ24 baseline mesh at
`fea/generated/wj24-baseline-patch-mesh/attempt-01`. At that time,
`fea.wood_joint_mesh_jacobian_audit` accepted only the historical WJ04
physical-hardware report schema and completion status. It stopped at that
input gate with the error:

`mesh report is not a completed WJ04 physical-hardware mesh`

The WJ24 report instead declares `wood_joint_wj24_patch_mesh/v1` and
`VERIFIED_WJ24_C3D10_MESH_ONLY_NO_SOLVER`.

The rejected attempt did not reach deck parsing or any Jacobian or volume
calculation. It created no audit JSON file and changed neither `mesh.json` nor
`mesh.inp`. This is an input-contract mismatch, not a mesh-quality result.

The auditor now has a separate WJ24 finished-wood profile with its exact five
body IDs and `WJ24_finished_geometry.volume_mm3` reference. The WJ04 hardware
profile retains its previous schema, status, scenario, body IDs, element-set
prefix and imported-CAD volume reference. The updated auditor still needs to be
run against the saved WJ24 mesh before any independent result can be reported.
