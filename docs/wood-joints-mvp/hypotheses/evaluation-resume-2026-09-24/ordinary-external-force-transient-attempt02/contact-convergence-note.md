# Contact settlement observations and follow-up

This note preserves the attempt02 pre-run hypotheses, terminal output, and
follow-up output-method check. The attempt02 input remains frozen.

## Documented convergence condition

The pinned [CalculiX 2.23 manual](https://dhondt.de/ccx_2.23.pdf), pp. 387–388,
requires the active-contact-count flag to be zero for face-to-face penalty
convergence. The default relative count-change limit `delcon` is .001, also
documented under *CONTROLS, PARAMETERS=CONTACT (p. 443). The current deck
does not override that default. Thus a near-zero printed force residual is
insufficient for acceptance.

The current first increment's contact counts at iterations 9–14 are 18,212,
18,604, 18,108, 18,314, 16,910 and 17,584. Changes of hundreds exceed the
roughly 17–19 contact-element limit for those counts. This is consistent with
the reported nonconvergence. The log does not identify which pairs change,
nor demonstrate a perfectly periodic contact cycle.

## Model settings requiring diagnosis

The first t=.001 s force factor is 9.8506e-6, so the applied unit-wrench
resultant is only 9.8506e-6 N per external member. The largest first-increment
displacement prints as 1.831460e-8 mm. Nearly unloaded, nominally touching
surfaces switching under numerical perturbations are therefore a plausible
explanation, not a demonstrated pair-level cause.

All 35 pairs use the same linear penalty K=100000 N/mm³ across different
wood and steel interfaces. That is a numerical scenario, not a validated
common physical contact stiffness. Pairwise normal stiffness, orthotropic
orientation and local mesh scale require consideration before changing K.
The manual's stiffness guidance is not a license to assign an arbitrary
softer contact to obtain a pass.

Page 231 discusses initial overlap, slave/master mesh density and simplified
contact debugging; dynamic startup immediately includes detected overlap.
Page 17 recommends face-to-face contact with quadratic elements, which the
present model already uses. Linear pressure-overclosure and frictionless
contact also follow its suggested initial simplifications. Face-to-face
small-sliding assumptions and the nut adapter's rotation limit still matter.

## Candidate output-only follow-up

The engineering question is which interfaces prevent contact-set settlement,
and whether their changing contacts carry meaningful action. Prefer the
documented *CONTACT FILE parameters CONTACT ELEMENTS and LAST ITERATIONS
(pp. 436–437), which save generated contact elements by iteration and
last-increment displacement history. These identify contact topology and
motion; they do not by themselves provide a validated per-iteration contact
wrench. Check their actual output before assuming otherwise.

A tightly bounded output-only diagnostic can identify the changing pairs
without a custom solver build or a physical-model change. Select any later
penalty, startup-ramp or convergence-control comparison from that evidence.
Keep the cleat free and retain independent balance/energy requirements.
Do not relax the contact-count criterion solely to obtain a pass.

## Terminal observation

The first increment did converge after 18 iterations at t=.001 s, before the
600-second startup stop. Its force-dual coordinate is approximately
2.4834634e-7 mm and maximum loaded-node displacement is 1.9497639e-8 mm.
The native log reports work 1.223180e-12 N·mm, elastic energy
1.020238e-12 N·mm, kinetic energy 2.030917e-13 N·mm and contact energy
8.583830e-18 N·mm. These are far below the frozen 1e-5 N·mm diagnostic
energy floor; the printed .012881% energy residual does not establish a
meaningful-load energy pass or joint response. The result supersedes any
assumption that startup could never converge.

The native impact rules then reduced the next increment to .000302978 s.
`pilot.sta` contains no later accepted increment. `pilot.cvg` records the next
increment through iteration 10 without convergence; its active-contact count
changes from 17,732 to 22,323 across those iterations. The log does not name
which pairs changed. The `.001 s` accepted state is therefore not a meaningful
joint response, and the current run never reached an engagement result.

Docker records the container as exited at `2026-09-27T04:20:04.546153258Z`,
with exit code 255 and `OOMKilled=false`. The launch runner's final record was
not persisted, so the reason for the nonzero exit is unknown. Parent
reconciliation verified all 42 frozen input hashes and captured hashes for
the available `pilot.*` outputs in `execution.json`. No input, mechanical
acceptance, or release flag changed.

Do not perform rate/timestep comparisons on this output. Before another
## CalculiX 2.23 output known-answer check

The paired coupon in
[`contact-output-known-answer-attempt01`](../contact-output-known-answer-attempt01/README.md)
passed with the pinned 2.23 executable. Baseline and instrumented `.sta`,
`.cvg`, and `.dat` files match byte-for-byte; `.frd` differs only in its
generated time header. The instrumented run wrote 16 CEL iteration groups,
and every group's element count matches its `.cvg` row. It also wrote
`ResultsForLastIterations.frd`. The coupon output confirms that the first
three CEL nodes belong to the master and the next three to the slave, matching
the owner-mapping order used by the existing contact audit. This verifies the
writer and parser convention on the small coupon only.

The result makes a separate output-only capture on the same 2.23 external-force
patch useful. Add `CONTACT ELEMENTS` to the existing contact-file output,
preserve every physical/load input and convergence criterion, then compare
CEL group totals to `.cvg` and map node owners to the frozen pair manifest.
This can locate changing pair topology; it cannot identify per-iteration force
or prove its physical cause. Do not perform rate/timestep comparisons until a
meaningful response exists.
