# Conditional washer-stack 3D contract

**Status:** source-bound preparation plan, 2026-10-01. No deck, input freeze,
native run, result, or acceptance is created here. All quantities below are
conditional scenarios; they do not identify delivered stock or hardware.

## First local scenario

Use the reviewed `compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`. Preserve the 92 candidate axes,
184 outer seats, twelve starting frame-bolt arrangements, and 66 panel-screw
axes. The first local stack is the partial nut-side seat
`center_principal_right_2` on `base_principal_center_right`. Its centered CAD
annulus support is 90.504635% (21.1486664 mm² projected area is lost into the
service passage). Its finished STEP
SHA-256 is
`9053a7210a781e919038a4a823f867325dd5c78907bd028d8b9e76dc0b46df58`.
In that receiver's source `X/T/N` frame, the seat is `(0, 37.57576013,
95.25) mm`; its bore is 7.3 mm. Retain the exact through-bore and the
38.1 mm-diameter, X-directed F1/G1 service passage
`bore_base_principal_center_right_072` (source SHA-256
`5c86941458a6a92432941fdf7e13b2b21ef2f933332e0e1ec602d4d57796f15f`). Do
not fill, bridge, smooth, or replace the passage with an area correction.

The first analysis domain is the exact finished BREP intersected with an
X-axis cylinder of radius 75 mm in the `T/N` plane about the target seat,
through the receiver's full 38.1 mm X thickness. It contains the target,
the full passage, and the adjacent nut seat
`center_principal_right_1` on the same receiver 53 mm away. Preserve every
natural edge, bore, passage and cut that intersects the crop. A radius-100 mm
crop is the declared domain-expansion branch. These are analysis domains, not
member geometry changes or conservative physical envelopes.

Use the existing source-bound signed actions; do not run another demand solve.
Both nuts load this receiver inward along source-local `+X` (global `+X` for
this receiver); their applied actions are
separate, centered axial resultants:

| Source case, full load | Target `center_principal_right_2` | Neighbor `center_principal_right_1` | Two-seat resultant |
|---|---:|---:|---:|
| A1 rear | 3.736414 N | 11.1575 N | 14.893914 N |
| A12 rear | 41.45025 N | 18.9599 N | 60.41015 N |
| K12 rear | 64.40226 N | 20.52895 N | 84.93121 N |

These are the three accepted rear-case joins at full load. Keep the two
washer/nut bearing lands, wood bores, and contact patches distinct even though
they share one receiver and support plane. If the load history is represented,
use the already-pinned factors `0.1, 0.2, 0.3, 0.45, 0.675, 0.925, 1.0`. The
first diagnostic comparison is K12; the two other rows remain the
source-supported case branches. The same receiver is not assigned the
cleat's grain direction.

## Conditional stack, materials, and load/support assumptions

Represent a 25NWUS-like washer as a finite solid annulus at the catalog
nominal ID 7.9248 mm, OD 18.653125 mm (the exact conversion of the listed
47/64 in), and thickness 1.5875 mm. This is a catalog-input geometry, not a
measured washer. The existing CAD envelope uses OD 18.6436 mm, ID 8.0 mm, and
thickness 1.651 mm; its OD is 0.009525 mm below the exact fractional
conversion, while both ODs lie within the Type A envelope. Keep the 184 seat
geometry unchanged and re-intersect the chosen washer body against the exact BREP. The
listed 25NWUS is plain/light-oil low-carbon steel, but its source supplies no
yield or hardness value. Use the generic elastic diagnostic `E=200000 MPa`,
`nu=0.30` only as an explicitly hypothetical solver input; keep the
documented `E=180000/200000/220000 MPa` and `nu=0.25/0.30/0.35` perturbations
as numerical sensitivity cases if needed. Also report the source-supported
Type A geometry corners `ID=0.327 in, OD=0.727 in, t=0.051 in` and
`ID=0.307 in, OD=0.749 in, t=0.080 in` if washer bending response is
compared. These are analyst-selected combinations of catalog limits, not
conservative stress bounds. No yield, plasticity, or 25NWUS resistance claim
is permitted from these inputs.

Use an idealized 1/4-20 finished-hex nut body only as a hypothetical load
spreader: 7/32 in (5.55625 mm) high, with a smooth 6.35 mm through-bore
standing in for unmodeled threads. The conditional hex body is 0.438 in
(11.1252 mm) across flats, the transcribed B18.2.2 maximum, while the product
listing's nominal silhouette is 7/16 in across flats. Keep that hex
silhouette (catalog maximum 0.505 in across corners) separate from its finite
bearing land. Test two explicit nut-side land shapes: **H1**, a flat annulus
with inner diameter 7.112 mm and outer diameter 11.1252 mm; **H2**, a flat
annulus with the same inner diameter and 10.0127 mm outer diameter,
transitioning by a hypothetical 45-degree conical chamfer to 11.1252 mm.
Place the timber/washer interface at `X=0`, the washer/nut land at
`X=-1.5875 mm`, and the outward nut face at `X=-7.14375 mm`. The B18.2.2
dimensions are from the recorded third-party transcription; neither profile
is a measured nut face, a conservative bound, or an adopted standard contact
definition. For the conditional force
introduction, apply uniform axial traction to each nut's complete outward
hexagonal end face, excluding the through-bore, with signed resultant `+X`
centered on its own bolt axis; integrate and verify its actual face force and
first moment. The hole is a smooth geometric surrogate, not a thread model.
The B18.2.1 head-gauge diameter is measured above its bearing plane and does
not define a head bearing land. The first scenario models the nut side only.

At each wood/washer and nut/washer interface use compression-only finite
penalty contact, allowing separation and leaving washer edges untied. Reuse
the already checked 2.23 contact/resultant method and its numerical
`K=100000 N/mm^3` penalty baseline; compare `K/2`, `K`, and `2K` as a declared
numerical sensitivity. Frictionless contact is the base branch: the source
tie join has no transverse action for these two axes. Optional `mu=0.4`
(nut/washer) and `mu=0.3` (washer/wood) branches reproduce only the Teranishi
study's reported comparator inputs; they are not candidate friction values.
The first composite scenario is K12, catalog-nominal washer, H1 nut land,
R/T-A, generic elastic metal, reciprocal wood tensor, frictionless interfaces,
`K=100000 N/mm^3`, and the 75 mm domain. Vary H2, R/T-B, catalog washer
corners, generic steel stiffness, friction, penalty, and the 100 mm domain one
factor at a time. These are diagnostic branches, not a full factorial or a
conservative envelope; keep every branch separate.

This load introduction omits thread engagement and bolt/nut load-transfer
detail; it is not a physical bolt-preload model. Start nut/washer faces in
nominal touch with no preload; actual clamp force, seating, and alignment are
unsourced. Use one explicit reaction-boundary branch: impose `u_X=0` on
remaining timber nodes of the opposite `X=38.1 mm` receiver face, keep
`u_T,u_N` free there, and select a remote-face anchor node `g0` with
`u_T=u_N=0`; at a second remote-face node `g1` offset from `g0` along `T`, set
only `u_N=0` to remove in-plane rotation. For each deformable nut and washer
body, use the same minimal tangential gauges at two distinct body nodes away
from its contact rims: at `g0`, set `u_T=u_N=0`; at `g1`, offset along `T`,
set only `u_N=0`. Do not
gauge `u_X` or suppress rotations/tilt through extra restraints; normal motion
and rocking must be governed by contact. These gauges remove only frictionless
rigid in-plane translation/spin of each separate solid. Transform all
directions from source `X/T/N` through the authenticated receiver basis to
solver coordinates; do not assume they are global solver DOFs 1/2/3. Record
per-DOF and per-body gauge force, moment about the receiver datum, and work,
separately from wood reactions. A non-negligible metal-gauge wrench or
gauge-placement sensitivity makes the centered frictionless response
unresolved; the gauges do not supply a physical lateral restraint. All other
cropped side faces are traction-free. This is a conditional reaction model,
not evidence that the assembled frame supports that plane. Repeat it on the
100 mm domain; physical boundary compatibility remains open unless
independently justified.

## Timber tensor and orientation

Use the documented reciprocal DF-L/clear-wood diagnostic tensor, not the
Teranishi cedar values or `Fc_perp` as a contact law: `E_L/R/T =
11032/750.176/551.6 MPa`; `G_LR/LT/RT = 706.048/860.496/77.224 MPa`; and
independent `nu_LR/LT/RT = 0.292/0.449/0.390`. Derive `nu_RL=0.019856`,
`nu_TL=0.02245`, `nu_TR=0.2867647059`. The sourced calculation gives positive
normal-compliance eigenvalues `8.83057e-5, 1.00253e-3, 2.14574e-3 MPa^-1`
and positive shear compliances. These are mathematical and source-based
scenario checks, not stock calibration or resistance.

The authenticated receiver grain is source-local `+T`; the map resolves it
to global `L=(0,0.6427876096865427,0.7660444431189752)`. Ring orientation is
unknown; carry both right-handed material frames expressed in global XYZ:
**R/T-A** `R=(1,0,0)`, `T=(0,0.7660444431189752,-0.6427876096865427)`; and
**R/T-B** `R=(0,0.7660444431189752,-0.6427876096865427)`, `T=(-1,0,0)`.
In source-local `X/T/N` components those frames are respectively
`(R,T)=((1,0,0),(0,0,-1))` and `((0,0,-1),(-1,0,0))`. Transform load,
support, gauge, and material axes with the receiver map's exact local-to-global
basis; audit orthogonality and right-handedness after serialization. Encode
CalculiX 2.23 `*ELASTIC, TYPE=ENGINEERING CONSTANTS` with axes `1/2/3=L/R/T`
and data order `E1,E2,E3,nu12,nu13,nu23,G12,G13,G23` (§7.47); recheck the
serialized compliance and orientation axes in the actual input. The
existing pinned 2.23 rotated-orthotropic matrix coupon validates solver
rotation/matrix semantics for a different tensor, not this receiver, C3D10
local stress, or contact response; do not rerun it as a blanket prerequisite.

## Mesh, checks, and later frozen gates

There is successful, audited pinned-Gmsh mesh preparation for other STEP
bundles: WJ24 principal `base_principal_center_right` used STEP SHA
`7b7e3880a87e959486072e9e174de1a4adb9b9014ceae916693625633cb5d0d8`, not the
target hash above. Earlier WJ04 mesh failures were adapter defects, and a
later attempt passed coarse geometry/Jacobian checks. Thus the mesh pipeline
is evidenced, but no exact mesh/semantic face map for this target is verified
here. Bind the current STEP and surface ownership, use the audited pinned
pipeline or another reviewed path, and stop on invalid geometry, missing or
duplicate TRI6 face coverage, nonpositive sampled Jacobians, or changed source
hash; do not blindly retry an old Gmsh route.

For a later preparation, compare local quadratic tetra meshes with nominally
2/4/8 elements through washer thickness and maximum local edge lengths
0.8/0.4/0.2 mm around contact rims, the clearance bore, and service-passage
edge. Independently check mesh connectivity,
volume/face reconciliation, and positive C3D10 Jacobians. Verify the emitted
2.23 material, contact, load, restraint and output cards from pinned manual
semantics; re-integrate each applied face force and origin moment from its
actual triangles. Check the pinned 2.23 output definitions and integration
point stress fields before interpreting local stresses; do not rely on nodal
averaging as a stress-convergence measure. The corrected contact coupon's
0.02 N force and 0.05 N·mm
moment limits compare its solver-rule TRI6 pressure quadrature with the
independent continuous integral. Its whole-model equilibrium limits are
0.1 N and 0.1 N·mm; contact/gauge comparisons use separate source-derived
limits. Its pass validates software load transfer and resultants only, not
local stress or partial-seat response.

Predeclare these numerical gates for any later parent-owned freeze: whole-model
force and first-moment residuals at most 0.1 N and 0.1 N·mm (the existing
contact coupon's frozen overall limits); applied-face solver-quadrature
differences at most 0.02 N and 0.05 N·mm (its separate TRI6 integration
limits); and each artificial in-plane gauge system (receiver, every washer,
and every nut) at most 0.02 N and 0.05 N·mm (new, explicitly stricter
diagnostic gates, not inherited from the coupon). Target-versus-neighbor
contact/resultants and wood support-plane, timber-gauge, metal-contact, and
metal-gauge wrenches must remain separately reported. Compare the 75/100 mm
domains, `K/2`, `K`, `2K`, and alternate in-plane gauge-node pairs for the same
physical branch; require changes no
greater than 5% in non-edge displacements, integrated contact force/centroid,
contact area, washer-volume von Mises 95th/99th percentiles, and wood-volume
source-normal stress 95th/99th percentiles in the fixed 0–1 mm subsurface band
under the projected nominal washer footprint. Bind identical geometric
volume masks and integration-point weighting across meshes. Apply that 5%
gate to mesh/domain/penalty/gauge-placement refinement only. H1/H2, both R/T frames, material
perturbations, friction, and initial alignment are distinct assumption
branches: report each, and keep interpretation unresolved if their outputs
differ materially; do not select a favorable branch. Report finite-edge/
contact-rim stress peaks separately from these percentiles; do not call a
diverging peak converged or map it to a 25NWUS yield criterion. Check
unilateral sign/closure (no tensile contact traction, and no traction on open
faces) as a method gate. A zero gap/penetration or an elastic stress value is
not product acceptance.

Teranishi et al. (2021) remains an optional method comparator: its three
paired stiffness/yield rows concern square washers, SS400, and Japanese cedar;
printed cedar Poisson pairs are not a reciprocal tensor. The paper compares
assembly load–embedment response, not local washer stress recovery. Its
reproduction, a physical test, product inspection, and outside approval are
not prerequisites to a clearly hypothetical conditional scenario. The
remaining dependencies are the exact target mesh/face map, the reviewed
idealized nut load face, and justified physical reaction boundaries before
any physical interpretation.

## Source pins inspected

- [Washer geometry exception](../remaining-candidate-washer-seats-2026-10-01/README.md), SHA-256 `9d8c9ebd6f7ba60fedf58e73baa3148aa5c34b55ae607a1889ead9262e2ca770`; [signed demand join](../remaining-candidate-washer-demands-2026-10-01/README.md), SHA-256 `d7784cf7451e6e1aa81589e4a3ebf5b23061a205a7dc482c4fbe0fca19df2685`.
- [Hardware source screen](../hardware-material-specification-2026-09-30/fasteners.md), SHA-256 `aac25eaccfcd123f41c180c93c6449e9f2da11c306c5b78fbf125c0ea81959f6`; [ordinary washer property boundary](../../current-ordinary-nut-washer-property-basis.md), SHA-256 `98a151ae040232aa1f2485826ba4c29dc0e0d0fb1ce6ac87ddd9bf062eeb6bcf`.
- [Receiver frame map](../evaluation-resume-2026-09-24/current-frame-timber-material-frame-map-attempt01/README.md), map SHA-256 `f867b4926ed23c9f356005c134778e138c8b1230547f0b69be7c3f9bc2a42409`; [reciprocal elastic scenario](../../orthotropic-material-scenario.md), SHA-256 `f6b723ddfc911284958df7a5348162f6d659396bbc03b83a74fcfbb125b3477f`.
- [Corrected 2.23 contact coupon](../washer-contact-known-answer-preflight-2026-10-01-attempt02/README.md), SHA-256 `1d1a48e249f4804c88528ef0f2b2a82f1dcc787c8c007a0d49dfb504ee6af4b6`; its [parent result](../washer-finite-sector-contact-native-2026-10-01-attempt02/parent-result.json) SHA-256 `8fa2c65a09395f177123ce77e7305a81f690f5e843bc69b1ff7b1e0cc9d1deea`. [Teranishi benchmark input record](../washer-metal-method-preflight-2026-10-01/benchmark-inputs.md), SHA-256 `2d484a4eb04faa9b1f30752e9536474c15f2060d7c15696fdc3f7f190ff5d9da`.
- [Generic steel elastic scenario](../../steel-elastic-material-scenario.md), SHA-256 `e97f7df51e6553698e1542079d722022cdbbedad83f740ee42d85b56e6b394c3`; it supplies only the generic stiffness diagnostic, not 25NWUS yield.
- Pinned CalculiX manual [`fea/generated/ccx_2.23.pdf`](../../../../fea/generated/ccx_2.23.pdf), SHA-256 `a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`; solver profile SHA-256 `f233cb12fe58983e968600befe78cc5ee0785903d60541a6269fe45e8489689c`; existing orthotropic matrix coupon freeze SHA-256 `221537619e0d8c3adf0ef68bd7a88231033f1df00733a81a2b2686a4d67a6c62`.
- Audited Gmsh 4.12.1 WJ24 mesh run: source `fea/wood_joint_wj24_patch_mesh.py` SHA-256 `80d26c667a0fa2c9d9603559f43b5654c67b1c018f297435672a772e3838d9bb`, tests SHA-256 `23472e4433734fed868728be73128723dfdff5bde12e62fd127356025309aa1d`, pinned image `sha256:083de8eefd4d9d9029d28ac1fdbb933a3b1e024225d8048165d6ef580d1b8f59`; successful attempt-03 WJ04 producer historical run pin `915ab6d14efc6e81b4a95c4338ffb8b98cb7e4fac1478d23b592bc8bb377564b`.
- Official catalog records: [25NWUS](https://www.kljack.com/products/25nwus/) and [25CNFH5Z](https://www.kljack.com/products/25cnfh5z/); these establish only their listed dimensions/material descriptions and do not identify a received item.
