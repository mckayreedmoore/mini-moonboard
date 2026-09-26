# Linked angular-output diagnostic build

The parent built this diagnostic in the existing immutable native image
`sha256:5adec98a0bb4f4cffbcc3fa15f5014db08621f1204b65cf1f130ff46d9cd32b0`
with two CPUs, 4 GiB and network disabled. The build was serialized after the
prior joint run and CAD check had ended. It is a linked build, not a native
joint result or trajectory-equivalence test.

The [build script](build.py) verified all 1176 upstream source-file hashes
against the preserved baseline manifest before replacing only `results.c`
and `printoutcontact.f`. The [make log](make.log) shows those two objects
recompiled and the library/executable relinked. The original and instrumented
binaries are retained here for a later matched-input comparison; neither is
the packaged `/usr/bin/ccx` used for the timestep-refinement branch.

- Instrumented binary SHA-256: `d4977dc31b3b8fa00c0162c9990c3abcd167b023d8089be92834fb02659683b6`.
- Unmodified upstream binary SHA-256: `cfa7fd110a41c209746137da8b5af0a1c06dee47d58682e797d31b8952b72e4b`.
- Packaged comparison-run binary SHA-256: `6adaabf5bf0382fc2bfd692b984320ed375dba777f7dc8297562f818043faa1b`.
- Build script SHA-256: `9538c878aa3689ea9d9f60b59608945d27f0cce43f6bce559573ad3ffef0c8c7`.
- Build-result SHA-256: `85b96476f832e6fcbb9a154fe1ed97ecd0a3e1d16411ce125e121c3e1579d2c5`.

The two source changes are the separately fixture-tested contact master
wrench/conditional storage printer and the syntax-checked accepted-state
MPC/acceleration hook. The optional contact-index counter is not included.
The MPC hook is enabled only by its explicit environment switch and requires
the exact 21-node RF output extension. Its frozen-input preflight still
applies. Full native output coverage, dynamic residual reconstruction and
comparison with the unmodified upstream executable remain to be performed.
No model, material, contact, strength, or candidate acceptance follows from
this successful build.
