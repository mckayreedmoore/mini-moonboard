# Native readiness review: first-point checkpoint

**Status: ready for the parent-controlled bounded diagnostic run.** This is a
setup review, not a native-result review or joint acceptance. The checkpoint
exists to capture and inspect the first converged transient point; it does not
replace the longer pilot or the joint evaluation.

The checkpoint changes four cards in `pilot.inp`: it sets
`TIME=TOTAL TIME` on `RAMP_N`, shortens the step end time from 0.025 s to
0.0025 s while retaining the 0.0025 s initial increment, requests
`LAST ITERATIONS,CONTACT ELEMENTS` in `*NODE FILE`, and adds
`*RESTART,WRITE,FREQUENCY=1`. The 12 common physical/load inputs are byte
identical to pilot03, including the mesh, materials, contact definition,
actuator, nut coupling, and output/analysis sets. No geometry or load change
was found.

For the fresh first step, local time and total time are both 0.0025 s, so the
amplitude is sampled at the same time as pilot03. This does not establish
first-point equivalence: changing the step period can change period-dependent
theta/internal-energy controls and the contact iteration path. Before reusing
the result, compare the first-point generalized displacement, energy terms,
convergence history, and generated per-iteration contact sets with
[pilot03](../ordinary-transient-pilot-attempt03/terminal-outcome.md). Pilot03
converged its first increment after 13 iterations; its second increment did
not complete before the external timeout. The log has no `divergence allowed`
message, so its iteration-dependent contact-element counts alone do not show
that the aleatoric removal branch ran. Do not infer random contact removal
from those counts.

The added file requests are diagnostic output. The pinned CalculiX 2.21 manual
describes `LAST ITERATIONS` as output for the last increment and
`CONTACT ELEMENTS` as per-iteration generated contact sets (§7.96).
`*RESTART,WRITE` writes at step end, so a `.rout` is available only if this
one-step checkpoint completes; it is not a mid-step recovery point or a
restart-read continuation. CalculiX also deletes an existing `.rout` before
its first write (§7.110), so preserve any result that must be retained before
reusing the job name. `TIME=TOTAL TIME` makes amplitude time continuous across
steps (§7.1), but this single first step does not validate a later continuation.

Manual: [`ccx_2.21.pdf`](../../../../../fea/generated/connection/ccx_2.21.pdf),
§§7.1, 7.96, 7.110. The bounded result can support inspection of this
diagnostic contact implementation only; solver convergence or a matching first
point does not establish physical thread behavior, capacity, or joint
acceptance.
