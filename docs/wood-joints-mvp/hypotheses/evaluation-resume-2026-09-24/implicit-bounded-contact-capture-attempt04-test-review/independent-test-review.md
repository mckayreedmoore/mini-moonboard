# Independent test review — attempt04

Reviewed 2026-09-27 (America/Denver). This review is bound to attempt04
`source-pins.json` SHA-256
`7a54d8ad4d85e278b111cc0afadd6abe3e3d77860ca9715ff87591602a2ceea4`.

I verified every hash in the packet’s 23-file inventory, all three archived
upstream source hashes, all three source hashes after patch generation, the
1,197-member archive count, and the recorded build manifest, provenance, and
binary hashes. All matched. The documented offline unit command passed 17/17
tests. I did not run Docker or invoke any solver. `review-pins.json` records
the inspected inputs and review-file hash.

## Coverage assessment

The suite binds the checked-in patch to the pinned source archive and sink,
checks additions-only source deltas, and statically follows the production
route from `nonlingeo.c` through `contact.c` to the Fortran generator. It
checks the in-loop generation-begin placement and key C hook expressions,
checks the CLI finalizer occurs once after the step loop’s output close, and
exercises a two-step sink lifecycle with one final footer. The recorded build
also pins the `-Werror=incompatible-pointer-types` caller check. These are
useful controls for the current source patch.

The mixed-pass test is a good positive reader/sink control: two ties have full
pass 1, while only one tie has pass 2, and the test checks the exact observed
FACE and MAP_SUMMARY keys. The reader also enforces full pass-1 face census,
contiguous offsets, exact face identities, per-tie pass-2 matching, summary
conservation, trial coverage, state links, event order, and footer totals.
Negative controls cover representative identity, reason, span, state-join,
acceptance, tie-count, duplicate, unclassified, span-loss, and byte-cap
failures.

The limits are that these controls call the standalone sink harness directly;
they do not execute the production Fortran generator, `nonlingeo` hooks, or
CLI. The mixed-pass case therefore validates sink and reader behavior, not
that native contact regeneration emits that case. Some production hook
assertions check counts or argument fragments rather than every Fortran/C
argument expression as an independent oracle. The CLI placement check is
static; the two-step harness exercises sink lifecycle, not the actual CLI
loop. Reader rejection tests do not mutate pass-2 face identity/offsets,
remove required record classes, or alter footer totals/flags. Error tests do
not inject file-open/write/flush failures, malformed provenance hashes, or
allocation failures. These gaps limit the suite’s breadth; the current
checked-in patch and its pins still match.

## Checker and reader findings

**Static write-policy checker gap:** `prepare_capture.py`’s C assignment scan
recognizes `=` targets, and its line-level call allowlist does not tokenize
additional side effects. I supplied an in-memory sink mutation
`ccxcap_missing_pair_();vold[0]++;`; `validate_c_capture_additions` accepted
it. The existing `vold[0]=0.;` negative fixture is rejected, but it does not
cover this write form. The pinned attempt04 sink contains no such write, so
this finding concerns the checker’s future guard, not an observed solver-array
write in the current patch. The Fortran mutation fixtures do reject the
tested `isol`, `clear`, and `xstate` assignments.

**Reader acceptance defect:** `capture_reader.py` checks the first header row,
then includes `CCXCAP` among generally known records without validating its
position or fields elsewhere. I inserted `CCXCAP\t999` before a valid
`RUN_END`, updated the footer’s pre-footer byte count, and the reader returned
`PASS_CAPTURE_STRUCTURE`. Add a regression requiring exactly one
`CCXCAP\t1` row at position zero and rejecting later schema records. This is a
reader defect and an uncovered test case; it does not indicate malformed
output from the current sink.

## Native behavior

No native solver case was run in this review. Hook execution, actual face and
trial capture, I/O behavior under solver execution, runtime overhead, and
mechanics behavior remain unverified. The 17 passing tests establish offline
source-policy and synthetic sink/reader behavior only.
