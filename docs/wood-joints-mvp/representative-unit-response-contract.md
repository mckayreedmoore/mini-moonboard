# Representative ordinary-joint unit-response contract

Status: implementation contract for a bounded, diagnostic WJ16 right-inner
full-stock G7 patch, 2026-09-24. It defines restraint, signed unit-wrench, and
reaction-accounting behavior. It is not a solved model, accepted response,
capacity method, complete-candidate load case, or release.

## Bound model and limits

Bind the exact five finished timber bodies, eight physical bolt stacks, four
wood interfaces, surface inventory, and source hashes in the
[full-stock mechanics input report](hypotheses/wj16-full-stock-mechanics-inputs/README.md).
Keep the five timber meshes independent at every interface. Include the
named steel bodies and contacts only under the separately pinned
hardware/engagement idealization. The current WJ16 composition is a partial
historical development layout; this contract cannot establish a response for
the later WJ24 composition or transfer a result to it. The 66 panel screws,
twelve retained frame bolts, other candidate duties, and full-frame boundary
conditions are outside this patch. Apply the mesh refinement and contact
penalty sensitivities required by the
[ordinary-joint response method](ordinary-joint-response-method.md) before
interpreting response stability.

Use global coordinates in mm, force in N, and moment in N·mm. Use the common,
right-handed WJ04 basis from the pinned source frame:

| Axis | Global unit vector |
| --- | --- |
| X | (1, 0, 0) |
| T | (0, 0.6427876096865394, 0.766044443118978) |
| N | (0, -0.766044443118978, 0.6427876096865394) |

Verify `X × T = N` in the loaded contract before creating cases. For each
interface, use its exact `shear_plane_datum.origin_global_xyz_mm` as the wrench
origin. Define the **host** as `source_host_face.part_id` and the **cleat** as
the other member in `members_head_to_nut`. A positive input wrench acts on the
host; the cleat receives its equal and opposite wrench at the same datum. This
paired loading gives zero net external force and moment for the whole patch. It
is a diagnostic action, not a prediction of service demand. Confirm signs from the
generated nodal loads in a pre-solve load-generation audit; do not infer them
from solver output labels.

## Six signed component diagnostics

For each of the four `physical_interfaces`, run the following twelve
independent cases. Do not combine columns or use linear superposition to
replace these runs: unilateral contact, clearances, and zero preload can make
the two polarities differ. Start each sign from the same unloaded,
zero-preload geometry and contact state; do not carry the active set or
displacement history from another sign.

| Case component | Host wrench at its interface datum |
| --- | --- |
| `FX+`, `FX-` | `(±1, 0, 0) N`; moment `(0, 0, 0) N·mm` |
| `FT+`, `FT-` | `(0, ±1, 0) N`; moment `(0, 0, 0) N·mm` |
| `FN+`, `FN-` | `(0, 0, ±1) N`; moment `(0, 0, 0) N·mm` |
| `MX+`, `MX-` | force `(0, 0, 0) N`; moment `(±1, 0, 0) N·mm` |
| `MT+`, `MT-` | force `(0, 0, 0) N`; moment `(0, ±1, 0) N·mm` |
| `MN+`, `MN-` | force `(0, 0, 0) N`; moment `(0, 0, ±1) N·mm` |

Thus the basis is `FX, FT, FN, MX, MT, MN`; `+` and `-` reverse the whole
host/cleat pair. Use the actual finite common face footprint for each side,
not the larger host face and not the cleat's reported planar area by itself.
The footprint, opposed normals, and surface-node ownership must be verified
from the finished solids before loading. Apply each requested wrench as a
deterministic area-weighted, minimum-norm nodal force distribution on that
side's finite patch. For nodal tributary areas `A_i`, minimize
`Σ(||f_i||²/A_i)` subject to `Σ f_i = F` and
`Σ[(r_i-r_0) × f_i] = M`. Realize pure moments with force couples because
solid nodes have no rotational degrees of freedom. Require a rank-six force
map on each loading patch and record the nodal forces, their reconstructed
six-vector, and the residual before launching a solver case. Loads and gauge
nodes must be disjoint.

