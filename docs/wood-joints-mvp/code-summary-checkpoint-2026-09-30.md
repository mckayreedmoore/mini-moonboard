# Code and summary checkpoint — September 30, 2026

This checkpoint publishes ongoing implementation, experiment source, tests,
build configuration and Markdown reports for the reviewed
`compact-floor-flush-wood-joints-development` revision
`led-clearance-2x6-runner-seated-blocks-v1`. It is a work-in-progress source
checkpoint, with unresolved validation issues recorded below.

The owner requested code and result summaries only. Raw solver outputs,
matrices, nodal/contact/time histories, generated CAD and mesh datasets,
JSON/CSV evidence packets, generated mesh/contact membership and mapping
tables, raw logs, source archives and copied evidence snapshot directories
remain local. Existing published history is preserved.
Reports retain their historical paths and hashes; detailed local evidence
links are consequently unavailable in this branch. This publication is not
a self-contained replay bundle for every experiment.

The [September 29 coordinator checkpoint](hypotheses/mvp-acceleration-2026-09-28/LUNA-MAX-COORDINATOR-CURRENT-CHECKPOINT-2026-09-29.md)
records no accepted path-complete six-case member/joint demand set and all 47
criteria pending. Its scope and supersession rules remain applicable. The
[development index](README.md) routes to the current continuation records.

The [September 30 upper-frame review](hypotheses/upper-frame-joint-review-2026-09-30/README.md)
adds bounded action extraction and conditional component comparisons for four
upper blocks and sixteen bolts. It accepts no complete joint and closes no
formal strength criterion.

Validation performed for publication on September 30:

- The NDS group-action and washer-response test modules pass: 66 tests.
- The upper-frame report and independent output-token checker both verify
  against the existing local frozen outputs. The checker reconstructs 336
  lateral actions and 672 signed member directions; this verifies export
  reconstruction and does not accept a complete joint or six-case envelope.
- Python syntax review passes for all 675 source files in the refreshed
  checkpoint. An earlier mismatched bracket in the native-mapping preparer
  was corrected in the shared workspace before publication.
- Ruff on 140 changed source files under the maintained-entry-point
  directories reports 151 findings across 72 files. The lint gate is open.
- Artifact replay tests require omitted local inputs. Previous source-only
  replay checks failed at those missing inputs, and older frozen WJ-08
  geometry/criteria checks detected method-map pin drift. Full CI and replay
  acceptance are not claimed.

Frozen experiment source was preserved rather than reformatted to satisfy
lint. No native job was launched or candidate geometry changed for this
publication. Joint acceptance, engineering completion and fabrication release
remain open.
