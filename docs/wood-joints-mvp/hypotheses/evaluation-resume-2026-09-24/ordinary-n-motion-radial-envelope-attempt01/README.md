# Radial surface envelopes for the candidate N-motion witness

This read-only calculation bounds the frozen attempt09 shaft and bore surfaces
under an assumed rigid translation. All eight wood-bore pairs have positive
computed separation when each shaft moves at most 0.25 mm relative to its
receiver. All eight washer-bore pairs also have positive separation when each
washer co-translates with its shaft. The smallest computed bound is
0.0931497349 mm; subtracting a 0.000001 mm numerical reporting reserve leaves
0.0931487349 mm. This is a geometric result, not a native contact result or
proof that the complete joint can follow that motion.

The translation assumption belongs to the candidate witness: rail +0.5 N,
principal −0.5 N, cleat stationary, and each of the four complete hardware
stacks translated halfway between its two receivers. Thus the two rail stacks
move +0.25 N and the two principal stacks −0.25 N. No displacement is applied
to a model here. Compatibility with the actual port/nut equations and all
planar interfaces is a separate witness review.

## Bound and reproduction

The input consists of attempt09's exact mesh, contact fragment, contact
manifest, bolt axes and 1 mm N-motion record. The fragment and manifest must
contain exactly 35 pairs in matching numbered order. This calculation reads
only the 16 radial pairs `WJCP_020` through `WJCP_035`, with exact face counts.
The pinned C3D10 face-node mapping identifies each TRI6 face's three vertices
and three edge midpoints.

For a quadratic triangle, convert its nodal positions to Bernstein controls:
vertex controls stay at the vertices, and an edge control is
`B_ij = 2*x_mid − (x_i+x_j)/2`. The six Bernstein basis weights are nonnegative
and sum to one over the closed parameter triangle. The surface therefore lies
in the convex hull of these six controls.

Project each control perpendicular to its recorded bolt axis. For each face,
choose a radial unit direction from its vertex centroid. The minimum control
projection along that direction is a lower bound on surface radius. The
maximum control radial norm is an upper bound on surface radius. Taking the
minimum over all bore faces and maximum over all paired shaft faces gives
`separation >= bore_radius_lower − shaft_radius_upper − translation_norm`.
The last term follows from the triangle inequality and conservatively allows
any translation direction of the stated magnitude. Washer pairs use zero
relative translation.

The original whole-face hull is too broad to prove separation for the wood
pairs; its worst computed margin is −0.4169031 mm. That inconclusive result is
retained in JSON and is not interpreted as overlap. Restricting the same
quadratic polynomial to the four midpoint parameter subtriangles gives tighter
hulls. This is an algebraic restriction of the unchanged surface, not a mesh
refinement or geometry alteration. Exactly one level is used for every face.
A separate Lagrange-versus-Bernstein evaluation verifies the restriction
formula on a nontrivial quadratic surface. That sampled identity check is a
programming guard; the hull bound follows from the nonnegative basis weights.

| Surface group | Pairs | Smallest computed subdivided separation (mm) |
| --- | ---: | ---: |
| Shaft / wood bore | 8 | 0.0931497349 |
| Co-moving shaft / washer bore | 8 | 0.6725859896 |

The calculation uses floating-point coordinates and NumPy. The 1e-6 mm reserve
is much larger than the polynomial reconstruction residual, but it is not an
outward-rounded interval-arithmetic certificate. It is not a manufactured
clearance, fabrication tolerance or structural acceptance limit.

Run from the repository root:

```sh
.venv/bin/python docs/wood-joints-mvp/hypotheses/evaluation-resume-2026-09-24/ordinary-n-motion-radial-envelope-attempt01/produce.py --verify
```

The writer is exclusive. The JSON binds all input files, both parsing helpers
and the producer; verification reconstructs the stored result byte for byte.
No solver, CAD rebuild, material law, preload, support or reviewed geometry is
changed. The other 19 planar pairs, shifted trimmed-seat overlaps, actual
CalculiX contact search/projection, equilibrium, contact onset and complete
joint behavior remain outside this result. A native solver could use contact
approximations that require their own applicability check; this artifact does
not equate a polynomial-surface bound with the solver's active-contact state.

Result file SHA-256:
`e459e979e33d9deb85ae5064fa27b2d2a78280ec87986bc40fc0ab4335a3ae3f`.
[Independent review](independent-review.md) reproduces the source-bound result
and confirms the mathematics and scope. Mechanical/joint acceptance and release
remain false.
