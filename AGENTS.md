# Repository working agreements

## Agent workflow

- Automated agents may work and commit locally at any time. Publish outside
  Monday–Thursday 07:30–18:00 America/Denver, accounting for daylight saving.
- Configure the local workflow guard with `git config --local core.hooksPath
  .githooks` after preserving any existing hooks. The guard applies to pushes
  from this configured clone; it is not agent identity detection or a scheduler.
- Preserve other contributors' work and verify remote state before publishing.
  History changes require explicit user direction, a local recovery reference
  and verification that only the requested metadata or content changed.

## Current hardware decision

For the next MVP candidate, use ordinary wood screws for face and kicker
panels and retain through-bolts/nuts. Retain manufacturer-specified structural
screws in commercial brackets. Do not include threaded inserts in new-build
panel connections. Inserts may be evaluated as a later worn-hole repair, with
receiver geometry and connection resistance checked for that repair; they are
not an automatic substitute. Preserve historical insert variants and evidence.
Keep a single-2x6 development baseline even when tests fail; record failures
and enlarge members selectively or revise connections. Do not double-stack
2x6s or introduce built-up substitutes. Prefer square-cut principals and open
LED access over the former lower housing and continuous relieved backing.
Reserve possible future insert space around panel screws without predrilling it.
The first revised layout/render keeps all lumber, including the header, single
2x6 even when bearing fails; larger stock remains a later option.

The preserved all-2x6 baseline is `single-2x6-development`: one center
principal/post and one middle rail per bay. Earlier square-2x6 variants retain
paired seam framing despite their single-stock descriptions. Check assembled
adjacency as well as individual stock sizes; do not call those variants unstacked.

The current `selective-2x6-development` retains nine single 2x6 members and
selectively uses four single 3x6 shared receivers and one single 2x10 header.
This addresses fit defects only; no strength or floor qualification transfers.

## Communication

Keep chat concise. Documentation, website text, code and commits use normal prose.
Preserve changes belonging to other agents, including untracked files.
