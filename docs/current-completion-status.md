# Current completion checkpoint

- Selected exterior candidate: six current cases pass all 25 listed conditional
  criteria; separate 5×5 left-load sensitivity passes. Current evidence is
  `fea/results/clear-space-exterior/` and `fea/results/exterior-revised-grid5/`.
- Two 96×36×5-inch crash pads are implemented and browser-verified, separate
  from structural geometry, weight and support calculations.
- Square recessed-runner trial remains unaccepted: local sharp-notch
  resistance was not established. Its actual cut-section ratio was 0.567;
  the 1.146 artificial full-height narrow-band diagnostic is not the actual leg.
- New `compact-floor-taper-development` uses a 457.2 mm 1:12 runout, keeps full
  2×6 runners and intact kickers. All 24 bolt receivers fit; 16 focused
  geometry/mesh/runner/resistance tests pass. All six current native cases meet
  all 35 listed conditional criteria. Maximum bolt lateral ratio is 0.928189
  (A12-forward); maximum sampled net-member ratio is 0.630641 (A12-left).
  See [the taper study](floor-runner-taper-study.md) for the case table and limits.
  Exterior remains selected; taper is a separate evaluated alternative.

Reproduction uses `scripts.clear_space_batch floortaper --friction-mu .4`
with the required geometry, native-prefix and archive-root arguments. Each
case archive under `fea/results/clear-space-floortaper/` retains its search
controller and history. Preceding or mirrored floor states only seed the search;
every case has an independently converged native response and assessment.
Viewer and construction artifacts are regenerated from these six results;
weight metadata authenticates the exported inventory. Crash pads are excluded.

Verification after resuming the interrupted session:

- Default test suite: 534 passed, 15 deselected.
- Independent six-case audit: all 35 criteria pass per case; all 1,760 native
  artifact hashes match, with matching archived reports and current sources.
- Taper export and construction packet regenerated; source hashes match.
- Browser checks cover the five candidate inventories and both crash pads.
- Full-root hardware sensitivities remain separate from the adopted criteria;
  see the taper study for their failing ratios and installation implications.

All current work is local. The owner explicitly retained the publication-hour
rule and requested local commits only: do not push. Monday–Thursday local
commits must also wait until 18:00 America/Denver. Do not assign artificial
author or committer timestamps. A staged binary recovery patch is saved at
`/tmp/mini-moonboard-completion-checkpoint.patch`.
