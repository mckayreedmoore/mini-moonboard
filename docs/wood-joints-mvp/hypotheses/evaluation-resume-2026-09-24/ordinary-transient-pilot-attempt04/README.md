# Longer bounded motion pilot with iteration diagnostics

This run retains the twelve physical/load artifacts of attempt03 byte for
byte, its 0.0025 s initial increment, adaptive stepping, and 0.025 s final
time. The input deck changes only the spelling of the same final-time value
and requests `LAST ITERATIONS,CONTACT ELEMENTS`. It does not split the
dynamic step or use a restart. Geometry, contact stiffness, materials,
engagement, loads and convergence controls remain unchanged.

The parent run budget is 2,400 seconds, four threads and 10 GiB. The earlier
600-second checkpoint stopped after 34 recorded iterations, before the native
default recovery at iteration 60. The [source review](../native-contact-recovery-review.md)
shows that this path retries with temporarily reduced contact stiffness and
requires original-stiffness reconvergence before accepting an increment. The
longer bound permits observing that existing algorithm; it guarantees neither
recovery nor completion. Verify the actual log before asserting that the
fallback occurred or that original stiffness was restored.

The checkpoint contact and trial-motion audits show changes on the initially
touching timber and bolt seating faces, open bolt bores, and a drifting trial
response. They do not justify dismissing the contact-count criterion or
accepting an unconverged field. This pilot retains those criteria.

The existing complete-sample motion limits remain in the frozen input record.
Its coarse first increment does not accurately integrate the sampled ramp;
discrete work/momentum accounting, time refinement, contact transfer and
clearance seating remain separate requirements. Execution status is governed
by `execution.json`. Neither successful execution nor solver convergence
establishes joint capacity or closes a service-load case.
