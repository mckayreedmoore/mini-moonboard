# Dependent-node mass rows

The parent executed the frozen postprocessor's mass-row extraction in the
pinned Gmsh image with one CPU and a 2 GiB limit. It completed successfully
in 1.619 seconds alongside the separately running native diagnostic. The
repository was mounted read-only; only this output directory was writable.
No native solver or CAD model was run by this extraction.

The [result](mass-rows.json), SHA-256
`f3c6d76da9391665015095269211dea709968580c169fb39f9f61709364530ad`,
contains 21 scalar rows and 355 nonzero coefficients from the 60 C3D10 bolt
elements incident on the dependent nodes. Their support spans 337 nodes.
It uses the native-reference four-point mass rule and steel density
7.85e-9 tonne/mm³, with no row lumping. The four bolt bodies contribute
18, 10, 12 and 20 support elements respectively.

The extraction verified the 34 child input artifacts and 25 paired-fixture
files before assembling rows. The frozen producer SHA-256 is
`626999de549f35a173ac1dcd478f0b4f02265f41d77e4d4d513a4e6c4965bf0f`.
The [execution record](execution.json) pins the command, driver and outputs.

These rows prepare the inertial term in the case-specific dependent-force
reconstruction. There is no measured hook CSV, acceleration history or
residual result in this folder. Native instrumentation checks, force
reconstruction and joint acceptance remain separate work.
