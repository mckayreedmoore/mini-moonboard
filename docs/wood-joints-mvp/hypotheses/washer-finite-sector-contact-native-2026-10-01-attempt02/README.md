# Frozen finite-sector contact method attempt 02

This parent-owned, frozen two-body hypothetical annulus fixture checks only
contact load transfer, origin moments and output extraction. The receiver is
isotropic diagnostic material, not wood; contact penalty is not material
compliance. Three fresh independent technical readiness reviews and the parent
receipt preceded its single serialized native launch. Frozen bounds were
60 seconds, 1 GiB, one CPU and one launch. That launch is consumed; no retry
is authorized.

The lower bottom is fixed in all three translation DOFs, and the upper body's
three in-plane gauge DOFs are declared in the actual deck. All 45 pressure
nodes remain disjoint from constrained nodes. Pressure is 2 MPa on 16 top
TRI6 faces, with initial area 18.36880475352431 mm² and force -36.73760950704862 N
in z. Initial origin moment is (-96.67494650869216, 96.67494650869219, 0) N·mm.
Under NLGEOM the verifier uses current face coordinates and the pinned 2.23
three-point element-load rule, also recording an independent six-point
continuous-integral comparison under separately declared fixed limits.

The primary independently parsed the actual constraint inventory, checked
the curved-face rational oracle and exact 2.23 load-assembly source, verified
all preparation hashes and ran seven offline tests, the receipt and Ruff.
The affine prerequisite's three result reviews and final parent receipt are
bound. Contact run `wj-washer-finite-sector-contact-20261001-a02` exited zero
in 5.596 seconds and reached all ten increments through time 1.0. The container
is terminal and the shared native slot returned to idle. The frozen output
audit reports `PASS_FINITE_CONTACT_RESULTANT_METHOD_FIXTURE`. Whole-model
residuals are `7.27e-7 N` and `0.000715 N·mm`, below the unchanged `0.1` limits.
CF equals CFN and all six CFS components are zero. The
[parent output receipt](parent-output-receipt.json) binds raw output,
execution, oracle, coordinate and verifier hashes. Three independent result reviews pass and the primary authenticated their
hashes, raw outputs, execution and unchanged input freeze in the
[final parent result](parent-result.json).

This method pass does not qualify local pressure/stress, washer bending, crushing,
plasticity, partial-seat resistance, actual material or products, joint
resistance, candidate acceptance or any physical operation. The original
unlaunched contact freeze remains preserved separately.

The result review identified an immaterial frozen-verifier detail: node 45's
free-x RF is included in the gauge wrench. Its observed `1.02e-15 N` value has
no effect on any gate, and independent constrained-DOF-only reconstruction
also passes. Preserve this frozen run; a future verifier should explicitly
mask constrained DOFs. This method result does not qualify local pressure,
contact footprint or stress.