The default mathematical amplitudes are 1 N and 1 N·mm as shown. If these are
below the selected solver's resolved tolerance, freeze a common positive scale
factor for the applicable force or moment family before any response run and
record it in every case. Do not tune amplitudes after viewing a response.
Where a unit case does not close a modeled clearance or engage a contact, its
reported direction is a free-travel diagnostic; it is not a stiffness value
through the gap. Separate monotone engagement steps need a predeclared scale
ladder and cap. Their values remain open until actual interface actions and a
numerical-resolution study are available.

Record for every case the input wrench, reconstructed applied nodal wrench,
relative face motion, all four wood-face contact states, every bolt/bore and
hardware-seat contact state, and contact/mesh/penalty settings. Extract the
relative interface translation and rotation at the datum by an area-weighted
least-squares rigid-plane fit to the two finite face-node patches. Fit
`u_i ≈ u(r_0) + θ × (r_i-r_0)` separately on each side and report
`(u_host-u_cleat, θ_host-θ_cleat)` plus each fit residual as a measure of
non-rigid face distortion. Also retain the full nodal displacement field.
These six signed columns are local response
diagnostics only; they do not provide a linear joint law outside the stated
contact state, material scenario, geometry, hardware idealization, and load
range.

## Minimal restraint and free-mode treatment

There are no physical supports in this self-equilibrated patch test. Apply only
a six-scalar **3-2-1 gauge** to select a global reference frame and remove
whole-assembly rigid translation/rotation. Use the far `T` end of
`base_principal_center_right`, whose pinned projected extent ends at
`T = 2415.403793361191 mm`, remote from the four G7 interfaces. If the mesh
contains the corresponding geometric corner nodes, define:

| Gauge node | Local source-frame coordinate | Global displacement components fixed |
| --- | --- | --- |
| A | `(X_min, T_max, N_min)` | `Ux, Uy, Uz` |
| B | `(X_max, T_max, N_min)` | `Uy, Uz` |
| C | `(X_min, T_max, N_max)` | `Uy` |

For this source frame, `AB` is parallel to global X and the N direction has a
nonzero global Z component, so these six constraints remove the six global
rigid modes. The preparation step must resolve each gauge node to the exact
mesh node, check these geometric relationships, and verify the constrained
rigid-body kinematic matrix has rank six. If those checks fail, define and
document another rank-six gauge before solving; do not silently clamp a full
end face. Repeat selected cases with a second remote gauge triad or shifted
remote location. A material response that changes materially with the gauge
location is not accepted as a local-joint response.

