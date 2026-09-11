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

Develop threaded inserts with machine screws for removable face and kicker
panels where receiver geometry and connection resistance support them. Retain
existing through-bolts/nuts and manufacturer-specified structural screws in
commercial brackets. Do not claim inserts are installed, qualified or build-ready
before the model, hardware schedule and checks are updated. Existing screw-based
variants and their evidence remain historical screw-based designs.
Keep a single-2x6 development baseline even when tests fail; record failures
and enlarge members selectively or revise connections. Do not double-stack
vertical 2x6s or introduce built-up vertical substitutes. Paired horizontal 2x6
rails are now permitted to give adjacent face panels separate screw receivers;
provide each rail's connections and do not assume composite action. Prefer square-cut principals and open
LED access over the former lower housing and continuous relieved backing.
Reserve possible future insert space around panel screws without predrilling it.
The first revised layout/render keeps all lumber, including the header, single
2x6 even when bearing fails; larger stock remains a later option.

The preserved all-2x6 baseline is `single-2x6-development`: one center
principal/post and one middle rail per bay. Earlier square-2x6 variants retain
paired seam framing despite their single-stock descriptions. Check assembled
adjacency as well as individual stock sizes; do not call those variants unstacked.

The preserved `selective-2x6-development` retains nine single 2x6 members and
selectively uses four single 3x6 shared receivers and one single 2x10 header.
This addresses fit defects only; no strength or floor qualification transfers.

The preserved `paired-rail-base-development` replaces the two 3x6 middle rails
with four independently clipped 2x6 rails and adds an ML24Z between the center
principal side and header top. Center principal/post remain single 3x6 stock.
The header's rearward load transfer remains unresolved. The render still uses
ordinary panel screws; the insert direction above requires a separate modeled
and checked hardware revision. Historical results do not qualify this assembly.

The current `vertical-principal-development` removes middle rails and adds
four independent full-height 2x6 principals with aligned single 2x10 posts and
explicit connections. Top rail, split bottom backing and header remain. Retain
existing gussets and bolts until actual joint-force analysis justifies changes.
The four face panels retain unconnected horizontal seam edges between framing;
do not tie those edges in analysis or transfer older strength/floor acceptance.

## Communication

Keep chat concise. Documentation, website text, code and commits use normal prose.
Preserve changes belonging to other agents, including untracked files.
