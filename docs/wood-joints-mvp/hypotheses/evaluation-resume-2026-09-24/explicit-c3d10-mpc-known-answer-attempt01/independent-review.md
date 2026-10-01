# Independent raw-output review

Reviewed 2026-09-27, read-only. This review covers the frozen one-element
CalculiX 2.23 C3D10 direct-versus-homogeneous-MPC mass-coordinate fixture. It
does not accept a joint, material model, structural criterion, or current-joint
analysis.

## Integrity and completion

The frozen input inventory matches `input-freeze.json` (SHA-256
`b83aed658ff4e1d9508eb5f76ff2eaacc5f9618f275fb1afb71c2306258a2e31`), and
both execution records' eight-file output inventories match their recorded
hashes. The execution record SHA-256 is
`3651d84181b5daaf31263dca8c5b8bdcdf44ef2a65f44212cfebeeb6f4c64011`; the
verifier JSON SHA-256 is
`3b6fe7db7c3175baa385f647921d4d9a400ef8a627a491452be143bc1163bed4` and its
recorded verifier source SHA-256 is
`e42c5e0b9ced533b461bc984e39d7a0d5081c45ddb1022206251bf7fbe909620`.

Both native processes exited 0, were not OOM-killed, completed normally, and
have empty stderr. Each FRD contains 100 timed states, increments 1–100 from
0.001 s through 0.100 s, with 10 physical nodes in DISP, VELO, and FORC and 10
physical-node ENER values per state. DAT and FRD physical U/V/RF parity passes.
There are no numeric STA/CVG rows, consistent with the explicit output path.
The solver warns that the requested initial increment is unused; it reports a
stable Courant increment of 0.2558639 s and selects 0.001 s. No mass- or
spring-scaling signal appears, and both `.12d` files are empty.

| Case | DAT SHA-256 | FRD SHA-256 | stdout SHA-256 |
| --- | --- | --- | --- |
| direct | `3a41d72c9b4392e811598d77f8106a3d809f0b34de5903305668c2d660bd2d11` | `3ea7d2d78dc33e0db510e638d91c4d50ce17ef2a0c26ac8343db96f49e6314ac` | `b327a758a8bf5bcf66014f6b2ad460846d56caf47a6cc2ed808c3ac5c1712eff` |
| mapped | `5ad1afd3fac3781378149f9af71c389be5dc3361ef81ae157215382fbf1f5e1a` | `8072916ba3c6042c006e16c3919fe49154fa0cff9f56a80e69de4d01a7f318a6` | `eb61a695bd503a6cc119c31257acb939655c9cdb9ed95199927f16486d3d6b2d` |

## Known-answer results

The unit tetrahedron has volume `1/6 mm³`; density `6 tonne/mm³` gives total
mass `1 tonne`. The pinned C3D10 lumped-mass fractions are `1203/44812 tonne`
at each of four corner nodes and `5000/33609 tonne` at each of six midside
nodes; their sum is exactly 1 tonne. Both DAT histories report `EMAS=1.000000`
and `EVOL=0.1666667` at the terminal state. The mass split is from the pinned
`e_c3d.f` member (SHA-256
`d009650b48e5ca150080aed9e19d1b65d2b2cf4869ab6d7f2b1a5cd55e2df3fc`, lines
1921–1975).

The direct-coordinate case reproduces the rigid-translation oracle at all 100
states. At 0.001 s, every physical node has `U1=5e-7 mm` and `V1=0.001 mm/s`;
at 0.100 s, all have `U1=0.005 mm` and `V1=0.1 mm/s`. Across all states, the
maximum U1 error is `8.67e-19 mm` and the maximum V1 error is zero. Terminal
DAT totals are `ELKE=0.005 N·mm`, `ELSE≈1.49e-33 N·mm`, `EMAS=1 tonne`, and
`EVOL=0.1666667 mm³`. The frozen verifier reports direct PASS.

The mapped case fails the same frozen physical-motion oracle. At 0.001 s,
`V1/t` for physical nodes 1–10 is approximately
`[1, 7.76e-8, -3.88e-8, -3.88e-8, 0.9999999, 1, 1, 1, 1, 1] mm/s²`;
controller node 11 has `U1=1.25e-7 mm`, one quarter of the rigid-motion
oracle's `5e-7 mm`. This finite-first-step pattern agrees with the pinned
source/preflight diagonal-only initial-acceleration diagnostic
`[1,0,0,0,1,1,1,1,1,1]` and controller acceleration `0.25 mm/s²`; it is a
diagnostic comparison, not a direct instantaneous-acceleration measurement.

At 0.100 s, mapped physical nodes 2–4 have `U1` of `2.595698e-6 mm` and
`-1.278478e-6 mm` each, with `V1` of `1.040094e-4 mm/s` and
`-5.084387e-5 mm/s` each, rather than the uniform `0.005 mm` and `0.1 mm/s`.
The other physical nodes are near the uniform displacement, while controller
node 11 is at `0.001252579 mm` rather than `0.005 mm`. Over the 100 DAT states,
maximum physical U1 and V1 errors are `0.005001278478 mm` and
`0.10005084387 mm/s`; the frozen limits are `5.01e-7 mm` and
`1.0001e-5 mm/s`. The frozen verifier therefore reports mapped FAIL. This is
the primary result: the mapped explicit inertia path does not preserve the
known-answer motion.

The mapped MPC equation residual peaks at `1.476e-9 mm`, slightly above its
frozen `1e-9 mm` absolute gate. The parent's independent Decimal rounding-bound
audit places all 100 printed residuals within rounding bounds (maximum residual
to rounding-bound ratio `0.9091`). The frozen gate still
fails and remains unchanged. It is not the primary failure: the physical
motion and controller displacement miss the oracle by orders of magnitude.
The native mapped terminal totals also miss the frozen uniform oracle
(`ELKE=0.006641083 N·mm`, `ELSE=2.493604e-6 N·mm`), while mass and volume still
pass.

## Energy interpretation and boundary

The energy numbers use distinct formulations. In the pinned source archive
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`,
`resultsmech.f` (SHA-256
`15fccc9fb553f259af5d33bc78e8d3808f1f9f338ee266ce92192bae33026fa6`, lines
1100–1107) interpolates nodal velocity to integration points and sets
`ener(2)=rho*|v|²/2`. `calcenergy.f` (SHA-256
`5f705ac94653c9a80b492fa9d1424c57ac04263f1b4bce260310b296c0b01a9e`, lines
304–324) and `printoutelem.f` (SHA-256
`e5da47dd83dd8e796fcbf8ec81e220b5139211b8f411c03adb17a782436e2544`, lines
417–430) integrate that quantity with quadrature weights and the element
Jacobian. This continuum-integrated native ELKE is not the same diagnostic as
`1/2 Σ m_i V_i²` using the explicit diagonal nodal masses when the mapped
motion is nonuniform.

Using the frozen nodal masses and mapped DAT velocities gives terminal
physical lumped kinetic energy `0.004593985098 N·mm`; adding native `ELSE`
gives `0.004596478702 N·mm`. The constant-force work from the physical nodal
loads and DAT displacements is `0.004596484914 N·mm`. This separate calculation
helps interpret the nonuniform response; it does not replace the frozen
uniform known-answer gates. In particular, `work - native ELKE` is not evidence
that energy was created.

The direct case's pass validates only this direct-coordinate one-element
trajectory. The mapped case's failure blocks relying on this pinned 2.23
explicit homogeneous-MPC coordinate path as a demonstrated method for the
intended application. It does not establish a current-joint result or imply a
joint geometry/material failure. Frozen inputs remain unchanged; no solve was
rerun for this review.
