# BG003 anisotropic-clearance finite-proxy adapter, attempt 01

This packet prepares, but does not run, exactly eight A12-rear BG003 bolt 1
finite proxies. It connects the already checked circular-gap/anisotropic point
law to the existing radial beam solver while keeping the solver's beam mesh,
source load mapping, continuation budgets, free ends, gauge, closure checks,
and 16/32 signed refinement gate. No native solve or finite joint case was run
to prepare this adapter.

## Frozen scenario

The sole source is A12-rear, knee_outer_left_side_1, at load factor 1.0. The
three source member wrenches are applied once to the rigid receiver DOFs using
the radial packet's frozen load_vector; they are not also applied to the
bolt beam. Receiver order is spine / side / inner block, with lengths
38.1 / 88.9 / 88.9 mm. The circular steel scenario retains
E = 190,000 MPa, d = 6.35 mm, I = 79.8113762731 mm^4,
EI = 15,164,161.4919 N·mm², free physical ends, and only the existing common
translation/slope gauge.

The eight requested combinations are the Cartesian product of two explicitly
non-adopted densities (350 and 550 kg/m³), two modeled radial gaps (0 and
0.575 mm), and 16 or 32 beam divisions per receiver. For each receiver the
existing equations give kf_parallel = 0.1374 rho - 12.9 and
kf_perpendicular = 0.0922 rho - 18.20 in N/mm³. The line stiffness is
K_line = d kf, rotated into the pinned grain frame, in N/mm². The law uses
K_point = quadrature_weight K_line in N/mm.

At a quadrature point, the batched evaluator returns point energy, force, and
tangent already weighted by that point's quadrature weight. It adds those
values directly to the residual/Hessian exactly once. Its solver postprocessing
returns force per unit length only because the unchanged radial postprocessor
multiplies by the weight once when forming integrated receiver resultants and
beam actions. The batch oracle explicitly checks homogeneity: multiplying K by
a weight scales energy, force, tangent, and lambda by that weight while leaving
the minimizer unchanged. This guards against a duplicated integration weight.
The pinned point law is U(delta) = min over |v| <= g of
0.5 (delta-v)^T K (delta-v). Inside the gap p=0; outside,
v=(K+lambda I)^-1 K delta with |v|=g and p=lambda v. The batch kernel
implements the same energy, force, and analytic symmetric tangent as the
scalar oracle in the preceding point-law fixture.

## Adapter verification

run_adapter.py imports the unchanged radial mesh, load-vector, and
continuation code after checking their hashes. Its new batch point kernel caches
the receiver eigenframes and solves each outside-gap scalar lambda equation by
vectorized bracketing/bisection; no matrix inversion or per-point scalar
eigensolve is used in Newton iterations.

The checked batch is compared with the frozen scalar oracle for isotropic
radial equivalence, mixed anisotropic force, open interior, rotated zero-gap
linear response, exact engagement, near engagement, and rigid transverse
rotation. The recorded maximum absolute difference is below 4e-14 across
energy, force, displacement, and tangent. Branch labels match exactly. The
weight-homogeneity check also passes.

Before finite responses are usable, the runner separately assembles a linear
anisotropic operator for each density/mesh at zero gap and compares its signed
actions and closure with the zero-gap continuation result. The eight rows retain
signed middle-cut Y/Z force and My/Mz couple; sampled peak nodal couple and its
coordinate/associated shear; signed receiver force and converted global My/Mz
first-moment closure;
and the existing gauge, free-end, and convergence checks. Each receiver also
gets the largest sampled line_force / d resultant in MPa, its axis location,
signed Y/Z line-force vector in the point-law p convention, grain direction,
force direction, and signed
force-to-parallel-grain angle. Pressure and action maxima are sampled values,
not continuous peaks or physical bounds. Grain force angle is calculated from
the returned constitutive force vector, not from displacement.

The producer pins the input register and its load report, geometry/method
records, radial and rotated diagnostic code/reports, scalar point-law code and
report, and the Python/NumPy runtime. SHA256SUMS pins this packet's producer,
README, and batch-oracle report.

## Replay and parent execution

From the repository root, replay only the small batch verification:

    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
      docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg003-anisotropic-clearance-finite-adapter-attempt01/run_adapter.py \
      --verify-batch

To recreate the checked batch report, use --write-batch and then --verify-batch.
Neither command assembles a finite beam response.

The parent-owned serial finite run is explicit opt-in and has not been run:

    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python \
      docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-bg003-anisotropic-clearance-finite-adapter-attempt01/run_adapter.py \
      --run-finite

Proposed parent limits are 120 CPU seconds per scenario, 900 CPU seconds for
the suite, 20 minutes wall time, and 2 GiB peak memory, with one BLAS thread.
The runner preserves the frozen Newton/continuation stop rules. Parent should
stop on any execution cap, tangent/continuation failure, closure failure, or
refinement failure; do not alter masks or stiffness inputs to force a pass.
A deterministic replay command is --verify-finite, after a parent run has
written finite-proxy-results.json.

## Scope boundary

The rotated anisotropic circular-clearance law is a constitutive hypothesis.
The cited directional regressions and the density values do not calibrate this
BG003 joint or establish a stiffness bound. Grain orientation and member order
remain proposed input fields, not stock inspections. Zero gap is a linear
reference for this same formulation, not evidence of actual fit or contact.

Even if all eight numerical rows converge and refine, they describe only the
isolated A12 bolt 1, three rigid receivers, and declared stiffness scenarios.
They do not establish actual pressure maxima, delivered material properties,
bearing resistance, axial-tie/washer capacity, preload, steel capacity,
friction, splitting, group action, shared timber compatibility, or full-joint
acceptance. No axial, strength, or interaction check is added here.
