# A12-left ideal-stick branch cycle and method boundary

## Finding

The recorded A12-left 10-cell and 11-cell support proposals form a strict
two-state recurrence at SPR1302. The frozen attempt02 10-cell branch predicts
11 strictly positive normals, so the normal-positive update adds
`floor_lumber_leg_left_1`. The frozen attempt03 11-cell branch predicts the
prior 10-cell set, so the same update removes that cell. This happens at all
seven reported load factors; the other 99 normal classifications agree at
each factor. Both native runs returned zero and reached factor 1, but each
proposed branch is rejected by its parent response assessment. A converged
fixed-mask solve therefore does not certify the support mask.

For SPR1302 at factor 1, the 10-cell run has a strictly positive projected
normal elongation interval `[0.00050569145, 0.00050569155] mm` and internal
force interval `[92.400545, 92.400555] N`; its input omits the cell. The
11-cell run has a strictly negative elongation interval
`[-0.0051027775, -0.0051027765] mm`, a zero table force, and an endpoint
internal-force interval containing zero; its input selects the cell. All
intervals remain sign-separated in the other six states. These are exact
source-bound classifications with rounding guards, not inferred from an
unrounded sign.

There was one draft source-pin error during preparation. The hash
`204c1402c145d7f29c16314fc6f2f8231a9bbbc1f58eb2a9d100fb5aeaf8b9bf` belongs
to `current-springa-selected-floor-a12-forward-attempt03/freeze.json`, as
confirmed by that file's current bytes and the A12-forward readiness and
diagnosis records. It was mistakenly assigned in an early draft to the
A12-left attempt03 freeze. The current A12-left freeze is
`9bc1bce4fcb681f48f2d528c7a72c6a0d5ddecbf34253e5cc850c6e165b446c3`; its own
authorization, parent readiness review, and source-bound cycle diagnosis all
record that value, and all 140 current freeze source entries rehash cleanly.
No archived A12-left freeze preimage with the `204...` hash was found, and
there is no evidence here of a post-run change to the A12-left freeze. The
forward-case files are pinned below only to identify the mistaken hash's
origin; no forward-case result or force is used.

In the deck/model, every normal carrier remains a one-sided SPRINGA with
`F = k max(q, 0)` in its recorded normal axis. The two selected tangent rows
for this cell are exact linear equations: source rows
`floor_lumber_leg_left_1_friction/local-dof-2` and
`.../local-dof-3`, mapped to global `+Y` and `-X`, tie the body point to a
fixed floor reference. They are present only when the cell is in the selected
mask. Their Lagrange reactions have no finite bound or constitutive link to
the normal force; the current lane's no-slip floor assumption is therefore a
conditional ideal constraint, not a Coulomb friction law. The one-sided
normal spring and the exact tangent-row gate are coupled: adding a tangent row
can change the normal spring's sign, which can then demand that row be
removed.

## Static branch and algorithm boundary

The 10-to-11-to-10 result disproves “replace the mask by the strictly positive
normal set” as a convergent algorithm for these A12-left branches. It proves
that neither of these two tested masks is self-consistent at the seven
reported states. It does not prove that no other 100-cell mask can be
self-consistent; the full mask space was not exhaustively searched.

There is no general existence result to transfer automatically. Classical
frictionless Signorini contact is commonly posed as a variational inequality
over a convex admissible set, with existence under specified hypotheses. That
result does not cover the added contact-dependent exact stick rows or their
unbounded reactions. Frictional-contact work instead formulates normal and
tangential conditions together as complementarity or nonsmooth systems, and
reports local convergence under its own constitutive and solver assumptions.
Neither class of theorem or convergence result directly proves existence or
convergence for this adapter's ideal `q>0 => t=0` gate.

