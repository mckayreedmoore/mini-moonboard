# A12-rear BG001 tie-stiffness sensitivity run preparation

This packet makes the one proposed sensitivity run reviewable for the parent.
It does not create a native freeze, launch CalculiX, or grant native readiness.
The prepared model and deck are exactly the already validated two-tie variant:

- model JSON SHA-256: `ddb65e7630eb0f6f5f44ae762eb00c61a53642122a62376f46959ccc7b1eccbb`
- deck SHA-256: `dd38c90d0aef23e109449992061e885cc79278b26bc42ab1dd1e63d58cf5383c`

The two overrides are SPR1771 and SPR1772, the BG001 left-post outer-seat
axial ties. Their effective stiffness changes from 4670.054188 to
2401.714360 N/mm (0.51428 times baseline). The one-sided tensile law, zero
gap/preload assumption, coordinate orientation, 100 mm numerical span,
force-table domain, geometry, materials, source loads, other springs, floor
MPCs and all 348 bilateral SPRING2 rows stay as recorded in `variant.json`.
This derives from local nominal-ring-case-A scenario 4 (190 GPa steel and an
uncalibrated two-equivalent-washer-diameter wood influence depth). It is one
conditional response-sensitivity point, not a calibrated property or physical
stiffness bound.

The copied floor mask has 25 selected cells and 75 inactive cells. It remains
`proposed_diagnostic_mask_only`; its pinned source screen is
`current-springa-selected-floor-branch-screen-attempt02/screen.json`
(SHA-256 `231b4fa22128bb01ae08f9bf21e6fec9ccb9c7578724781fae01a6f79856ed93`)
and is rejected as an adopted support branch. The sensitivity audit must
recheck strict normal positivity/separation and zero inactive reactions at
every accepted native increment. It cannot iterate or replace the mask. Even
if the numerical audit passes, this branch remains conditional and does not
establish release/recontact, uniqueness, floor qualification or acceptance.

The six-case program remains the project scope. This is one A12-rear
sensitivity case and cannot satisfy the other cases or establish six-case
robustness. It also does not claim the standard 711 case-context validator:
the parent-reviewed response-core fork uses the exact sealed sensitivity input
contract because this legacy A12-rear branch does not supply the standard
all-bearing controls context.

`prepare_readiness.py` checks the exact prepared inputs, prior input-verifier
result, parent method-review result, solver profile and source hashes. It also
copies source-code/method snapshots into `sources/`. Run it after reviewing
these artifacts:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-rear-bg001-seat-stiffness-run-readiness-attempt01/prepare_readiness.py
```

The generated `readiness-contract.json` and `source-snapshot-manifest.json`
are preparation evidence only. For a parent-owned freeze, create a new
attempt directory, copy the prepared `model.json` and `model.inp` byte for
byte, copy this packet's `sources/` tree, and copy
`source-snapshot-manifest.json` to the run root as
`readiness-source-snapshot-manifest.json`. Do not rebuild the model through
the standard structure serializer: the sealed sensitivity validator requires
these exact bytes. The parent freeze should use schema
`wood_joint_reduced_native_freeze/v1`; bind `files_sha256` to both exact model
and deck hashes and to `readiness-source-snapshot-manifest.json`, and use the
`source_snapshots` entries in that manifest for `source_sha256`. Also bind the
readiness contract itself using its repository-relative path and SHA from
`readiness_contract_snapshot`. Copy each listed source to the matching
`run-directory/sources/<repository-relative-path>` location so the standard
runner can verify live and frozen source bytes. Include the pinned 2.23 solver
profile, this single A12-rear/BG001 sensitivity scope, candidate and geometry
revision. Set `native_solve_executed` and `mechanical_acceptance` to false. The
readiness contract records the complete fields and hashes. The parent must
independently audit the concrete freeze and recheck the serialized native slot
before launch.

After the parent writes an independent `parent-readiness-review.json` bound
to that exact `freeze.json`, the one permitted launch command is:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 -c 'from fea.wood_joint_reduced_native import launch; print(launch("<frozen-run-directory>", "a12rear-bg001-stiffness-sensitivity-attempt01", "<frozen-run-directory>/parent-readiness-review.json", timeout_seconds=240, memory="4g"))'
```

This uses the existing serialized runner and ledger. A fresh run directory and
run ID are required; there is no automatic retry.

If and only if that execution is successful and terminal, the post-run fork
audit checks the frozen input hashes, solver provenance and unchanged physical
gates, then writes `response.json` next to the native output:

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-a12-rear-bg001-seat-stiffness-run-readiness-attempt01/audit_variant_run.py <frozen-run-directory>
```

Then run the independent all-50-body/global force-and-moment check from its
frozen source snapshot (it writes its audit beside that snapshot):

```sh
OPENBLAS_NUM_THREADS=1 uv run --no-sync python3 <frozen-run-directory>/sources/docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-springa-selected-floor-parent-response-audit-attempt01/check.py <frozen-run-directory>/model.json <frozen-run-directory>/response.json
```

The fork rechecks every source SPRINGA law and table domain, the two changed
tie laws, all MPCs, the 348 bilateral components, the provisional floor mask,
and every body and global balance at every increment. The independent parent
check separately recomputes the 50-body and global printed/rounding-interval
resultants. A failed gate means no variant force demand is exported. A pass is
only a conditional A12-rear response at this one stiffness point; it is not a
joint-capacity finding, physical stiffness bound, six-case pass, or design
acceptance.
