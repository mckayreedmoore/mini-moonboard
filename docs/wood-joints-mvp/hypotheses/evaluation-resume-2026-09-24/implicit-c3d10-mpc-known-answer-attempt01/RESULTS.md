# Implicit C3D10 free-coordinate translation result

Status: **PASS for this frozen known-answer fixture.** Both direct and mapped
cases completed all 100 increments on the unmodified pinned CalculiX 2.23
binary. This result qualifies the tested uniform-translation mass row sums
and load mapping, not a current joint or a structural criterion.

The physical displacement and velocity values printed in DAT are identical
between cases at every accepted state. All ten physical nodes and the mapped
free controller follow the frozen Newmark reference. At 0.1 s, the reference
displacement is 0.000166675 mm, velocity is 0.005 mm/s, and kinetic energy is
0.0000125 N·mm. Across both cases, maximum displacement error is 5.0e-11 mm
in DAT and 5.0e-10 mm in FRD, within the frozen output-precision thresholds.
The maximum reported elastic energy is 3.616e-32 N·mm. All 100 kinetic-energy,
mass, volume, and accepted-state coverage checks pass. The printed mapped
equation residual is zero at all 100 states.

The [verifier result](verifier.json) records every gate. The
[frozen acceptance contract](acceptance.json) supplies the selected numerical
thresholds; the older tolerance-status field in `expected.json` records its
earlier preparation state. The
[parent integrity audit](parent-postrun-integrity.json) confirms all eleven
frozen local files and four external dependencies are unchanged, and all
eighteen captured case-file hashes match. Both runs exited normally without
OOM or overlap, using one CPU and a 1 GiB memory cap each. They took about
0.94 and 1.04 seconds including capture overhead.

The freeze SHA-256 is
`b9e74647a23fbf5e458c0d2873eb491a0428c5bbae341ce72ff25f399db8036c`;
the execution record SHA-256 is
`918d43a5a6da7591f2b724004596ed7393eec11846725cd4d90359b8b8afbcec`.
The [independent preflight](independent-preflight.md) preceded this freeze.
The completed [independent postrun review](independent-postrun.md) confirms
the file inventories, serialized execution and raw state-by-state results.

CalculiX's four-point C3D10 mass integration is underintegrated for arbitrary
quadratic mass modes. Its row sums and the uniform mode exercised here have
the known answer documented in [the design](design.md). The native startup
uses its built-in mass-plus-stiffness operator with zero initial load. This
result does not establish arbitrary mass modes, offset or rotational
physical-pivot mappings, zero-density nut-carrier behavior, contact, a physical
demand history, or joint resistance. The earlier explicit mapped failure and
the separate implicit contact failure remain unchanged.
