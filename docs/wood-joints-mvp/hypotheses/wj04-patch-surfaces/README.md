# Representative-joint mesh surface identities

Status: source-bound geometric classification, 2026-09-24. The parent ran
this adapter against the frozen coarse mesh in 0.77 seconds. It matched all
four wood interface pairs and sixteen candidate bolt-bore/member pairs.
No contact law, load, material, pressure, resistance, or release is assigned.

The [classification](classification.json) authenticates the exact mesh,
five-body STEP inventory, source snapshots, and parent finite-face overlap
probe. Plane selection checks analytic support normals and every referenced
quadratic boundary node against the pinned plane. Cylinder selection checks
axis, radius and ordered member-layer stations, including the two reversed
upper-rail stacks. The radius inferred from the archived occupancy cylinder
is cross-checked against its bounds. Split entities are grouped by physical
identity; transient Gmsh entity numbers are only local pointers.

The four finite nominal face overlaps match their cleat trimmed areas:
10,552.972707 mm² for each lower interface and 7,637.052707 mm² for each upper
interface. The larger host faces retain their own areas; their full area is
not credited as the common contact footprint. Thirty-five other cylindrical
surfaces remain explicitly unclassified. They are not silently assigned to
the eight candidate bolts. No physical steel hardware is meshed yet.

The classifier treats Gmsh parametric normals as unsigned. A separate
[parent normal audit](parent-normal-audit.json) uses the actual C3D10 deck:
for every classified planar exterior triangle, orient its corner cross
product away from the owning tetrahedron's opposite vertex, then compare
against the independently pinned signed CAD datum normal. All eight
interface sides pass; seven unique mesh surfaces occur because the two
principal connections share a larger host face. Minimum outward alignment
is 0.9999999999999998. This supplements the frozen classifier's deliberately
unresolved outward-normal field; it does not assign contact pressure.

Eight focused tests pass. The [execution](execution.json),
[source/test snapshots](sha256.json), and independent audit source are
archived with exact hashes. The classification SHA-256 is
`8134945198c284c734494cadf18476cae1d89cf0197a57f012b1471c7a12eb42`.
The source hash is
`5bd96498eae7379a66658b627873dbe0e85da8ec3abec1f90d86a5abf5e8838c`.

The next mechanics work is the actual bolt/head/nut/washer and timber contact
formulation, including gap, zero-preload seating, stable restraints, material
orientations, and numerical sensitivities. A successful geometric mapping is
not a native structural response or an acceptance of the representative joint.
