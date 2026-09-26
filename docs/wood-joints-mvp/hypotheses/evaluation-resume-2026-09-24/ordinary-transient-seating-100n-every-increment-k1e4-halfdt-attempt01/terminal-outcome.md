# Half-timestep diagnostic terminal outcome

The parent explicitly stopped this diagnostic to prioritize the paired
constraint-output check after reproducing the first-transition work and
contact-storage audits. This was not an OOM or runtime-limit stop.
`execution.json` records return code 137 after 5560.122 seconds;
its status `process_failed` describes that externally stopped process, not
a failed structural criterion. The 0.025 s target was not reached.

There are 43 accepted increments through 0.0206025 s and
1 rejected attempt. The final complete monitor has q =
0.916211153523 mm, maximum loaded displacement
0.748827925368 mm and maximum
controller rotation 0.000927412384 rad.
No sampled motion stop was triggered. The terminal validation verifies all
34 frozen input artifacts and 12 output hashes.

The immutable first-transition prefix remains separate from this terminal
output. At its 0.0195 s state the parent-reproduced source-conditional storage
bound leaves at least 0.142278622574 N mm outside the represented contact
envelope. The exact 0.019 s coarse/half-step comparison is available; no
accepted half-step 0.020 s state exists, so the requested same-time contact
comparison cannot be claimed. Independent audit reviews are finishing.

The stop does not establish a cause for the energy gap, time accuracy,
physical bolt engagement, quasistatic response, joint capacity or acceptance.
The frozen inputs and reviewed model are unchanged. Historical input-only
wording in the execution scope belongs to input preparation; it does not
negate this recorded diagnostic execution.

See `parent-stop-decision.json`, `execution.json`, and
`parent-terminal-validation.json` for the decision and artifact identities.