The gauge is not a support or load path. It must be placed outside all load and
contact patches, and its reaction wrench should be zero to the frozen
accounting tolerance because each unit case is externally self-equilibrated.
Do not add springs, weak stabilization, ties, bonded interfaces, friction,
pretension, prescribed interface motion, or additional supports to suppress a
singularity. The [CalculiX 2.21 User's Manual](https://www.dhondt.de/ccx_2.21.pdf)
describes its single-point boundary conditions and `RF` output. The
[2.22 manual](https://www.dhondt.de/ccx_2.22.pdf) lists the contact result
variables used below. Verify exact behavior against the pinned 2.21 executable
before an eventual run.

Start with a no-load, zero-preload equilibrium state. There is no bolt
pretension or initial stress; timber faces use the declared nominal zero-gap
scenario, and bolt/bore clearances remain named input scenarios. Head/washer,
nut/washer, and wood contacts are compression-only, frictionless, and allowed
to open. A zero-load static convergence with zero displacements does not prove
that the connection has a unique tangent response. Separately identify the six
whole-model rigid modes and any additional internal free modes for the
zero-preload state and each one-sided contact state used by the signed cases.
Use a solver-validated tangent-rank/eigenmode method; its implementation and
threshold are an explicit open choice. If the method is unavailable, a
singular signed case, unconstrained body, or non-unique displacement is
reported as `FREE_MODE_PRESENT`, not repaired with artificial stiffness.

The first native attempt should be a **zero-load, gauge-only free-mode
preflight**, before any of the 48 force-controlled cases. If it shows internal
mechanisms, preserve that state and stop the force-controlled sweep. Do not
use a solver stabilization to make it run. If a later bounded
displacement-controlled trial is justified to seat a named clearance, give it
a separate case/state ID, prescribe only the declared relative motion, and
record the imposed displacement, support/contact reactions, and external
work. Its result describes that imposed seated state; it is not the
zero-preload initial stiffness, a physical preload, or a service action. The
seat direction and amplitude remain unresolved until the actual contact pair
and modeled gap are frozen.

In particular, the model must name how the nut/thread engagement transmits
bolt tension. Smooth cylinders with frictionless contact do not by themselves
provide axial thread engagement. If no supported engagement idealization is
bound, axial response is `UNRESOLVED_ENGAGEMENT`; it cannot be reported as
zero bolt force, a passing restraint, or accepted stiffness. A zero-preload
case also credits no washer friction or clamp-generated shear transfer.

## Reaction and wrench accounting

Retain both contact sides, not only a solver-reported scalar force. For every
contact surface, save force vectors at their contact integration/node
locations, then shift each to the relevant interface datum:

`F(r0) = Σ f_i`

`M(r0) = Σ[(r_i - r0) × f_i]`.

Keep separate resultants for direct wood-face compression, each bolt's
wood-bore contacts, head/nut washer seats, and any named bolt/nut engagement
idealization. Sum them only when reporting the complete interface transfer;
never count one physical bolt more than once. Contact force vectors on the two
sides of each contact pair must be equal and opposite within the frozen
integration tolerance. Report pressure distribution and opening separately
from integrated wrench. The
[CalculiX 2.22 User's Manual](https://www.dhondt.de/ccx_2.22.pdf) identifies
`CF`, `CFN`, and `CFS` as total slave-surface contact forces, and `CDIS`/`CSTR`
as contact displacement/stress outputs. Surface totals can check force sums;
they do not alone provide the lever arms needed for moments, so the
postprocessor must retain/reconstruct the force locations and audit the
recovered force against the surface total.

For each timber body and each complete physical interface, emit the signed
six-component action at the applicable datum with named ownership. For a
body free-body check, include its applied nodal load, gauge reactions if any,
and all contact forces on that body; its force and moment residuals must close.
For the full patch, contacts are internal and must cancel pairwise; close the
applied loads plus gauge reactions to zero force and moment about one declared
global origin. Shift every force before summing moments. Preserve host-on-joint
and joint-on-host as exact opposites in the output, not as two positive
magnitudes.

If `RF` is used for the gauge reactions, place no applied nodal loads on the
gauge nodes and use global-coordinate single-point constraints. CalculiX
documents `RF` as external force that combines applied and reaction forces in
a node and notes that forces induced by multiple-point constraints are not
reported. Therefore, do not sum `RF` on loaded nodes or use it as an
unqualified reaction total. Compute the gauge resultant and moment from its
unloaded constrained-node reactions and coordinates, then independently
reconcile with the full-model force/contact accounting. Freeze absolute and
normalized component tolerances before solving; include raw residuals and
their tolerance source in the artifact. No equilibrium tolerance or response
pass is selected by this contract.

## Required run record and unresolved choices

Each case artifact must bind the case ID/sign, exact input and reconstructed
wrench, interface datum/basis, mesh and source hashes, material schema and
`scenario_sha256` with each member's grain/R/T orientation branch, hardware
scenario IDs, all contact-pair names, zero-preload declaration, initial gap
and clearance values, solver/container/executable identity, gauge node IDs,
load nodes/forces, convergence history, active contacts, six-component
interface resultants, support reactions, per-body and global residuals, and
limitations. Preserve failed, singular, open-contact, and non-convergent
attempts.

Before a bounded run can be called implementation-ready, freeze these items:

1. The final finite loading/contact footprint and exact node/area weights for
   each side of all four wood interfaces.
2. A solver-validated zero-preload tangent free-mode method and cutoff for
   internal modes, including the contact active-set treatment.
3. The steel bolt/nut engagement idealization and its applicability to axial
   restraint, or an explicit unresolved status for axial cases.
4. Resolved unit amplitudes, any engagement-step ladder/cap, and numerical
   residual/penetration tolerances.
5. The contact force location export or reconstruction used for moments, and
   an independent wrench-equilibrium audit.

These are model/method choices, not capacity inputs. Passing them only permits
execution of the bounded unit diagnostics. It does not close the ordinary
joint resistance methods, the complete candidate's fresh six-case analysis,
the outstanding WJ24 layout gates, or any physical-build/release gate.
