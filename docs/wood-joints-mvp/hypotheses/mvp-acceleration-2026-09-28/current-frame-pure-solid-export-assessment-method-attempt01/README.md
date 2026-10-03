# Current-frame pure-solid sparse export assessment method — attempt01

## Bounded result

This packet provides a sparse reader and post-export assessment for the
parent-owned pure physical-solid MATRIXSTORAGE export proposal. It can check
the emitted .dof map against the pinned 12,549-node source inventory, read the
.sti upper triangle into SciPy CSR without assembling elements, and assess
disconnected-body operator structure plus six kinematic rigid fields for each
of the 50 physical bodies.

The packet contains no current-frame .sti or .dof output. It has not launched
CalculiX, frozen an input, assembled current-frame stiffness, projected
constraints or connectors, or assessed gravity. The earlier
[pure-solid export proposal](../current-frame-pure-solid-matrix-export-preflight-attempt01/README.md)
remains unchanged and input-only. Parent retains exact freeze and native
execution ownership.

The source model is candidate
compact-floor-flush-wood-joints-development, geometry revision
led-clearance-2x6-runner-seated-blocks-v1, case a12-rear. The method preserves
the exact source physical node IDs and coordinates; it does not edit geometry.

## Reproduce parser fixtures

Use the repository virtual environment, where NumPy and SciPy are available:

    OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py --verify-fixtures

This verifies the pinned input/output source hashes, reparses the completed
free C3D20 cube export, checks its 60-label map and 1,830 unique upper-triangle
pairs, and compares rigid-field residuals and analytic shear energy. Synthetic
tests cover signed off-diagonals, symmetric reconstruction, duplicate pairs,
lower-triangle rejection, index bounds, diagonal completeness/positivity,
non-finite values, malformed triplets, and .dof missing/duplicate labels.
The cube's separate parent-owned execution provenance is pinned as a source
artifact but is not re-verified by this reader.
The recorded replay used NumPy 2.5.2 and SciPy 1.18.1.

The fixture replay is a read-only parser/known-answer check. It does not invoke
CalculiX or produce a frame result. Its captured output is
[fixture-results.json](fixture-results.json).

## Use after the separately owned frame export

After a parent-frozen export is run and its execution provenance is checked,
pass the job base name to the reader:

    OPENBLAS_NUM_THREADS=1 .venv/bin/python docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-frame-pure-solid-export-assessment-method-attempt01/assess_matrixstorage.py --assess-matrix /path/to/job-base

The reader looks for job-base.sti and job-base.dof and emits JSON on stdout.
It also checks the source model against the packet's exact source pins. The
reader does not decide whether those matrix files came from an approved run;
parent freeze and execution records must bind their hashes to the exact deck.

The assessment requires:

- Exactly 37,647 unique node.direction labels, bijective with the 12,549
  physical source node IDs and directions 1, 2, and 3.
- A single one-based upper triangle, with no repeated pair, finite values, one
  strictly positive diagonal entry per equation, and exact symmetry after
  reconstruction.
- No nonzero stiffness coefficient between DOFs owned by different physical
  bodies.
- Six source-coordinate rigid fields per body: three 1 mm translations and
  three 1 rad rotations. Rotations use the arithmetic mean of that body's
  exact source mesh-node coordinates as their origin. This is a kinematic
  origin, not an asserted mass or volume centroid.

Each residual is

    ||K_body v||_infinity / (||K_body||_infinity-row-sum * ||v||_infinity)

The recorded tolerance is 1e-8. The operator scale is reported in N/mm; the
residual numerator and normalized denominator are both in N. The method
reports all six residuals for each body, their mode amplitudes, and the scale
used.

## Limits

Passing these checks only verifies sparse map/structure and the body's six
rigid kinematic fields. It does not establish exact full-stiffness rank,
positive definiteness on a deformational subspace, absence of internal
mechanisms, or a gravity-compatible equilibrium. In particular, six small
residuals do not prove that these are the only null modes.

The assessment is for the unloaded pure physical-solid operator. It does not
apply the nonphysical auxiliary density to gravity, recover the permanent
MPC/SPC expansion, map physical loads, assemble springs, impose floor stick,
select unilateral contact states, or construct a constrained frame tangent.
It is not a frame-readiness or design-acceptance result.
