# Attempt09 independent correctness review

Reviewed 2026-09-28. The frozen attempt09 package passes the bounded offline
correctness checks described here. New confirmed findings: **0** (no P0–P3
findings within scope). The two attempt08 test-coverage gaps recorded in its
pinned independent review are closed by explicit same-source and mutation
controls in attempt09.

This review is bound to attempt09 source-pins.json, SHA-256
bcbf1bc560cbf436fb0ad6547ac5e6abf10e83b849829c42eac256f66c60de62. The
attempt09 archive SHA-256 is
9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7, its
additions-only patch SHA-256 is
abaaa6d65d709edb53043619e4a974184b2ec278ef0a3e1cba9dde7c92a84e5e, and its
contract SHA-256 is
8de249a8429e43485c8ba5618ee0296fbb4ce3d551d908e9fb0e8a7be6a4a441. Attempt09
pins attempt08 source-pins.json at
998b35f0e8c885e76ea8c93435751871a07a97151ffde62f41a37479b33e00bb and the
attempt08 test-review report at
95c568b2018566ac4b2af28bd373a38ba2065481945fcdfd08a35145f13ad41f. The
companion verification.json binds this report and records the complete
artifact hashes.

The attempt08 review’s P2 hook-order gap is closed in
tests/test_patch_policy.py:20–36,146–170. The guard locates
checkconvergence and the single production iteration-link call in the same
regenerated nonlingeo.c text. Its mutant moves the link before convergence
in that text and the guard rejects it. This removes the earlier comparison
between offsets taken from different source versions. The production call
remains after checkconvergence in the regenerated source.

The attempt08 review’s P3 empty-current-set gap is closed in
tests/test_capture.py:412–469 and tests/sink_harness.c:271–295. Generation one
has one unmapped point candidate; the adjacent generation has an empty current
candidate set. The contract requires this eligible join to report
old_missing=1, and the test validates that count through the reader. It also
compiles a sink mutant that skips the join when the current candidate array is
empty; the same assertion rejects that output. This directly exercises the
previously uncovered disappearing-old-candidate path.

I independently checked all 14 packet inventory hashes. The attempt09 archive
matches the pinned attempt08 archived input. Replaying capture.patch with
patch --batch -p1 --fuzz=0 succeeds and reproduces all three pinned modified
member hashes for ccx_2.23.c, gencontelem_f2f.f, and nonlingeo.c. The existing
additions-only policy test passes; attempt09 changes coverage and contract
artifacts while retaining the same patch hash as attempt08.

The reader binds each MAP_SUMMARY step, increment, attempt, and iteration to
its GEN_BEGIN identity, rejects negative STATE_JOIN counts, and checks the
eligible state-join conservation equations against the latest map census.
The writer validates post-hook iteration/cutback transitions and closes an
invalid link as an error; the reader checks serialized attempt/control and
requires complete map/trial flags for accepted links. The offline suite
reported 39 tests passing, including the new order and empty-current mutation
controls.

The documented post-hook iit stream limitation remains: the writer validates
live post-hook iit, but ITERATION_LINK does not serialize it for an independent
reader check. The capture remains process-local and single-serial; it does not
aggregate concurrent calls, ranks, processes, or jobs. These are explicit
contract boundaries, not newly confirmed defects in this review.

All attempt09 readiness and authorization flags remain false: candidate
release, current-joint input freeze, parent readiness, production build,
Docker invocation, solver execution, and native execution authorization.
This is an offline source-and-harness review only. It does not establish
production-build, solver-integration, native-case, or joint acceptance.
No production build, Docker, solver, coupon, or joint was run.
