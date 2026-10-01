# Stock Code_Aster trial results

The bounded primitive trial passes. The pinned community Code_Aster 17.4.0
image reproduces the tested elastic, constraint, planar-contact and discrete
impact answers without local solver modifications. It is worth continuing
with candidate-specific translation checks. This is method evidence for small
fixtures, not a migrated or accepted wood joint.

Runtime identity is recorded in [runtime.json](runtime.json), including the
immutable image digest. [runtime-confirmation.stdout](runtime-confirmation.stdout)
records the runtime version and library hashes. The distribution is the Simvia
container linked from the official download portal. Its package reports
`spack-local` rather than an upstream commit hash; the image digest fixes the
tested executable environment. We did not audit the publisher's build patches.

[validation.json](validation.json) records the final input-integrity checks,
analysis snapshots and raw-output hashes, including failed attempts. These
preserve provenance; the individual analytical audits establish the bounded
mechanical results below.

| Check | Evidence and result | Applicability |
| --- | --- | --- |
| Bundled `forma01a` | [Audit](upstream-forma01a-attempt01/audit.json): published regression and analytical checks pass | Installation smoke test, using that example's own analytical tolerances |
| Orthotropic elasticity | [Audit](orthotropic-attempt01/embedded-check-audit.json): all four analytical checks pass at 1e-9 absolute tolerance | One HEXA8, zero Poisson ratios, one rotated material direction; not the full timber constitutive tensor |
| Linear constraint force transfer | [Audit](liaison-attempt01/embedded-check-audit.json): all six checks pass at 1e-9 absolute tolerance | Two bars and a scalar linear relation; not the distributed A09 port or nut map |
| Contact opening, compression and reopening | [Audit](contact-attempt03/contact-audit.json): all 14 states match the 600 N/mm plane-strain oracle; peak force 240 N | Two linear 2D elements with planar continuous contact; no curved bore, shared-edge or dynamic surface-contact qualification |
| Constrained inertia | [Audit](constraints-attempt01/checker-report.json): both 101-state histories pass displacement, velocity, acceleration and kinetic-energy checks | Primitive TETRA4 and zero-density rigid-motion carrier; not A09 quadratic elements or actual fit coefficients |
| Free impact | [Audit](impact-bounds-audit.json): 97 coarse and 193 fine states pass frozen bounds; halving the timestep reduces motion/gap errors by about fourfold | Stock discrete impact law and implicit integration; does not qualify dynamic surface contact |

The constraint histories' largest nonzero relative state error is 2.46e-10;
their largest relative kinetic-energy error is 3.46e-14. Kinetic energy is
computed from extracted velocities and the independent consistent mass
matrix, not inferred from successful time stepping.

For impact, maximum gap error decreases from 0.0006416 mm to 0.0001606 mm.
Maximum relative mechanical-energy drift decreases from 0.0161% to 0.00204%;
momentum drift stays below 2.4e-13 tonne·mm/s. Both runs satisfy the
[limits frozen before the first mechanics run](impact-readiness.json).
The reconstructed penalty force comes from the known law and measured gap;
it is not an independent check of native contact-force output. The observed
roughly fourfold motion-error reduction agrees with the smooth-contact
Newmark phase-error estimate, while event handling remains part of the
tested numerical response.

## Changes required to obtain valid inputs

The first contact attempt rejected numeric mesh identifiers. Correcting the
mesh format fixed that input error. Attempt02 then stalled on its first open
state: the absolute force residual was approximately 1e-15 N, while the
relative residual compared effectively zero force quantities. No nonzero
contact resistance was expected in that state.

Attempt03 uses only `RESI_GLOB_MAXI=1e-9 N`. The pinned
[v17 convergence documentation](https://code-aster.org/doc/v17/manuals/man_u/u4/u4.51.03/Reglages_Convergence.html)
explains the difficulty of a zero-load first increment and permits an absolute
criterion. Independent force and gap tolerances were retained. This is a
documented input setting; no equilibrium equation or solver code was changed.

The orthotropic fixture also resolved one concrete axis convention by native
observation: `ANGL_REP=(90,0,0)` gives the expected longitudinal response under
global-Y extension in this test. The v17 `MASSIF` documentation has inconsistent
axis-order descriptions, recorded in the [fixture notes](../../../../fea/code_aster_trial/elastic/README.md).
This single case does not establish all orientations or Poisson/shear mappings.

The constraint run's `DISCRETS_26` alarm states that the control point has no
assigned discrete mass and therefore defaults to zero. That is the intended
control-point assumption; the separate physical tetra carries inertia. The
warning is retained rather than hidden. Execution success alone does not
validate the physical mass reduction or state histories.

The impact setup's first attempt rejected a misplaced mesh-style `TITRE`
block in its export file, before native mechanics began. Removing that input
syntax error allowed the prepared model to run. Both successful impact runs
retain `MODELISA8_14` warnings that the point-mass elements share their nodes
with the contact segment. That overlap is deliberate: mass lives on the two
points, while the segment carries the contact law and has zero mass.

One contact-output convention still needs care. In the planar compression
fixture the extracted `RNX` sum is -240 N, whereas the physical force on the
right/slave body acts in +X. The audit checks contact-force magnitude and the
independent signed end force (-240 N). It does not approve using raw `RNX`
as a signed slave-body wrench in the candidate model.

## Current-mesh contact screen

[a09-topology.json](a09-topology.json) reconstructs all 70 contact surface node
sets from the frozen C3D10 element-face references. Every membership equals
the recorded producer set. The first two slave surfaces share seven nodes;
hypothetically reversing pair002 removes all slave-node intersections. No
candidate input was changed. This establishes a possible orientation route,
not its contact integration, normals, force equivalence or numerical accuracy.

## Boundary of this trial

The independent parent checks and frozen attempts preserve the reviewed
geometry and prior evidence. Actual A09 port/nut maps, quadratic curved and
shared-edge surface contact, dynamic surface impact, physical joint response
and candidate resistance remain separate applicability work. No full joint
or frame solve is justified merely by the primitive fixture results.

The smallest useful continuation is the actual first A09 bolt/nut map in a
small-motion inertia comparison, together with representative quadratic
surface-contact checks. The mass reference must follow Code_Aster 17.4's
element integration; CalculiX's quadratic mass rules cannot be assumed to
transfer. Preserve the current weighted equations, zero-density carrier
assumption and contact interfaces. No full-frame migration or solver-source
development is warranted by this trial.

Four Luna agents at maximum reasoning effort prepared and checked the fixture
inputs and analytical audits. The parent reviewed and corrected inputs before
running jobs serially, reproduced the independent audits, and owns this
interpretation. No selected-candidate or development geometry was changed.
