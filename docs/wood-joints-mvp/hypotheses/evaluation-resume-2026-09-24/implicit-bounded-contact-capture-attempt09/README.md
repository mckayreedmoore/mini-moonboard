# Implicit bounded contact capture — attempt09 coverage closure

Attempt09 is an offline-only test-coverage update based on the exact attempt08
archived CalculiX source input. The archive SHA-256 is
`9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7`; attempt08
`source-pins.json` is
`998b35f0e8c885e76ea8c93435751871a07a97151ffde62f41a37479b33e00bb`, and its
patch is
`abaaa6d65d709edb53043619e4a974184b2ec278ef0a3e1cba9dde7c92a84e5e`. The
attempt08 independent test-coverage review is pinned at
`../implicit-bounded-contact-capture-attempt08-test-review-2026-09-28/report.md`,
SHA-256 `95c568b2018566ac4b2af28bd373a38ba2065481945fcdfd08a35145f13ad41f`.
Attempt09 preserves attempts01–08 and every prior review artifact.

The production hook-order control now finds both `checkconvergence` and the one
`ccxcap_iteration_link_` call in the same regenerated `nonlingeo.c` text. It
also creates an in-memory mutant with the link moved before convergence and
asserts that the order guard rejects it. The source patch itself remains an
additions-only delta regenerated in full from the attempt08 archived input.

A two-generation sink fixture now starts with one prior unmapped candidate and
then presents an empty current candidate set under the exact adjacent state
join. The test requires generation two's tie-one `old_missing` count to equal
one. It compiles a sink mutant that skips `wjcc_join_previous()` when the
current candidate array is empty and verifies that the same assertion rejects
the mutant. This directly covers disappearing old candidates; the earlier
empty-prior/new-missing and zero-to-zero controls remain in the suite.

Run the offline controls from this directory with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest discover -s tests -v
```

The suite contains 39 tests and compiles only standalone sink harnesses. The
complete additions-only patch is regenerated from the pinned source archive,
then replayed with `patch --batch -p1 --fuzz=0`; all modified source-member
hashes are compared with `patch-preparation.json`. No production build, Docker
invocation, solver execution, coupon, or current-joint input freeze was
performed.

The sink remains process-local and single-serial. It does not synchronize
concurrent hook calls or aggregate multiple ranks, processes, or jobs into one
sidecar. One stream-format limitation from attempt08 remains: ITERATION_LINK
serializes captured iteration but not post-hook live `iit`, so the writer checks
the latter against the pinned source while the reader cannot independently
repeat that check. Readiness, production build, solver execution, and native
execution authorization remain false; fresh independent review and parent-owned
validation are still required.
