# Independent review of left-leg motion attempt02

This read-only review covers the exact-sweep source, report, and attempt04
readback record. I did not run CAD or regenerate geometry.

## Finding

For the modeled post-removal scene, the report supports a clear straight
translation of `lumber_leg_left` by 62.468 mm in global `-X`. The claim is
limited to no computed solid-volume overlap above the configured `1e-6 mm³`
hit threshold. It establishes no path clearance margin, support or staging
method, usable tool/cable access, physical transport, or complete removal
sequence.

## Sweep construction and guards

The refinement is appropriately bounded to the hash-pinned target. The code
rejects any boundary surface other than planes and cylinders; requires exactly
eight planes and four cylinders; checks every cylindrical axis parallel to
translation; and requires exactly one planar leading face aligned to `-X`.
The report records all eight plane classifications and four axial-cylinder
checks. The leading plane has four inner wires, passed to `extrudeLinear` along
with its outer wire, so the bolt openings are retained in the swept prism.
The source solid and prism fuse to one valid solid; the union-volume difference
is `2.556e-6 mm³`, below the recorded `0.038461205 mm³` tolerance.

For this boundary inventory, the construction covers a straight translation:
the swept set is the original solid plus the extrusion of every boundary
patch whose outward normal has positive dot product with the travel direction.
Here there is one such patch; the other planar patches trail or are tangent,
and the axial cylinders are tangent. The report also confirms computed
containment of the source and translated endpoint in the constructed sweep,
with zero reported outside volume at both checks. This theorem and result apply
to this guarded BRep/path, not arbitrary timber shapes or rotations.

## Convex-hull transfer and floor check

The source-vertex hull contains the five sampled poses, and the exact
source-plus-prism sweep is separately contained in that same convex hull. The
reported outside volume is `0.0 mm³` with a `0.038461205 mm³` containment
tolerance. The hull has one broadphase candidate and one exact obstacle test:
`base_floor_left`, with a conservative hull intersection of `89,894.589576
mm³`. The other 189 obstacles are excluded by disjoint bounds against the
hull; the report does not claim 189 separate OCC intersection tests. Since the
refined sweep is contained in the hull, those hull-separated obstacles remain
clear for the refined sweep under the report's solid-volume criterion.

The exact sweep is then tested against `base_floor_left`; that single test
returns no hit above `1e-6 mm³`. The output does not record the raw sub-threshold
intersection volume, and it reports no positive clearance or tolerance
margin. This resolves the convex-hull false positive as no computed material
overlap for the refined sweep, not as a measured gap or proof of free sliding.

The endpoint distance is selected from the target and obstacle projected
bounds so the target interval is 1.0 mm beyond every remaining obstacle along
`-X`. This is an endpoint condition only; the continuous path is assessed by
the sweep checks above.

## Provenance and state limits

The on-disk producer hash
`fdaf703a4b387d2789998533e857c28c7269fe3401fb222d20b26bd650f35499` matches
the report's `producer_sha256`. The report binds the attempt04 manifest
(`d90a9344…b1e538b`), source inventory digest, canonical frozen-geometry
digest, current revision/trial IDs, and exact target STEP hash. Its loader
verifies all 211 listed STEP hashes before importing the 191 target and
stationary-scene shapes used in this screen, then checks validity, solid
count, volume, bounds, and center of mass against the manifest. The separate
attempt04 readback record also passes for all 211 STEP artifacts; it checks
geometric summaries rather than exact Boolean equivalence.

No missing geometry-source content pin was found. The report does not record
CadQuery/OpenCASCADE or SciPy versions, however, which would improve exact
replay of the Boolean and hull calculations. The result assumes all 92
candidate connector stacks, panels and 66 panel screws, holds/T-nuts, and
lights were removed beforehand; only the four named retained stacks are
removed for this member; all other retained roles and 131 modeled wires stay
stationary. Supports, catch surfaces, workspace, actual cable paths, and
stable staging are absent. The report correctly leaves transport and full
sequence claims false.
