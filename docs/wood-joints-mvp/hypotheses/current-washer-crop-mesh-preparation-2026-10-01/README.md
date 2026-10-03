# R75/H1 washer-seat mesh preparation

**Status:** source-only preparation, 2026-10-01. No CAD import, Boolean,
geometry export, mesh, solver deck, native run, or input freeze was created.
This packet prepares one bounded parent-owned mesh-only job. It does not close
any candidate acceptance gate.

## Frozen scenario definition

The only planned geometry branch is the current
`compact-floor-flush-wood-joints-development`, revision
`led-clearance-2x6-runner-seated-blocks-v1`, with an R75 mm crop and the H1
idealized nut profile. The five independent bodies are the exact finished
`base_principal_center_right` BREP crop, one conditional 25NWUS-like washer
and one conditional H1 nut on each of `center_principal_right_2` and
`center_principal_right_1`. This is the K12 full-load branch. The source-bound
inward actions are 64.40226 N and 20.52895 N, each along receiver-local `+X`.
The nuts, washers, wood, and their semantic surfaces remain distinct.

The authenticated receiver basis is source-local `X/T/N` to global
`X=(1,0,0)`, `T=(0,0.6427876096865394,0.766044443118978)`, and
`N=(0,-0.766044443118978,0.6427876096865394)`. The target and companion
centers are transformed from the parent crosscheck's signed-seat points; they
are 53 mm apart in source `T`. The crop cylinder is centered on target
`center_principal_right_2`, runs through the full 38.1 mm member thickness,
and is aligned with receiver `X`. Its radius is 75 mm. It contains the full
38.1 mm F1/G1 service passage and both washer footprints. The output must
preserve every natural cut that intersects the crop.

The washer inputs are OD 18.653125 mm (catalog nominal 47/64 in), ID
7.9248 mm, and thickness 1.5875 mm. The earlier CAD envelope OD 18.6436 mm
is recorded as a separate reference; it does not define this body, and the
90.504635% support result for that earlier envelope is not transferred. Both
new annuli must be re-intersected with the exact current receiver BREP.

The additive parent profile defines the complete H1 nut solid. Its regular
11.1252 mm across-flats hex is clipped by a coaxial 12.827 mm circle; the
bearing-side outer relief grows at 45 degrees from radius 5.5626 mm; the inner
relief transitions from radius 3.556 mm to the 3.175 mm smooth bore over
0.381 mm. Its 0-degree clocking is an analyst assumption. At the washer plane
only the H1 annulus is coplanar. Preserve the whole nut body and report any
later conical-relief contact; do not constrain contact permanently to the
initial annulus. The separate 30-degree clocking and H2 profile are outside
this first mesh branch.

Independent source-only arithmetic in `prepare.py` gives the H1 nut volume
415.50205345278425 mm³, outward load-face area 75.51784511932227 mm², initial
land area 57.48292325873653 mm², and the two washer volumes 355.5139185846077
mm³ each. These match the separate parent geometry-oracle receipt within
floating-point tolerance. They are analytic conditional-shape checks, not
CAD import checks or evidence about delivered hardware.

## Future one-run mesh-only procedure

The producer may run only after the parent freezes exact inputs and completes
the runtime/resource preflight. One invocation covers this single R75/H1
branch; the retry budget is zero. If preflight fails, no Gmsh process starts.
If a run fails, preserve that isolated failure record and stop. Any changed
source hash, body count, semantic map, mesh gate, or runtime pin requires a
new parent decision before another launch.

Reuse the audited Gmsh 4.12.1 OCC and high-order C3D10 preparation pattern in
the pinned WJ24 adapter, its shared mesh worker, and the WJ04 attempt-03
receipt. The historical attempt-03 receipt records Python 3.12.3, NumPy
1.26.4, Gmsh 4.12.1, image `sha256:083de8eefd4d9d9029d28ac1fdbb933a3b1e024225d8048165d6ef580d1b8f59`,
two CPUs, 4 GiB memory, no network, and a 12.30-second five-body run. This is
historical method evidence only; the actual launch must verify the image ID,
Gmsh/Python/NumPy versions, writable isolated output, and available resource
limits before consuming its one mesh attempt. Bound a future launch to one
300-second, two-CPU, 4-GiB container invocation with a 512-MiB scratch mount,
read-only sources, no network, and no retry. The 300-second ceiling is a
predeclared resource stop, not a performance prediction.

Use independent Gmsh models for each solid, then stitch with disjoint node
and element IDs. The initial mesh target is nominally two C3D10 layers through
the washer thickness and at most 0.8 mm local edges around contact rims,
receiver bores, and the F1/G1 passage edge. The mesh must report the achieved
through-thickness resolution and local edge maxima; fail if either target is
missed. A later 4/8-layer mesh, 0.4/0.2 mm refinement, or R100 crop is a
separate branch and is not part of this one-run budget.

Resolve source-face ownership before meshing. Use source BREP surface type
and analytic plane/cylinder parameters, exact source frame, and complete
trim/boundary information to form stable semantic identities. Trace surviving
source faces through the OCC crop where ancestry is available, then reconcile
every mapped face with its source signature and clipped area. Record
crop-created R75 cylinder surfaces separately. Transient Gmsh tags are only
local references. Bounding boxes alone cannot identify a load, contact,
bore, passage, or support face. Ambiguous ancestry, missing natural cuts,
unclassified source faces, or a duplicate semantic owner is a refusal.

The mesh-only report and independent audit must establish:

- exactly the five named solids, each valid, connected, and separately owned;
- exact BREP source and cropped-host volume/centroid/bounds reconciliation;
- analytic washer and nut volume/face-area reconciliation;
- complete source-face ownership, with natural source faces separated from
  crop-created faces;
- C3D10 connectivity, disjoint body node ownership, positive sampled and
  Gmsh Gauss5 Jacobians, and mesh-integrated volume within 0.1% of each exact
  BREP body volume;
- a one-to-one mapping from every exterior C3D10 face to exactly one TRI6
  face, including semantic face assignment and no missing, duplicate, or
  nonmanifold faces;
- an external integration of each nut's actual outward-face TRI6 triangles,
  using CAD face area for uniform traction, with K12 force residual at most
  0.02 N and first moment at most 0.05 N·mm about that nut axis;
- a mesh input containing only nodes, C3D10 elements, and body sets: no
  material, contact, tie, load, restraint, preload, or solver cards.

No mesh result is supplied here. The only load-face output in this stage is a
separate geometric area/centroid/resultant oracle; no load card is written.
Future wood source-normal stress masks must use the declared local/global
output frame and serialized orientation. Solver `S` output defaults require
explicit frame verification before reading source-normal components. Mesh
completion alone does not validate material, contact, support, stress,
resistance, or candidate acceptance.

## Source-only tools

`prepare.py` authenticates the current source pins, checks the receiver frame
and two signed seat positions, independently integrates the hypothetical
hardware geometry, and emits a deterministic preparation record. It imports
no CAD, Gmsh, solver, Docker, or networking library and has no launch path.
`mesh_oracles.py` contains pure TRI6 surface integration and fail-closed
report-contract checks for a later parent-produced mesh report. The tests in
this directory use only small synthetic records and arithmetic; they do not
create geometry or meshes.

The machine pins in `source-pins.json` bind the current contract bytes, the
additive nut profile, signed source crosscheck, receiver STEP/frame, catalog
records, and audited mesh implementation/runtime receipts. A pin drift causes
source preparation to stop until the parent reviews the new bytes.
