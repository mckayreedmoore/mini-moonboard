# Independent review: early force-history prefix

The work and scalar impulse values in [report.json](report.json) reproduce
from the frozen prefix. This is an immutable, non-atomic capture from a live
run, not a terminal history or complete-joint/contact audit. The `.sta` file
contains two accepted increments (`0.001` and `0.002 s`) and no rejected
attempts. The DAT snapshot contains one complete 339-node monitor block at
each of those times; both match the accepted status times exactly after
decimal parsing. The later in-progress increment is outside the accepted
history in this snapshot.

I independently checked the snapshot's four file size/hash pins, its manifest
SHA-256 `015be6dfc6b81df69766d2754ee52a523fbd66ef1809d15c092be7e8f49b249e`,
and all 27 input artifacts against the input-freeze hash map. The recursive
`pilot.inp` include closure is eight files and each is among the pinned
artifacts. The emitted deck has one `*CLOAD,AMPLITUDE=RAMP_N` card with 662
nonzero scalar terms. Its node/DOF support matches the frozen 331-node unit
force pattern; each serialized load is 100 times its reference term, with
maximum scale-ratio deviation `1.5e-14`. The tabular ramp has 101 piecewise
linear points; its values at the accepted interval ends are `A(0)=0`,
`A(0.001)=0.000298`, and `A(0.002)=0.001184`.

Recomputing the complete-field virtual-work projection from the 339 DAT rows
gives `q=2.4127148817204604e-5 mm` at `0.001 s` and
`q=1.7898901164922133e-4 mm` at `0.002 s`. The component print-rounding
bounds reproduce the report. Applying
`Σ 0.5·(Aᵢ+Aᵢ₋₁)·(qᵢ−qᵢ₋₁)·100` gives cumulative discrete work
`3.5949451737634857e-7 N·mm` and `1.1834758553228786e-5 N·mm`. The native
log reports `3.594945e-7` and `1.183476e-5 N·mm`; residuals are respectively
`1.74e-14` and `−1.45e-12 N·mm`, inside the combined print bounds
`7.00e-13` and `1.89e-11 N·mm`.

The serialized load-factor integral is `1.49e-5 N·s` for `0–0.001 s` and
`7.41e-5 N·s` for `0.001–0.002 s`, totaling `8.90e-5 N·s`. Endpoint
trapezoids equal the piecewise-linear integral because both intervals end on
ramp knots. This is the scalar coefficient impulse multiplying the frozen
self-equilibrated nodal pattern; it is neither a net-resultant vector impulse
nor an impulse transferred through contact.

The work bounds cover printed displacement components, ramp-amplitude change
from printed DAT time, and native external-work rounding. They exclude solver
integration error and any difference between discrete work accounting and a
continuous-path work integral. The agreement verifies the captured force and
displacement accounting only; it does not establish contact equilibrium,
material validity, quasi-static behavior, seating, capacity, or mechanical
acceptance. The report records `mechanical_acceptance: false`.

The reported implementation pins reproduce: `audit.py` SHA-256
`e8f287377775bc7f8936dd6721401a8f4d4b749983f1558b602002ce451a24e3`,
history helper `7c8d3ff46161576f3ed13605e666c9ea3aba14bdeaa439ede52a7cab562f374c`,
and launcher observation parser
`d1e3feeb9352640f2a06dc1ad6cf40e1ce3b7bbd3f8b974113a39c041c4cdd7c`.
The report SHA-256 is
`fad4f7c2256de031503f5ffdd72e15747293a72132ae670cc5cf1ed1abce240f`.
