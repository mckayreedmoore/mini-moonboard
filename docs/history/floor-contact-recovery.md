# Contact recovery threshold experiment

This isolated experiment retains the frozen quadratic timber mesh, unpinned
frame, fixed ground, gravity then 1.2 kN downward load, and μ=0.3 with normal /
tangent penalty slopes 10,000 / 100 N/mm³ from the original floor-contact study.
Only the face-to-face recovery threshold changes from 60 to 12 iterations;
additional contact output records active integration-point values and per-pair
forces, moments and areas. Historical artifacts are never overwritten.

The [official CalculiX 2.21 manual](https://www.dhondt.de/ccx_2.21.htm.tar.bz2),
sections 6.10.2, `*CONTROLS` and `*CONTACT PRINT`, documents the four controls:
`delcon=0.001`, `alea=0.1`, `kscalemax=100`, `itf2f=60`. The first three defaults
are retained. The recovery strategy temporarily lowers normal and tangential
slopes together and requires restoring their nominal values before accepting
convergence. Its default random contact-removal mechanism is retained, not
introduced by this experiment. The original runtime stops at 16–24 iterations
did not reach the normal 60-iteration recovery threshold.

A separate read-only topology audit finds one connected component and no
duplicate coordinates rounded to eight decimal places. Every selected six-node
floor face occurs once on the mesh exterior and has outward normal exactly -Z.
Corner-triangle areas are 7,340.576249 mm² on each leg and 147,543.551816 mm²
on the kicker patch. These checks remove obvious disconnected-body, duplicate-node
and wrong-floor-face explanations; they do not prove free contact equilibrium.

The runner creates a unique ignored `fea/generated/recovery-it12-*` directory,
records input/code/deck hashes before launch, bounds the solve, and retains log,
convergence history and outputs. Integrated mesh mass and centroid are checked
against the prepared CAD context. A complete solve is passed through the existing
deformed global force/moment and aggregate friction auditor. Convergence alone
does not establish acceptable local contact, friction or structural performance.

```sh
docker run --rm --user "$(id -u):$(id -g)" -e OMP_NUM_THREADS=2 \
  -v "$PWD:/work" mini-moonboard-fea:box-v1 \
  python3 -m fea.floor_contact_recovery --max-seconds 600
uv run pytest -q tests/test_floor_contact_recovery.py
```

The bounded run stopped at 600.13 seconds with **zero accepted increments**.
The changed threshold triggered four documented reductions of the penalty slopes
and advanced through five attempts of the first gravity increment. The fifth
attempt last recorded iteration 10. Nominal-stiffness restoration messages:
**zero**. The DAT file is empty, so no integration-point, equilibrium or physical
result is available. Earlier recovery alone did not resolve startup within this
experiment; it is not evidence that the free board is physically unstable.

The [compact report](../fea/results/floor_contact_recovery/report.json),
[solver log](../fea/results/floor_contact_recovery/recovery.log),
[step history](../fea/results/floor_contact_recovery/recovery.sta), and
[iteration history](../fea/results/floor_contact_recovery/recovery.cvg) retain
the stopped partial state. The
[compressed input/context archive](../fea/results/floor_contact_recovery/inputs_and_context.tar.gz)
contains the exact launched deck, full record including nodal gravity weights,
partial DAT/FRD and exact launch generator. Its SHA-256 is
`fee0d25cd146ee801d23869c71dc9ae2e89b698e2af66b90d14b9084fda52752`.
The [launch generator](../fea/results/floor_contact_recovery/floor_contact_recovery.launch.py)
matches its prelaunch hash; subsequent harness changes add earlier finite-context
and independent source-summary provenance checks, which were replayed successfully
against these launch inputs. Six focused regressions and Ruff pass.
