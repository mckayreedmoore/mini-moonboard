# Current checkpoint: flush floor-runner development

`compact-floor-flush-development` is selected. Authority promotion, frozen
criteria and nominal FR-3 shop geometry are complete. Two fresh no-slip cases
pass 36 adopted checks each; A12-forward fails numerical contact convergence
after three bounded searches, so the remaining cases and aggregate evidence
remain pending. See the [case log](floor-runner-mvp-case-log.md). Historical finite-friction, tapered-runner and
spliced-knee results do not transfer. See the [MVP master
plan](floor-runner-mvp-master-plan.md) and [criteria
ledger](floor-runner-mvp-criteria.md). This is not a fabrication release.

## Preserved spliced flush-top checkpoint

The following checkpoint is historical and describes
`compact-spliced-flush-top-development`.

Six fresh assembled no-slip cases meet the listed conditional criteria. The
maximum adopted nominal lateral ratio is 0.746. The tightest directional
placement margin is 0.361 mm and minimum group-spacing margin is 1.9 mm.
Full-root lateral sensitivity exceeds 1.0 in four cases (maximum 1.081), and is
not adopted. This remains engineer-unreviewed conditional evidence, not an
unconditional rating or construction release. Retained ML24Z/SDS separation
capacity and independent flange-couple applicability remain an open completion
gate. Historical floor-flush/taper and
compact-spliced-kicker evidence is preserved and does not transfer.
The [online angle-options review](compact-spliced-flush-top-angle-options.md)
found no catalog-only larger ML angle or screw substitution. Written
applicability for the unchanged ML24Z assembly is the shortest completion path;
otherwise a connection redesign and fresh affected cases are required.
No push is authorized; local commits follow the repository time rule.

## Preserved floor-flush checkpoint

The following is historical. References to current selection, unfinished gates
or verification counts apply to the preceding floor-flush investigation, not
the compact spliced flush-top candidate above.

### Revised native checkpoint

The A12 left-load continuation converged normal contact and the explicit
Coulomb force law at a maximum residual of 0.009729 N. All 482 native artifact
hashes and 211 source hashes were verified. The archived result is
`fea/results/clear-space-floorflush/a12-left/`; preceding exhausted searches
remain preserved. Numerical acceptance does not establish design completion.

The current assessment meets 37 of 38 implemented criteria; the existing rim
end-cut screen fails. Bolt lateral ratio is 0.8792, sampled net-member ratio
0.7488 and explicit timber face-bearing ratio 0.1196. See
[fresh assessment](floor-flush-a12-left-assessment.json). The independently
reviewed native model retains gross rim end assumptions and finite contact
penalty/sampling; it is not an exact solid model of all cuts and bolt bores.

The [cut-method review](flush-cut-method-review.md) distinguishes the terminal
seat screen from the NDS support-edge measurement. Nearby cut-side tension
prevents assuming the compression-only rule applies. The
[taper review](taper-method-applicability-review.md) also identifies a tensile
corner on the actual side taper and missing local resistance justification.
These are open technical gates, not documentation-only qualifications. Remaining
cases should follow a supported disposition of this first case, rather than
accumulating results for a detail still failing its adopted screen.

### Local verification checkpoint

The default suite passed 547 tests with 15 historical tests deselected. Five
subsequently added construction/analytic-diagnostic tests passed separately.
The six-candidate browser check passed, and the selected candidate's two loose
crash pads passed their browser checks. Current documents and construction
manifest are reachable from the local viewer. The selected frame mass is
210.575 kg, excluding pads. These are implementation/artifact checks, not a
structural release.

## Preserved preceding checkpoint

The following is historical. Its references to "current" or "selected" apply
to the candidate described there, not the flush revision above.

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
