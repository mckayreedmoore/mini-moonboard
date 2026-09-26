# Independent review of right-leg motion attempt01

This read-only review covers the right-leg adapter, its pinned report, the
shared sweep helpers, and the attempt04 STEP manifest and files. I did not run
CAD or regenerate geometry. The four manifest-only adapter tests pass.

For the modeled post-removal scene, the report supports a straight
`lumber_leg_right` translation of 62.468 mm in global `+X`, with no computed
sweep-obstacle solid-volume overlap above `1e-6 mm³`. It establishes no positive
clearance margin, support or staging method, tool/cable access, physical
transport, or complete removal sequence.

## Right-specific inputs and guards

The producer SHA-256 in the report matches the adapter on disk
(`a2cf2a29…f792defad2a`); its shared-runner hash matches the reviewed attempt02
source (`fdaf703a…50f35499`). The report binds revision/trial
`led-clearance-2x6-runner-seated-blocks-v1`, manifest SHA-256
`d90a9344…b1e538b`, source-inventory and frozen-geometry digests, and the exact
right-leg STEP SHA-256. I independently checked all 211 manifest-listed STEP
hashes and byte counts: none were missing or changed, and there were no
unlisted STEP files. The right-leg dependency row names exactly
`lumber_leg_bolt_right_1`, `lumber_leg_bolt_right_2`, `rail_rear_bolt_right_1`,
and `rail_rear_bolt_right_2`. The adapter derives `+X` from the right member's
own positive-X manifest bounds and injects those pinned dependencies into the
shared loader; the report's 191 imported shapes are one target plus 190
stationary obstacles. This is a right-specific check, not an inferred mirror
of the left-side result.

The continuous-sweep refinement accounts for every reported boundary face:
eight planes and four cylinders, with unsupported surface types or
nonparallel cylinder axes rejected. Its distinct right-side ordering has one
leading plane at face 3 (`normal·+X = 1`) and four inner wires; the face's outer
and inner wires are all passed to the linear extrusion. The remaining planes
trail or are tangent, and all four cylinders have axis alignment 1.0. For this
guarded BRep, the source union the leading-face prism covers the full straight
translation: advancing boundary patches are extruded, while the remaining
surfaces cannot advance material along this axial path. Source and endpoint
are contained in the resulting sweep, and the complete sweep is contained in
the conservative vertex hull. This supports this guarded translation only,
not arbitrary members or rotations.

## Collision result and limits

The hull has one exact obstacle test and one hit, `base_floor_right`, at
`89,894.589574 mm³`. The refined sweep is tested against that hull-hit obstacle
and returns no hit above `1e-6 mm³`; the other 189 obstacles are excluded by
the hull and remain clear by sweep-subset containment. The exact test does not
record sub-threshold intersection volume, so this is not a measured gap or a
positive clearance claim. The 1 mm endpoint condition is based on projected
obstacle bounds and does not establish useful staging or handling space.

The stated operation assumptions remain substantial: all 92 candidate
connector stacks, panels and their 66 screws, holds/T-nuts, and lights are
removed first; only the four named right-side retained stacks are removed for
this motion; the remaining retained roles and 131 modeled wires stay fixed.
The report correctly leaves support/staging, compatible tools or transport,
and a complete sequence unestablished. The adjacent README still says parent
execution is pending even though this report exists. Runtime CadQuery,
OpenCASCADE, and SciPy versions are also absent from this right-run report, so
they are not pinned for exact replay.
