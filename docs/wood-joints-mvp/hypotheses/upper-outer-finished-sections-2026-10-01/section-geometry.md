# Upper outer finished-section geometry helper

Status: bounded, read-only geometry method check. This helper reports planar
properties of the saved or synthetic CadQuery solid supplied by its caller. It
does not rebuild or heal that solid, inspect built wood, calculate section
tractions or capacity, or establish a construction or climbing acceptance.

The helper runs with CadQuery 2.8.0 and `cadquery-ocp` 7.9.3.1.1, recorded in
each result's `kernel` field. The repository lock resolves those versions.

## API and returned values

Import `section_geometry.py` from this directory and call:

```python
section_properties(shape, origin, grain, u, v, *, tolerance_mm=1e-5)
```

`shape` must be a valid CadQuery shape with exactly one solid and no loose
geometry outside it. CadQuery's boolean operations may wrap a single solid in a
compound; that wrapper is accepted. Multiple solids, invalid geometry, a
malformed basis, a plane with no positive-area result, and unsupported result
topology raise `SectionGeometryError`.

`origin` is a global point on the section plane. `grain` is its unit normal;
`u` and `v` are the reporting directions. The supplied frame is checked before
any Open CASCADE direction can normalize it: all axes must be finite and unit
length within `1e-8`, pairwise dot products must be within `1e-8`, and
`dot(cross(grain, u), v)` must be within `1e-8` of `+1`. Only after these
checks does the helper normalize round-off in the basis. `tolerance_mm` must be
finite and positive. It controls plane-coincidence checks and the cutter's edge
margin; it does not move the plane or enable fuzzy Boolean intersection.

The returned mapping contains:

| Field | Meaning |
| --- | --- |
| `area_mm2` | Total positive section area, counting unique section faces once. |
| `centroid_global_xyz_mm` | Area centroid in global coordinates. |
| `centroid_relative_uv_mm` | Centroid coordinates projected from `origin` onto `u` and `v`. |
| `area_covariance_integrals_mm4` | `uu = ∫(u-cu)² dA`, `uv = ∫(u-cu)(v-cv) dA`, and `vv = ∫(v-cv)² dA`. |
| `component_count` | Number of positive-area face groups connected by shared positive-length BRep edges. |
| `disconnected_ligaments` | True when `component_count > 1`; point-only contact does not join groups. |
| `components` | Per-group area, global and relative centroid, covariance integrals, and `wire_count`. |
| `kernel` | CadQuery and OCP package metadata versions. |

For a component with multiple planar face patches, `wire_count` is the sum of
those faces' boundary-wire counts; it is not a count of unique outer loops.
Total centroid and covariance describe the whole measured set. When
`disconnected_ligaments` is true, they do not imply one connected section or a
common strain field. Use the per-component values and preserve that distinction
in later mechanics work.

## Extraction and inertia convention

The code makes one finite planar face large enough to cover the input solid's
projected bounding box, then runs OCCT `BRepAlgoAPI_Common` between that face
and the supplied solid. The plane is bounded with a margin so its perimeter
does not clip the solid. The same common operation covers interior and terminal
planes; the section is not obtained by splitting the solid into two halves,
which would produce two coincident cut faces. Empty or unsupported results are
refused rather than partially measured.

Identical face topology is deduplicated with `TopoDS_Shape.IsSame`. Every
remaining result face must be planar and lie in the requested plane. Independent
edges or vertices outside those face boundaries are also refused. Face groups
are joined only through shared positive-length topological edges in the common
result. This uses the Boolean result's edge identity; the helper does not weld
geometrically coincident but distinct edges or repair near-coincident BReps.
Those cases are a limitation and require an explicit upstream geometry review.

OCP `BRepGProp.SurfaceProperties` is called per face with triangulation disabled.
OCCT 7.9.3 resets the supplied `GProp_GProps` in that call, so the code creates
fresh face properties and combines them with `GProp_GProps.Add`, which applies
Huygens' theorem when reference points differ. This also keeps multiple faces
in one connected section component from being silently reduced to the last
face's statistics. `UseTriangulation=False` selects the exact BRep surface
geometry path rather than mesh triangles. OCP's standard surface integration
does not return a certified error bound for this overload; `tolerance_mm` is a
plane/topology tolerance, not an inertia integration tolerance. The included
known answers bound observed error for their analytic primitives only.

`GProp_GProps.MatrixOfInertia()` is a central symmetric tensor in the global
Cartesian directions. For axes `u` and `v` in the section plane, the area
covariances are rotated from that tensor as
`Cuu = vᵀ I v`, `Cvv = uᵀ I u`, and `Cuv = -uᵀ I v`. The minus sign accounts
for OCCT's inertia-tensor off-diagonal convention. The code contracts the
global tensor with the caller's axes directly, so arbitrary proper rotations
preserve the reported local integrals.

## Known-answer checks

`test_section_geometry.py` builds synthetic CadQuery solids only. It checks:

- a `20 × 30 mm` rectangle against its analytic area and second moments;
- a circular hole offset from both section axes against subtracted-disk area,
  centroid, and covariance formulas, including the nonzero product integral;
- a transverse cylindrical bore that leaves two unequal, disconnected strips,
  against each strip's analytic area and the full-set moments;
- an arbitrary 3D rotation and translation against invariant relative values and
  the transformed global centroid;
- both terminal faces of a box, empty/outside sections, and malformed bases.
- a fused solid with two adjacent terminal face patches, checked as one
  connected component against the combined rectangle's area and moments.

Focused result on the pinned environment: `12 passed`; focused Ruff check:
`All checks passed!`. The segmented terminal-face fixture retains two boundary
wires and checks accumulation across both faces without merging away the seam.

## Primary references and pinned-runtime observations

- [OCCT 7.9.3 `BRepAlgoAPI_Common.hxx`](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_9_3/src/BRepAlgoAPI/BRepAlgoAPI_Common.hxx) defines the operation as a Boolean common / intersection of arguments and tools.
- [OCCT 7.9.3 `BRepGProp.hxx`](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_9_3/src/BRepGProp/BRepGProp.hxx) documents `SurfaceProperties`, its `SkipShared` and `UseTriangulation` flags, and that disabling triangulation selects exact geometry rather than face triangulations.
- [OCCT 7.9.3 `BRepGProp.cxx`](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_9_3/src/BRepGProp/BRepGProp.cxx) shows `SurfaceProperties` resets the passed properties object before computing a shape's surfaces (the two-argument implementation at lines 199–208 in the tagged file). The helper therefore accumulates one face per fresh object.
- [OCCT 7.9.3 `GProp_GProps.hxx`](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_9_3/src/GProp/GProp_GProps.hxx) documents central `MatrixOfInertia` axes, `Add`, and reference-point handling.
- [OCCT 7.9.3 `BRepGProp_Gauss.cxx`](https://github.com/Open-Cascade-SAS/OCCT/blob/V7_9_3/src/BRepGProp/BRepGProp_Gauss.cxx) shows the surface-inertia conversion and off-diagonal signs at lines 411–414 in the tagged file.
- [CadQuery `Shape.intersect` API](https://cadquery.readthedocs.io/en/latest/classreference.html) documents shape intersection. The implementation calls the equivalent pinned OCP `BRepAlgoAPI_Common` binding directly so it can check completion and result topology.

The OCCT source references above are pinned to tag `V7_9_3`, matching the OCP
kernel in this environment. Their behavior was also checked against the
installed Python binding's docstrings and known-answer tests; the current online
OCCT reference-manual URLs redirect to 8.0.1 and are not used as the pinned
version evidence here.
