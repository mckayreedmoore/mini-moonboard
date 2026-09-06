# Three-stitch, two-ply leg comparison

**Preparation in progress; no contact solve or capacity result.** The purpose is
to measure how the three proposed internal bolts transfer shear between the
actual right-leg plies. The existing independent-ply calculation has no such
connectors; the earlier pin coupon fixes its pins to the world. Neither answers
this question. The [baseline observer audit](mortar-frame-observer.md) also
remains unqualified and is not a source of approved design loads.

## Actual geometry and explicit idealizations

The source is `screw-spacing-development`, not a new viewer design. Two separate
19.05 mm plywood solids retain the actual knee, flat feet, four upper bores and
three stitch bores. No plywood faces are fused, glued or tied.

Each nominal stitch has a 9.525 mm shank in a 10 mm wood bore: 0.2375 mm radial
clearance. The bolt core includes its head as one solid. Its two washers and nut
are separate annular solids, unlike the overlapping solid display cylinders.
Together with the two plies this gives fourteen separate solids. The nominal
57.15 mm bolt length, 38.1 mm grip, two 2 mm washers and 9 mm nut leave 6.05 mm
projection. These are current CAD assumptions, not selected-product tolerances.

`fea/stitch_joint_geometry.py` checks complete bores, separate floor faces,
nominal stack contact and absence of positive-volume intersections above the
0.001 mm³ CAD tolerance. Its optional export creates a unique directory with
STEP files, source snapshots and hashes. Geometry checks do not establish
contact mechanics. In particular, a smooth cylindrical nut bore supplies no
threaded axial retention by itself.

The first separate-body mesh completed in 7.40 seconds with exit zero in the
immutable Gmsh image `sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646`.
It contains 145787 nodes and 70148 C3D10 elements, with no shared node IDs
between bodies. The maximum relative body-volume error against CAD is
1.748945e−6; the minimum sampled Jacobian is positive (0.170668). Complete
quadratic exterior faces are associated with the individual CAD surfaces.
These are mesh gates, not contact convergence, material quality or strength gates.
The [frozen mesh evidence](../fea/results/stitch_joint_mesh/README.md) includes
STEP files, source snapshots, the raw mesh, runtime records and portable topology
checks. Its replay does not recalculate CAD geometry or mesh Jacobians.

The intended mechanical idealization is a nut-to-shank tie **only** to represent
locked thread retention, without preload. No wood-to-bolt, washer-to-shank or
ply-to-ply tie is permitted. Washer and wood interfaces remain frictionless,
unilateral contact. Thread stresses, tightening, loosening, real washer bore
clearance, bolt grip/thread transition and product resistance remain outside
this first comparison. The smooth hardware is nominal, not manufacturer CAD.

## Matched fixture experiment

Both models retain the same drilled plies and fix their complete four upper
bore surfaces. Only the three stitch assemblies are present or absent. A
distributed displacement of the inner ply's floor face drives in-plane shear;
the outer floor is unloaded. The exact direction, ramp, duration, mesh and
numerical gates must be frozen in the launch record before solving. The fixed
upper bores and driven floor are a synthetic test fixture, **not** anchoring
allowed in the real freestanding board or a model of its actual floor support.

With freely moving hardware, 0.2375 mm inner-ply motion does not necessarily
engage both sides of a bolt. Clearance can be taken up on each ply before a
complete shear path forms; the two radial clearances total 0.475 mm nominally.
Actual local engagement must be measured, not inferred from floor displacement
or forced equal across the three stations.

An unloaded, loose bolt can have unconstrained rigid motion in a static start.
Fixing it to make that calculation solvable would create an external load path.
The proposed route is implicit transient contact with explicit material mass,
zero initial velocity, no gravity in this synthetic experiment, and no artificial
grounding or weak springs. It is initially a **transient experiment**, not a
quasi-static result. Slower-ramp and timestep comparisons must establish whether
inertia is small enough for a quasi-static interpretation.

The [CalculiX 2.21 manual](https://www.dhondt.de/ccx_2.21.pdf) documents implicit
`*DYNAMIC`, density, amplitudes and energy/contact output. The proposed
`*DYNAMIC,ALPHA=0` procedure omits `EXPLICIT` entirely, uses automatic increments and no alpha-method
numerical damping. An explicit displacement amplitude avoids a suddenly applied
full dynamic displacement. The manual warns that reported `RF` excludes dynamic
forces; summing it as if it were a static reaction balance would be incorrect.
The first native control exposed a manual/parser discrepancy: although the
bundled manual describes numeric `EXPLICIT` values, the verified 2.21 parser
enables explicit structural integration whenever that parameter is present,
including `EXPLICIT=0`. Its actual run log confirmed explicit integration. That
attempt is retained as failed qualification; it is not an implicit control.

Generic elastic wood and steel properties may define a conditional mechanics
comparison, but cannot establish plywood, bolt or connection resistance. Any
densities used must be explicitly identified as assumptions. In N–mm–s units,
density is tonne/mm³: multiply kg/m³ by 10⁻¹².

## Required evidence before interpreting the result

- Mesh each body independently; preserve disjoint node/element ownership and
  complete quadratic contact surfaces. Coincident coordinates do not authorize
  merging nodes across bodies.
- Record every accepted time, displacement, velocity, contact force/moment,
  opening/penetration and strain/kinetic/contact energy. Retain failed attempts.
- Compute hardware linear and angular momentum with consistent volume
  quadrature, including deformed position in angular momentum. Equal nodal mass
  or a lumped shortcut is not an independent audit of curved quadratic elements.
  Keep the solver's own integration rule separate from higher-order physical
  integration: source inspection shows CalculiX 2.21 implicit C3D10 mass uses
  four points. The Gauss8 reference operator is not solver-identical. Native
  kinetic-energy controls with quadratic velocity fields have now passed for
  four untransformed straight/curved cases; [scope and remaining checks](dynamic-momentum-qualification.md)
  are explicit. This does not establish contact impulse/momentum balance.
- Compare contact impulse with momentum change for each complete hardware
  assembly; internal thread-tie forces then cancel. Audit freely contacting
  washers separately or inside that complete assembly, without omitting forces.
- Report each station's transfer to each ply, bolt motion/bending and recipient
  ply response. Do not divide the total by three or count artificial fixture
  reactions as stitch transfer.
- Check mesh, timestep, ramp-rate and contact-enforcement sensitivity; initial
  contact energy/preload; and full energy accounting. Stop on unsupported modes,
  missing outputs, material interpenetration, or failed balance/sensitivity gates.

Even a successful comparison would establish transfer only under its stated
fixture and assumed elastic properties. It would not establish whole-frame
sharing, lateral composite action, three-bolt adequacy, fastener resistance or
permission to build/climb. The complete upper joint also needs a finite bearing
and retention representation: its four collinear point-force locations cannot
transfer the recovered moment about the line of those bolts.
