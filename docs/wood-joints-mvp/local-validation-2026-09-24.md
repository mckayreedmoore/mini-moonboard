# Local validation checkpoint, September 24, 2026

Status: work in progress, uncommitted during repository quiet hours. This
checkpoint does not claim that the full CI sequence passes.

## Resumed session checkpoint

The old full-suite process stopped at session reload. Its log reaches about
46%, contains nine failure markers, and has no final summary. A tentative
cache-order mapping selected nine tests for reproduction; seven failed and
two passed, so that mapping does not identify all nine original failures.
The new [triage note](test-triage-2026-09-24.md) records actual tracebacks and
repairs. The full suite still needs a completed run; do not call it passing
or still running on the basis of the old log.

The parent independently ran the material and equilibrium helper batch:
18 tests passed in 1.58 seconds. Those helpers remain preparation-only, and
subsequent edits require focused revalidation. The first representative steel
mesh completed and its separate deck audit passed; see the
[mesh evidence](hypotheses/wj04-hardware-patch-mesh/README.md). None of these
checks is a fresh structural load case.

## Parent follow-up at 15:53 Denver

The current full-suite process, started at 15:37 with `uv run --no-sync
pytest -q --tb=short`, remains live. Its log is
`/tmp/wood-joints-full-pytest-20260924-1537.log`; the observed progress exceeds
43% and includes a failure marker. This is not a completed test result.

After the material and wrench portability edits, the parent ran the five
focused files for wood materials, steel materials, equilibrium, wrench
operations, and the independent mesh Jacobian audit: **49 passed in 1.52
seconds**. This verifies the helper contracts covered by those tests; it does
not establish physical joint behavior.

The corrected WJ24 access-relief attempt03 completed in 55.0528 seconds with
the exact archived baseline composition reproduced and producer/test hashes
unchanged through execution. Its geometry scenarios retain the original
candidate and all release flags remain false. The current WJ24 five-body
representative STEP export also completed; historical WJ16 mesh results are
not substituted for that new geometry.

## Owner-directed stop for design review

The owner requested a 3D model MVP and design adjustments before further
engineering calculations. The parent interrupted the live full-suite process
with SIGINT and preserved its log. The terminal result was **20 failed,
2,093 passed, 16 deselected, and 9 errors in 2,499.37 seconds**, followed by
`KeyboardInterrupt`. This is an interrupted run, not a complete-suite pass.
Its failures have not yet been triaged from this final trace. Do not restart
engineering testing or calculations while the owner reviews the model.

The local viewer and scene both returned HTTP 200 on port 8765. The live CAD
session remains idle so the model can be adjusted after owner feedback.

## Preserved earlier checkpoint

The required command `uv run --no-sync python -m scripts.current_candidate
--check-exports` exits 1 before rebuilding exports, with:

```
Stale geometry source snapshot: mini_moonboard/compact_floor_flush_frame.py
geometry does not identify current model revision
```

The current model file has no working-tree changes. Its SHA-256 is
`8764bec57564efa79f2636e589aa0e35b229c48975c791eec5c47b20183bf17a`;
the selected geometry and its preserved source ZIP instead bind
`4cc03e086b381de2cd04685578bfccccfa72ee6e3545814d8e2469a3196de045`.
The parent read the model and geometry directly from Git at both current HEAD
`ec33d9c5` and the wood-lane handoff
`df7f5eca86ae831b35a8bcf9e6dcd7ae8af852bb`; both have this identical mismatch.
Commit `7cdd2e37ed2d364b47879a960b9eb15b93c67048` on September 17 moved the two
`clip_split_base_center_*` stations and rebuilt their receivers. Its message
explicitly records that the frozen six-case snapshot retains the former
station. This is a pre-existing baseline evidence mismatch, not a new
wood-joint regression or an accepted geometry change in an old solve.

Keep the check failed. Do not change hashes in historical geometry to make
it pass, weaken the checker, or claim a current baseline solve. The wood
candidate requires its own fresh complete-layout evidence regardless. This
checkpoint does not authorize native work on the selected baseline.

The independent `scripts.wood_joint_authority_integrity` preservation check
passes: both selected/barrel authority files and all 725 selected kerf-right
export bytes still match the handoff. That narrower result proves byte
preservation, not baseline model/evidence agreement. The repository CAD smoke
test also passes (CadQuery 2.8.0, OCP viewer 4.0.1, STEP round trip).

The mesh and top-center focused batch passes 37 tests. The final bottom-outer
batch passes 17, bottom-center 10, and surface classifier 8. Their focused
Ruff checks and the working-tree whitespace check pass. The complete-layout
compositor now passes eleven focused tests; the hardware inventory and
representative physical hardware each pass seven. The complete WJ24
composition passes all eighteen implemented static/source checks, while
explicit contact and access findings remain open. The parent hardware audit
also verifies 64 contained metal solids and 64 finite opposed seat pairs
across the two response-only profiles.

Whole-repository `uv run --no-sync ruff check --no-cache .` passes at this
checkpoint. The full default `uv run --no-sync pytest -q` was started after
the completed composition and remains in progress; observed failures have
not yet been triaged. Do not report a full test pass. Each archived diagnostic
separately records its precise source and input hashes, scope, and remaining
gates; passing tests do not turn contact/access findings into accepted joints.
