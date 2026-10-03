# Two-cell reset fixture: historical-source replay

The original two-cell `--verify` stops on its frozen AGENTS.md hash because
the September 30 repository policy adds exclusive-master workflow. Parent
checked that change with `git show 596a8034 -- AGENTS.md`; it changes no
fixture mechanics. The old verifier, input, output and source pins are
preserved. This packet does not silently replace the original policy pin or
claim the original CLI passed.

The [replay](replay.py) authenticates the old policy against Git commit
`33d0e129` and all three other source pins against current files, then runs
the unchanged fixture core and requires byte-identical historical output.
All eight stages pass their existing known answers, unique normal masks,
equilibrium, open-tangent release and reference-reset assertions. Current
policy is separately recorded in [assessment.json](assessment.json); it
remains the authority for future work.

This fixture's normal and tangent coordinates are separate. Its reset uses
the preceding open-stage coordinate. It does not validate a continuous
contact-event reference for the coupled frame. The proposed gravity-settle
then climber-ramp scenario still needs coupled state selection, event
localization/refinement and explicit no-state/multiple-state/cycle stops.
No native solve, frame response or joint acceptance follows.

Read-only replay from repository root:

```sh
python3 docs/wood-joints-mvp/hypotheses/mvp-acceleration-2026-09-28/current-two-cell-historical-source-replay-2026-10-01/replay.py --verify
```
