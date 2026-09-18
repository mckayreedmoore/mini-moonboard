# Curved leg-section geometry integration

The two selected archived leg sub-bodies satisfy the predeclared **geometry
arithmetic checks**. This is not native section-force extraction, a stress or
contact test, a joint demand, or approval to build.

The [preflight](leg-section-preflight.md) selects complete inner-ply elements
below the fixed bore fixtures using mean corner Z < 1400 mm. Those conforming
cuts are jagged mesh interfaces, not planar sections. Their quadratic midsides
deviate from straight edge midpoints by up to 0.352720 mm and 0.198462 mm.

## Measured geometric comparisons

The complete outward quadratic boundary is integrated using Gmsh TRI6
Lagrange values/gradients and Gauss8/Gauss12 rules. Signed area-vector closure,
divergence volume and first moment are checked. A separate C3D10 Gauss5 volume
integration supplies the comparison volume and centroid. Both routes use Gmsh;
they are different boundary/volume calculations, not independent software
implementations. No stress field is integrated.

| Mesh | Selected elements | Boundary faces | Cut faces | Integrated sub-body volume (mm³) |
| --- | ---: | ---: | ---: | ---: |
| 40 mm | 1,496 | 1,176 | 22 | 5,140,856.796808 |
| 25 mm | 3,665 | 2,712 | 26 | 5,138,105.484369 |

| Check | Largest observed value | Predeclared limit |
| --- | ---: | ---: |
| Closed signed area-vector norm / total area | 1.763e−16 | 1e−10 |
| Boundary/volume relative volume difference | 2.027e−13 | 1e−8 |
| Centroid difference / characteristic length | 4.664e−16 | 1e−8 |
| Gauss8/Gauss12 relative boundary-area difference | 3.851e−13 | 1e−8 |
| Opposed cut area-vector cancellation / cut area | 2.147e−15 | 1e−10 |

All sampled surface Jacobians and orientation comparisons were positive; the
smallest sampled orientation cosine was approximately 0.988947. This does
**not** prove positive Jacobians or injectivity everywhere between samples.
Opposed cuts use the actual upper/lower element connectivity. The two meshes
have different jagged cut surfaces, so their differing scalar cut areas are
not a physical planar-area comparison or a convergence result.

## Retained attempts and reproducibility limits

The [evidence archive](../fea/results/leg_section_geometry/evidence.tar.gz)
preserves both attempts unchanged; its
[manifest](../fea/results/leg_section_geometry/manifest.json) identifies every
retained member and references the existing large actual-leg archive by hash.

1. `leg-section-geometry-rMNuN4` failed immediately because the pinned image
   lacked NumPy. It produced no geometry result. Its import traceback, frozen
   inputs, command, container state and successful cleanup are retained.
2. `leg-section-geometry-2N0ZGp` completed with exit 0 and successful owned-CID
   cleanup. Its container start/finish timestamps span about 8.60 seconds.
   Both per-mesh JSONs and the full report are retained; a successful-run
   process log was not captured in the retained directory.

Both attempts used image
`sha256:37671083a88ded305c4fcd83960a767dad4c2acb480976cb75fab5df261e2646`,
120/140-second inner/outer bounds, 2 GiB memory/memory-plus-swap, one CPU,
two-thread environment limits, no network, and read-only frozen-source and
input mounts. The successful run records Python 3.12.3, Gmsh 4.12.1 and NumPy
2.5.2. NumPy and its libraries were mounted read-only from the existing host
environment; they were **not** part of the pinned image. The lockfile is
retained, but mounted package bytes were not archived or independently hashed.
Publication hashes authenticate retained files, not a retroactive prelaunch
manifest or a fully self-contained dependency environment.

```sh
uv run pytest -q tests/test_leg_section_geometry.py tests/test_leg_section_geometry_publication.py
```

The first suite uses analytic synthetic geometry; the publication suite checks
retained provenance and recomputes gates from reported derived integrals.
Neither reruns Gmsh or independently reconstructs the complete integration.
The subsequent [native section comparison](leg-section-response.md) failed
against the separately established external-load references. These passing
geometry checks alone do not qualify that recovery path.
