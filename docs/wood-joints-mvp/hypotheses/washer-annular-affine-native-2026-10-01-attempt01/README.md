# Affine annulus native method attempt 01

October 1, 2026. Exact input freeze prepared for independent review; no
launch or result is recorded at this checkpoint. This is a hypothetical
C3D10 elastic software patch, not the current candidate washer, wood model
or a resistance check. The contact job remains separate and unapproved.

The parent verified the source preparation's five offline tests, Ruff,
eight generated-file hashes and five supporting-code hashes. This attempt
copies the affine deck, expected contract (`model.json`), coordinates,
verifier, known contact-output parser and source receipts. Nine exact live
source copies, the pinned solver profile and all seven input-file hashes are
bound by `freeze.json`, SHA-256
`093ab967c805858b33e3d0530cadab25625cc3b8c69f696d3c39885302fa6817`.
The existing `fea/wood_joint_reduced_native.py` freeze verification passes.

The mesh has 800 nodes, including 288 free interior nodes, and 384 C3D10
elements. With 16 angular sectors, inner/outer radii 2.5/5.5 mm and height
1.5 mm, an independent regular-polygon calculation gives area
73.47521901409723 mm² and volume 110.21282852114585 mm³. For hypothetical
`E=200000 MPa`, `nu=0` and prescribed axial strain `-0.0001`, the targets
are `sigma_zz=-20 MPa`, top reaction `-1469.5043802819441 N`, the opposite
bottom reaction and elastic energy `0.11021282852114585 N mm`. These agree
with the generated contract without using any solver output.

The parent checked the pinned 2.23 manual's C3D10, face-contact, surface
labels, pressure loading, nodal force, integration-point stress and energy
sections. Exact applicable output and tolerance gates are in `model.json`;
the verifier requires the complete node/element/integration-point identities.
All values are diagnostic assumptions and do not qualify steel or wood.

Independent correctness, testing and architecture reviewers own their
separate readiness records. Parent must inspect their conclusions before
writing a concrete ready receipt. Only then may it use the existing native
protocol for one serialized launch, at most 60 seconds, 1 GiB and one CPU.
Stop and diagnose after any launch or method gate failure. No contact run,
repeat attempt, altered tolerance or criterion acceptance follows by default.

Raw native files and freezes remain local. Preserve every consumed attempt.
No geometry, purchased hardware, selected-candidate authority, physical
operation, candidate selection or release flag changes in this packet.

## Recorded result

The parent subsequently satisfied all three independent readiness reviews
and recorded the exact one-launch/60-second/1-GiB/one-CPU caller controls in
`parent-readiness.json`. Run `wj-washer-annular-affine-20261001-a01` exited
successfully, with native CalculiX time 0.032404 seconds; the container was
confirmed terminal and the shared slot returned idle. This freeze is consumed
and must not be relaunched.

The unchanged frozen verifier passes all 800 displacement and RF rows and
1,536 integration-point stress rows. Maximum stress-component error is
`2.952276e-14 MPa`; free-interior displacement error is
`2.7592085202762085e-20 mm`. Printed top/bottom reaction magnitude is
`1469.504208 N`, differing from the oracle by `0.000172281944 N` within the
frozen `0.015695043803 N` gate. Printed energy is `0.1102128 N mm`, also
within its frozen gate. Whole-boundary force and moment closure pass.

Three independent result reviews pass with no substantial findings. The
parent authenticated their hashes, execution and all raw output pins in
`parent-result.json`, SHA-256
`8ef7b5a09f683ab3c8e0cc7e5f27707d536122ed17a4ddae867381d1c500c44c`.
The reusable conclusion is limited to this affine elastic software fixture.
Contact, bending, actual material, candidate resistance and criterion
acceptance remain outside the result.
