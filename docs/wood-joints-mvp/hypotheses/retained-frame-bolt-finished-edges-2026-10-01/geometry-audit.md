# Saved-signature audit and frozen query metric

The read-only Luna/max geometry audit authenticated the current face register
(`33fff67e…b2f6eb`), axis register (`bebb4274…4513e19`) and retained load report
(`f068cd5a…bed661cc1`). All twelve axes have exactly two current receiver
memberships, each with one matched bore patch. The eight receiver members have
74 planar faces and 68 cylindrical faces. Their recorded edges comprise
296 lines and 272 full circles. Every cylinder spans a full turn and its
finite trim has two circles and one seam line.

An independent reconstruction closed each unordered straight planar loop.
Polygon-minus-circle or circular-disk areas differed from the saved face
areas by at most 5.12e-7 mm². Cylinder trim parameter lengths and saved axial
interval lengths differed by at most 2.88e-10 mm. Full circles need no missing
parameter phase or x-direction. Plane normals already include the oriented
solid normal returned by the pinned CAD producer.

These observations support nominal analytic plane and cylinder intersection
with the present simple trims. They do not establish kernel-equivalent
classification at a tangent or vertex. The signatures omit BRep tolerances
and edge-occurrence orientation. Unsupported topology or ambiguous crossings
therefore return explicit NULL results instead of a stock-box substitution.

The audit also identified that the physical interface force points lie in
the mating-face planes. A ray from that point would need a coplanar trim
method. The primary instead accepted the specific interior centerline metric
recorded in `geometry-plan.md`: independent positive/negative grain and
stock-q rays at three interior bore depths. The physical source force point
is retained separately, and the sampled geometry origin is never described
as the point where the physical force acts. No total-resultant interface ray
or through-depth minimum is claimed.

The audit ran no CAD, native mechanics, geometry mutation or Git operation.
It did not issue joint acceptance or change any criterion disposition.
