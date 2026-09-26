# Observed impact-triggered recovery in pilot04

This immutable [log prefix](pilot-log-prefix.txt) was copied while pilot04
was running. [Its record](observation.json) binds the exact prefix and frozen
input hashes. It ends before increment 2, attempt 3 begins iterating; it is
not a terminal execution record or an accepted second increment.

The first increment converged in eight iterations. During the second
increment, attempt 1 reached iteration 28 before an impact check requested
a maximum increment of 7.7707417e-5 s, one quarter of the current duration.
The first retry retained the original 3.1082967e-4 s duration and used
`kscale=100`. Attempt 2 restored the original stiffness after iteration 10,
but iteration 11 triggered another impact retry. Attempt 3 then applied the
smaller 7.7707417e-5 s duration and again began with scaled stiffness.
Restoration occurred; acceptance at that restored stiffness did not occur
in this prefix.

This is distinct from the iteration-60 slow-convergence route described in
the [recovery source review](../native-contact-recovery-review.md). In the
pinned CCX 2.21 source, `checkimpacts.f:150–157` requests a quarter-step cap
when the normalized change in energy residual is below −0.008 and the
contact-element count has not fallen below the increment-start count. That
branch identification is an inference from the logged cap ratio and pinned
source; the exact residual is not printed here. `checkconvergence.c` skips
applying the cap on the first face-to-face retry, then applies it on later
retries. Its original-stiffness reconvergence requirement remains in force.

Neither the additional contact elements under temporarily softened stiffness
nor the restoration message establishes convergence, load transfer, physical
contact onset, or joint capacity. Later results belong to pilot04's live and
eventual terminal execution record.