A separate source-bound K12-right report records the independent sequence
right01 original10 → right02 updated10 → right03 selected11 → right02
updated10, with only `floor_lumber_leg_right_0` / SPR1311 toggling in the
right02/right03 recurrence. Its 700-row report has 65 external source pins,
all rehashed cleanly; at full factor right03's selected SPR1311 has a
strictly separated q interval `[-0.0057160855, -0.0057160845] mm`. This is a
separate case and is used only as a second example of this mask-update
failure mode; no K12-right forces, acceptance, or case response are transferred
to A12-left.

There is currently no validated coupled solver method for this exact gated
law in the pinned CalculiX workflow. The manual and scalar spring coupon verify
the one-sided normal spring behavior; the fixed-mask adapter verifies exact
linear tangent constraints for an explicitly chosen mask. Neither verifies
simultaneous normal contact and release/recontact of unbounded exact tangent
constraints. A mathematical disjunctive formulation can state that law, but
that alone does not establish a solver implementation. Frictionless contact,
finite Coulomb friction, penalty stick, and permanent anchoring each change
the current assumption. Exhaustive fixed-mask solving with a complete gate
check would be decisive only after all masks were assessed; this report does
not do that for the 100-cell frame. Therefore leave the current A12-left
support branch unresolved for the affected loads. Do not promote either 10 or
11 cells, treat the update cycle as proof that the frame has no other branch,
loosen the strict criterion, substitute another support law, or infer physical
failure. A future method claim needs a known-answer fixture that demonstrates
the exact gate and reaction behavior in the selected solver path.

The cited frictionless result is limited to a no-friction variational
inequality. The cited primal-dual active-set paper solves complementarity
conditions for Tresca/Coulomb laws and reports local superlinear convergence;
it is method-class context only. The pinned [CalculiX 2.23 manual](../../../../../fea/generated/ccx_2.23.pdf)
(SHA-256 `a0bf3fc03f374912ff2bf28da3f7dfb6a61428dd7f41b281a2e7e1fdb318f330`,
sections 6.2.42 and 7.122) documents the nonlinear SPRINGA and tabular spring
behavior. The paired run record and emitted equations establish the applied
adapter semantics for this case.

## Discriminating hand fixture

`fixture-spec.json` is a three-DOF known-answer specification, not a solver
deck and not a verified native method. It preserves the same switch: two
exact tangent directions are tied together when the one-sided normal spring
is strictly positive, and released otherwise. The structural matrix is SPD,
the normal spring is monotone, and both fixed-mask equilibria close exactly.
Yet each equilibrium violates its own support gate, so the complete gated
problem has no static branch. This is a counterexample to guaranteed branch
existence for the idealized rule, not evidence that A12-left itself has no
other branch.

No geometry, loads, material, criteria, physical floor assumptions, or native
inputs were changed. No native solve was launched. This diagnosis adds no
friction test, support capacity, acceptance, or physical failure conclusion.

## Sources

- [Haslinger and Hlaváček, “Contact between elastic bodies. I. Continuous problems”](https://dml.cz/handle/10338.dmlcz/103868), *Aplikace matematiky* 25 (1980), pp. 324–347: unilateral contact without friction; displacement variational inequalities and existence/uniqueness discussion under stated conditions.
- [Hüeber, Stadler, and Wohlmuth, “A Primal-Dual Active Set Algorithm for Three-Dimensional Contact Problems with Coulomb Friction”](https://doi.org/10.1137/060671061), *SIAM Journal on Scientific Computing* 30 (2008): complementarity-function formulation for Tresca/Coulomb contact and local convergence results for that law.
- [Official CalculiX 2.23 manual](https://www.dhondt.de/ccx_2.23.pdf), sections 6.2.42 and 7.122; local pinned copy and hash recorded above.

`source-pins.json` binds the reported run inputs/outputs, the existing source-bound
cycle diagnoses, and the pinned manual. Both frozen A12-left source maps (103
attempt02 entries and 140 attempt03 entries), all 46 source-map entries of the
prior A12-left cycle diagnosis, and all 65 external entries of the K12-right
recurrence report were rehashed with zero mismatches on 2026-09-30.
