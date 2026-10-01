# Source review: slave contact-point census

Date: 2026-09-27. Read-only source clarification for the point-census proposal in [the current-joint capture design](../implicit-contact-point-trace-attempt01/current-joint-capture-design.md). This note does not change that historical proposal, prepare a patch, build a solver, run a native case, or qualify joint behavior.

## Finding

For the pinned CalculiX 2.23 face-to-face contact path, the frozen slave-face roster is a valid static census target; a fixed expected quadrature count such as three points per C3D10 face is not. The number of `pslavsurf` points associated with a slave face is generated from its current geometric overlap with the opposite master surface. It can be zero and can change between contact-generation sweeps.

In `gencontelem_f2f.f`, the initial element-type value for a C3D10 face is `mint2d=3` (lines 215–218), but the routine replaces it before the point loop with `islavsurf(2,jj+1)-islavsurf(2,jj)` (lines 296–304). A zero span skips the face. The loop's actual point records come from `pslavsurf(1:3,indexf+m)`, so the offset span—not the initial three—is the number consumed for that face.

## Source path

`tiefaccont.f:391–403` loads the element-face slave surface into `islavsurf(1,*)` and associates its face range with the contact tie. That gives a frozen, pair-specific face roster from the input surface definitions. The second `islavsurf` column is later reused as a pointer array: `slavintpoints.f:77–82` stores the starting `nintpoint` offset for a face, and `slavintpoints.f:892` stores the ending offset after it has generated points.

`nonlingeo.c:1740–1781` resets the point count and calls `precontact` during contact regeneration. `precontact.c:138–146` visits the faces in each active contact tie and calls `slavintpoints`. That routine forms slave face coordinates from `co + vold` (`slavintpoints.f:99–109`), then searches for covered master faces and their orientation (`:231–281`). Its own header comment says the integration-point locations depend on the triangulation of the opposite master surface (`:20–23`).

For the quadratic triangular master face relevant to C3D10 surfaces, `slavintpoints.f:348–420` subdivides its six-node face into four three-node subfaces before clipping. `treatmasterface.f:60–65, 71–90` clips projected subfaces against the slave face and fan-triangulates each remaining polygon. It skips polygons with fewer than three vertices and fan triangles below its `1e-4` local-area threshold (`:71, 94–122`); for each retained triangle it appends seven integration points and stores slave-local coordinates plus a weighted area (`:124–156`). Thus the count depends on search, projection, overlap clipping, subface subdivision, and cutoffs. This is why a three-point-per-face multiplier would misstate even the source's nominal generation path.

## Recommended census contract

Freeze and independently enumerate the complete slave-face roster for each pair from the deck/surface definitions, then record each face on every generation sweep, including faces with zero points. For each face, capture both `islavsurf(2,jj)` offsets, their nonnegative difference, and the exact point-index range consumed by `gencontelem_f2f`. Require contiguous, nonoverlapping face ranges; require the sum of all per-face spans to equal the sweep's `nintpoint`; and require every consumed point to produce exactly one classified generation outcome. Record no-point faces explicitly instead of inventing candidate points for them.

This gives an independent full-face census and a source-consistent, sweep-specific point-range census. It does **not** give an independently predicted geometric point count: that would require a separate implementation of the pinned `precontact` search/projection/clipping path evaluated on the same configuration state. A small known-answer coupon can validate source point-loop accounting, including zero-overlap and partial-overlap cases, before the instrumentation is relied on. For a real sweep, do not report the live `islavsurf` span as an independently predicted count.

`igauss=indexf+m` is an index into the current sweep's regenerated `pslavsurf` array, not a persistent physical point ID. Keep it as a sweep-local index. Use the frozen pair plus encoded slave face and a local ordinal/local coordinates for within-sweep keys; any cross-sweep correspondence needs an independently checked geometric/mapping match and must allow points to be added, removed, or remapped. The face roster may remain fixed while the point ranges and their local coordinates change.

The evidence here describes the pinned source algorithm and its accounting fields. It says nothing about whether a generated contact point is physically correct for the mesh, whether the native contact law converges, or whether a joint has capacity.

## Pins

The reviewed archive and member SHA-256 values, with exact source line ranges, are in [source-pins.json](source-pins.json). The archive is the same pinned 2.23 source used by the trace design and diagnostic build. The captured lines establish the face roster, geometric point generation, per-face offsets, and the generation loop that consumes those ranges.
