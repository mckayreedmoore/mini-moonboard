# Archive-only MORTAR geometry and coverage diagnostic

The finest untied 2×8-foot100 MORTAR run remains a **global-equilibrium
diagnostic**, not a locally validated contact solution. No solver run, archive
replacement, CAD change or acceptance-threshold change was made here.

Following the [exact 2.21 local-audit basis](mortar-local-audit-basis.md),
`fea/mortar_geometry_diagnostic.py` checks the published 0.125 and 0.0625
archives. It reuses deck reconstruction and archive hashing, parses CONTACT
fixed-width fields (including adjacent negative numbers and continuation
records), and requires the exact slave-node set at every accepted output time.
Endpoint geometry uses DAT displacements and verified launch-context coordinates,
not rounded FRD coordinates. The regenerated deck binds all six-node slave faces
and paired C3D8 S2 master faces to the actual input.

## What the existing evidence now establishes

Both archives contain exactly **610 slave nodes** at every accepted CONTACT
time: 16 times for 0.125, 32 for 0.0625. There are no missing or unknown slave
nodes. All endpoint samples project inside their paired deformed bilinear master
faces. Projection uses three starting points, checks local Hessian/Jacobian
degeneracy, rejects escaped/reversed geometry rather than clamping it, and
requires tangential residual below 1e-7 mm. It is not a proof of global projection
uniqueness for arbitrary warped surfaces.

At the finest loaded endpoint, the geometric clearances are:

| Patch | Nodal minimum, mm | Quadratic sampled minimum, mm | Sampled maximum, mm |
| --- | ---: | ---: | ---: |
| LEFT | −0.000357009 | −0.000363051 | 0.107508919 |
| RIGHT | −0.000326809 | −0.000330468 | 0.093601659 |
| KICKER | −0.0000166865 | −0.0000166865 | 0.118583305 |

Positive means above the master along its outward normal. Each slave face is
evaluated at uniform barycentric subdivisions of 4 and 8 (15 and 45 samples).
Between-node curvature gives lower LEFT/RIGHT minima than nodal checks alone;
the minima also change between the two sampling resolutions. These are sampled
extrema, not continuous bounds. Finite LINEAR contact intentionally permits
penetration, so a negative gap is **not** itself an inadmissibility finding.

The 0.125 loaded sampled minima are −0.000363042, −0.000330454 and
−0.0000143684 mm. Most endpoint geometric extrema are close across the two
increment schedules, but the kicker's minimum changes by roughly 0.000002318 mm.
Do not call these differences a mesh-convergence result or an accuracy tolerance.
DAT displacement rounding is propagated to input sample-position bounds;
normal/projection perturbation, continuous sampling error and model errors are
not enclosed by those bounds. Small gap differences remain qualified accordingly.

## The local-law question is still open—and localized

On the finest run, **31 kicker nodes at gravity and 15 under full load** have a
displayed `hypot(CSHEAR1,CSHEAR2)-mu*CPRESS` excess larger than the propagated
ASCII FRD rounding plus float-cast bound. LEFT and RIGHT have none. The raw
maximum kicker excess is about 1.3420e-7 at gravity and 9.0489e-7 under load.
The report records the relevant node IDs, field ranges and representation bounds.

These counts are deliberately **not Coulomb-law violation counts**. The
[2.21 source](https://www.dhondt.de/ccx_2.21.src.tar.bz2),
`stressmortar.c:984–1017`, exports projections of transformed multipliers;
the internal law uses different weighted components and frozen bases. The
same source's opening output is a weighted gap expression. Therefore neither
raw FRD pressure/slip nor reconstructed geometric clearance can substitute for
the internal normal/tangential complementarity variables. This result falsifies
the convenient assumption that every displayed excess must be printing noise;
it does **not** establish that the specified discrete law failed.

Ranked diagnostic hypotheses now stand as follows:

1. Missing or wrongly identified slave output: not supported by the exact
   node/time/deck coverage checks on these two archives.
2. Misleading wood-Z clearance or nodal-only geometry: confirmed as a diagnostic
   limitation; deformed master geometry and quadratic sampling are necessary.
3. Exported-versus-internal variable transformation explains the small kicker
   excess: source-supported hypothesis requiring internal variables to test.
4. Actual internal normal/friction residual, exclusion or history-state problem:
   still unresolved; global force/moment balance cannot exclude it.

## Smallest next decisive numerical step

Do **not** run another series of increment refinements solely to shrink the FRD
excess. First add a narrowly scoped, separately identified CalculiX 2.21
diagnostic exporter and verify it on the existing sliding cube, where the load
path is small and tangential movement is real. Export accepted-state, full-
precision pair/node identity, eligibility/activity, frozen normals/tangents,
`Ln`, `Lt`, `Lt_start`, `q`, `ut`, `b`, algorithmic constants and law parameters.
The exact formulas and additional matrices needed for independent reconstruction
are specified in [the local-audit basis](mortar-local-audit-basis.md).

Then, if the exporter is independently checked, reproduce the **unchanged
0.0625 full-frame case once**, exporting those quantities for all slave
constraints (the small kicker subset is the first place to inspect, not a
reason to omit other constraints). Bind the solver binary/source patch, image,
deck, material/load/ground context and accepted increment history by hashes.
Compare the original global force/moment gates and state the effect of the
instrumentation. Check the regularized normal complementarity, internal friction
cone, tangential history law and excluded-state coverage without inferring them
from CONTACT visualization fields. A local residual exporter alone is not fully
independent reconstruction; retaining coupling operators/multipliers and
segmentation is required for that stronger claim.

This is a proposed next run, **not launched here**. Real flooring compliance and
friction, orthotropic stock, mechanical joints, untied stability, asymmetric
loads and mesh sensitivity remain separate candidate-validation requirements.

## Replay and retained evidence

The new [diagnostic report](../fea/results/mortar_geometry_diagnostic/report.json)
binds both unchanged archives and the diagnostic source by SHA256. Its stated
scope is sampled geometry/coverage, never local-law acceptance.

```sh
uv run pytest tests/test_mortar_geometry_diagnostic.py
uv run python -m fea.mortar_geometry_diagnostic fea/results/full_frame_refinement/0.0625.tar.gz
```

Tests cover fixed-width signed/continued FRD fields, malformed/missing/duplicate
output, flat and warped master geometry, escaped/reversed/degenerate projections,
quadratic between-node penetration, and replay of the actual finest archive.
