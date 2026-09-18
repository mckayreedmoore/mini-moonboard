# Prospective curved-leg native section comparison

**Predeclared diagnostic protocol; subsequent [runs rejected section recovery](leg-section-response.md).** This concerns
homogeneous, contact-free section recovery on the archived independent-ply leg
fixture. It does not address the unresolved surface-contact diagnostic or make
a construction recommendation.

## Frozen comparison

Use the two archived meshes and nine serialized unit-load steps identified by
the [cut preflight](leg-section-preflight.md). Retain the original geometry,
material, separate ply nodes, bore restraints, forces, per-ply energy and
displacement/reaction output. Add only the two opposed internal surfaces and
native section-output requests. Removing these additions must recover each
archived deck byte-for-byte. Do not substitute a planar cut, linear elements,
equal-sharing-only cases or bonded plies.

Before launch, the curved-boundary integration check must pass its declared
geometry gates on both meshes. Preserve its source, input identities and report.
The native run must use a separately recorded existing solver image/version,
not a modified contact build. Use at most 120 seconds per mesh, two threads,
and a bounded container with no network; retain timeout/nonzero-exit results.
The exact launcher and resource/cleanup checks require review before execution.

## Observations and sign convention

Request `SOF` on both opposed cuts in every step. The
[CalculiX 2.21 manual](https://www.dhondt.de/ccx_2.21.htm.tar.bz2), `*SECTION PRINT`,
states that SOF also requests moments and areas. Its first vector uses global
force and moment about the origin; the selected side determines the sign.
Translate to the preflight reference R using **M_R = M_0 − R × F** before
comparing to the upper-on-lower references. The upper cut must give the opposite
vector. Do not compare centroid moments directly with fixed-reference moments.

Require exactly two section records for each of the nine endpoints on each
mesh, with finite vectors and positive areas. Verify both section areas against
independently integrated curved-face areas. The native interpolation averages
nodal stresses; passing here would not qualify discontinuous material or contact
interfaces.

## Numerical gates declared before native observations

These are project diagnostic targets, not code limits, material safety factors
or allowable displacements. Existing failed results retain their own gates.

| Check | Prospective criterion |
| --- | --- |
| Existing fixture force/moment, displacement and per-ply energy checks | Preserve all `independent_leg_response.GATES` and case coverage unchanged |
| Each section force component versus its signed reference | Absolute error ≤ max(0.001 N, 1% of that reference component's magnitude) |
| Each fixed-reference section moment component | Absolute error ≤ max(0.01 N·mm, 1% of that reference component's magnitude) |
| Sum of opposed vectors | Same component limits as above, scaled by the nonzero reference, not by their near-zero sum |
| Coarse/fine section-vector difference | Same component limits as above; compare at the common fixed reference |
| Native area versus integrated area, each mesh and side | Relative error ≤ 0.01% |

The absolute floors retain tight checks on nominally zero components; the 1%
target limits errors in nonzero recovered demands. Passing two meshes is only
the declared comparison, not a general convergence proof. If a gate fails,
preserve the result and investigate output/geometry/interpolation sensitivity
before deciding whether a different extractor is needed. Do not adjust these
limits after seeing a failing result to label the same trial accepted.

Archive decks, geometry/preflight identities, exact runtime and audit sources,
solver identity, logs, native outputs, cleanup record and the complete signed
comparison, including failures. The subsequent evidence preserves failed
comparisons; native curved-leg section recovery remains **unqualified**.
