# Attempt05 architecture review

Reviewed 2026-09-28 against repository `AGENTS.md`. Scope was the attempt05
source-delta package and its pinned CalculiX integration context. No earlier
review reports were consulted. This is a static architecture review; I did not
run the offline tests, build CalculiX, invoke Docker, or run a solver or coupon.

## Hash binding

The worktree was dirty, so this review is bound to the attempt05 packet pins,
not to the branch name. SHA-256 of `source-pins.json` is
`a671a0c53266cfae4986c403d63fb31c9180c8fafbf885e5018e52621efb2570`.
I independently recomputed and matched every entry in that file's
`packet_file_inventory` (14 files). Key inputs are:

| Input | SHA-256 |
| --- | --- |
| `build/context/source.tar.bz2` | `9c88385c10fb04f5dc6c4e98027a51bebdd8aee3920e05190d6c1dd08357d6e7` |
| `build/context/capture.patch` | `e536c707f83c9ef11ffdfc55480d750ffd7b9dc68a73abd3e72c648eb20b4dba` |
| `capture-sink.inc` | `8ca64a40d8f5c4a093cd0750b9c31de85109dc9acc3158cb8502a5b512907a52` |
| `capture_reader.py` | `ab2d466508895e28a4e45656f60bbd0aee6b27997fc5378d6f9044333223a1e4` |
| `prepare_capture.py` | `030745d7701b4517f428bc31010b9b2c2f275d4da0af20df8c4b07f0d8def090` |
| `capture-contract.json` | `6bc77a005a1f21cf83c77d7bf47514030e8fe4e7d35562629b28971b7a12db38` |

## Assessment

The package has a clear offline-only boundary and a generally coherent
instrumentation architecture. The patch is regenerated from a pinned source
archive, targets three upstream files, and checks that upstream changes are
additions-only. The C sink is appended to `nonlingeo.c`, which keeps the
candidate from requiring another production build target; the tradeoff is a
large, single translation-unit module with hand-maintained C/Fortran ABI
declarations. The preparer narrows this risk with explicit caller and sink
write-target policies, but documents that these are bounded lexical checks,
not a C parser.

The job-level sink lifecycle is well separated from per-step work: it opens an
exclusive sibling temporary, flushes generation records, writes one footer at
the top-level job boundary, checks final flush/close, and uses a no-overwrite
hard link for publication. I/O failures leave the configured path absent;
structural failures can retain an error capture for rejection. The documented
lack of `fsync` and hard-link filesystem requirement accurately limits the
publication claim.

The writer and reader agree on the 250,000 candidate-row limit across pass 1
and all observed pass-2 rows per generation. The writer applies the limit to
the single generation candidate buffer; the reader independently totals
`MAP_SUMMARY` candidates per generation and also reconciles them against live
face spans and `GEN_END`. Pass 2 is correctly modeled as an optional per-tie
observation: the writer compares observed rows to pass 1, and the reader checks
the same identities, offsets, spans, and status while requiring summaries only
for observed groups.

Scope and readiness are explicitly bounded. The contract disclaims search
completeness, current-joint applicability without parent rebinding, first local
bearing, force history, work, whole-model energy balance, and structural or
joint acceptance. `source-pins.json` records no patched solver build or solver
run; the README also states that prior unmodified coupon output does not test
the instrumentation. These boundaries are appropriate and should remain
attached to any later result.

## Ranked finding

**P2 — Capture can start outside the implicit branch whose iteration hook closes it.**

`capture.patch` calls `ccxcap_generation_begin_` whenever `*mortar==1`, without
checking the execution-mode flag (`capture.patch`, lines 20–26). The matching
`ccxcap_iteration_link_` insertion sits immediately before the `}else{` that
closes the pinned `nonlingeo.c` `if(*iexpl<=1)` branch (`capture.patch`, lines
70–76; pinned source archive, `nonlingeo.c`, original lines 3321 and 3461).
Thus, if a face-to-face explicit route (`*iexpl>1`) reaches the instrumented
contact regeneration with the capture path enabled, it can set `pending` and
write generation records but skips the only iteration-link call. The job
footer is then incomplete (`capture-sink.inc`, lines 596–617), and the reader
rejects the missing link (`capture_reader.py`, lines 468–490). This fails
closed rather than producing a passing capture, but it makes mode selection an
implicit operator requirement and can leave a published incomplete sidecar.

Bind capture activation to the same implicit-mode scope, for example by
guarding the generation-begin call with `*iexpl<=1` as well as `*mortar==1`,
and add a lightweight control that confirms an explicit route does not start a
capture. Keep explicit execution outside the accepted contract unless its
iteration lifecycle is deliberately brought into scope.

## Finding disposition

No architecture finding was identified in the job-finalizer placement,
temporary-file publication policy, combined candidate-cap contract,
pass-2 writer/reader agreement, or documented mechanics/readiness limits. The
P2 mode-boundary issue is the only ranked finding. The package remains an
offline source-delta proposal; pinned offline-test status is evidence about
the harness and contract only, and native ABI/runtime behavior remains
unqualified until the parent-controlled build and validation gates are run.
